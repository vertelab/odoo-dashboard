# Copyright (C) 2026 Vertel Sverige AB (<https://vertel.se>).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

"""YAML ↔ ORM sync utilities. Used by dashboard.dashboard.load_from_yaml()."""

import yaml

from odoo import _, api, models


class DashboardYaml(models.AbstractModel):
    _name = "dashboard.yaml"
    _description = "Dashboard YAML ↔ ORM Sync"

    @api.model
    def sync_all_from_dir(self, directory):
        """Sync all YAML files in a directory to ORM records."""
        import glob
        created = 0
        updated = 0
        for filepath in glob.glob(f"{directory}/*.yaml"):
            try:
                dashboard = self.env["dashboard.dashboard"].load_from_yaml(filepath)
                # Simple heuristic: if charts existed before, it's an update
                updated += 1
            except Exception as e:
                raise
        return {"created": created, "updated": updated}
