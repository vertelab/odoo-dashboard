# Copyright (C) 2026 Vertel Sverige AB.
# License AGPL-3.0 or later.

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    dashboard_ceo_active = fields.Boolean(
        "CEO Overview", config_parameter="dashboard_vrtl_finance.ceo_active", default=True)
    dashboard_cfo_daily_active = fields.Boolean(
        "CFO Daily", config_parameter="dashboard_vrtl_finance.cfo_daily_active", default=True)
    dashboard_cfo_monthly_active = fields.Boolean(
        "CFO Monthly", config_parameter="dashboard_vrtl_finance.cfo_monthly_active", default=True)
    dashboard_dept_active = fields.Boolean(
        "Department Spend", config_parameter="dashboard_vrtl_finance.dept_active", default=True)
    dashboard_bookkeeper_active = fields.Boolean(
        "Bookkeeper Workspace", config_parameter="dashboard_vrtl_finance.bookkeeper_active", default=True)
    dashboard_project_active = fields.Boolean(
        "Project Manager", config_parameter="dashboard_vrtl_finance.project_active", default=True)
    dashboard_sales_active = fields.Boolean(
        "Sales Manager", config_parameter="dashboard_vrtl_finance.sales_active", default=True)

    def set_values(self):
        super().set_values()
        mapping = {
            "ceo_overview": self.dashboard_ceo_active,
            "cfo_daily": self.dashboard_cfo_daily_active,
            "cfo_monthly": self.dashboard_cfo_monthly_active,
            "department_spend": self.dashboard_dept_active,
            "bookkeeper_workspace": self.dashboard_bookkeeper_active,
            "project_manager": self.dashboard_project_active,
            "sales_manager": self.dashboard_sales_active,
        }
        for key, active in mapping.items():
            dashboard = self.env["dashboard.dashboard"].search([("key", "=", key)], limit=1)
            if dashboard:
                dashboard.write({"menu_active": active})
                if dashboard.created_menu_id:
                    dashboard.created_menu_id.write({"active": active})
