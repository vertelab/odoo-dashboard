# Copyright (C) 2026 Vertel Sverige AB (<https://vertel.se>).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models


class DashboardSourceMixin(models.AbstractModel):
    """Interface that all dashboard data sources must implement."""
    _name = "dashboard.source.mixin"
    _description = "Dashboard Source Interface"

    def get_schema(self):
        """Return the source's schema: measures, dimensions, filters, chart_types.

        Returns:
            dict: {
                "name": str, "description": str, "icon": str, "category": str,
                "measures": [{"name": str, "label": str, "type": str, "color": str}],
                "dimensions": [{"name": str, "label": str, "type": str}],
                "filters": [{"name": str, "label": str, "type": str, "default": any}],
                "chart_types": [str],
                "drill_enabled": bool,
                "security": {"respects_ir_rule": bool, "row_level": bool, "safe_for_shared_cache": bool},
                "interactions": {"emit_filters": [...], "accept_filters": [...], "drill": {...}},
            }
        """
        raise NotImplementedError("get_schema() must be implemented by the source.")

    def get_data(self, measures, dimensions, filters, options=None):
        """Fetch data for the requested measures and dimensions.

        Returns:
            dict: {"labels": [...], "series": [{"name": str, "values": [...]}], "rows": [...], "currency": {...}}
        """
        raise NotImplementedError("get_data() must be implemented by the source.")

    def get_drill_action(self, context):
        """Return an Odoo action for drill-down, or None."""
        return None


class DashboardSourceModel(models.AbstractModel):
    """Builtin source for direct Odoo model binding via _read_group()."""
    _name = "dashboard.source.model"
    _inherit = "dashboard.source.mixin"
    _description = "Builtin Odoo Model Source"

    def get_schema(self):
        return {
            "name": "Odoo Model",
            "description": "Direct binding to any Odoo model",
            "category": "Builtin",
            "measures": [],
            "dimensions": [],
            "filters": [],
            "chart_types": ["bar", "line", "pie", "kpi", "table"],
            "drill_enabled": True,
            "security": {"respects_ir_rule": True, "row_level": True, "safe_for_shared_cache": False},
            "interactions": {"emit_filters": [], "accept_filters": []},
        }

    def get_data(self, measures, dimensions, filters, options=None):
        """Delegate to dashboard.metric.get_data() which handles model sources."""
        metric_id = options.get("metric_id") if options else None
        if metric_id:
            return self.env["dashboard.metric"].browse(metric_id).get_data(filters)
        return {"labels": [], "series": []}

    def get_drill_action(self, context):
        return None


class DashboardSource(models.Model):
    """Registry of available data sources. Auto-populated from installed metrics and adapters."""
    _name = "dashboard.source"
    _description = "Dashboard Data Source Registry"

    name = fields.Char(required=True)
    technical_name = fields.Char(required=True)
    model_name = fields.Char(required=True, help="AbstractModel implementing dashboard.source.mixin")
    category = fields.Char()
    source_type = fields.Selection([("model", "Model"), ("service", "Service"), ("sql", "SQL")])
    is_active = fields.Boolean(default=True)
    is_builtin = fields.Boolean(default=False)
    schema_json = fields.Json()
    module_id = fields.Many2one("ir.module.module")

    def refresh_schema(self):
        for source in self:
            if source.model_name:
                try:
                    impl = self.env[source.model_name]
                    source.schema_json = impl.get_schema()
                except Exception:
                    pass

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records.refresh_schema()
        return records
