# Copyright (C) 2026 Vertel Sverige AB (<https://vertel.se>).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models


class DashboardFilter(models.Model):
    _name = "dashboard.filter"
    _description = "Dashboard Global Filter"

    dashboard_id = fields.Many2one("dashboard.dashboard", required=True, ondelete="cascade")
    key = fields.Char(required=True, help="e.g. 'period', 'customer', 'company'")
    name = fields.Char(required=True, translate=True)
    filter_type = fields.Selection([
        ("date_range", "Date Range"), ("many2one", "Many2One"),
        ("companies", "Companies"), ("selection", "Selection"),
    ], required=True, default="date_range")
    model = fields.Char(help="Technical Odoo model name for many2one type, e.g. 'res.partner'")
    model_id = fields.Many2one(
        "ir.model", string="Filter Model",
        help="Model whose records this filter selects (many2one type).")
    field = fields.Char(
        string="Filter Field",
        help="Field name on the metric/chart models that this filter maps to "
             "(e.g. 'brand_id', 'account_id'). The selected value is applied as "
             "[field, '=', value] on compatible charts.")
    field_id = fields.Many2one(
        "ir.model.fields", string="Filter Field (picker)",
        domain="[('model_id','=', model_id or False)]",
        help="Convenience picker for the filter field. Syncs into the field name.")
    optional = fields.Boolean(default=True)
    sequence = fields.Integer(default=10)
    default_from = fields.Char(help="Default 'from' for date_range, e.g. 'this_year_start'")
    default_to = fields.Char(help="Default 'to' for date_range, e.g. 'today'")
    shortcuts = fields.Json(help='[{"label":"This Month","from":"this_month_start","to":"today"}]')

    chart_filter_mapping_ids = fields.One2many("dashboard.chart.filter_mapping", "filter_id")

    def load_from_yaml(self, dashboard, data):
        existing = self.search([("key", "=", data["key"]), ("dashboard_id", "=", dashboard.id)], limit=1)
        vals = {
            "key": data["key"], "name": data.get("label", data["key"]),
            "filter_type": data.get("type", "date_range"),
            "model": data.get("model"), "optional": data.get("optional", True),
            "sequence": data.get("sequence", 10),
            "default_from": data.get("default", {}).get("from") if isinstance(data.get("default"), dict) else None,
            "default_to": data.get("default", {}).get("to") if isinstance(data.get("default"), dict) else None,
            "shortcuts": data.get("shortcuts", []),
        }
        # Resolve model_id / field_id (many2one & selection filters)
        if data.get("model"):
            model_rec = self.env["ir.model"].sudo().search([("model", "=", data["model"])], limit=1)
            if model_rec:
                vals["model_id"] = model_rec.id
        if data.get("field"):
            vals["field"] = data["field"]
            field = self.env["ir.model.fields"].sudo().search([
                ("model_id.model", "=", vals.get("model") or data.get("model")),
                ("name", "=", data["field"]),
            ], limit=1)
            if field:
                vals["field_id"] = field.id
        if existing:
            existing.write(vals)
            return existing
        vals["dashboard_id"] = dashboard.id
        return self.create(vals)

    def _filter_to_yaml_dict(self):
        return {
            "key": self.key, "label": self.name, "type": self.filter_type,
            "model": self.model, "optional": self.optional,
            "default": {"from": self.default_from, "to": self.default_to} if self.default_from else None,
            "shortcuts": self.shortcuts,
        }

    def _filter_to_dict(self):
        """Serialize the filter for the dashboard frontend (filter bar)."""
        self.ensure_one()
        return {
            "key": self.key,
            "name": self.name,
            "type": self.filter_type,
            "model": self.model or (self.model_id.model if self.model_id else False),
            "model_id": self.model_id.id if self.model_id else False,
            "field": self.field or (self.field_id.name if self.field_id else False),
            "optional": self.optional,
            "default_from": self.default_from,
            "default_to": self.default_to,
            "shortcuts": self.shortcuts or [],
        }
