# Copyright (C) 2026 Vertel Sverige AB (<https://vertel.se>).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import json
from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

# Short-form chart types accepted in YAML (and by third-party authors) mapped
# to the canonical ``chart_type`` selection values. Keeps dashboards-as-code
# portable: ``type: line`` loads as ``line_chart`` instead of crashing.
CHART_TYPE_ALIASES = {
    "line": "line_chart",
    "bar": "bar_chart",
    "column": "column_chart",
    "area": "area_chart",
    "doughnut": "doughnut_chart",
    "pie": "pie_chart",
    "funnel": "funnel_chart",
    "pyramid": "pyramid_chart",
    "radar": "radar_chart",
    "radial": "radial_chart",
    "scatter": "scatter_chart",
    "stacked": "stackedcolumn_chart",
    "stackedcolumn": "stackedcolumn_chart",
    "meter": "meter_chart",
    "map": "map_chart",
    "sankey": "sankey_chart",
    "treemap": "treemap_chart",
    "sunburst": "sunburst_chart",
    "wordcloud": "wordcloud_chart",
}


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
    filter_field = fields.Char(
        string="Filter Field",
        help="Field (possibly dotted, e.g. 'account_id.media_type') used as the "
             "cross-chart filter key when a chart element is clicked. Defaults to "
             "the group_by field.",
    )

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
    previous_period_type = fields.Selection([("percentage", "Percentage"), ("value", "Value")], default="percentage")
    kpi_target_value = fields.Float(string="KPI Target Value", help="Target for KPI progress display.")

    # Email
    image = fields.Binary(string="Chart Image", attachment=True, copy=False,
                          help="Captured PNG of this chart (amCharts export) used in scheduled emails.")

    # State
    customized = fields.Boolean(default=False,
                               help="Set to True when user modifies via GUI. Prevents YAML overwrite.")

    company_id = fields.Many2one("res.company", default=lambda self: self.env.company)

    # ── Filter Mapping ──
    filter_mapping_ids = fields.One2many("dashboard.chart.filter_mapping", "chart_id")

    def action_open_dashboard(self):
        """Open the parent dashboard so this chart is shown in context."""
        self.ensure_one()
        dashboard = self.dashboard_id
        return {
            "type": "ir.actions.client",
            "tag": "dashboard_vrtl_amcharts",
            "params": {
                "record": dashboard.id,
                "dashboard_name": dashboard.name,
                "chart_id": self.id,
            },
            "target": "current",
        }

    def set_image(self, image_b64):
        """Store a captured chart PNG (base64, no data-URI prefix) for emails."""
        self.ensure_one()
        self.image = image_b64 or False
        return True

    def _get_active_filters(self, global_filters=None, cross_filters=None):
        """Build the effective filter dict for this chart's metric.

        Combines, in order of precedence (later wins):
        - the chart's own ``date_filter_option`` and ``group_by`` configuration
        - the chart's static ``domain``
        - global dashboard filters (date range, selection/many2one)
        - cross-chart / drill-down filters emitted by other charts

        Returns a dict ready to pass to ``dashboard.metric.get_data()``,
        e.g. ``{"date_from": ..., "date_to": ..., "group_by": ...,
        "domain": [[field, '=', value], ...]}``.
        """
        global_filters = global_filters or {}
        cross_filters = cross_filters or {}
        filters = {}

        # 1. Chart-level date filter option (e.g. "Last 30 Days")
        if self.date_filter_option and self.date_filter_option != "none":
            date_from, date_to = self._compute_date_range(self.date_filter_option)
            if date_from:
                filters["date_from"] = date_from
            if date_to:
                filters["date_to"] = date_to
            if self.date_filter_field_id:
                filters["date_field"] = self.date_filter_field_id.name

        # 2. Chart-level group by (e.g. "date_order:month")
        if self.group_by_id:
            group_by = self.group_by_id.name
            if self.time_range:
                group_by = "%s:%s" % (group_by, self.time_range)
            filters["group_by"] = group_by

        # 3. Chart-level static domain
        try:
            chart_domain = json.loads(self.domain or "[]")
        except (TypeError, ValueError):
            chart_domain = []
        if chart_domain:
            filters["domain"] = list(chart_domain)

        # 4. Global dashboard filters
        domain = filters.get("domain", [])
        for key, value in global_filters.items():
            if value in (None, "", False):
                continue
            if key in ("date_from", "date_to"):
                filters[key] = value
            elif key == "date_field":
                filters["date_field"] = value
            elif self._cross_filter_applicable(key):
                # selection / many2one filter: map key -> domain on the metric model
                domain.append([key, "=", value])
        if domain:
            filters["domain"] = domain

        # 5. Cross-chart / drill-down filters
        cross_domain = []
        for key, value in cross_filters.items():
            if value in (None, "", False):
                continue
            if key in ("date_from", "date_to", "date_field", "domain"):
                filters[key] = value
            elif self._cross_filter_applicable(key):
                cross_domain.append([key, "=", value])
            # else: field not usable on this metric's model — skip silently
        if cross_domain:
            filters["domain"] = filters.get("domain", []) + cross_domain

        # 6. Kanban charts request the rows/columns format from model sources
        if self.chart_type == "kanban":
            filters["format"] = "kanban"

        # 7. KPI previous-period comparison (evaluated by the metric layer)
        if self.previous_period_comparison:
            filters["comparison"] = "previous_period"
            filters["comparison_type"] = self.previous_period_type or "percentage"

        return filters

    def _cross_filter_applicable(self, field_name):
        """Return True if a cross/global filter field can be applied to this
        chart's metric model (field exists and is reachable via dotted path).

        Service and composite sources decide their own filter handling, so
        the filter is passed through for them.
        """
        metric = self.metric_id
        if not metric or metric.source_type != "model" or not metric.model_id:
            return True
        current = metric.model_id.sudo().model
        parts = str(field_name).split(".")
        for idx, part in enumerate(parts):
            field = self.env["ir.model.fields"].sudo().search([
                ("model_id.model", "=", current), ("name", "=", part),
            ], limit=1)
            if not field:
                return False
            if idx < len(parts) - 1:
                if field.ttype in ("many2one", "many2many", "one2many") and field.relation:
                    current = field.relation
                else:
                    return False
        return True

    def _compute_date_range(self, option):
        """Return ``(date_from, date_to)`` for a chart ``date_filter_option``."""
        today = fields.Date.context_today(self)
        if option == "today":
            return (today, today)
        if option == "this_week":
            return (today - timedelta(days=today.weekday()), today)
        if option == "this_month":
            return (today.replace(day=1), today)
        if option == "this_quarter":
            quarter_month = ((today.month - 1) // 3) * 3 + 1
            return (today.replace(month=quarter_month, day=1), today)
        if option == "this_year":
            return (today.replace(month=1, day=1), today)
        days = {
            "last_7_days": 7,
            "last_30_days": 30,
            "last_90_days": 90,
            "last_365_days": 365,
        }
        if option in days:
            return (today - timedelta(days=days[option]), today)
        return (False, False)

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
        chart_type = data.get("type")
        if chart_type in CHART_TYPE_ALIASES:
            chart_type = CHART_TYPE_ALIASES[chart_type]
        if chart_type not in dict(self._fields["chart_type"].selection):
            raise ValidationError(
                _("Unknown chart type '%s' for chart '%s'. Supported: %s") % (
                    chart_type, data.get("label", data.get("key")),
                    ", ".join(v for _, v in self._fields["chart_type"].selection)))
        comparison = data.get("comparison") == "previous_period"
        return {
            "key": data.get("key"), "name": data.get("label", data.get("key")),
            "metric_id": metric.id, "chart_type": chart_type,
            "group_by_id": self._resolve_field(data.get("config", {}).get("group_by")),
            "filter_field": data.get("config", {}).get("filter_field"),
            "sort_order": data.get("config", {}).get("sort", "desc"),
            "limit_record": data.get("config", {}).get("limit", 0),
            "drill_enabled": bool(data.get("drill")),
            "drill_path": data.get("drill", {}).get("path", []),
            "theme": data.get("theme", "material"),
            "previous_period_comparison": comparison,
            "previous_period_type": data.get("comparison_type", "percentage"),
            "kpi_target_value": data.get("config", {}).get("target", 0.0),
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
        if self.previous_period_comparison:
            d["comparison_type"] = self.previous_period_type
        if self.kpi_target_value:
            d.setdefault("config", {})["target"] = self.kpi_target_value
        return d


class DashboardChartFilterMapping(models.Model):
    _name = "dashboard.chart.filter_mapping"
    _description = "Chart Filter Mapping"

    chart_id = fields.Many2one("dashboard.chart", required=True, ondelete="cascade")
    filter_id = fields.Many2one("dashboard.filter", required=True, ondelete="cascade")
    compatible = fields.Boolean(default=True)
    param_mapping = fields.Json(help='{"from": "date_from", "to": "date_to"}')
