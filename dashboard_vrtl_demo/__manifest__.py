# Copyright (C) 2026 Vertel Sverige AB (<https://vertel.se>).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Vertel Dashboard — Demo Data",
    "version": "18.0.1.0.0",
    "category": "Reporting",
    "summary": "Full demo dashboards for dashboard_vrtl built on Odoo demo data (model sources only)",
    "author": "Vertel Sverige AB",
    "website": "https://vertel.se",
    "license": "AGPL-3",
    "depends": ["dashboard_vrtl", "sale", "account", "crm", "project"],
    "data": ["data/dashboard_data.xml"],
    "demo": True,
    "installable": True,
    "application": False,
    "auto_install": False,
}
