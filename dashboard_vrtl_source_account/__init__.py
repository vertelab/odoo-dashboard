# Copyright (C) 2026 Vertel Sverige AB (<https://vertel.se>).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from . import models

_logger = logging.getLogger(__name__)


def _post_init_load_dashboards(cr, registry):
    """Load journal kanban dashboard YAML on module install."""
    try:
        env = registry.env
        env["dashboard.dashboard"].load_from_module_yaml(
            "dashboard_vrtl_source_account", "dashboards/journal_kanban.yaml"
        )
        _logger.info("dashboard_vrtl_source_account: Journal Kanban dashboard loaded.")
    except Exception as e:
        _logger.warning("dashboard_vrtl_source_account: Could not load dashboard: %s", e)
