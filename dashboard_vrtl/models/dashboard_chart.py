# Copyright (C) 2026 Vertel Sverige AB (<https://vertel.se>).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import json

from odoo import _, api, fields, models


class DashboardChart(models.Model):
    _name = "dashboard.chart"
    _description = "Dashboard Chart"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(required=True, translate=True)
    key = fields.Char(help="Unique key for YAML cross-referencing")
    active = fields.Boolean(default=True)
    dashboard_id = fields.Many2one("dashboard.dashboard", required=True, ondelete="cascade")

    metric_id = fields.Many2one("dashboard.metric", required=True,
                                help="The metric this chart visualizes")
    chart_type = fields.Selection([
        ("kpi", "KPI"), ("tile", "Tile View"),
        ("bar_chart", "Bar Chart"), ("column_chart", "Column Chart"),
        ("doughnut_chart", "Doughnut Chart"), ("area_chart", "Area Chart"),
        ("funnel_chart", "Funnel Chart"), ("pyramid_chart", "Pyramid Chart"),
        ("line_chart", "Line Chart"), ("pie_chart", "Pie Chart"),
        ("radar_chart", "Radar Chart"), ("stackedcolumn_chart", "StackedColumn"),
        ("radial_chart", "Radial Chart"), ("scatter_chart", "Scatter Chart"),
        ("map_chart", "Map Chart"), ("meter_chart", "Meter Chart"),
        ("sankey_chart", "Sankey Diagram"), ("treemap_chart", "Treemap"),
        ("sunburst_chart", "Sunburst"), ("wordcloud_chart", "Word Cloud"),
        ("table", "Table"), ("list", "List View"), ("to_do", "To Do"),
        ("kanban", "Kanban"),
    ], required=True, tracking=True)

    # Grouping
    group_by_id = fields.Many2one("ir.model.fields", string="Group By")
    sub_group_by_id = fields.Many2one("ir.model.fields", string="Sub Group By")
    time_range = fields.Selection([
        ("day", "Day"), ("week", "Week"), ("month", "Month"),
        ("quarter", "Quarter"), ("year", "Year"),
    ])

    # Sorting & limits
    sort_field_id = fields.Many2one("ir.model.fields")
    sort_order = fields.Selection([("asc", "Ascending"), ("desc", "Descending")], default="desc")
    limit_record = fields.Integer(default=0, help="0 = no limit")

    # Filters
    date_filter_field_id = fields.Many2one("ir.model.fields", string="Date Filter Field")
    date_filter_option = fields.Selection([
        ("none", "None"), ("today", "Today"), ("this_week", "This Week"),
        ("this_month", "This Month"), ("this_quarter", "This Quarter"),
        ("this_year", "This Year"), ("last_7_days", "Last 7 Days"),
        ("last_30_days", "Last 30 Days"), ("last_90_days", "Last 90 Days"),
        ("last_365_days", "Last 365 Days"),
    ], default="none")
    domain = fields.Text(default="[]")

    # Drill-down
    drill_enabled = fields.Boolean(default=True)
    drill_path = fields.Json(help="[{field: 'product_id', label: 'Product'}, ...]")

    # Access
    chart_group_ids = fields.Many2many("res.groups", "chart_group_rel", "chart_id", "group_id",
                                       string="Access Groups",
                                       help="Only these groups see this chart. Empty = all dashboard viewers.")

    # Appearance
    theme = fields.Selection([
        ("animated", "Animated"), ("frozen", "Frozen"), ("kelly", "Kelly"),
        ("material", "Material"), ("moonrise", "Moonrise"), ("spirited", "Spirited"),
    ], default="material")
    background_color = fields.Char()
    show_unit = fields.Boolean(default=True)
    unit_type = fields.Selection([("monetary", "Monetary"), ("custom", "Custom")], default="monetary")
    custom_unit = fields.Char()
    icon = fields.Char()
    font_color = fields.Char()
    font_size = fields.Integer(default=14)
    font_weight = fields.Selection([(str(i), str(i)) for i in range(100, 1001, 100)])

    # Comparison
    previous_period_comparison = fields.Boolean()
    previous_period_type = fields.Selection([("percentage", "Percentage"), ("value", "Value")])

    # State
    customized = fields.Boolean(default=False,
                               help="Set to True when user modifies via GUI. Prevents YAML overwrite.")

    company_id = fields.Many2one("res.company", default=lambda self: self.env.company)

    # ── Filter Mapping ──
    filter_mapping_ids = fields.One2many("dashboard.chart.filter_mapping", "chart_id")

    def _get_active_filters(self):
        """Get active filters for this chart from the dashboard context."""
        filters = {}
        # Global filter integration handled by dashboard-level component
        return filters

    # ──────────────────────────────────────────────────────────────
    # YAML Support
    # ──────────────────────────────────────────────────────────────

    @api.model
    def load_from_yaml(self, dashboard, data):
        key = data.get("key")
        existing = self.search([("key", "=", key), ("dashboard_id", "=", dashboard.id)], limit=1)
        if existing and existing.customized:
            return existing
        vals = self._yaml_to_chart_vals(dashboard, data)
        if existing:
            existing.write(vals)
            return existing
        vals["dashboard_id"] = dashboard.id
        return self.create(vals)

    def _yaml_to_chart_vals(self, dashboard, data):
        metric = self.env["dashboard.metric"].search([("key", "=", data.get("metric"))], limit=1)
        return {
            "key": data.get("key"), "name": data.get("label", data.get("key")),
            "metric_id": metric.id, "chart_type": data.get("type"),
            "group_by_id": self._resolve_field(data.get("config", {}).get("group_by")),
            "sort_order": data.get("config", {}).get("sort", "desc"),
            "limit_record": data.get("config", {}).get("limit", 0),
            "drill_enabled": bool(data.get("drill")),
            "drill_path": data.get("drill", {}).get("path", []),
            "theme": data.get("theme", "material"),
            "previous_period_comparison": data.get("comparison") == "previous_period",
        }

    def _resolve_field(self, field_ref):
        if not field_ref:
            return False
        parts = field_ref.rsplit(".", 1)
        model_name = parts[0] if len(parts) > 1 else ""
        field_name = parts[-1]
        model = self.env["ir.model"].sudo().search([("model", "=", model_name)], limit=1) if model_name else False
        domain = [("name", "=", field_name)]
        if model:
            domain.append(("model_id", "=", model.id))
        return self.env["ir.model.fields"].sudo().search(domain, limit=1).id

    def _chart_to_yaml_dict(self):
        d = {
            "key": self.key, "label": self.name, "metric": self.metric_id.key,
            "type": self.chart_type, "layout": {"x": 0, "y": 0, "w": 6, "h": 4},
            "theme": self.theme, "comparison": "previous_period" if self.previous_period_comparison else None,
        }
        if self.chart_type == "kanban":
            d["layout"] = {"x": 0, "y": 0, "w": 12, "h": 5}  # Kanban needs more space
        return d


class DashboardChartFilterMapping(models.Model):
    _name = "dashboard.chart.filter_mapping"
    _description = "Chart Filter Mapping"

    chart_id = fields.Many2one("dashboard.chart", required=True, ondelete="cascade")
    filter_id = fields.Many2one("dashboard.filter", required=True, ondelete="cascade")
    compatible = fields.Boolean(default=True)
    param_mapping = fields.Json(help='{"from": "date_from", "to": "date_to"}')
