# Copyright (C) 2026 Vertel Sverige AB (<https://vertel.se>).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import hashlib
import json
from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval


class DashboardMetric(models.Model):
    _name = "dashboard.metric"
    _description = "Dashboard Metric Definition"
    _inherit = ["mail.thread"]

    name = fields.Char(required=True, translate=True)
    key = fields.Char(
        required=True,
        help="Unique key, e.g. 'sales.net_revenue'. Used for cross-referencing in YAML.",
    )
    description = fields.Text()
    category = fields.Char(help="Finance, Sales, HR, Inventory, etc.")
    active = fields.Boolean(default=True)

    # ── Source Definition ──
    source_type = fields.Selection(
        [("model", "Odoo Model"), ("sql", "Custom SQL"),
         ("service", "Service Source"), ("composite", "Composite")],
        required=True, default="model",
    )
    model_id = fields.Many2one("ir.model", string="Odoo Model")
    field_id = fields.Many2one("ir.model.fields", string="Field", domain="[('model_id','=', model_id or False)]")
    sql_query = fields.Text(help="SQL query for source_type=sql. Use %(param)s for parameters.")
    service_model = fields.Char(help="Technical model name for source_type=service, e.g. 'finance.dashboard'")
    service_method = fields.Char(help="Method name, e.g. '_chart_revenue_vs_expenses'")

    # ── Aggregation ──
    aggregation = fields.Selection(
        [("sum", "Sum"), ("avg", "Average"), ("count", "Count"),
         ("min", "Minimum"), ("max", "Maximum"), ("custom", "Custom")],
        default="sum",
    )
    default_domain = fields.Text(default="[]", help="Odoo domain as JSON string")
    date_field_id = fields.Many2one("ir.model.fields", string="Date Field")
    unit = fields.Selection(
        [("monetary", "Monetary"), ("percentage", "Percentage"),
         ("integer", "Integer"), ("float", "Float"), ("duration", "Duration")],
        default="float",
    )

    # ── Composite ──
    composite_formula = fields.Text(help="e.g. '{net_revenue} / {orders_count}'")
    composite_metric_ids = fields.Many2many("dashboard.metric", "metric_composite_rel",
                                            "metric_id", "composite_id")

    # ── Kanban Configuration ──
    state_field = fields.Char(help="Row column name for state, e.g. 'state'. Used by kanban charts.")
    state_colors = fields.Text(
        default='{}',
        help='JSON mapping state value → CSS color, e.g. {"active": "#28a745", "locked": "#6c757d"}',
    )
    state_icons = fields.Text(
        default='{}',
        help='JSON mapping state value → Font Awesome icon, e.g. {"active": "fa-check-circle"}',
    )
    card_title_field = fields.Char(help="Row column name for card title, e.g. 'name'")
    card_subtitle_field = fields.Char(help="Row column name for card subtitle, e.g. 'code'")
    # Convenience m2o/m2m fields for picking model fields in the UI (model sources).
    # They sync into the Char/JSON fields above; service sources may still set
    # custom column names via the Char fields directly.
    card_title_field_id = fields.Many2one(
        "ir.model.fields", string="Card Title Field",
        domain="[('model_id','=', model_id or False), ('ttype','in',['char','text'])]")
    card_subtitle_field_id = fields.Many2one(
        "ir.model.fields", string="Card Subtitle Field",
        domain="[('model_id','=', model_id or False), ('ttype','in',['char','text'])]")
    card_body_field_ids = fields.Many2many(
        "ir.model.fields", "metric_kanban_body_rel", "metric_id", "field_id",
        string="Card Body Fields",
        domain="[('model_id','=', model_id or False)]")
    card_footer_field_ids = fields.Many2many(
        "ir.model.fields", "metric_kanban_footer_rel", "metric_id", "field_id",
        string="Card Footer Fields",
        domain="[('model_id','=', model_id or False)]")
    card_body_fields = fields.Text(
        default='[]',
        help='JSON list of column names to display as KPI badges on card body',
    )
    card_footer_fields = fields.Text(
        default='[]',
        help='JSON list of column names to display in card footer',
    )
    card_actions = fields.Text(
        default='[]',
        help='JSON list of action definitions for inline buttons. Each: {name, label, icon, action, params, confirm?}',
    )
    kanban_group_field = fields.Char(help="Column name for grouping cards into columns, e.g. 'type'")
    kanban_draggable = fields.Boolean(
        default=False,
        help="Enable HTML5 drag-and-drop on kanban cards. When True, cards can be dragged between group columns.",
    )
    kanban_drag_group_field = fields.Char(
        help="Field to update when a card is dropped into a new column, e.g. 'journal_id'",
    )

    # ── Row-Level Security ──
    respects_ir_rule = fields.Boolean(default=True)
    row_level_security = fields.Boolean(default=True)
    safe_for_shared_cache = fields.Boolean(default=False)
    ir_rule_check_result = fields.Json()

    # ── Company ──
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company)

    _sql_constraints = [
        ("key_unique", "UNIQUE(key)", "Metric key must be unique."),
    ]

    # ──────────────────────────────────────────────────────────────
    # Data Retrieval
    # ──────────────────────────────────────────────────────────────

    def get_data(self, filters=None):
        """Return metric data for the given filters. Dispatches by source_type."""
        self.ensure_one()
        filters = filters or {}
        handler = {
            "model": self._get_data_model,
            "sql": self._get_data_sql,
            "service": self._get_data_service,
            "composite": self._get_data_composite,
        }
        return handler[self.source_type](filters)

    def _get_data_model(self, filters):
        """Use _read_group() for Odoo model aggregation. ir.rule applied automatically."""
        # Resolve the model name with sudo (ir.model is admin-only); the actual
        # data query below still runs in the caller's env so ir.rule apply.
        model_name = self.model_id.sudo().model
        field_name = self.field_id.sudo().name
        domain = self._build_domain(filters)

        # Kanban charts consume a rows/columns format, not labels/series.
        if filters.get("format") == "kanban":
            return self._get_data_model_kanban(model_name, domain, filters)

        groupby = [self.date_field_id.sudo().name] if self.date_field_id and filters.get("group_by_date") else []
        if filters.get("group_by"):
            groupby.insert(0, filters["group_by"])

        aggregates = [f"{field_name}:{self.aggregation}"]
        if self.aggregation == "count":
            aggregates = ["__count"]

        records = self.env[model_name].with_context(active_test=True)._read_group(
            domain=domain, groupby=groupby, aggregates=aggregates, limit=filters.get("limit", 1000),
        )
        if not groupby:
            # No grouping: _read_group returns one row per aggregate WITHOUT a
            # group-value prefix, i.e. [(value,)]. The single value is the KPI.
            labels = [self.name]
            values = [(records[0][-1] or 0) if records else 0]
        else:
            labels = [r[0].display_name if hasattr(r[0], "display_name") else str(r[0]) for r in records]
            values = [r[-1] or 0 for r in records]
        # ``values`` carries the stored group value (record id, selection key or
        # date) so the frontend can filter by value instead of display label.
        filter_values = [
            (r[0].id if hasattr(r[0], "id") else r[0])
            if groupby else (records[0][-1] if records else 0)
            for r in records
        ]
        result = {
            "labels": labels,
            "values": filter_values,
            "series": [{"name": self.name, "values": values}],
        }
        # KPI previous-period comparison (only meaningful without grouping).
        if not groupby and filters.get("comparison") == "previous_period":
            comparison = self._compute_comparison(model_name, field_name, filters, values[0])
            if comparison:
                result["comparison"] = comparison
        return result

    def _get_data_model_kanban(self, model_name, domain, filters):
        """Return kanban rows/columns format for a model-source metric.

        The format consumed by ``KanbanView``: a ``columns`` list plus ``rows``
        (dicts keyed by column name), a ``units`` map for body KPI formatting
        and the kanban group field. ``kanban_config`` (state/colors/icons, card
        fields, drill model) is embedded by the dashboard layer.
        """
        limit = filters.get("limit", 1000)
        records = self.env[model_name].with_context(active_test=True).search(domain, limit=limit)
        group_field = self.kanban_group_field
        columns = ["id"]
        for field_name in (
            self.state_field, self.card_title_field,
            self.card_subtitle_field, group_field,
        ):
            if field_name and field_name not in columns:
                columns.append(field_name)
        for field_name in json.loads(self.card_body_fields or "[]"):
            if field_name and field_name not in columns:
                columns.append(field_name)
        for field_name in json.loads(self.card_footer_fields or "[]"):
            if field_name and field_name not in columns:
                columns.append(field_name)
        units = {field_name: self.unit for field_name in json.loads(self.card_body_fields or "[]")}
        rows = [
            {col: self._kanban_field_value(record, col) for col in columns}
            for record in records
        ]
        return {
            "columns": columns,
            "rows": rows,
            "units": units,
            "group_by": group_field,
        }

    @staticmethod
    def _kanban_field_value(record, field_name):
        """Serialize one record field for a kanban row dict."""
        if not field_name or field_name not in record._fields:
            return False
        field = record._fields[field_name]
        value = record[field_name]
        if isinstance(value, models.BaseModel):
            return value.display_name if value else False
        if field.type == "datetime" and value:
            return fields.Datetime.to_string(value)
        if field.type == "date" and value:
            return fields.Date.to_string(value)
        if field.type == "many2many":
            return value.mapped("display_name")
        return value

    def _compute_comparison(self, model_name, field_name, filters, current):
        """Compute previous-period value/delta for a KPI (no groupby).

        Requires an explicit date window (chart date-filter option or global
        period filter). Shifts the window back by its own span and re-runs the
        aggregation. Returns None when no window is available.
        """
        date_from = filters.get("date_from")
        date_to = filters.get("date_to")
        if not date_from or not date_to:
            return None
        try:
            from_date = fields.Date.from_string(date_from)
            to_date = fields.Date.from_string(date_to)
        except (TypeError, ValueError):
            return None
        span = (to_date - from_date).days + 1
        if span <= 0:
            return None
        prev_to = from_date - timedelta(days=1)
        prev_from = prev_to - timedelta(days=span - 1)
        prev_filters = dict(filters)
        prev_filters["date_from"] = fields.Date.to_string(prev_from)
        prev_filters["date_to"] = fields.Date.to_string(prev_to)
        prev_domain = self._build_domain(prev_filters)
        aggregates = [f"{field_name}:{self.aggregation}"]
        if self.aggregation == "count":
            aggregates = ["__count"]
        records = self.env[model_name].with_context(active_test=True)._read_group(
            domain=prev_domain, groupby=[], aggregates=aggregates, limit=1,
        )
        previous = (records[0][-1] or 0) if records else 0
        comparison_type = filters.get("comparison_type") or "percentage"
        if comparison_type == "value":
            delta = current - previous
        else:
            delta = ((current - previous) / previous * 100.0) if previous else None
        return {
            "type": comparison_type,
            "value": current,
            "previous_value": previous,
            "delta": delta,
        }

    def _get_data_sql(self, filters):
        """Execute SQL with security bridge."""
        if not self.respects_ir_rule and self.model_id:
            # Get authorized IDs via ORM
            records = self.env[self.model_id.sudo().model].search(self._build_domain(filters))
            authorized_ids = records.ids
            if not authorized_ids:
                return {"labels": [], "series": []}
            filters["authorized_ids"] = authorized_ids

        self.env.cr.execute(self.sql_query, self._prepare_sql_params(filters))
        rows = self.env.cr.fetchall()
        return {
            "labels": [r[0] for r in rows],
            "series": [{"name": self.name, "values": [r[1] for r in rows]}],
        }

    def _get_data_service(self, filters):
        """Delegate to a service AbstractModel."""
        service = self.env[self.service_model]
        method = getattr(service, self.service_method)
        return method(filters)

    def _get_data_composite(self, filters):
        """Evaluate composite formula."""
        values = {}
        for metric in self.composite_metric_ids:
            result = metric.get_data(filters)
            values[metric.key] = result.get("series", [{}])[0].get("values", [0])[0] if result.get("series") else 0
        result = safe_eval(self.composite_formula, values)
        return {
            "labels": [self.name],
            "series": [{"name": self.name, "values": [result]}],
        }

    def _build_domain(self, filters):
        domain = self._resolve_domain_sentinels(json.loads(self.default_domain or "[]"))
        model_name = self.model_id.sudo().model if self.model_id else False
        # Only scope by company when the queried model actually has a company_id
        # field (some models, e.g. social.agency.document, do not).
        if (self.company_id and model_name and "company_id" not in str(domain)
                and "company_id" in self.env[model_name]._fields):
            domain.append(["company_id", "in", [self.company_id.id, False]])
        # date_field can be overridden per request (e.g. by the chart's
        # date_filter_field_id), falling back to the metric's own date field.
        # Only apply date filters when the field is actually a date/datetime
        # field — otherwise a wrong date_field would crash the query.
        date_field = filters.get("date_field") or (self.date_field_id.sudo().name if self.date_field_id else False)
        if date_field and self._field_is_date(date_field):
            if filters.get("date_from"):
                domain.append([date_field, ">=", filters["date_from"]])
            if filters.get("date_to"):
                domain.append([date_field, "<=", filters["date_to"]])
        if filters.get("domain"):
            domain.extend(self._resolve_domain_sentinels(filters["domain"]))
        return domain

    @staticmethod
    def _resolve_domain_sentinels(domain):
        """Replace date sentinels (e.g. 'today_approx') with concrete dates.

        Resolved at query time so 'late invoices' stays relative to now instead
        of being frozen at load time. Handles flat prefix domains and nested
        lists; leaves are ``[field, operator, value]`` triples.
        """
        resolved = []
        for item in domain:
            if isinstance(item, (list, tuple)) and len(item) == 3 and isinstance(item[0], str):
                field, operator, value = item
                if isinstance(value, str) and value == "today_approx":
                    value = fields.Date.today()
                resolved.append([field, operator, value])
            elif isinstance(item, str):
                resolved.append(item)  # domain operators '&' '|' '!'
            elif isinstance(item, (list, tuple)):
                resolved.append(DashboardMetric._resolve_domain_sentinels(item))
            else:
                resolved.append(item)
        return resolved

    def _field_is_date(self, field_name):
        """Return True if ``field_name`` is a date/datetime field on the metric model."""
        if not self.model_id or not field_name:
            return False
        field = self.env["ir.model.fields"].sudo().search([
            ("model_id", "=", self.model_id.id), ("name", "=", field_name),
        ], limit=1)
        return bool(field and field.ttype in ("date", "datetime"))

    def _prepare_sql_params(self, filters):
        params = {"date_from": filters.get("date_from"), "date_to": filters.get("date_to"),
                  "company_id": self.company_id.id}
        if filters.get("authorized_ids"):
            params["authorized_ids"] = filters["authorized_ids"]
        return params

    # ──────────────────────────────────────────────────────────────
    # Row-Level Security Auto-Detection
    # ──────────────────────────────────────────────────────────────

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records:
            record._check_ir_rule_compatibility()
        records.with_context(skip_kanban_sync=True)._sync_kanban_fields()
        return records

    def write(self, vals):
        result = super().write(vals)
        if any(f in vals for f in ("model_id", "source_type")):
            self._check_ir_rule_compatibility()
        if not self.env.context.get("skip_kanban_sync"):
            # Guard against recursion: the sync below writes the Char/JSON
            # fields, which would otherwise re-enter write() -> _sync_kanban_fields
            self.with_context(skip_kanban_sync=True)._sync_kanban_fields()
        return result

    def action_view_records(self):
        """Open the underlying model records filtered by this metric's domain."""
        self.ensure_one()
        if not self.model_id:
            raise UserError(_("No model selected for this metric."))
        domain = json.loads(self.default_domain or "[]")
        return {
            "type": "ir.actions.act_window",
            "name": self.name,
            "res_model": self.model_id.sudo().model,
            # Kanban first: metrics configured as kanban charts center on the
            # card view of their underlying records; falls back to list when
            # the model has no kanban view.
            "view_mode": "kanban,list,form",
            "domain": domain,
            "target": "current",
        }

    def _sync_kanban_fields(self):
        """Sync the m2o/m2m card field pickers into the Char/JSON fields the
        frontend consumes (which may also hold custom column names from service
        sources). Only writes when something actually changed."""
        for metric in self:
            vals = {}
            if (metric.card_title_field_id
                    and metric.card_title_field != metric.card_title_field_id.name):
                vals["card_title_field"] = metric.card_title_field_id.name
            if (metric.card_subtitle_field_id
                    and metric.card_subtitle_field != metric.card_subtitle_field_id.name):
                vals["card_subtitle_field"] = metric.card_subtitle_field_id.name
            body = json.dumps(metric.card_body_field_ids.mapped("name")) if metric.card_body_field_ids else False
            if body and metric.card_body_fields != body:
                vals["card_body_fields"] = body
            footer = json.dumps(metric.card_footer_field_ids.mapped("name")) if metric.card_footer_field_ids else False
            if footer and metric.card_footer_fields != footer:
                vals["card_footer_fields"] = footer
            if vals:
                metric.write(vals)

    def _check_ir_rule_compatibility(self):
        """Auto-detect row-level security based on ir.rule."""
        for metric in self:
            if metric.source_type == "model" and metric.model_id:
                rules = self.env["ir.rule"].sudo().search([
                    ("model_id", "=", metric.model_id.id), ("active", "=", True),
                ])
                if rules:
                    metric.row_level_security = True
                    metric.respects_ir_rule = True
                    metric.safe_for_shared_cache = False
                    metric.ir_rule_check_result = {
                        "rule_count": len(rules),
                        "rules": [{"name": r.name, "groups": r.groups.ids} for r in rules],
                    }
                else:
                    metric.row_level_security = False
                    metric.safe_for_shared_cache = True
            elif metric.source_type == "sql":
                metric.row_level_security = True
                metric.respects_ir_rule = False
                metric.safe_for_shared_cache = False
            elif metric.source_type == "service":
                try:
                    service = self.env[metric.service_model]
                    schema = service.get_schema()
                    sec = schema.get("security", {})
                    metric.respects_ir_rule = sec.get("respects_ir_rule", True)
                    metric.row_level_security = sec.get("row_level", True)
                    metric.safe_for_shared_cache = sec.get("safe_for_shared_cache", False)
                except Exception:
                    metric.row_level_security = True
                    metric.safe_for_shared_cache = False

    # ──────────────────────────────────────────────────────────────
    # YAML Support
    # ──────────────────────────────────────────────────────────────

    @api.model
    def load_from_yaml(self, data):
        key = data.get("key")
        if not key:
            return None
        existing = self.search([("key", "=", key)], limit=1)
        vals = self._yaml_to_metric_vals(data)
        if existing:
            existing.write(vals)
            return existing
        return self.create(vals)

    def _yaml_to_metric_vals(self, data):
        kanban = data.get("kanban", {})
        return {
            "key": data["key"], "name": data.get("label", data["key"]),
            "source_type": data.get("source_type", "model"),
            "model_id": self._resolve_model_ref(data.get("model")) if data.get("model") else False,
            "field_id": self._resolve_field_ref(data.get("model"), data.get("field")) if data.get("field") else False,
            "aggregation": data.get("aggregation", "sum"),
            "default_domain": json.dumps(data.get("domain", [])),
            "date_field_id": self._resolve_field_ref(data.get("model"), data.get("date_field")) if data.get("date_field") else False,
            "unit": data.get("unit", "float"),
            "sql_query": data.get("sql_query"),
            "service_model": data.get("service_model"),
            "service_method": data.get("service_method"),
            # Kanban fields
            "state_field": kanban.get("state_field"),
            "state_colors": json.dumps(kanban.get("state_colors", {})) if kanban.get("state_colors") else "{}",
            "state_icons": json.dumps(kanban.get("state_icons", {})) if kanban.get("state_icons") else "{}",
            "card_title_field": kanban.get("card_title_field"),
            "card_subtitle_field": kanban.get("card_subtitle_field"),
            "card_body_fields": json.dumps(kanban.get("card_body_fields", [])),
            "card_footer_fields": json.dumps(kanban.get("card_footer_fields", [])),
            "card_actions": json.dumps(kanban.get("card_actions", [])),
            "kanban_group_field": kanban.get("group_field"),
            "kanban_draggable": kanban.get("draggable", False),
            "kanban_drag_group_field": kanban.get("drag_group_field"),
        }

    def _resolve_model_ref(self, model_name):
        return self.env["ir.model"].sudo().search([("model", "=", model_name)], limit=1).id

    def _resolve_field_ref(self, model_name, field_name):
        if not model_name or not field_name:
            return False
        model = self.env["ir.model"].sudo().search([("model", "=", model_name)], limit=1)
        field = self.env["ir.model.fields"].sudo().search([
            ("model_id", "=", model.id), ("name", "=", field_name),
        ], limit=1)
        return field.id

    def _metric_to_yaml_dict(self):
        d = {
            "key": self.key, "label": self.name,
            "source_type": self.source_type,
            "model": self.model_id.sudo().model,
            "field": self.field_id.sudo().name,
            "aggregation": self.aggregation,
            "domain": json.loads(self.default_domain or "[]"),
            "date_field": self.date_field_id.sudo().name,
            "unit": self.unit,
        }
        # Include kanban config if any is set
        kanban = {}
        if self.state_field:
            kanban["state_field"] = self.state_field
        if self.state_colors and self.state_colors != "{}":
            kanban["state_colors"] = json.loads(self.state_colors)
        if self.state_icons and self.state_icons != "{}":
            kanban["state_icons"] = json.loads(self.state_icons)
        if self.card_title_field:
            kanban["card_title_field"] = self.card_title_field
        if self.card_subtitle_field:
            kanban["card_subtitle_field"] = self.card_subtitle_field
        if self.card_body_fields and self.card_body_fields != "[]":
            kanban["card_body_fields"] = json.loads(self.card_body_fields)
        if self.card_footer_fields and self.card_footer_fields != "[]":
            kanban["card_footer_fields"] = json.loads(self.card_footer_fields)
        if self.card_actions and self.card_actions != "[]":
            kanban["card_actions"] = json.loads(self.card_actions)
        if self.kanban_group_field:
            kanban["group_field"] = self.kanban_group_field
        if self.kanban_draggable:
            kanban["draggable"] = True
        if self.kanban_drag_group_field:
            kanban["drag_group_field"] = self.kanban_drag_group_field
        if kanban:
            d["kanban"] = kanban
        return d
