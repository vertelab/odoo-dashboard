## MODIFIED Requirements

### Requirement: Chart model
The system SHALL provide a `dashboard.chart` model that references a metric, defines chart type and visual configuration, and stores grid position.

#### Scenario: Chart referencing a metric
- **WHEN** user creates a bar chart referencing metric "net_revenue" with group_by="date_order:month"
- **THEN** the chart fetches data via the metric's source and renders as a bar chart with monthly aggregation

#### Scenario: Chart with per-chart group access
- **WHEN** a chart has chart_group_ids set to ["Sales Managers"]
- **THEN** only users in that group see the chart; others see remaining charts on the dashboard

#### Scenario: Kanban chart type
- **WHEN** user creates a chart with chart_type="kanban" referencing a metric configured for kanban display
- **THEN** the chart renders as a kanban card grid with state-based coloring, configurable field layout, grouping, and inline actions

#### Scenario: All supported chart types available
- **WHEN** user selects chart_type for a new chart
- **THEN** the selection includes: kpi, tile, bar_chart, column_chart, doughnut_chart, area_chart, funnel_chart, pyramid_chart, line_chart, pie_chart, radar_chart, stackedcolumn_chart, radial_chart, scatter_chart, map_chart, meter_chart, sankey_chart, treemap_chart, sunburst_chart, wordcloud_chart, table, list, to_do, kanban

### Requirement: Metric kanban configuration
The system SHALL support kanban-specific configuration fields on `dashboard.metric` that define card layout, state visualization, grouping, and actions.

#### Scenario: Metric with kanban configuration
- **WHEN** a metric is configured with kanban fields: state_field="state", state_colors='{"draft":"#ffc107","posted":"#28a745"}', card_title_field="name", card_subtitle_field="code", group_by="type"
- **THEN** charts of type "kanban" referencing this metric render cards with state-colored ribbons, journal name as title, code as subtitle, and grouped by journal type

#### Scenario: Kanban configuration is optional
- **WHEN** a metric has no kanban configuration fields set
- **THEN** the metric can still be used by non-kanban chart types without errors; kanban charts referencing this metric show cards with default layout (title from the first string field, no state coloring, no grouping)

#### Scenario: Kanban default card title
- **WHEN** a metric has no card_title_field set and the source provides rows
- **THEN** the kanban view uses the first string-type column from the row as the card title

## ADDED Requirements

### Requirement: Account journal kanban source adapter
The system SHALL provide a `dashboard.source.account.journals` adapter in module `dashboard_vrtl_source_account` that returns journal data optimized for kanban display.

#### Scenario: Journals kanban data
- **WHEN** `dashboard.source.account.journals.get_data()` is called
- **THEN** it returns rows with columns: id, name, code, type, state (active/locked), pending_moves (count of draft moves), total_debit, total_credit, balance, last_activity (datetime), currency_id, company_id

#### Scenario: Journals filtered by company
- **WHEN** the global company filter is active and the source declares compatibility
- **THEN** get_data() filters journals by the selected company_id

#### Scenario: Journals kanban schema
- **WHEN** `dashboard.source.account.journals.get_schema()` is called
- **THEN** it returns chart_types including "kanban" with kanban_defaults: {state_field: "state", state_colors: {active: "#28a745", locked: "#6c757d"}, card_title_field: "name", card_subtitle_field: "type", card_body_fields: ["pending_moves", "balance"]}
