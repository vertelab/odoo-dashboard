# Copyright (C) 2026 Vertel Sverige AB (<https://vertel.se>).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import datetime

from odoo import _, api, fields, models
from odoo.tools.safe_eval import safe_eval


class DashboardAlert(models.Model):
    _name = "dashboard.alert"
    _description = "Dashboard Alert Rule"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(required=True, translate=True)
    key = fields.Char(help="Unique key for YAML cross-referencing")
    active = fields.Boolean(default=True)
    dashboard_id = fields.Many2one("dashboard.dashboard", required=True, ondelete="cascade")

    metric_id = fields.Many2one("dashboard.metric", required=True,
                                help="Metric to monitor for this alert")
    condition = fields.Char(required=True,
                            help="Expression: 'value < 10', 'delta < -30 and value < 50000'")
    severity = fields.Selection([
        ("info", "Information"), ("warning", "Warning"), ("critical", "Critical"),
    ], default="warning")

    trigger_type = fields.Selection([
        ("cron", "Scheduled"), ("event", "On Change"),
    ], default="cron")
    schedule = fields.Char(default="0 */4 * * *", help="Cron expression")
    cooldown = fields.Integer(default=3600, help="Minimum seconds between alerts")
    max_per_day = fields.Integer(default=10)

    channels = fields.Json(default=lambda self: ["notification"],
                           help='["notification", "activity"]')
    recipients = fields.Json(default=lambda self: [],
                             help='[{"type":"group","id":5}, {"type":"user","id":7}]')

    state = fields.Selection([
        ("ok", "OK"), ("triggered", "Triggered"), ("acknowledged", "Acknowledged"),
    ], default="ok")

    last_value = fields.Float()
    previous_value = fields.Float()
    last_evaluated = fields.Datetime()
    last_triggered = fields.Datetime()
    trigger_count_today = fields.Integer(default=0)

    company_id = fields.Many2one("res.company", default=lambda self: self.env.company)

    _sql_constraints = [
        ("key_unique_alert", "UNIQUE(key, dashboard_id)", "Alert key must be unique per dashboard."),
    ]

    # ──────────────────────────────────────────────────────────────
    # Evaluation
    # ──────────────────────────────────────────────────────────────

    @api.model
    def _cron_evaluate_all(self):
        """Evaluate all active cron-type alerts. Called by ir.cron."""
        alerts = self.search([("active", "=", True), ("trigger_type", "=", "cron")])
        for alert in alerts:
            alert._evaluate_and_notify()

    def _evaluate_and_notify(self):
        self.ensure_one()
        try:
            data = self.metric_id.get_data({})
            value = data.get("series", [{}])[0].get("values", [0])[0] if data.get("series") else 0
        except Exception:
            return

        previous = self.last_value or value
        delta = ((value - previous) / previous * 100.0) if previous else 0.0

        context = {"value": value, "previous_value": previous, "delta": delta}
        try:
            triggered = safe_eval(self.condition, context)
        except Exception:
            triggered = False

        if triggered and self._cooldown_ok():
            self._send_notifications(value, context)
            self.state = "triggered"
            self.last_triggered = fields.Datetime.now()
            self.trigger_count_today += 1
        elif not triggered and self.state == "triggered":
            self.state = "ok"  # Auto-reset

        self.previous_value = previous
        self.last_value = value
        self.last_evaluated = fields.Datetime.now()

    def _cooldown_ok(self):
        if self.trigger_count_today >= self.max_per_day:
            return False
        if not self.last_triggered:
            return True
        elapsed = (fields.Datetime.now() - self.last_triggered).total_seconds()
        return elapsed >= self.cooldown

    def _send_notifications(self, value, context):
        channels = self.channels or ["notification"]
        for channel in channels:
            if channel == "notification":
                self._notify_discuss(value, context)
            elif channel == "activity":
                self._notify_activity(value, context)

    def _notify_discuss(self, value, context):
        channel = self.env["mail.channel"].search([("name", "=", "Dashboard Alerts")], limit=1)
        if not channel:
            channel = self.env["mail.channel"].create({
                "name": "Dashboard Alerts", "public": "groups",
                "group_ids": [(6, 0, [self.env.ref("dashboard_vrtl.group_dashboard_user").id])],
            })
        channel.message_post(
            body=f"⚠️ **{self.name}** ({self.severity.upper()})\n\n"
                 f"Metric: {self.metric_id.name}\n"
                 f"Current value: {value}\n"
                 f"Condition: {self.condition}\n"
                 f"[View Dashboard](/odoo/action-{self.dashboard_id.created_action_id.id})",
            message_type="notification",
        )

    def _notify_activity(self, value, context):
        for recipient in (self.recipients or []):
            user_ids = []
            if recipient.get("type") == "group":
                group = self.env["res.groups"].browse(recipient["id"])
                user_ids = group.users.ids
            elif recipient.get("type") == "user":
                user_ids = [recipient["id"]]

            for user_id in user_ids:
                self.env["mail.activity"].create({
                    "res_model": "dashboard.alert", "res_id": self.id,
                    "user_id": user_id,
                    "activity_type_id": self.env.ref("mail.mail_activity_data_todo").id,
                    "summary": self.name,
                    "note": f"Metric '{self.metric_id.name}' = {value}. Condition: {self.condition}",
                })

    def action_acknowledge(self):
        self.state = "ok"
        self.trigger_count_today = 0

    # ──────────────────────────────────────────────────────────────
    # YAML Support
    # ──────────────────────────────────────────────────────────────

    def load_from_yaml(self, dashboard, data):
        existing = self.search([("key", "=", data["key"]), ("dashboard_id", "=", dashboard.id)], limit=1)
        metric = self.env["dashboard.metric"].search([("key", "=", data["metric"])], limit=1)
        vals = {
            "key": data["key"], "name": data.get("label", data["key"]),
            "metric_id": metric.id,
            "condition": data.get("condition"), "severity": data.get("severity", "warning"),
            "trigger_type": data.get("trigger_type", "cron"),
            "schedule": data.get("schedule", "0 */4 * * *"),
            "cooldown": data.get("cooldown", 3600),
            "channels": data.get("channels", ["notification"]),
            "recipients": data.get("recipients", []),
        }
        if existing:
            existing.write(vals)
            return existing
        vals["dashboard_id"] = dashboard.id
        return self.create(vals)

    def _alert_to_yaml_dict(self):
        return {
            "key": self.key, "label": self.name, "metric": self.metric_id.key,
            "condition": self.condition, "severity": self.severity,
            "trigger_type": self.trigger_type, "schedule": self.schedule,
            "cooldown": self.cooldown, "channels": self.channels,
        }
