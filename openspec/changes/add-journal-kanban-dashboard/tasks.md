## 1. Kanban fields on dashboard.metric

- [x] 1.1 Add `state_field` (Char), `state_colors` (Text/JSON), `state_icons` (Text/JSON) fields to `dashboard.metric`
- [x] 1.2 Add `card_title_field` (Char), `card_subtitle_field` (Char), `card_body_fields` (Text/JSON), `card_footer_fields` (Text/JSON) fields to `dashboard.metric`
- [x] 1.3 Add `card_actions` (Text/JSON) field to `dashboard.metric` for inline action button definitions
- [x] 1.4 Add `kanban_group_field` (Char) field to `dashboard.metric` for explicit kanban column grouping
- [x] 1.5 Update `dashboard.metric` form view with a "Kanban Configuration" tab/section

## 2. Kanban chart type on dashboard.chart

- [x] 2.1 Add `kanban` to `chart_type` Selection field choices
- [x] 2.2 Update `dashboard.chart` form view to show kanban-specific options when chart_type="kanban"

## 3. Kanban OWL components

- [x] 3.1 Create `KanbanCard` OWL component (card rendering: title, subtitle, state badge, body KPIs, footer, action buttons)
- [x] 3.2 Create `KanbanView` OWL component (grouped columns or fluid grid, card rendering, empty state, loading state)
- [x] 3.3 Implement state-based coloring (ribbon/border) and icon rendering on `KanbanCard`
- [x] 3.4 Implement card body KPI formatting (currency, count, percentage based on unit metadata)
- [x] 3.5 Implement kanban grouping logic with column headers and counts
- [x] 3.6 Implement inline action buttons with ir.actions integration and optional confirmation dialog
- [x] 3.7 Implement "More" dropdown when actions exceed 3
- [x] 3.8 Implement empty state display

## 4. Integration with existing chart system

- [x] 4.1 Add `KanbanView` dispatch in `ChartComponent` template for chart_type="kanban"
- [x] 4.2 Ensure kanban charts participate in global filter pipeline (re-fetch on filter change)
- [x] 4.3 Implement kanban card click → cross-chart filter (emit filter event to dashboard)
- [x] 4.4 Implement kanban card click → drill-down (trigger get_drill_action when drill_enabled)
- [x] 4.5 Ensure kanban charts respect `chart_group_ids` access control
- [x] 4.6 Add kanban CSS styles (responsive grid, card styling, state colors, hover effects)

## 5. Kanban in dashboard-as-code YAML

- [x] 5.1 Update YAML schema to support `chart_type: kanban` with kanban-specific fields
- [x] 5.2 Ensure `load_from_yaml()` on `dashboard.dashboard` handles kanban fields on metric and chart
- [x] 5.3 Ensure `export_to_yaml()` serializes kanban configuration correctly

## 6. Account journal source module (dashboard_vrtl_source_account)

- [x] 6.1 Create module skeleton: `__manifest__.py`, `__init__.py`, models, views, security
- [x] 6.2 Implement `dashboard.source.account.journals` adapter (extends `dashboard.source.mixin`)
- [x] 6.3 Implement `get_schema()` returning measures, dimensions, chart_types with kanban defaults
- [x] 6.4 Implement `get_data()` querying `account.journal` with pending moves count, balances, last activity
- [x] 6.5 Implement `get_drill_action()` returning `act_window` for journal form or move tree
- [x] 6.6 Register source in dashboard.source registry on module install
- [x] 6.7 Add `dashboard_vrtl` and `account` as dependencies in manifest

## 7. Journal kanban dashboard YAML

- [x] 7.1 Create `dashboards/journal_kanban.yaml` with dashboard definition
- [x] 7.2 Define metric `account.journals` with kanban configuration (state_field, colors, card layout, actions)
- [x] 7.3 Add kanban chart for journals grouped by journal type
- [x] 7.4 Add supporting KPI charts (total pending moves, total balance by journal type)
- [x] 7.5 Add data file entry in `__manifest__.py` for the YAML dashboard

## 8. Updates to existing artifacts

- [x] 8.1 Update `SKILL.md` with kanban patterns, field mappings, journal adapter reference, and usage examples
- [x] 8.2 Update `dashboard_vrtl/__manifest__.py` if needed (no hard account dependency — adapter lives in separate module)

## 9. Testing and verification

- [x] 9.1 Verify kanban chart renders in dashboard grid with journal data
- [x] 9.2 Verify state colors and icons display correctly for active/locked journals
- [x] 9.3 Verify grouping by journal type produces correct columns
- [x] 9.4 Verify inline action "New Entry" opens account.move with journal pre-filled
- [x] 9.5 Verify card click filters other charts on the dashboard
- [x] 9.6 Verify card click drill-down opens journal form
- [x] 9.7 Verify empty state displays when no journals match
- [x] 9.8 Verify YAML load/export round-trip for kanban dashboard
- [x] 9.9 Verify group-based access control hides kanban chart from unauthorized users
