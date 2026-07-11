# Copyright (C) 2026 Vertel Sverige AB (<https://vertel.se>).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

"""Account journal kanban data source for Vertel Dashboard."""

from odoo import _, api, fields, models


class DashboardSourceAccountJournals(models.AbstractModel):
    _name = "dashboard.source.account.journals"
    _inherit = "dashboard.source.mixin"
    _description = "Account Journals"

    # ── Source Interface ──

    @api.model
    def get_schema(self):
        return {
            "measures": [
                {"name": "pending_moves", "label": "Pending Moves", "type": "integer"},
                {"name": "total_debit", "label": "Total Debit", "type": "monetary"},
                {"name": "total_credit", "label": "Total Credit", "type": "monetary"},
                {"name": "balance", "label": "Balance", "type": "monetary"},
            ],
            "dimensions": [
                {"name": "id", "label": "ID"},
                {"name": "name", "label": "Journal Name"},
                {"name": "code", "label": "Code"},
                {"name": "type", "label": "Journal Type"},
                {"name": "state", "label": "State"},
                {"name": "last_activity", "label": "Last Activity", "type": "datetime"},
            ],
            "filters": [
                {"name": "type", "label": "Journal Type", "type": "selection",
                 "options": ["sale", "purchase", "bank", "cash", "general"]},
                {"name": "company_id", "label": "Company", "type": "many2one", "model": "res.company"},
            ],
            "chart_types": ["kanban", "table", "kpi", "bar_chart"],
            "drill_enabled": True,
            "drill_model": "account.journal",
            "filter_compatibility": {
                "period": {"compatible": False},
                "company": {"compatible": True, "mapping": {"value": "company_id"}},
            },
            "kanban_defaults": {
                "state_field": "state",
                "state_colors": {"active": "#28a745", "locked": "#6c757d"},
                "state_icons": {"active": "fa-check-circle", "locked": "fa-lock"},
                "card_title_field": "name",
                "card_subtitle_field": "type",
                "card_body_fields": ["pending_moves", "balance"],
                "card_footer_fields": ["last_activity"],
                "card_actions": [
                    {
                        "name": "new_move", "label": "New Entry", "icon": "fa-plus",
                        "action": "ir.actions.act_window",
                        "params": {"res_model": "account.move", "views": [[False, "form"]],
                                   "context": {"default_journal_id": "{id}"}},
                    },
                    {
                        "name": "view_journal", "label": "Open Journal", "icon": "fa-book",
                        "action": "ir.actions.act_window",
                        "params": {"res_model": "account.journal", "res_id": "{id}",
                                   "views": [[False, "form"]]},
                    },
                ],
                "kanban_group_field": "type",
            },
            "security": {
                "respects_ir_rule": True,
                "row_level": True,
                "safe_for_shared_cache": False,
            },
        }

    @api.model
    def get_data(self, filters=None):
        """Return account.journal data optimized for kanban display."""
        filters = filters or {}
        domain = []

        # Company filter
        if filters.get("company_id"):
            domain.append(("company_id", "=", int(filters["company_id"])))
        else:
            domain.append(("company_id", "in", self.env.companies.ids))

        # Type filter
        if filters.get("type"):
            domain.append(("type", "=", filters["type"]))

        journals = self.env["account.journal"].sudo().search(domain)

        # Get pending moves count per journal
        journals_with_counts = self._get_pending_counts(journals)

        # Get last activity per journal
        journals_with_activity = self._get_last_activity(journals)

        # Get balance per journal
        journals_with_balance = self._get_balances(journals)

        # Build rows
        columns = ["id", "name", "code", "type", "state",
                   "pending_moves", "total_debit", "total_credit", "balance",
                   "last_activity", "currency_id", "company_id"]
        units = {
            "pending_moves": "integer", "total_debit": "monetary",
            "total_credit": "monetary", "balance": "monetary",
        }

        rows = []
        for journal in journals:
            row = {
                "id": journal.id,
                "name": journal.name,
                "code": journal.code or "",
                "type": dict(journal._fields["type"].selection).get(journal.type, journal.type),
                "state": "active" if journal.active else "locked",
                "pending_moves": journals_with_counts.get(journal.id, 0),
                "total_debit": journals_with_balance.get(journal.id, {}).get("debit", 0),
                "total_credit": journals_with_balance.get(journal.id, {}).get("credit", 0),
                "balance": journals_with_balance.get(journal.id, {}).get("balance", 0),
                "last_activity": journals_with_activity.get(journal.id, ""),
                "currency_id": journal.currency_id.id,
                "company_id": journal.company_id.id,
            }
            rows.append(row)

        return {
            "columns": columns,
            "rows": rows,
            "units": units,
        }

    @api.model
    def get_drill_action(self, context=None):
        """Return action to open journal form or move tree."""
        context = context or {}
        journal_id = context.get("id")
        if journal_id:
            return {
                "type": "ir.actions.act_window",
                "res_model": "account.journal",
                "res_id": journal_id,
                "views": [[False, "form"]],
            }
        return {
            "type": "ir.actions.act_window",
            "res_model": "account.journal",
            "views": [[False, "tree"], [False, "form"]],
        }

    # ── Helpers ──

    def _get_pending_counts(self, journals):
        """Get count of draft/posted moves per journal. Uses _read_group for ir.rule safety."""
        if not journals:
            return {}
        result = self.env["account.move"]._read_group(
            domain=[("journal_id", "in", journals.ids), ("state", "=", "draft")],
            groupby=["journal_id"],
            aggregates=["__count"],
        )
        return {journal.id: count for journal, count in result}

    def _get_last_activity(self, journals):
        """Get the date of the most recent move per journal."""
        if not journals:
            return {}
        result = self.env["account.move"]._read_group(
            domain=[("journal_id", "in", journals.ids)],
            groupby=["journal_id"],
            aggregates=["date:max"],
        )
        return {journal.id: str(max_date) if max_date else "" for journal, max_date in result}

    def _get_balances(self, journals):
        """Get total debit/credit per journal for posted moves."""
        if not journals:
            return {}
        result = self.env["account.move.line"]._read_group(
            domain=[("journal_id", "in", journals.ids), ("parent_state", "=", "posted")],
            groupby=["journal_id"],
            aggregates=["debit:sum", "credit:sum", "balance:sum"],
        )
        out = {}
        for journal, debit, credit, balance in result:
            out[journal.id] = {
                "debit": debit or 0.0,
                "credit": credit or 0.0,
                "balance": balance or 0.0,
            }
        return out
