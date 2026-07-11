# Copyright (C) 2026 Vertel Sverige AB (<https://vertel.se>).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import hashlib
import json

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval


class DashboardMetric(models.Model):
    _name = "dashboard.metric"
    _description = "Dashboard Metric Definition"
    _inherit = ["mail.thread"]

    name = fields.Char(required=True, translate=True)
    key = fields.Char(
        required=True,
        help="Unique key, e.g. 'sales.net_revenue'. Used for cross-referencing in YAML.",
    )
    description = fields.Text()
    category = fields.Char(help="Finance, Sales, HR, Inventory, etc.")
    active = fields.Boolean(default=True)

    # ── Source Definition ──
    source_type = fields.Selection(
        [("model", "Odoo Model"), ("sql", "Custom SQL"),
         ("service", "Service Source"), ("composite", "Composite")],
        required=True, default="model",
    )
    model_id = fields.Many2one("ir.model", string="Odoo Model")
    field_id = fields.Many2one("ir.model.fields", string="Field", domain="[('model_id','=',model_id)]")
    sql_query = fields.Text(help="SQL query for source_type=sql. Use %(param)s for parameters.")
    service_model = fields.Char(help="Technical model name for source_type=service, e.g. 'finance.dashboard'")
    service_method = fields.Char(help="Method name, e.g. '_chart_revenue_vs_expenses'")

    # ── Aggregation ──
    aggregation = fields.Selection(
        [("sum", "Sum"), ("avg", "Average"), ("count", "Count"),
         ("min", "Minimum"), ("max", "Maximum"), ("custom", "Custom")],
        default="sum",
    )
    default_domain = fields.Text(default="[]", help="Odoo domain as JSON string")
    date_field_id = fields.Many2one("ir.model.fields", string="Date Field")
    unit = fields.Selection(
        [("monetary", "Monetary"), ("percentage", "Percentage"),
         ("integer", "Integer"), ("float", "Float"), ("duration", "Duration")],
        default="float",
    )

    # ── Composite ──
    composite_formula = fields.Text(help="e.g. '{net_revenue} / {orders_count}'")
    composite_metric_ids = fields.Many2many("dashboard.metric", "metric_composite_rel",
                                            "metric_id", "composite_id")

    # ── Kanban Configuration ──
    state_field = fields.Char(help="Row column name for state, e.g. 'state'. Used by kanban charts.")
    state_colors = fields.Text(
        default='{}',
        help='JSON mapping state value → CSS color, e.g. {"active": "#28a745", "locked": "#6c757d"}',
    )
    state_icons = fields.Text(
        default='{}',
        help='JSON mapping state value → Font Awesome icon, e.g. {"active": "fa-check-circle"}',
    )
    card_title_field = fields.Char(help="Row column name for card title, e.g. 'name'")
    card_subtitle_field = fields.Char(help="Row column name for card subtitle, e.g. 'code'")
    card_body_fields = fields.Text(
        default='[]',
        help='JSON list of column names to display as KPI badges on card body',
    )
    card_footer_fields = fields.Text(
        default='[]',
        help='JSON list of column names to display in card footer',
    )
    card_actions = fields.Text(
        default='[]',
        help='JSON list of action definitions for inline buttons. Each: {name, label, icon, action, params, confirm?}',
    )
    kanban_group_field = fields.Char(help="Column name for grouping cards into columns, e.g. 'type'")
    kanban_draggable = fields.Boolean(
        default=False,
        help="Enable HTML5 drag-and-drop on kanban cards. When True, cards can be dragged between group columns.",
    )
    kanban_drag_group_field = fields.Char(
        help="Field to update when a card is dropped into a new column, e.g. 'journal_id'",
    )

    # ── Row-Level Security ──
    respects_ir_rule = fields.Boolean(default=True)
    row_level_security = fields.Boolean(default=True)
    safe_for_shared_cache = fields.Boolean(default=False)
    ir_rule_check_result = fields.Json()

    # ── Company ──
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company)

    _sql_constraints = [
        ("key_unique", "UNIQUE(key)", "Metric key must be unique."),
    ]

    # ──────────────────────────────────────────────────────────────
    # Data Retrieval
    # ──────────────────────────────────────────────────────────────

    def get_data(self, filters=None):
        """Return metric data for the given filters. Dispatches by source_type."""
        self.ensure_one()
        filters = filters or {}
        handler = {
            "model": self._get_data_model,
            "sql": self._get_data_sql,
            "service": self._get_data_service,
            "composite": self._get_data_composite,
        }
        return handler[self.source_type](filters)

    def _get_data_model(self, filters):
        """Use _read_group() for Odoo model aggregation. ir.rule applied automatically."""
        model_name = self.model_id.model
        field_name = self.field_id.name
        domain = self._build_domain(filters)

        groupby = [self.date_field_id.name] if self.date_field_id and filters.get("group_by_date") else []
        if filters.get("group_by"):
            groupby.insert(0, filters["group_by"])

        aggregates = [f"{field_name}:{self.aggregation}"]
        if self.aggregation == "count":
            aggregates = ["__count"]

        records = self.env[model_name].with_context(active_test=True)._read_group(
            domain=domain, groupby=groupby, aggregates=aggregates, limit=filters.get("limit", 1000),
        )
        if self.aggregation == "count":
            return {
                "labels": [r[0].display_name if hasattr(r[0], "display_name") else str(r[0]) for r in records],
                "series": [{"name": self.name, "values": [r[1] for r in records]}],
            }
        return {
            "labels": [r[0].display_name if hasattr(r[0], "display_name") else str(r[0]) for r in records],
            "series": [{"name": self.name, "values": [r[-1] for r in records]}],
        }

    def _get_data_sql(self, filters):
        """Execute SQL with security bridge."""
        if not self.respects_ir_rule and self.model_id:
            # Get authorized IDs via ORM
            records = self.env[self.model_id.model].search(self._build_domain(filters))
            authorized_ids = records.ids
            if not authorized_ids:
                return {"labels": [], "series": []}
            filters["authorized_ids"] = authorized_ids

        self.env.cr.execute(self.sql_query, self._prepare_sql_params(filters))
        rows = self.env.cr.fetchall()
        return {
            "labels": [r[0] for r in rows],
            "series": [{"name": self.name, "values": [r[1] for r in rows]}],
        }

    def _get_data_service(self, filters):
        """Delegate to a service AbstractModel."""
        service = self.env[self.service_model]
        method = getattr(service, self.service_method)
        return method(filters)

    def _get_data_composite(self, filters):
        """Evaluate composite formula."""
        values = {}
        for metric in self.composite_metric_ids:
            result = metric.get_data(filters)
            values[metric.key] = result.get("series", [{}])[0].get("values", [0])[0] if result.get("series") else 0
        result = safe_eval(self.composite_formula, values)
        return {
            "labels": [self.name],
            "series": [{"name": self.name, "values": [result]}],
        }

    def _build_domain(self, filters):
        domain = json.loads(self.default_domain or "[]")
        if self.company_id and "company_id" not in str(domain):
            domain.append(["company_id", "in", [self.company_id.id, False]])
        if filters.get("date_from") and self.date_field_id:
            domain.append([self.date_field_id.name, ">=", filters["date_from"]])
        if filters.get("date_to") and self.date_field_id:
            domain.append([self.date_field_id.name, "<=", filters["date_to"]])
        if filters.get("domain"):
            domain.extend(filters["domain"])
        return domain

    def _prepare_sql_params(self, filters):
        params = {"date_from": filters.get("date_from"), "date_to": filters.get("date_to"),
                  "company_id": self.company_id.id}
        if filters.get("authorized_ids"):
            params["authorized_ids"] = filters["authorized_ids"]
        return params

    # ──────────────────────────────────────────────────────────────
    # Row-Level Security Auto-Detection
    # ──────────────────────────────────────────────────────────────

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records:
            record._check_ir_rule_compatibility()
        return records

    def write(self, vals):
        result = super().write(vals)
        if any(f in vals for f in ("model_id", "source_type")):
            self._check_ir_rule_compatibility()
        return result

    def _check_ir_rule_compatibility(self):
        """Auto-detect row-level security based on ir.rule."""
        for metric in self:
            if metric.source_type == "model" and metric.model_id:
                rules = self.env["ir.rule"].sudo().search([
                    ("model_id", "=", metric.model_id.id), ("active", "=", True),
                ])
                if rules:
                    metric.row_level_security = True
                    metric.respects_ir_rule = True
                    metric.safe_for_shared_cache = False
                    metric.ir_rule_check_result = {
                        "rule_count": len(rules),
                        "rules": [{"name": r.name, "groups": r.groups.ids} for r in rules],
                    }
                else:
                    metric.row_level_security = False
                    metric.safe_for_shared_cache = True
            elif metric.source_type == "sql":
                metric.row_level_security = True
                metric.respects_ir_rule = False
                metric.safe_for_shared_cache = False
            elif metric.source_type == "service":
                try:
                    service = self.env[metric.service_model]
                    schema = service.get_schema()
                    sec = schema.get("security", {})
                    metric.respects_ir_rule = sec.get("respects_ir_rule", True)
                    metric.row_level_security = sec.get("row_level", True)
                    metric.safe_for_shared_cache = sec.get("safe_for_shared_cache", False)
                except Exception:
                    metric.row_level_security = True
                    metric.safe_for_shared_cache = False

    # ──────────────────────────────────────────────────────────────
    # YAML Support
    # ──────────────────────────────────────────────────────────────

    @api.model
    def load_from_yaml(self, data):
        key = data.get("key")
        if not key:
            return None
        existing = self.search([("key", "=", key)], limit=1)
        vals = self._yaml_to_metric_vals(data)
        if existing:
            existing.write(vals)
            return existing
        return self.create(vals)

    def _yaml_to_metric_vals(self, data):
        kanban = data.get("kanban", {})
        return {
            "key": data["key"], "name": data.get("label", data["key"]),
            "source_type": data.get("source_type", "model"),
            "model_id": self._resolve_model_ref(data.get("model")) if data.get("model") else False,
            "field_id": self._resolve_field_ref(data.get("model"), data.get("field")) if data.get("field") else False,
            "aggregation": data.get("aggregation", "sum"),
            "default_domain": json.dumps(data.get("domain", [])),
            "date_field_id": self._resolve_field_ref(data.get("model"), data.get("date_field")) if data.get("date_field") else False,
            "unit": data.get("unit", "float"),
            "sql_query": data.get("sql_query"),
            "service_model": data.get("service_model"),
            "service_method": data.get("service_method"),
            # Kanban fields
            "state_field": kanban.get("state_field"),
            "state_colors": json.dumps(kanban.get("state_colors", {})) if kanban.get("state_colors") else "{}",
            "state_icons": json.dumps(kanban.get("state_icons", {})) if kanban.get("state_icons") else "{}",
            "card_title_field": kanban.get("card_title_field"),
            "card_subtitle_field": kanban.get("card_subtitle_field"),
            "card_body_fields": json.dumps(kanban.get("card_body_fields", [])),
            "card_footer_fields": json.dumps(kanban.get("card_footer_fields", [])),
            "card_actions": json.dumps(kanban.get("card_actions", [])),
            "kanban_group_field": kanban.get("group_field"),
            "kanban_draggable": kanban.get("draggable", False),
            "kanban_drag_group_field": kanban.get("drag_group_field"),
        }

    def _resolve_model_ref(self, model_name):
        return self.env["ir.model"].sudo().search([("model", "=", model_name)], limit=1).id

    def _resolve_field_ref(self, model_name, field_name):
        if not model_name or not field_name:
            return False
        model = self.env["ir.model"].sudo().search([("model", "=", model_name)], limit=1)
        field = self.env["ir.model.fields"].sudo().search([
            ("model_id", "=", model.id), ("name", "=", field_name),
        ], limit=1)
        return field.id

    def _metric_to_yaml_dict(self):
        d = {
            "key": self.key, "label": self.name,
            "source_type": self.source_type,
            "model": self.model_id.model,
            "field": self.field_id.name,
            "aggregation": self.aggregation,
            "domain": json.loads(self.default_domain or "[]"),
            "date_field": self.date_field_id.name,
            "unit": self.unit,
        }
        # Include kanban config if any is set
        kanban = {}
        if self.state_field:
            kanban["state_field"] = self.state_field
        if self.state_colors and self.state_colors != "{}":
            kanban["state_colors"] = json.loads(self.state_colors)
        if self.state_icons and self.state_icons != "{}":
            kanban["state_icons"] = json.loads(self.state_icons)
        if self.card_title_field:
            kanban["card_title_field"] = self.card_title_field
        if self.card_subtitle_field:
            kanban["card_subtitle_field"] = self.card_subtitle_field
        if self.card_body_fields and self.card_body_fields != "[]":
            kanban["card_body_fields"] = json.loads(self.card_body_fields)
        if self.card_footer_fields and self.card_footer_fields != "[]":
            kanban["card_footer_fields"] = json.loads(self.card_footer_fields)
        if self.card_actions and self.card_actions != "[]":
            kanban["card_actions"] = json.loads(self.card_actions)
        if self.kanban_group_field:
            kanban["group_field"] = self.kanban_group_field
        if self.kanban_draggable:
            kanban["draggable"] = True
        if self.kanban_drag_group_field:
            kanban["drag_group_field"] = self.kanban_drag_group_field
        if kanban:
            d["kanban"] = kanban
        return d
