# Copyright (C) 2026 Vertel Sverige AB (<https://vertel.se>).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Vertel Dashboard — Finance Sources",
    "version": "18.0.1.0.0",
    "category": "Reporting",
    "summary": "Adapters for 52 financial reports from mn_finance_insights as dashboard data sources",
    "author": "Vertel Sverige AB",
    "website": "https://vertel.se",
    "license": "AGPL-3",
    "depends": ["dashboard_vrtl", "mn_finance_insights"],
    "data": ["data/sources.xml"],
    "installable": True,
    "application": False,
    "auto_install": False,
}
