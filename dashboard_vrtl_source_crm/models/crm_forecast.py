# Copyright (C) 2026 Vertel Sverige AB.
# License AGPL-3.0 or later.

"""CRM weighted pipeline → revenue forecast adapter."""

from odoo import api, fields, models


class DashboardSourceCrmForecast(models.AbstractModel):
    _name = "dashboard.source.crm.forecast"
    _inherit = "dashboard.source.mixin"
    _description = "CRM Weighted Forecast"

    @api.model
    def get_schema(self):
        return {
            "measures": [
                {"name": "forecast_value", "label": "Weighted Forecast", "type": "monetary"},
                {"name": "pipeline_value", "label": "Pipeline Value", "type": "monetary"},
                {"name": "deal_count", "label": "Deal Count", "type": "integer"},
                {"name": "weighted_win_rate", "label": "Weighted Win Rate", "type": "percentage"},
            ],
            "dimensions": [
                {"name": "month", "label": "Expected Close Month"},
                {"name": "stage", "label": "Stage"},
                {"name": "team", "label": "Sales Team"},
                {"name": "user", "label": "Salesperson"},
            ],
            "filters": [
                {"name": "team_id", "label": "Sales Team", "type": "many2one", "model": "crm.team"},
                {"name": "user_id", "label": "Salesperson", "type": "many2one", "model": "res.users"},
            ],
            "chart_types": ["bar_chart", "line_chart", "funnel_chart", "kpi", "table"],
            "drill_enabled": True,
            "drill_model": "crm.lead",
            "filter_compatibility": {
                "period": {"compatible": False},
                "company": {"compatible": True},
            },
            "security": {"respects_ir_rule": True, "row_level": True, "safe_for_shared_cache": False},
        }

    @api.model
    def get_data(self, filters=None):
        filters = filters or {}
        domain = [("active", "=", True), ("probability", ">", 0), ("probability", "<", 100)]
        if filters.get("team_id"):
            domain.append(("team_id", "=", int(filters["team_id"])))
        if filters.get("user_id"):
            domain.append(("user_id", "=", int(filters["user_id"])))
        if filters.get("company_id"):
            domain.append(("company_id", "=", int(filters["company_id"])))

        leads = self.env["crm.lead"].search(domain)
        if not leads:
            return {"rows": [], "columns": ["stage", "forecast_value", "pipeline_value", "deal_count"]}

        # Weighted forecast: expected_revenue × probability / 100
        # Priority: stage.probability → lead.probability
        total_forecast = 0.0
        total_pipeline = 0.0
        by_stage = {}
        for lead in leads:
            prob = lead.stage_id.probability or lead.probability or 0
            value = lead.expected_revenue or 0
            weighted = value * prob / 100.0
            total_forecast += weighted
            total_pipeline += value
            stage_name = lead.stage_id.name or "Unknown"
            if stage_name not in by_stage:
                by_stage[stage_name] = {"forecast": 0, "pipeline": 0, "count": 0}
            by_stage[stage_name]["forecast"] += weighted
            by_stage[stage_name]["pipeline"] += value
            by_stage[stage_name]["count"] += 1

        rows = []
        for stage_name, vals in sorted(by_stage.items(), key=lambda x: x[1]["forecast"], reverse=True):
            rows.append({
                "stage": stage_name,
                "forecast_value": round(vals["forecast"], 2),
                "pipeline_value": round(vals["pipeline"], 2),
                "deal_count": vals["count"],
            })

        return {
            "rows": rows,
            "columns": ["stage", "forecast_value", "pipeline_value", "deal_count"],
            "units": {"forecast_value": "monetary", "pipeline_value": "monetary", "deal_count": "integer"},
            "totals": {
                "forecast_value": round(total_forecast, 2),
                "pipeline_value": round(total_pipeline, 2),
                "deal_count": len(leads),
            },
        }

    @api.model
    def get_drill_action(self, context=None):
        return {
            "type": "ir.actions.act_window",
            "res_model": "crm.lead",
            "views": [[False, "tree"], [False, "form"]],
        }
