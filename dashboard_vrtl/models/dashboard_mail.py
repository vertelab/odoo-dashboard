# Copyright (C) 2026 Vertel Sverige AB (<https://vertel.se>).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
import html
import logging
from datetime import timedelta

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class DashboardMail(models.Model):
    _name = "dashboard.mail"
    _description = "Dashboard Mail Schedule"

    dashboard_id = fields.Many2one("dashboard.dashboard", required=True, ondelete="cascade")
    name = fields.Char(required=True)
    chart_ids = fields.Many2many("dashboard.chart", string="Charts")
    recipient_ids = fields.Many2many("res.partner", string="Recipients")
    recipient_group_ids = fields.Many2many("res.groups", string="Recipient Groups")
    recipient_user_ids = fields.Many2many("res.users", string="Recipient Users")
    is_automated = fields.Boolean(default=True)
    interval_number = fields.Integer(default=1)
    interval_type = fields.Selection(
        [("minutes", "Minutes"), ("hours", "Hours"), ("days", "Days"),
         ("weeks", "Weeks"), ("months", "Months")],
        default="days",
    )
    next_run = fields.Datetime(string="Next Run", copy=False)
    last_sent_at = fields.Datetime(string="Last Sent", copy=False, readonly=True)
    active = fields.Boolean(default=True)

    # ──────────────────────────────────────────────────────────────
    # Scheduling
    # ──────────────────────────────────────────────────────────────

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("is_automated") and not vals.get("next_run"):
                vals["next_run"] = self._compute_next_run(
                    vals.get("interval_number", 1), vals.get("interval_type", "days"))
        return super().create(vals_list)

    def write(self, vals):
        res = super().write(vals)
        if (vals.get("is_automated")
                and any(f in vals for f in ("interval_number", "interval_type", "is_automated"))
                and not any(f in vals for f in ("next_run", "last_sent_at"))):
            for rec in self:
                rec.next_run = rec._compute_next_run(rec.interval_number, rec.interval_type)
        return res

    @api.model
    def _compute_next_run(self, number, interval_type):
        now = fields.Datetime.now()
        if interval_type == "minutes":
            return now + timedelta(minutes=number)
        if interval_type == "hours":
            return now + timedelta(hours=number)
        if interval_type == "weeks":
            return now + timedelta(weeks=number)
        if interval_type == "months":
            return now + relativedelta(months=number)
        return now + timedelta(days=number)

    # ──────────────────────────────────────────────────────────────
    # Delivery
    # ──────────────────────────────────────────────────────────────

    def _recipient_partners(self):
        """Resolve recipients from partners, groups and users (deduplicated)."""
        self.ensure_one()
        partners = self.recipient_ids
        for group in self.recipient_group_ids:
            partners |= group.users.partner_id
        for user in self.recipient_user_ids:
            partners |= user.partner_id
        return partners

    @api.model
    def _cron_send_due(self):
        """Send all due automated schedules. Called by ir.cron."""
        now = fields.Datetime.now()
        mails = self.search([
            ("active", "=", True),
            ("is_automated", "=", True),
            ("next_run", "<=", now),
        ])
        for mail in mails:
            try:
                mail._send()
                mail.write({
                    "last_sent_at": fields.Datetime.now(),
                    "next_run": mail._compute_next_run(mail.interval_number, mail.interval_type),
                })
            except Exception:
                # Keep next_run unchanged so the next cron run retries.
                _logger.exception("Failed to send dashboard mail schedule '%s'", mail.name)

    def _send(self):
        """Build and send one mail.mail for this schedule."""
        self.ensure_one()
        partners = self._recipient_partners()
        emails = list({p.email for p in partners if p.email})
        if not emails:
            _logger.warning("Dashboard mail '%s' has no recipients with an email address", self.name)
            return False

        body_parts = []
        for chart in self.chart_ids.filtered("active"):
            data = {}
            try:
                data, _from_cache = self.env["dashboard.cache"].get_or_compute(
                    chart.metric_id, self.env.user, chart._get_active_filters(),
                    ttl=self.dashboard_id.cache_ttl,
                )
            except Exception:
                data = {}
            body_parts.append(self._chart_email_html(chart, data))

        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        link = ""
        if self.dashboard_id.created_action_id:
            link = '<p><a href="%s/odoo/action-%s">View Dashboard</a></p>' % (
                base_url, self.dashboard_id.created_action_id.id)

        mail = self.env["mail.mail"].create({
            "subject": "Dashboard: %s" % self.name,
            "body_html": (
                "<div style='font-family: Arial, sans-serif;'>"
                "<h3>%s</h3>%s%s</div>"
            ) % (html.escape(self.name), "".join(body_parts), link),
            "email_to": ",".join(emails),
        })
        mail.send()
        return mail

    def _chart_email_html(self, chart, data):
        """Render one chart for the email body.

        SVG-based charts are embedded as real PNG images (captured client-side
        and stored on ``chart.image``). HTML-based chart types (kpi, tile, list,
        table, to_do, kanban) fall back to a compact HTML summary of their data.
        """
        title = "<h4>%s</h4>" % html.escape(chart.name)
        if chart.image:
            try:
                img_b64 = base64.b64encode(chart.image).decode()
                return "<div style='margin:16px 0'>%s<img src='data:image/png;base64,%s' style='max-width:100%%'/></div>" % (
                    title, img_b64)
            except Exception:
                pass
        summary = self._chart_summary_html(chart, data)
        if summary:
            return "<div style='margin:16px 0'>%s%s</div>" % (title, summary)
        return "<div style='margin:16px 0'>%s<p>No data to display.</p></div>" % title

    def _chart_summary_html(self, chart, data):
        """Compact HTML fallback for charts without a captured PNG image."""
        if chart.chart_type in ("kpi", "tile"):
            series = (data or {}).get("series") or []
            value = series[0].get("values", [0])[0] if series else 0
            return "<p><strong>%s</strong></p>" % (value or 0)
        if chart.chart_type in ("list", "table") and isinstance(data, dict):
            rows = data.get("rows") or []
            if rows:
                cols = list(rows[0].keys())
                table = "<table border='1' cellpadding='4' style='border-collapse:collapse'>"
                table += "<tr>%s</tr>" % "".join("<th>%s</th>" % html.escape(str(c)) for c in cols)
                for row in rows[:10]:
                    table += "<tr>%s</tr>" % "".join(
                        "<td>%s</td>" % html.escape(str(row.get(c, ""))) for c in cols)
                table += "</table>"
                return table
        return ""
