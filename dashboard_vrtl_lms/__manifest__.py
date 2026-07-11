# Copyright (C) 2026 Vertel Sverige AB (<https://vertel.se>).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Vertel Dashboard — eLearning",
    "version": "18.0.1.0.0",
    "category": "Education",
    "summary": "eLearning course: Build BI dashboards with dashboard_vrtl",
    "author": "Vertel Sverige AB",
    "website": "https://vertel.se",
    "license": "AGPL-3",
    "depends": ["dashboard_vrtl", "website_slides"],
    "data": [
        "security/ir.model.access.csv",
        "data/slide_channel.xml",
        "data/slide_slides.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
