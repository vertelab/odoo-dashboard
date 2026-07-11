# Copyright (C) 2026 Vertel Sverige AB (<https://vertel.se>).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import json
import os

import yaml

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
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
         ("120000", "2 Minutes"), ("300000", "5 Minutes"), ("900000", "15 Minutes")],
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
        return {
            "key": data["key"], "name": data.get("name", data["key"]),
            "icon": data.get("icon", "fa-chart-line"),
            "category": data.get("category", ""),
            "auto_reload_duration": str(data.get("auto_refresh", 300000)),
            "cache_ttl": data.get("cache_ttl", 300),
            "menu_mode": data.get("menu_mode", "submenu"),
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
        self.grid_stack_dimensions = layout_data

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

    def unlink(self):
        # Restore original menu actions before deleting dashboards
        for rec in self:
            if rec.menu_mode == "replace" and rec.replaces_menu_id and rec._original_menu_action:
                rec.replaces_menu_id.write({"action": rec._original_menu_action})
        return super().unlink()

    # ──────────────────────────────────────────────────────────────
    # Chart Data Retrieval
    # ──────────────────────────────────────────────────────────────

    def get_charts_details(self):
        """Return chart data and positioning for dashboard rendering."""
        self.check_access("read")
        charts = []
        grid = self.grid_stack_dimensions or []
        existing_ids = {g["chartId"] for g in grid}

        for chart in self.chart_ids:
            if chart.id not in existing_ids:
                pos = self._find_next_position(grid, 6)
                pos["chartId"] = chart.id
                grid.append(pos)
            else:
                pos = next(g for g in grid if g["chartId"] == chart.id)

            data, from_cache = self.env["dashboard.cache"].get_or_compute(
                chart.metric_id, self.env.user, chart._get_active_filters(),
                ttl=self.cache_ttl,
            )
            # Embed kanban config into data for KanbanView component
            chart_kanban_config = self._get_kanban_config(chart) if chart.chart_type == "kanban" else {}
            if chart_kanban_config and isinstance(data, dict) and data.get("type") != "error":
                data["kanban_config"] = chart_kanban_config

            charts.append({
                "id": str(chart.id), "name": chart.name,
                "chart_type": chart.chart_type, "theme": chart.theme or "material",
                "data": data,
                "background_color": chart.background_color,
                "x": pos.get("x", 0), "y": pos.get("y", 0),
                "w": pos.get("w", 6), "h": pos.get("h", 4),
            })

        return [int(self.auto_reload_duration), charts, self.name]

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
            "_drill_model": metric.model_id.model if metric.source_type == "model" else "",
            "_res_model": metric.model_id.model if metric.source_type == "model" else "",
        }

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


class DashboardMail(models.Model):
    _name = "dashboard.mail"
    _description = "Dashboard Mail Schedule"

    dashboard_id = fields.Many2one("dashboard.dashboard", required=True, ondelete="cascade")
    name = fields.Char(required=True)
    chart_ids = fields.Many2many("dashboard.chart")
    recipient_ids = fields.Many2many("res.partner", required=True)
    is_automated = fields.Boolean()
