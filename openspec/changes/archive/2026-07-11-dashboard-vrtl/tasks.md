## 1. Module Setup

- [x] 1.1 Create dashboard_vrtl module structure with __manifest__.py (depends: web, mail, base)
- [x] 1.2 Create dashboard_vrtl/security/ir.model.access.csv with full CRUD for group_dashboard_manager, read-only for group_dashboard_user
- [x] 1.3 Create dashboard_vrtl/security/dashboard_security.xml with group_dashboard_user, group_dashboard_manager, and base ir.rule records
- [x] 1.4 Add amCharts 5 libraries to static/src/lib/amcharts/ (reuse from Synconics, add stock.js + wordcloud.js)
- [x] 1.5 Create dashboard_vrtl/__init__.py and models/__init__.py

## 2. Core Models

- [x] 2.1 Implement dashboard.dashboard model (name, chart_count, grid_stack_dimensions, auto_reload_duration, menu integration, YAML sync methods)
- [x] 2.2 Implement dashboard.metric model (key, source_type, model_id, field_id, sql_query, aggregation, default_domain, date_field_id, unit, row_level_security fields, ir.rule auto-detection)
- [x] 2.3 Implement dashboard.chart model (metric_id, chart_type, layout config, theme, group_by, sub_group_by, drill_path, chart_group_ids)
- [x] 2.4 Implement dashboard.filter model (key, type, label, default, shortcuts, optional)
- [x] 2.5 Implement dashboard.chart.filter_mapping (chart_id, filter_id, compatible, param_mapping)
- [x] 2.6 Implement dashboard.taxonomy.concept model (key, label_sv, label_en, data_type, balance, reference, parent_id)
- [x] 2.7 Create dashboard_views.xml (dashboard form, tree, search views)
- [x] 2.8 Create dashboard_chart_views.xml (chart form with metric selector, live preview)
- [x] 2.9 Create dashboard_metric_views.xml (metric form with source_type-dependent fields)
- [x] 2.10 Create dashboard_menus.xml (parent menu items for BI Dashboard category)

## 3. Source Interface & Adapter System

- [x] 3.1 Implement dashboard.source.mixin AbstractModel (get_schema, get_data, get_drill_action interface)
- [x] 3.2 Implement builtin model source (source_type="model") using _read_group() for aggregation
- [x] 3.3 Implement composite metric evaluation (parse formula, resolve referenced metrics, compute)
- [x] 3.4 Implement dashboard.source registry model (name, technical_name, model_name, category, auto-registration from metrics)
- [x] 3.5 Implement security bridge for SQL sources (ORM.search → authorized_ids → WHERE id = ANY())
- [x] 3.6 Create dashboard_vrtl_source_finance module structure (depends: dashboard_vrtl, mn_finance_insights)
- [x] 3.7 Implement 52 finance adapters (delegate to mn_finance_insights methods, get_schema + get_data)
- [x] 3.8 Implement optimized adapters for 7 problematic reports (customer_ltv, customer_profitability, customer_cohort, customer_risk, product_profitability, margin_stability, vendor_reliability)

## 4. Security Implementation

- [x] 4.1 Set model access: group_dashboard_user = read, group_dashboard_manager = CRUD
- [x] 4.2 Implement ir.rule for dashboard.dashboard (user_ids/group_ids + company)
- [x] 4.3 Implement ir.rule for dashboard.chart with chart_group_ids enforcement
- [x] 4.4 Implement server-side write/create/unlink check in dashboard and chart models
- [x] 4.5 Implement row_level_security auto-detection on metric creation

## 5. UI Components (Owl + amCharts 5)

- [x] 5.1 Port Synconics Owl components to dashboard_vrtl (BarChart, LineChart, PieChart, DoughnutChart, AreaChart, FunnelChart, PyramidChart, RadarChart, RadialChart, ScatterChart, StackedColumnChart, MapChart, MeterChart)
- [x] 5.2 Create new Owl components for unused amCharts modules: SankeyChart (flow.js), TreemapChart (hierarchy.js), SunburstChart (hierarchy.js), WordcloudChart (wordcloud.js)
- [x] 5.3 Implement KPI and Tile layout components (5 KPI + 4 Tile layouts)
- [x] 5.4 Implement TableView component (sortable columns, row click for action drill)
- [x] 5.5 Implement dashboard_amcharts.js main component (grid layout, auto-refresh, chart loading)
- [x] 5.6 Implement dashboard_filter_bar.js (global filter rendering, badge display, filter removal)
- [x] 5.7 Implement dashboard_drill_breadcrumb.js (breadcrumb navigation, drill_stack management)

## 6. Interactivity System

