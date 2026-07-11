{
    "name": "Vertel Dashboard — CRM Source",
    "version": "18.0.1.0.0",
    "category": "Reporting",
    "summary": "CRM pipeline forecast data source for Vertel Dashboard",
    "author": "Vertel Sverige AB",
    "website": "https://vertel.se",
    "license": "AGPL-3",
    "depends": ["dashboard_vrtl", "crm"],
    "data": [
        "security/ir.model.access.csv",
        "data/dashboard_source_data.xml",
    ],
    "installable": True,
    "auto_install": False,
}
