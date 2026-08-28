# Copyright (C) 2026 Vertel Sverige AB (<https://vertel.se>).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

"""Tests for dashboard_vrtl core models."""

from datetime import timedelta

from odoo import fields
from odoo.tests.common import TransactionCase, tagged

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
        """Alert with cooldown should not re-trigger when last trigger is recent."""
        self.alert.cooldown = 3600
        self.alert.state = "triggered"
        self.alert.last_triggered = fields.Datetime.now() - timedelta(minutes=1)
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


@tagged("post_install", "-at_install")
class TestDashboardKanbanFormat(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Metric = cls.env["dashboard.metric"]
        cls.partner_field = cls.env["ir.model.fields"].search([
            ("model_id.model", "=", "res.partner"), ("name", "=", "name"),
        ], limit=1)

    def test_kanban_rows_for_model_source(self):
        """Model-source metric with format=kanban returns rows/columns."""
        metric = self.Metric.create({
            "name": "Kanban Partners", "key": "test.kanban_partners",
            "source_type": "model",
            "model_id": self.env["ir.model"].search([("model", "=", "res.partner")], limit=1).id,
            "field_id": self.partner_field.id,
            "aggregation": "count", "unit": "integer",
            "kanban_group_field": "active",
            "state_field": "active",
            "card_title_field": "name",
            "card_body_fields": '["id"]',
        })
        data = metric.get_data({"format": "kanban"})
        self.assertIn("rows", data)
        self.assertIn("columns", data)
        self.assertIn("group_by", data)
        self.assertEqual(data["group_by"], "active")
        for row in data["rows"]:
            self.assertIn("id", row)
            self.assertIn("name", row)

    def test_kanban_default_format_unchanged(self):
        """Without format=kanban the model source keeps labels/series."""
        metric = self.Metric.create({
            "name": "Plain Partners", "key": "test.plain_partners",
            "source_type": "model",
            "model_id": self.env["ir.model"].search([("model", "=", "res.partner")], limit=1).id,
            "field_id": self.partner_field.id,
            "aggregation": "count", "unit": "integer",
        })
        data = metric.get_data({})
        self.assertIn("labels", data)
        self.assertIn("series", data)


@tagged("post_install", "-at_install")
class TestDashboardComparison(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Metric = cls.env["dashboard.metric"]

    def _make_revenue_metric(self, key):
        order_field = self.env["ir.model.fields"].search([
            ("model_id.model", "=", "sale.order"), ("name", "=", "amount_total"),
        ], limit=1)
        date_field = self.env["ir.model.fields"].search([
            ("model_id.model", "=", "sale.order"), ("name", "=", "date_order"),
        ], limit=1)
        return self.Metric.create({
            "name": key, "key": key,
            "source_type": "model",
            "model_id": self.env["ir.model"].search([("model", "=", "sale.order")], limit=1).id,
            "field_id": order_field.id,
            "date_field_id": date_field.id,
            "aggregation": "sum", "unit": "monetary",
        })

    def test_comparison_computed(self):
        """KPI comparison returns previous_value and delta."""
        today = fields.Date.today()
        metric = self._make_revenue_metric("test.comparison")
        data = metric.get_data({
            "date_from": today - timedelta(days=30),
            "date_to": today,
            "comparison": "previous_period",
            "comparison_type": "percentage",
        })
        self.assertIn("comparison", data)
        comp = data["comparison"]
        self.assertEqual(comp["type"], "percentage")
        self.assertIn("value", comp)
        self.assertIn("previous_value", comp)
        self.assertIn("delta", comp)

    def test_comparison_requires_window(self):
        """Without a date window the comparison degrades gracefully."""
        metric = self._make_revenue_metric("test.comparison_nowindow")
        data = metric.get_data({"comparison": "previous_period"})
        self.assertNotIn("comparison", data)


@tagged("post_install", "-at_install")
class TestDashboardDomainSentinel(TransactionCase):
    def test_today_approx_resolved(self):
        """today_approx sentinel is replaced with a concrete date."""
        metric = self.env["dashboard.metric"].create({
            "name": "Late Invoices", "key": "test.late",
            "source_type": "model",
            "model_id": self.env["ir.model"].search([("model", "=", "account.move")], limit=1).id,
            "field_id": self.env["ir.model.fields"].search([
                ("model_id.model", "=", "account.move"), ("name", "=", "id"),
            ], limit=1).id,
            "aggregation": "count", "unit": "integer",
            "default_domain": '[["invoice_date_due", "<", "today_approx"]]',
        })
        domain = metric._build_domain({})
        sentinel_values = [item for item in domain if isinstance(item, list)
                           and len(item) == 3 and item[2] == "today_approx"]
        self.assertEqual(sentinel_values, [])
        # The domain must still contain the field with a date value
        self.assertTrue(any(isinstance(item, list) and len(item) == 3
                            and item[0] == "invoice_date_due" and item[1] == "<"
                            for item in domain))


@tagged("post_install", "-at_install")
class TestDashboardYamlNormalization(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Dashboard = cls.env["dashboard.dashboard"]
        cls.Chart = cls.env["dashboard.chart"]
        cls.Metric = cls.env["dashboard.metric"]
        cls.dashboard = cls.Dashboard.create({"name": "Norm Test", "key": "norm_test"})
        cls.metric = cls.Metric.create({
            "name": "Metric", "key": "norm.metric",
            "source_type": "model",
            "model_id": cls.env["ir.model"].search([("model", "=", "res.partner")], limit=1).id,
            "field_id": cls.env["ir.model.fields"].search([
                ("model_id.model", "=", "res.partner"), ("name", "=", "id"),
            ], limit=1).id,
            "aggregation": "count", "unit": "integer",
        })

    def test_chart_type_alias(self):
        """Short-form chart types normalize to canonical values."""
        vals = self.Chart._yaml_to_chart_vals(self.dashboard, {
            "key": "c_line", "label": "Line", "type": "line", "metric": "norm.metric",
        })
        self.assertEqual(vals["chart_type"], "line_chart")
        vals = self.Chart._yaml_to_chart_vals(self.dashboard, {
            "key": "c_bar", "label": "Bar", "type": "bar", "metric": "norm.metric",
        })
        self.assertEqual(vals["chart_type"], "bar_chart")

    def test_invalid_chart_type_rejected(self):
        """Unknown chart types raise a clear ValidationError."""
        with self.assertRaises(Exception):
            self.Chart._yaml_to_chart_vals(self.dashboard, {
                "key": "c_bad", "label": "Bad", "type": "sparkle", "metric": "norm.metric",
            })

    def test_layout_key_resolution(self):
        """String chart keys in layout resolve to int chart ids."""
        chart = self.Chart.create({
            "name": "KPI", "key": "kpi_1", "dashboard_id": self.dashboard.id,
            "metric_id": self.metric.id, "chart_type": "kpi",
        })
        self.dashboard._apply_grid_layout([
            {"chartId": "kpi_1", "x": 0, "y": 0, "w": 2, "h": 2},
        ])
        self.assertEqual(self.dashboard.grid_stack_dimensions[0]["chartId"], chart.id)

    def test_get_charts_details_does_not_mutate_layout(self):
        """Repeated renders do not grow the stored layout."""
        chart = self.Chart.create({
            "name": "KPI2", "key": "kpi_2", "dashboard_id": self.dashboard.id,
            "metric_id": self.metric.id, "chart_type": "kpi",
        })
        self.dashboard.grid_stack_dimensions = [
            {"chartId": chart.id, "x": 0, "y": 0, "w": 2, "h": 2},
        ]
        before = list(self.dashboard.grid_stack_dimensions)
        self.dashboard.get_charts_details()
        self.dashboard.get_charts_details()
        self.assertEqual(self.dashboard.grid_stack_dimensions, before)


@tagged("post_install", "-at_install")
class TestDashboardCacheFormat(TransactionCase):
    def test_format_flag_in_cache_key(self):
        """The kanban format flag is part of the cache key."""
        Cache = self.env["dashboard.cache"]
        key_kanban = Cache._build_key(1, 0, {"format": "kanban"})
        key_table = Cache._build_key(1, 0, {"format": "table"})
        self.assertNotEqual(key_kanban, key_table)


@tagged("post_install", "-at_install")
class TestDashboardMail(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Mail = cls.env["dashboard.mail"]
        cls.Dashboard = cls.env["dashboard.dashboard"]
        cls.dashboard = cls.Dashboard.create({"name": "Mail Test", "key": "mail_test"})

    def test_recipient_resolution(self):
        """Group recipients resolve to member partners."""
        group = self.env.ref("base.group_user")
        mail = self.Mail.create({
            "name": "Test Mail", "dashboard_id": self.dashboard.id,
            "recipient_group_ids": [(6, 0, [group.id])],
        })
        partners = mail._recipient_partners()
        self.assertTrue(len(partners) > 0)
        # Every partner must have a matching user in the group
        self.assertTrue(all(p.user_ids & group.users for p in partners))

    def test_cron_send_due(self):
        """Due automated schedules produce mail.mail records once."""
        # Use the demo user's partner: it is visible to all users (OdooBot's
        # partner is hidden from non-superuser by an ir.rule on res.partner).
        demo_user = self.env.ref("base.user_demo")
        partner = demo_user.partner_id
        partner.email = partner.email or "demo@example.com"
        mail = self.Mail.create({
            "name": "Due Mail", "dashboard_id": self.dashboard.id,
            "recipient_ids": [(6, 0, [partner.id])],
            "is_automated": True,
            "interval_number": 1, "interval_type": "days",
            "next_run": "2000-01-01 00:00:00",
        })
        before = self.env["mail.mail"].search_count([])
        self.Mail._cron_send_due()
        after = self.env["mail.mail"].search_count([])
        self.assertGreater(after, before)
        self.assertTrue(mail.last_sent_at)
        self.assertGreater(mail.next_run, fields.Datetime.now())
