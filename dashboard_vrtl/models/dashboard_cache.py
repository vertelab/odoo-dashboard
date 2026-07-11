# Copyright (C) 2026 Vertel Sverige AB (<https://vertel.se>).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import hashlib
import json
from datetime import timedelta

from odoo import _, api, fields, models


class DashboardCache(models.Model):
    _name = "dashboard.cache"
    _description = "Dashboard Data Cache"

    cache_key = fields.Char(required=True, index=True)
    metric_id = fields.Many2one("dashboard.metric", required=True, index=True, ondelete="cascade")
    user_id = fields.Many2one("res.users", index=True)
    filter_hash = fields.Char(index=True)
    data_json = fields.Json(required=True)
    created_at = fields.Datetime(default=fields.Datetime.now)
    expires_at = fields.Datetime(required=True)
    hit_count = fields.Integer(default=0)

    _sql_constraints = [
        ("unique_cache_key", "UNIQUE(cache_key)", "Cache key must be unique."),
    ]

    # ──────────────────────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────────────────────

    @api.model
    def get_or_compute(self, metric, user, filters, ttl=300, include_user_in_key=True):
        """Get data from cache or compute and store.

        Returns: (data_dict, from_cache_bool)
        """
        cache_key = self._build_key(metric.id, user.id if include_user_in_key else 0, filters)

        cached = self.search([
            ("cache_key", "=", cache_key), ("expires_at", ">", fields.Datetime.now()),
        ], limit=1)

        if cached:
            cached.hit_count += 1
            return cached.data_json, True

        # Cache miss — compute
        data = metric.get_data(filters)

        # Store in cache
        self.create({
            "cache_key": cache_key,
            "metric_id": metric.id,
            "user_id": user.id if include_user_in_key else False,
            "filter_hash": self._hash_filters(filters),
            "data_json": data,
            "expires_at": fields.Datetime.now() + timedelta(seconds=ttl),
        })

        return data, False

    # ──────────────────────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────────────────────

    @staticmethod
    def _build_key(metric_id, user_id, filters):
        raw = f"m:{metric_id}|u:{user_id}|{DashboardCache._hash_filters(filters)}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    @staticmethod
    def _hash_filters(filters):
        canonical = json.dumps(filters, sort_keys=True, default=str)
        return hashlib.md5(canonical.encode()).hexdigest()[:12]

    # ──────────────────────────────────────────────────────────────
    # Cleanup
    # ──────────────────────────────────────────────────────────────

    @api.model
    def _cron_cleanup_expired(self):
        """Remove expired cache entries. Called by ir.cron every 15 minutes."""
        self.search([("expires_at", "<", fields.Datetime.now())]).unlink()

    @api.model
    def _cron_cleanup_cold(self):
        """Remove overflow entries (>1000 per metric)."""
        self.env.cr.execute("""
            DELETE FROM dashboard_cache
            WHERE id IN (
                SELECT id FROM (
                    SELECT id, ROW_NUMBER() OVER (
                        PARTITION BY metric_id ORDER BY created_at DESC
                    ) AS rn
                    FROM dashboard_cache
                ) ranked
                WHERE ranked.rn > 1000
            )
        """)
