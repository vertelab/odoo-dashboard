# Copyright (C) 2026 Vertel Sverige AB (<https://vertel.se>).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Vertel Dashboard — Sales",
    "version": "18.0.1.0.0",
    "category": "Reporting",
    "summary": "Pre-built sales dashboards for dashboard_vrtl",
    "author": "Vertel Sverige AB",
    "website": "https://vertel.se",
    "license": "AGPL-3",
    "depends": ["dashboard_vrtl", "sale"],
    "data": ["data/dashboard_data.xml"],
    "installable": True,
    "application": False,
    "auto_install": False,
}
