# Copyright (C) 2026 Vertel Sverige AB.
# License AGPL-3.0 or later.

import logging

from . import models

_logger = logging.getLogger(__name__)

# Models are in separate files — no models/__init__.py needed
# This __init__ only provides the post_init_hook


def _post_init_load_dashboards(cr, registry):
    """Load all 7 persona dashboards on module install."""
    dashboards = [
        "cfo_daily",
        "ceo_overview",
        "cfo_monthly",
        "department_spend",
        "bookkeeper_workspace",
        "project_manager",
        "sales_manager",
    ]
    for name in dashboards:
        try:
            env = registry.env
            env["dashboard.dashboard"].load_from_module_yaml(
                "dashboard_vrtl_finance", f"data/dashboards/{name}.yaml"
            )
            _logger.info("dashboard_vrtl_finance: Loaded %s dashboard.", name)
        except Exception as e:
            _logger.warning("dashboard_vrtl_finance: Could not load %s: %s", name, e)
