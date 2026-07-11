# Copyright (C) 2026 Vertel Sverige AB.
# License AGPL-3.0 or later.

"""Project P&L, WIP, and Budget adapters for Vertel Dashboard."""

from odoo import api, fields, models


class DashboardSourceProjectMargin(models.AbstractModel):
    _name = "dashboard.source.project.margin"
    _inherit = "dashboard.source.mixin"
    _description = "Project Margin (P&L)"

    @api.model
    def get_schema(self):
        return {
            "measures": [
                {"name": "revenue", "label": "Revenue", "type": "monetary"},
                {"name": "cost", "label": "Cost", "type": "monetary"},
                {"name": "margin", "label": "Margin", "type": "monetary"},
                {"name": "margin_pct", "label": "Margin %", "type": "percentage"},
            ],
            "dimensions": [
                {"name": "project", "label": "Project"},
                {"name": "month", "label": "Month"},
            ],
            "filters": [
                {"name": "project_id", "label": "Project", "type": "many2one", "model": "project.project"},
            ],
            "chart_types": ["bar_chart", "line_chart", "kpi", "table"],
            "drill_enabled": True,
            "drill_model": "project.project",
            "security": {"respects_ir_rule": True, "row_level": True, "safe_for_shared_cache": False},
        }

    @api.model
    def get_data(self, filters=None):
        filters = filters or {}
        domain = []
        if filters.get("project_id"):
            domain.append(("account_id", "=", int(filters["project_id"])))

        # Revenue: negative amounts (credit side in analytic)
        rev_result = self.env["account.analytic.line"]._read_group(
            domain=domain + [("amount", "<", 0)],
            groupby=[], aggregates=["amount:sum"],
        )
        # Cost: positive amounts (debit side in analytic)
        cost_result = self.env["account.analytic.line"]._read_group(
            domain=domain + [("amount", ">", 0)],
            groupby=[], aggregates=["amount:sum"],
        )
        revenue = abs(rev_result[0][0]) if rev_result and rev_result[0][0] else 0
        cost = cost_result[0][0] if cost_result and cost_result[0][0] else 0
        margin = revenue - cost
        margin_pct = (margin / revenue * 100) if revenue else 0

        return {
            "rows": [{
                "revenue": round(revenue, 2),
                "cost": round(cost, 2),
                "margin": round(margin, 2),
                "margin_pct": round(margin_pct, 1),
            }],
            "columns": ["revenue", "cost", "margin", "margin_pct"],
            "units": {"revenue": "monetary", "cost": "monetary", "margin": "monetary", "margin_pct": "percentage"},
        }

    @api.model
    def get_drill_action(self, context=None):
        return {"type": "ir.actions.act_window", "res_model": "project.project",
                "views": [[False, "form"]]}


class DashboardSourceProjectWip(models.AbstractModel):
    _name = "dashboard.source.project.wip"
    _inherit = "dashboard.source.mixin"
    _description = "Project WIP (Work In Progress)"

    @api.model
    def get_schema(self):
        return {
            "measures": [
                {"name": "unbilled_hours", "label": "Unbilled Hours", "type": "float"},
                {"name": "unbilled_cost", "label": "Unbilled Cost", "type": "monetary"},
            ],
            "dimensions": [
                {"name": "project", "label": "Project"},
                {"name": "aging_bucket", "label": "Aging"},
            ],
            "filters": [
                {"name": "project_id", "label": "Project", "type": "many2one", "model": "project.project"},
            ],
            "chart_types": ["bar_chart", "table", "kpi"],
            "drill_enabled": True,
            "drill_model": "account.analytic.line",
            "security": {"respects_ir_rule": True, "row_level": True, "safe_for_shared_cache": False},
        }

    @api.model
    def get_data(self, filters=None):
        filters = filters or {}
        domain = [("timesheet_invoice_id", "=", False)]
        if filters.get("project_id"):
            domain.append(("account_id", "=", int(filters["project_id"])))

        lines = self.env["account.analytic.line"]._read_group(
            domain=domain, groupby=[], aggregates=["unit_amount:sum", "amount:sum"],
        )
        hours = lines[0][0] if lines and lines[0][0] else 0
        cost = lines[0][1] if lines and lines[0][1] else 0

        return {
            "rows": [{"unbilled_hours": round(hours, 1), "unbilled_cost": round(cost, 2)}],
            "columns": ["unbilled_hours", "unbilled_cost"],
            "units": {"unbilled_hours": "float", "unbilled_cost": "monetary"},
        }

    @api.model
    def get_drill_action(self, context=None):
        return {"type": "ir.actions.act_window", "res_model": "account.analytic.line",
                "views": [[False, "tree"], [False, "form"]]}


class DashboardSourceProjectBudget(models.AbstractModel):
    _name = "dashboard.source.project.budget"
    _inherit = "dashboard.source.mixin"
    _description = "Project Budget vs Actual"

    @api.model
    def get_schema(self):
        return {
            "measures": [
                {"name": "budget", "label": "Budget", "type": "monetary"},
                {"name": "actual", "label": "Actual", "type": "monetary"},
                {"name": "variance", "label": "Variance", "type": "monetary"},
                {"name": "variance_pct", "label": "Variance %", "type": "percentage"},
            ],
            "dimensions": [
                {"name": "project", "label": "Project"},
            ],
            "filters": [
                {"name": "project_id", "label": "Project", "type": "many2one", "model": "project.project"},
            ],
            "chart_types": ["bar_chart", "kpi", "table"],
            "drill_enabled": True,
            "drill_model": "project.project",
            "security": {"respects_ir_rule": True, "row_level": True, "safe_for_shared_cache": False},
        }

    @api.model
    def get_data(self, filters=None):
        filters = filters or {}
        domain = []
        if filters.get("project_id"):
            domain.append(("account_id", "=", int(filters["project_id"])))

        # Actual costs from analytic lines
        actual_result = self.env["account.analytic.line"]._read_group(
            domain=domain + [("amount", ">", 0)],
            groupby=[], aggregates=["amount:sum"],
        )
        actual = actual_result[0][0] if actual_result and actual_result[0][0] else 0

        # Budget from crossovered.budget.lines if available
        budget = 0.0
        if filters.get("project_id"):
            project = self.env["project.project"].browse(int(filters["project_id"]))
            if project.analytic_account_id:
                budget_lines = self.env["crossovered.budget.lines"].search([
                    ("analytic_account_id", "=", project.analytic_account_id.id),
                ])
                budget = sum(budget_lines.mapped("planned_amount"))

        variance = budget - actual
        variance_pct = (variance / budget * 100) if budget else 0

        return {
            "rows": [{
                "budget": round(budget, 2),
                "actual": round(actual, 2),
                "variance": round(variance, 2),
                "variance_pct": round(variance_pct, 1),
            }],
            "columns": ["budget", "actual", "variance", "variance_pct"],
            "units": {"budget": "monetary", "actual": "monetary", "variance": "monetary", "variance_pct": "percentage"},
        }

    @api.model
    def get_drill_action(self, context=None):
        return {"type": "ir.actions.act_window", "res_model": "project.project",
                "views": [[False, "form"]]}
