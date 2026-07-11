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
    model = fields.Char(help="Odoo model for many2one type, e.g. 'res.partner'")
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
