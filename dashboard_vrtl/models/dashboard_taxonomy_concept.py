# Copyright (C) 2026 Vertel Sverige AB (<https://vertel.se>).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models


class DashboardTaxonomyConcept(models.Model):
    _name = "dashboard.taxonomy.concept"
    _description = "Taxonomy Concept (from taxonomier.se)"

    key = fields.Char(required=True, help="e.g. 'se-gaap.Nettoomsattning'")
    name = fields.Char(required=True)
    label_sv = fields.Char(help="Swedish label, e.g. 'Nettoomsättning'")
    label_en = fields.Char(help="English label, e.g. 'Net Revenue'")
    description = fields.Text()

    data_type = fields.Selection([
        ("monetary", "Monetary"), ("string", "String"), ("integer", "Integer"),
        ("float", "Float"), ("date", "Date"), ("boolean", "Boolean"),
    ])
    balance = fields.Selection([("debit", "Debit"), ("credit", "Credit")])
    period_type = fields.Selection([("instant", "Point in Time"), ("duration", "Period")])

    parent_id = fields.Many2one("dashboard.taxonomy.concept", string="Parent Concept")
    child_ids = fields.One2many("dashboard.taxonomy.concept", "parent_id")

    reference_name = fields.Char(help="Law reference, e.g. 'ÅRL'")
    reference_number = fields.Char(help="e.g. '1995:1554'")
    reference_chapter = fields.Char()
    reference_paragraph = fields.Char()

    taxonomy_source = fields.Char(help="Which taxonomy file/version this came from")
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ("unique_taxonomy_key", "UNIQUE(key)", "Taxonomy concept key must be unique."),
    ]
