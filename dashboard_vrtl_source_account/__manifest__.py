# Copyright (C) 2026 Vertel Sverige AB (<https://vertel.se>).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Vertel Dashboard — Account Source",
    "version": "18.0.1.0.0",
    "category": "Reporting",
    "summary": "Account journal and financial data sources for Vertel Dashboard",
    "author": "Vertel Sverige AB",
    "website": "https://vertel.se",
    "license": "AGPL-3",
    "depends": ["dashboard_vrtl", "account"],
    "external_dependencies": {},
    "data": [
        "security/ir.model.access.csv",
        "data/dashboard_source_data.xml",
    ],
    "post_init_hook": "_post_init_load_dashboards",
    "installable": True,
    "application": False,
    "auto_install": False,
}
