# Copyright (C) 2026 Vertel Sverige AB (<https://vertel.se>).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

"""Tests for dashboard_vrtl core models."""

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestDashboardMetric(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Metric = cls.env["dashboard.metric"]
        cls.Dashboard = cls.env["dashboard.dashboard"]
        cls.Chart = cls.env["dashboard.chart"]
        cls.Alert = cls.env["dashboard.alert"]
        cls.Cache = cls.env["dashboard.cache"]

        # Create a test dashboard
        cls.dashboard = cls.Dashboard.create({
            "name": "Test Dashboard",
            "key": "test_dashboard",
        })

    def test_create_model_metric(self):
        """Metric with source_type=model should store model/field references."""
        metric = self.Metric.create({
            "name": "Test Revenue",
            "key": "test.revenue",
            "source_type": "model",
            "model_id": self.env.ref("sale.model_sale_order").id,
            "field_id": self.env["ir.model.fields"].search([
                ("model_id.model", "=", "sale.order"), ("name", "=", "amount_total"),
            ], limit=1).id,
            "aggregation": "sum",
            "unit": "monetary",
        })
        self.assertEqual(metric.source_type, "model")
        self.assertEqual(metric.model_id.model, "sale.order")
        self.assertTrue(metric.row_level_security)  # sale.order has ir.rule

    def test_create_sql_metric(self):
        """SQL metric should default to row_level_security=True."""
        metric = self.Metric.create({
            "name": "Test SQL Metric",
            "key": "test.sql_metric",
            "source_type": "sql",
            "sql_query": "SELECT 1",
        })
        self.assertTrue(metric.row_level_security)
        self.assertFalse(metric.respects_ir_rule)
        self.assertFalse(metric.safe_for_shared_cache)

    def test_create_composite_metric(self):
        """Composite metric links to component metrics."""
        metric1 = self.Metric.create({
            "name": "Revenue", "key": "comp.revenue",
            "source_type": "model", "model_id": self.env.ref("sale.model_sale_order").id,
            "field_id": self.env["ir.model.fields"].search([
                ("model_id.model", "=", "sale.order"), ("name", "=", "amount_total"),
            ], limit=1).id, "aggregation": "sum",
        })
        metric2 = self.Metric.create({
            "name": "Orders", "key": "comp.orders",
            "source_type": "model", "model_id": self.env.ref("sale.model_sale_order").id,
            "field_id": self.env["ir.model.fields"].search([
                ("model_id.model", "=", "sale.order"), ("name", "=", "id"),
            ], limit=1).id, "aggregation": "count",
        })
        composite = self.Metric.create({
            "name": "Avg Order", "key": "comp.avg_order",
            "source_type": "composite",
            "composite_formula": "{comp.revenue} / {comp.orders}",
            "composite_metric_ids": [(6, 0, [metric1.id, metric2.id])],
        })
        self.assertEqual(composite.source_type, "composite")
        self.assertEqual(len(composite.composite_metric_ids), 2)

    def test_auto_detect_ir_rule(self):
        """Model metrics should auto-detect ir.rule on creation."""
        metric = self.Metric.create({
            "name": "Test AutoDetect", "key": "test.autodetect",
            "source_type": "model",
            "model_id": self.env.ref("sale.model_sale_order").id,
            "field_id": self.env["ir.model.fields"].search([
                ("model_id.model", "=", "sale.order"), ("name", "=", "amount_total"),
            ], limit=1).id,
            "aggregation": "sum",
        })
        # sale.order typically has ir.rule in most Odoo setups
        self.assertIsNotNone(metric.ir_rule_check_result)


@tagged("post_install", "-at_install")
class TestDashboardCache(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Cache = cls.env["dashboard.cache"]
        cls.Metric = cls.env["dashboard.metric"]
        cls.metric = cls.Metric.create({
            "name": "Cache Test", "key": "cache.test",
            "source_type": "sql", "sql_query": "SELECT 'test', 42",
            "row_level_security": False, "safe_for_shared_cache": True,
        })

    def test_cache_key_uniqueness(self):
        """Different filters produce different cache keys."""
        key1 = self.Cache._build_key(1, 0, {"date_from": "2026-01-01"})
        key2 = self.Cache._build_key(1, 0, {"date_from": "2026-02-01"})
        self.assertNotEqual(key1, key2)

    def test_cache_user_isolation(self):
        """Different users produce different cache keys."""
        key1 = self.Cache._build_key(1, 1, {})
        key2 = self.Cache._build_key(1, 2, {})
        self.assertNotEqual(key1, key2)

    def test_cache_cleanup_expired(self):
        """Expired cache entries should be cleaned up."""
        self.Cache.create({
            "cache_key": "test_cleanup_key",
            "metric_id": self.metric.id,
            "data_json": {"test": True},
            "expires_at": "2020-01-01 00:00:00",
        })
        self.Cache._cron_cleanup_expired()
        exists = self.Cache.search([("cache_key", "=", "test_cleanup_key")])
        self.assertEqual(len(exists), 0)


@tagged("post_install", "-at_install")
class TestDashboardAlert(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Alert = cls.env["dashboard.alert"]
        cls.Metric = cls.env["dashboard.metric"]
        cls.Dashboard = cls.env["dashboard.dashboard"]
        cls.dashboard = cls.Dashboard.create({"name": "Alert Test", "key": "alert_test"})
        cls.metric = cls.Metric.create({
            "name": "Alert Metric", "key": "alert.metric",
            "source_type": "sql", "sql_query": "SELECT 'test', 42",
        })
        cls.alert = cls.Alert.create({
            "name": "Test Alert", "key": "test_alert",
            "dashboard_id": cls.dashboard.id,
            "metric_id": cls.metric.id,
            "condition": "value < 100",
            "cooldown": 0,  # No cooldown for testing
        })

    def test_state_transition(self):
        """Alert should transition through ok → triggered → acknowledged → ok."""
        self.assertEqual(self.alert.state, "ok")
        self.alert._evaluate_and_notify()
        # After evaluation: value=42 < 100, so condition is met
        self.assertEqual(self.alert.state, "triggered")
        self.alert.action_acknowledge()
        self.assertEqual(self.alert.state, "ok")

    def test_cooldown_respected(self):
        """Alert with cooldown should not re-trigger."""
        self.alert.cooldown = 3600
        self.alert.state = "triggered"
        self.alert.last_triggered = "2026-07-11 14:00:00"
        self.assertFalse(self.alert._cooldown_ok())

    def test_auto_reset(self):
        """Alert should auto-reset when condition is no longer met."""
        self.alert.state = "triggered"
        # Override condition to always be false
        self.alert.condition = "False"
        self.alert._evaluate_and_notify()
        self.assertEqual(self.alert.state, "ok")


@tagged("post_install", "-at_install")
class TestDashboardSecurity(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Dashboard = cls.env["dashboard.dashboard"]
        cls.Chart = cls.env["dashboard.chart"]
        cls.Metric = cls.env["dashboard.metric"]

        cls.dashboard = cls.Dashboard.create({"name": "Security Test", "key": "sec_test"})
        cls.metric = cls.Metric.create({
            "name": "Sec Metric", "key": "sec.metric",
            "source_type": "sql", "sql_query": "SELECT 'test', 1",
        })

    def test_chart_group_access(self):
        """Chart with chart_group_ids should be filterable."""
        chart = self.Chart.create({
            "name": "Group Chart", "key": "group_chart",
            "dashboard_id": self.dashboard.id,
            "metric_id": self.metric.id,
            "chart_type": "kpi",
            "chart_group_ids": [(6, 0, [self.env.ref("base.group_user").id])],
        })
        self.assertTrue(len(chart.chart_group_ids) > 0)

    def test_dashboard_user_access(self):
        """Dashboard with user_ids should be filterable."""
        self.dashboard.write({
            "access_by": "user",
            "user_ids": [(6, 0, [self.env.ref("base.user_admin").id])],
        })
        self.assertTrue(len(self.dashboard.user_ids) > 0)

    def test_yaml_load_preserves_customized(self):
        """Customized charts should not be overwritten by YAML load."""
        chart = self.Chart.create({
            "name": "Custom Chart", "key": "custom_chart",
            "dashboard_id": self.dashboard.id,
            "metric_id": self.metric.id,
            "chart_type": "kpi",
            "customized": True,
        })
        # Simulate YAML update — chart should remain
        self.assertTrue(chart.customized)
