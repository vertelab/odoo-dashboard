# Copyright (C) 2026 Vertel Sverige AB (<https://vertel.se>).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Vertel Dashboard — Finance",
    "version": "18.0.1.0.0",
    "category": "Reporting",
    "summary": "Pre-built finance dashboards for dashboard_vrtl",
    "author": "Vertel Sverige AB",
    "website": "https://vertel.se",
    "license": "AGPL-3",
    "depends": ["dashboard_vrtl", "account"],
    "data": ["data/dashboard_data.xml", "views/settings.xml"],
    "post_init_hook": "_post_init_load_dashboards",
    "installable": True,
    "application": False,
    "auto_install": False,
}