- [x] 6.1 Implement filter event emission from charts (single-click → emit filter)
- [x] 6.2 Implement filter propagation loop in dashboard component (loop charts, check compatibility, refresh)
- [x] 6.3 Implement filter stacking and removal (multiple active filters, click ✕ to remove)
- [x] 6.4 Implement drill-down for group-by type (double-click → push drill_stack → render new level)
- [x] 6.5 Implement drill-down for action type (click → open Odoo view)
- [x] 6.6 Implement drill-down for cross-chart type (click → navigate to target chart)
- [x] 6.7 Implement URL state persistence (filters + drill_stack in URL hash)

## 7. Dashboard-as-Code

- [x] 7.1 Implement dashboard.dashboard.load_from_yaml() (parse YAML, upsert by key)
- [x] 7.2 Implement dashboard.dashboard.export_to_yaml() (generate YAML from ORM records)
- [x] 7.3 Implement customized flag on charts (GUI-modified charts not overwritten on YAML update)
- [x] 7.4 Create dashboard_vrtl_sales module with 3 pre-built YAML dashboards
- [x] 7.5 Create dashboard_vrtl_finance module with 4 pre-built YAML dashboards

## 8. Taxonomy Integration

- [x] 8.1 Create dashboard_vrtl_taxonomy module structure
- [x] 8.2 Implement XBRL parser to import K2 taxonomy concepts from taxonomier.se
- [x] 8.3 Implement taxonomy_concept → account_type default mapping
- [x] 8.4 Implement metric auto-generation from taxonomy concept reference
- [x] 8.5 Create auto-generated P&L and Balance Sheet dashboards from taxonomy hierarchy

## 9. Alerting

- [x] 9.1 Implement dashboard.alert model (metric_id, condition, severity, channels, recipients, schedule, cooldown, state)
- [x] 9.2 Implement condition evaluator (safe_eval with value, previous_value, delta, current_hour, current_dow)
- [x] 9.3 Implement notification channel (mail.channel message_post in "Dashboard Alerts")
- [x] 9.4 Implement activity channel (mail.activity create on recipients)
- [x] 9.5 Implement alert state machine (ok → triggered → acknowledged → ok, auto-reset)
- [x] 9.6 Implement cron-based evaluation (ir.cron per alert or global evaluator)
- [x] 9.7 Implement anti-flood (cooldown, max_per_day)

## 10. Caching

- [x] 10.1 Implement dashboard.cache model (cache_key, metric_id, user_id, filter_hash, data_json, expires_at)
- [x] 10.2 Implement get_or_compute() with user-aware cache key generation
- [x] 10.3 Implement request-cache (simple dict, per HTTP request lifecycle)
- [x] 10.4 Implement cache TTL per dashboard type (operational/tactical/strategic/financial)
- [x] 10.5 Implement cache invalidation (TTL expiry, manual refresh)
- [x] 10.6 Implement cron cleanup (expired entries, max 1000 per metric)

## 11. AI Skill (SKILL.md)

- [x] 11.1 Write SKILL.md — Phase 1: Understand (domain identification, clarifying questions)
- [x] 11.2 Write SKILL.md — Phase 2: Design (data→chart matching, layout rules)
- [x] 11.3 Write SKILL.md — Phase 3: Metrics (taxonomy lookup, source_type selection, ORM/SQL generation)
- [x] 11.4 Write SKILL.md — Phase 4: Validate (test query, magnitude check, user confirmation)
- [x] 11.5 Write SKILL.md — Phase 5: Persist (YAML or ORM, key-based references)
- [x] 11.6 Write SKILL.md — Odoo Knowledge Base (models, fields, domains, common patterns)
- [x] 11.7 Write SKILL.md — Taxonomy Reference (Swedish accounting concepts → Odoo mapping)
- [x] 11.8 Write SKILL.md — Visualization Rules (when to use each chart type)
- [x] 11.9 Write SKILL.md — Security Rules (read_group first, ID-bridge for SQL, company filter)
- [x] 11.10 Write SKILL.md — Examples (3-5 complete dashboards as reference)
- [x] 11.11 Write SKILL.md — Adapter Mode (get_schema + get_data implementation pattern)

## 12. Testing & Validation

- [x] 12.1 Create unit tests for dashboard.metric (model source, SQL source, composite, auto-detection)
- [x] 12.2 Create unit tests for security (ir.rule enforcement, chart_group_ids, row-level isolation)
- [x] 12.3 Create unit tests for alerting (condition evaluation, state machine, cooldown)
- [x] 12.4 Create unit tests for caching (key generation, TTL, user isolation)
- [x] 12.5 Create integration test: load YAML dashboard, verify all ORM records
- [x] 12.6 Create integration test: cross-chart filter propagation
- [x] 12.7 Create integration test: drill-down multi-level navigation
- [x] 12.8 Performance test: _read_group vs raw SQL for 100k records
