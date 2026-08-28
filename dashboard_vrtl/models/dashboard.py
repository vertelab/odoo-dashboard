# Copyright (C) 2026 Vertel Sverige AB (<https://vertel.se>).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import json
import os

import yaml

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.http import request
from odoo.modules import get_module_path


class DashboardDashboard(models.Model):
    _name = "dashboard.dashboard"
    _description = "Dashboard"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    def _compute_chart_count(self):
        for dashboard in self:
            dashboard.chart_count = len(dashboard.chart_ids)

    name = fields.Char(required=True, tracking=True)
    key = fields.Char(
        required=True,
        help="Unique identifier for dashboard-as-code. Used as YAML filename and cross-reference key.",
        tracking=True,
    )
    description = fields.Text()
    icon = fields.Char(default="fa-chart-line")
    category = fields.Char(help="Grouping category: Sales, Finance, HR, etc.")

    chart_count = fields.Integer(compute="_compute_chart_count")
    chart_ids = fields.One2many("dashboard.chart", "dashboard_id", copy=False)
    filter_ids = fields.One2many("dashboard.filter", "dashboard_id", string="Global Filters")
    alert_ids = fields.One2many("dashboard.alert", "dashboard_id", string="Alert Rules")

    grid_stack_dimensions = fields.Json(default=[], copy=False)
    auto_reload_duration = fields.Selection(
        [("15000", "15 Seconds"), ("30000", "30 Seconds"), ("60000", "1 Minute"),
         ("120000", "2 Minutes"), ("300000", "5 Minutes"), ("900000", "15 Minutes"),
         ("1800000", "30 Minutes"), ("3600000", "1 Hour")],
        default="300000",
    )
    cache_ttl = fields.Integer(
        default=300,
        help="Cache TTL in seconds. Operational=30, Tactical=300, Strategic=900, Financial=3600.",
    )

    # Access
    access_by = fields.Selection([("access_group", "Access Groups"), ("user", "Users")])
    group_ids = fields.Many2many("res.groups", "dashboard_group_rel", "dashboard_id", "group_id")
    user_ids = fields.Many2many("res.users", "dashboard_user_rel", "dashboard_id", "user_id")

    # Menu
    parent_menu_id = fields.Many2one("ir.ui.menu", domain=[("action", "=", False)])
    created_menu_id = fields.Many2one("ir.ui.menu", copy=False, tracking=True)
    created_action_id = fields.Many2one("ir.actions.client", copy=False)
    menu_sequence = fields.Integer(default=1)
    menu_active = fields.Boolean(default=True)
    menu_mode = fields.Selection([
        ("submenu", "Submenu"),
        ("replace", "Replace Main Menu"),
    ], default="submenu", tracking=True,
        help="Submenu: dashboard appears as child under the parent menu. Replace: dashboard replaces the parent menu's default action.")
    replaces_menu_id = fields.Many2one("ir.ui.menu",
        help="When menu_mode=replace, this menu's action will be replaced by the dashboard.")
    _original_menu_action = fields.Char(
        help="Stored original action ref (e.g. 'ir.actions.act_window,123') for restoration.")

    # Email
    dashboard_mail_ids = fields.One2many("dashboard.mail", "dashboard_id")
    mail_cron_id = fields.Many2one("ir.cron", copy=False)

    company_id = fields.Many2one("res.company", default=lambda self: self.env.company)

    _sql_constraints = [
        ("key_unique", "UNIQUE(key)", "Dashboard key must be unique."),
    ]

    # ──────────────────────────────────────────────────────────────
    # YAML ↔ ORM Sync
    # ──────────────────────────────────────────────────────────────

    @api.model
    def load_from_yaml(self, yaml_path):
        """Load a dashboard from a YAML file, creating or updating ORM records."""
        with open(yaml_path) as f:
            data = yaml.safe_load(f)

        dash_data = data.get("dashboard", {})
        existing = self.search([("key", "=", dash_data.get("key"))], limit=1)

        vals = self._yaml_to_dashboard_vals(dash_data)
        if existing:
            existing.write(vals)
            dashboard = existing
        else:
            dashboard = self.create(vals)

        # Load metrics
        metric_obj = self.env["dashboard.metric"]
        for metric_data in data.get("metrics", []):
            metric_obj.load_from_yaml(metric_data)

        # Load filters
        for filter_data in data.get("filters", []):
            self._load_filter_from_yaml(dashboard, filter_data)

        # Load charts
        for chart_data in data.get("charts", []):
            self._load_chart_from_yaml(dashboard, chart_data)

        # Load alerts
        for alert_data in data.get("alerts", []):
            self._load_alert_from_yaml(dashboard, alert_data)

        # Create/update menu
        dashboard.create_update_menu()

        # Apply grid layout
        if data.get("layout"):
            dashboard._apply_grid_layout(data["layout"])

        return dashboard

    @api.model
    def load_from_module_yaml(self, module_name, relative_path):
        """Load a dashboard from a YAML file relative to a module directory."""
        module_path = get_module_path(module_name)
        if not module_path:
            raise ValidationError(_("Module not found: %s") % module_name)
        yaml_path = os.path.join(module_path, relative_path)
        return self.load_from_yaml(yaml_path)

    def export_to_yaml(self, filepath=None):
        """Export dashboard to YAML format."""
        self.ensure_one()
        output = {"dashboard": self._dashboard_to_yaml_dict()}
        if filepath:
            with open(filepath, "w") as f:
                yaml.dump(output, f, default_flow_style=False, allow_unicode=True)
        return yaml.dump(output, default_flow_style=False, allow_unicode=True)

    def _dashboard_to_yaml_dict(self):
        d = {
            "key": self.key, "name": self.name, "icon": self.icon,
            "category": self.category, "auto_refresh": self.auto_reload_duration,
            "cache_ttl": self.cache_ttl, "groups": self.group_ids.mapped("name"),
            "filters": [f._filter_to_yaml_dict() for f in self.filter_ids],
            "metrics": [m._metric_to_yaml_dict() for m in self.env["dashboard.metric"].search([])],
            "charts": [c._chart_to_yaml_dict() for c in self.chart_ids],
            "alerts": [a._alert_to_yaml_dict() for a in self.alert_ids],
        }
        if self.menu_mode:
            d["menu_mode"] = self.menu_mode
        if self.replaces_menu_id:
            d["replaces_menu"] = self.replaces_menu_id.xml_id or str(self.replaces_menu_id.id)
        return d

    def _yaml_to_dashboard_vals(self, data):
        parent_menu_id = False
        parent_menu = data.get("parent_menu")
        if parent_menu:
            if "." in parent_menu:
                menu = self.env.ref(parent_menu, raise_if_not_found=False)
            else:
                menu = self.env["ir.ui.menu"].search([("name", "=", parent_menu)], limit=1)
            parent_menu_id = menu.id if menu else False
        return {
            "key": data["key"], "name": data.get("name", data["key"]),
            "icon": data.get("icon", "fa-chart-line"),
            "category": data.get("category", ""),
            "auto_reload_duration": str(data.get("auto_refresh", 300000)),
            "cache_ttl": data.get("cache_ttl", 300),
            "menu_mode": data.get("menu_mode", "submenu"),
            "parent_menu_id": parent_menu_id,
            "menu_sequence": data.get("menu_sequence", 1),
        }

    def _load_filter_from_yaml(self, dashboard, data):
        # Implemented in dashboard_filter.py
        self.env["dashboard.filter"].load_from_yaml(dashboard, data)

    def _load_chart_from_yaml(self, dashboard, data):
        # Implemented in dashboard_chart.py
        self.env["dashboard.chart"].load_from_yaml(dashboard, data)

    def _load_alert_from_yaml(self, dashboard, data):
        # Implemented in dashboard_alert.py
        self.env["dashboard.alert"].load_from_yaml(dashboard, data)

    def _apply_grid_layout(self, layout_data):
        """Persist a grid layout, resolving string chart keys to chart ids.

        YAML layouts reference charts by their string ``key`` (e.g. ``chartId:
        kpi_revenue``) while the frontend and ``get_charts_details()`` work with
        int chart ids. Resolving at load time makes the declared layout apply
        from the first render.
        """
        layout = layout_data or []
        key_to_id = {c.key: c.id for c in self.chart_ids if c.key}
        resolved = []
        for entry in layout:
            chart_id = entry.get("chartId")
            if isinstance(chart_id, str) and chart_id in key_to_id:
                entry = {**entry, "chartId": key_to_id[chart_id]}
            resolved.append(entry)
        self.grid_stack_dimensions = resolved

    def _normalize_grid(self, grid):
        """Return a copy of ``grid`` with string chart keys resolved to int ids.

        Heals layouts stored before key-resolution existed (legacy YAML loads)
        without mutating the stored field.
        """
        key_to_id = {c.key: c.id for c in self.chart_ids if c.key}
        normalized = []
        for entry in grid:
            chart_id = entry.get("chartId")
            if isinstance(chart_id, str) and chart_id in key_to_id:
                entry = {**entry, "chartId": key_to_id[chart_id]}
            normalized.append(entry)
        return normalized

    # ──────────────────────────────────────────────────────────────
    # Menu Management
    # ──────────────────────────────────────────────────────────────

    def create_update_menu(self):
        for rec in self:
            action_data = {
                "name": rec.name,
                "tag": "dashboard_vrtl_amcharts",
                "params": {"record": rec.id, "dashboard_name": rec.name},
            }
            if not rec.created_action_id:
                action = self.env["ir.actions.client"].create({**action_data, "target": "current"})
                rec.created_action_id = action.id
            else:
                rec.created_action_id.write(action_data)

            action_ref = f"ir.actions.client,{rec.created_action_id.id}"

            if rec.menu_mode == "replace" and rec.replaces_menu_id:
                # Store original action before replacing
                if not rec._original_menu_action:
                    rec._original_menu_action = rec.replaces_menu_id.action
                rec.replaces_menu_id.write({"action": action_ref})
                # Also create a child menu so the dashboard appears in navigation
                menu_data = {
                    "name": rec.name, "action": action_ref,
                    "parent_id": rec.replaces_menu_id.id,
                    "sequence": rec.menu_sequence, "active": rec.menu_active,
                }
            else:
                # Restore original menu action if dashboard was previously replacing
                if rec._original_menu_action and rec.replaces_menu_id:
                    rec.replaces_menu_id.write({"action": rec._original_menu_action})
                    rec._original_menu_action = False
                menu_data = {
                    "name": rec.name, "action": action_ref,
                    "parent_id": rec.parent_menu_id.id,
                    "sequence": rec.menu_sequence, "active": rec.menu_active,
                }

            if not rec.created_menu_id:
                menu = self.env["ir.ui.menu"].create(menu_data)
                rec.created_menu_id = menu.id
            else:
                rec.created_menu_id.write(menu_data)

    def action_delete_menu(self):
        for rec in self:
            # Restore original menu action if we replaced it
            if rec.menu_mode == "replace" and rec.replaces_menu_id and rec._original_menu_action:
                rec.replaces_menu_id.write({"action": rec._original_menu_action})
            if rec.created_menu_id:
                rec.created_menu_id.unlink()
            if rec.created_action_id:
                rec.created_action_id.unlink()

    def action_open_dashboard(self):
        """Open this dashboard in the BI (amcharts) view."""
        self.ensure_one()
        return {
            "type": "ir.actions.client",
            "tag": "dashboard_vrtl_amcharts",
            "params": {"record": self.id, "dashboard_name": self.name},
            "target": "current",
        }

    def action_save_layout(self, layout):
        """Persist the grid layout from the edit mode.

        ``layout`` is a list of ``{"chartId": int, "x": int, "y": int,
        "w": int, "h": int}`` dicts as returned by GridStack.save().
        """
        self.ensure_one()
        self.write({"grid_stack_dimensions": layout or []})
        return True

    def action_set_brand_context(self, brand_id):
        """Set the focused brand in the session (brand context).

        Brand-aware models (via ``social.brand.focus.mixin``) then scope all
        their data to the selected brand — the same pattern the brand kanban
        root uses. Pass 0/False to clear the brand context.
        """
        self.ensure_one()
        request.session["social_brand_id"] = brand_id or False
        return True

    def unlink(self):
        # Restore original menu actions before deleting dashboards
        for rec in self:
            if rec.menu_mode == "replace" and rec.replaces_menu_id and rec._original_menu_action:
                rec.replaces_menu_id.write({"action": rec._original_menu_action})
        return super().unlink()

    # ──────────────────────────────────────────────────────────────
    # Chart Data Retrieval
    # ──────────────────────────────────────────────────────────────

    def get_charts_details(self, filters=None):
        """Return chart data, positioning and filter definitions for rendering.

        ``filters`` is an optional dict with:
        - ``global``: values of the dashboard's global filters (date range, etc.)
        - ``cross``: cross-chart / drill-down filters emitted by other charts
        """
        self.check_access("read")
        filters = filters or {}
        global_filters = filters.get("global", {}) or {}
        cross_filters = filters.get("cross", {}) or {}
        charts = []
        # Work on a copy: the stored layout must never be mutated in place
        # (repeated renders would otherwise append duplicate positions).
        grid = self._normalize_grid(list(self.grid_stack_dimensions or []))
        existing_ids = {g["chartId"] for g in grid}

        for chart in self.chart_ids:
            if chart.id not in existing_ids:
                pos = self._find_next_position(grid, 6)
                pos["chartId"] = chart.id
                grid.append(pos)
            else:
                pos = next(g for g in grid if g["chartId"] == chart.id)

            active_filters = chart._get_active_filters(
                global_filters=global_filters,
                cross_filters=cross_filters,
            )
            try:
                data, from_cache = self.env["dashboard.cache"].get_or_compute(
                    chart.metric_id, self.env.user, active_filters,
                    ttl=self.cache_ttl,
                )
            except Exception as exc:
                # One failing chart must not break the whole dashboard
                data = {"type": "error", "message": str(exc)}
            # Embed kanban config into data for KanbanView component
            chart_kanban_config = self._get_kanban_config(chart) if chart.chart_type == "kanban" else {}
            if chart_kanban_config and isinstance(data, dict) and data.get("type") != "error":
                data["kanban_config"] = chart_kanban_config

            charts.append({
                "id": str(chart.id), "name": chart.name,
                "chart_type": chart.chart_type, "theme": chart.theme or "material",
                "data": data,
                "background_color": chart.background_color,
                "kpi_target_value": chart.kpi_target_value,
                "group_by_field": chart.filter_field or (chart.group_by_id.name if chart.group_by_id else False),
                "x": pos.get("x", 0), "y": pos.get("y", 0),
                "w": pos.get("w", 6), "h": pos.get("h", 4),
            })

        filter_defs = [f._filter_to_dict() for f in self.filter_ids]
        return [int(self.auto_reload_duration), charts, self.name, filter_defs]

    def _find_next_position(self, items, width, columns=12):
        if not items:
            return {"x": 0, "y": 0, "w": width, "h": 4}
        last = max(items, key=lambda i: (i["y"], i["x"]))
        next_x = last["x"] + last.get("w", 6)
        if next_x + width <= columns:
            return {"x": next_x, "y": last["y"], "w": width, "h": 4}
        return {"x": 0, "y": last["y"] + last.get("h", 4), "w": width, "h": 4}

    def _get_kanban_config(self, chart):
        """Return kanban configuration dict from the chart's metric."""
        metric = chart.metric_id
        if not metric:
            return {}
        drill_model = self._get_drill_model(metric)
        return {
            "state_field": metric.state_field,
            "state_colors": metric.state_colors or "{}",
            "state_icons": metric.state_icons or "{}",
            "card_title_field": metric.card_title_field,
            "card_subtitle_field": metric.card_subtitle_field,
            "card_body_fields": metric.card_body_fields or "[]",
            "card_footer_fields": metric.card_footer_fields or "[]",
            "card_actions": metric.card_actions or "[]",
            "kanban_group_field": metric.kanban_group_field,
            "kanban_draggable": metric.kanban_draggable,
            "kanban_drag_group_field": metric.kanban_drag_group_field,
            "_drill_model": drill_model,
            "_res_model": drill_model,
        }

    def _get_drill_model(self, metric):
        """Resolve the drill-down model for a metric.

        - model sources: the bound Odoo model
        - service sources: the source schema's drill_model (if declared)
        """
        if metric.source_type == "model" and metric.model_id:
            return metric.model_id.model
        if metric.source_type == "service" and metric.service_model:
            try:
                schema = self.env[metric.service_model].get_schema()
                return schema.get("drill_model", "")
            except Exception:
                return ""
        return ""

    @api.model
    def validate_all(self):
        """Validate all dashboards. Returns list of issues."""
        issues = []
        for dashboard in self.search([]):
            for chart in dashboard.chart_ids:
                try:
                    data = chart.metric_id.get_data({})
                    if not data or (isinstance(data, dict) and data.get("type") == "error"):
                        issues.append(f"[{dashboard.key}] Chart '{chart.name}': no data")
                except Exception as e:
                    issues.append(f"[{dashboard.key}] Chart '{chart.name}': {e}")
        return issues

    def get_mail_capture_chart_ids(self):
        """Chart ids referenced by active mail schedules (PNG capture targets).

        The frontend exports these charts to PNG (amCharts) and stores them on
        ``dashboard.chart.image`` so the email cron can embed real images.
        """
        self.ensure_one()
        mails = self.dashboard_mail_ids.filtered(lambda m: m.is_automated and m.active)
        chart_ids = set()
        for mail in mails:
            chart_ids.update(mail.chart_ids.ids)
        return sorted(chart_ids)
