# Copyright (C) 2026 Vertel Sverige AB (<https://vertel.se>).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

"""Adapters for mn_finance_insights reports → dashboard_vrtl sources."""

from odoo import api, fields, models
from odoo.tools import float_round


class FinanceDashboardSource(models.AbstractModel):
    _name = "dashboard.source.finance.dashboard"
    _inherit = "dashboard.source.mixin"
    _description = "Finance: Executive Dashboard"

    @api.model
    def get_schema(self):
        return {
            "name": "Revenue vs Expenses",
            "description": "Monthly revenue and expenses trend with key metrics",
            "icon": "fa-line-chart", "category": "Finance",
            "measures": [
                {"name": "revenue", "label": "Revenue", "type": "monetary", "color": "#4CAF50"},
                {"name": "expenses", "label": "Expenses", "type": "monetary", "color": "#F44336"},
                {"name": "net_profit", "label": "Net Profit", "type": "monetary", "color": "#2196F3"},
            ],
            "dimensions": [{"name": "month", "label": "Month", "type": "date"}],
            "filters": [
                {"name": "date_from", "label": "From", "type": "date"},
                {"name": "date_to", "label": "To", "type": "date"},
            ],
            "chart_types": ["line", "bar", "area", "kpi"],
            "drill_enabled": True,
            "security": {"respects_ir_rule": True, "row_level": False, "safe_for_shared_cache": True},
            "interactions": {"emit_filters": [], "accept_filters": ["period", "company"]},
        }

    @api.model
    def get_data(self, measures, dimensions, filters, options=None):
        source = self.env["finance.dashboard"]
        raw = source._chart_revenue_vs_expenses({
            "date_from": filters.get("date_from", "2026-01-01"),
            "date_to": filters.get("date_to", "2026-07-11"),
            "company_ids": filters.get("company_ids", self.env.companies.ids),
        })
        series = []
        if "revenue" in measures:
            series.append({"name": "Revenue", "values": raw["revenue"], "color": "#4CAF50"})
        if "expenses" in measures:
            series.append({"name": "Expenses", "values": raw["expenses"], "color": "#F44336"})
        return {"labels": raw["labels"], "series": series,
                "currency": {"symbol": self.env.company.currency_id.symbol}}


class FinanceARAgingSource(models.AbstractModel):
    _name = "dashboard.source.finance.ar_aging"
    _inherit = "dashboard.source.mixin"
    _description = "Finance: AR Aging"

    @api.model
    def get_schema(self):
        return {
            "name": "Accounts Receivable Aging",
            "description": "Outstanding receivables by age bucket",
            "icon": "fa-table", "category": "Finance",
            "measures": [{"name": "amount", "label": "Amount", "type": "monetary"}],
            "dimensions": [{"name": "bucket", "label": "Age Bucket", "type": "category"}],
            "filters": [{"name": "as_of", "label": "As Of", "type": "date"}],
            "chart_types": ["bar", "pie", "doughnut", "table"],
            "drill_enabled": True,
            "security": {"respects_ir_rule": True, "row_level": True, "safe_for_shared_cache": False},
            "interactions": {"emit_filters": [], "accept_filters": ["customer", "company"]},
        }

    @api.model
    def get_data(self, measures, dimensions, filters, options=None):
        source = self.env["finance.aged.receivable"]
        raw = source.get_aged_data({"as_of": filters.get("as_of", fields.Date.today().isoformat())})
        return {
            "labels": [b["label"] for b in raw["buckets"]],
            "series": [{"name": "Outstanding", "values": raw["bucket_totals"]}],
            "rows": raw["rows"], "grand_total": raw["grand_total"],
            "currency": raw.get("currency", {}),
        }


class FinanceCustomerLTVSource(models.AbstractModel):
    _name = "dashboard.source.finance.customer_ltv"
    _inherit = "dashboard.source.mixin"
    _description = "Finance: Customer LTV (Optimized)"

    @api.model
    def get_schema(self):
        return {
            "name": "Customer Lifetime Value",
            "description": "Total revenue per customer over all time",
            "icon": "fa-user-chart", "category": "Finance",
            "measures": [
                {"name": "ltv", "label": "LTV", "type": "monetary"},
                {"name": "invoices", "label": "Invoices", "type": "integer"},
            ],
            "dimensions": [{"name": "partner", "label": "Customer", "type": "entity"}],
            "filters": [{"name": "limit", "label": "Max Customers", "type": "integer", "default": 100}],
            "chart_types": ["bar", "table", "scatter"],
            "drill_enabled": True,
            "security": {"respects_ir_rule": True, "row_level": True, "safe_for_shared_cache": False},
            "interactions": {"emit_filters": [], "accept_filters": ["company"]},
        }

    @api.model
    def get_data(self, measures, dimensions, filters, options=None):
        limit = int(filters.get("limit", 100))
        company_ids = filters.get("company_ids", self.env.companies.ids)

        rows = self.env["account.move.line"]._read_group(
            domain=[
                ("parent_state", "=", "posted"), ("company_id", "in", company_ids),
                ("move_id.move_type", "in", ["out_invoice", "out_refund"]),
                ("account_id.account_type", "in", ["income", "income_other"]),
                ("partner_id", "!=", False),
            ],
            groupby=["partner_id"], aggregates=["debit:sum", "credit:sum"],
            order="credit:sum desc", limit=limit,
        )

        if not rows:
            return {"labels": [], "series": []}

        partner_ids = [p.id for (p, d, c) in rows]
        self.env.cr.execute("""
            SELECT partner_id, MIN(invoice_date), MAX(invoice_date),
                   COUNT(*) FILTER (WHERE move_type='out_invoice')
            FROM account_move
            WHERE partner_id = ANY(%s) AND move_type IN ('out_invoice','out_refund')
              AND state='posted' AND company_id = ANY(%s)
            GROUP BY partner_id
        """, (partner_ids, company_ids))
        meta = {r[0]: {"first_date": r[1], "last_date": r[2], "count": r[3]}
                for r in self.env.cr.fetchall()}

        out = []
        for (p, d, c) in rows:
            ltv = (c or 0) - (d or 0)
            m = meta.get(p.id, {})
            inv_count = m.get("count", 0)
            out.append({
                "id": p.id, "name": p.display_name, "ltv": float_round(ltv, 2),
                "invoices": inv_count,
                "avg_invoice": float_round(ltv / inv_count if inv_count else 0, 2),
                "first_date": str(m.get("first_date", "")),
                "last_date": str(m.get("last_date", "")),
            })

        return {
            "labels": [r["name"] for r in out],
            "series": [
                {"name": "LTV", "values": [r["ltv"] for r in out], "color": "#4CAF50"},
                {"name": "Invoices", "values": [r["invoices"] for r in out], "color": "#2196F3"},
            ],
            "rows": out,
            "currency": {"symbol": self.env.company.currency_id.symbol},
        }
