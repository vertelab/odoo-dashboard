# Copyright (C) 2026 Vertel Sverige AB (<https://vertel.se>).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class DashboardMail(models.Model):
    """Demo-only helper to wire up the scheduled email on the demo gallery."""

    _inherit = "dashboard.mail"

    @api.model
    def _demo_create_schedule(self, dashboard_key, name, chart_keys,
                              interval_number=7, interval_type="days"):
        """Create a demo email schedule for a YAML-loaded dashboard.

        The YAML loader does not create records with xmlids, so the schedule
        must be wired up by key lookup. Recipients default to the demo user.
        """
        dashboard = self.env["dashboard.dashboard"].search(
            [("key", "=", dashboard_key)], limit=1)
        if not dashboard:
            return False
        existing = self.search([
            ("name", "=", name),
            ("dashboard_id", "=", dashboard.id),
        ], limit=1)
        if existing:
            return existing.id
        charts = self.env["dashboard.chart"].search([
            ("dashboard_id", "=", dashboard.id),
            ("key", "in", chart_keys),
        ])
        demo_user = self.env.ref("base.user_demo", raise_if_not_found=False) \
            or self.env.ref("base.user_admin")
        mail = self.create({
            "name": name,
            "dashboard_id": dashboard.id,
            "chart_ids": [(6, 0, charts.ids)],
            "recipient_ids": [(6, 0, [demo_user.partner_id.id])],
            "is_automated": True,
            "interval_number": interval_number,
            "interval_type": interval_type,
        })
        return mail.id
