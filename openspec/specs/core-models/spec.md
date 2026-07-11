## ADDED Requirements

### Requirement: Dashboard model
The system SHALL provide a `dashboard.dashboard` model with fields for name, layout (grid_stack_dimensions), auto-refresh interval, and access control (user_ids, group_ids, access_by).

#### Scenario: Create dashboard
- **WHEN** user creates a new dashboard with name "Sales Overview" and assigns it to group "Sales Managers"
- **THEN** the dashboard is created with a new ir.actions.client + ir.ui.menu, visible only to members of "Sales Managers"

#### Scenario: Dashboard with global filters
- **WHEN** a dashboard is defined with a date_range filter "Period" and a company filter
- **THEN** the filter bar renders above the chart grid, and all compatible charts respond to filter changes

### Requirement: Chart model
The system SHALL provide a `dashboard.chart` model that references a metric, defines chart type and visual configuration, and stores grid position.

#### Scenario: Chart referencing a metric
- **WHEN** user creates a bar chart referencing metric "net_revenue" with group_by="date_order:month"
- **THEN** the chart fetches data via the metric's source and renders as a bar chart with monthly aggregation

#### Scenario: Chart with per-chart group access
- **WHEN** a chart has chart_group_ids set to ["Sales Managers"]
- **THEN** only users in that group see the chart; others see remaining charts on the dashboard

### Requirement: Metric model
The system SHALL provide a `dashboard.metric` model that defines a reusable data definition with source_type (model/sql/service/composite), aggregation method, default domain, date field, and unit.

#### Scenario: Model metric via read_group
- **WHEN** a metric is defined with source_type="model", model="sale.order", field="amount_total", aggregation="sum"
- **THEN** get_data() uses _read_group() on sale.order with the metric's default domain, respecting all ir.rule automatically

#### Scenario: Composite metric
- **WHEN** a metric is defined with source_type="composite", formula="{net_revenue} / {orders_count}"
- **THEN** get_data() evaluates the two referenced metrics and computes the formula

#### Scenario: Auto-detect row-level security
- **WHEN** a metric with source_type="model" is created for a model that has active ir.rule records
- **THEN** row_level_security is automatically set to True and safe_for_shared_cache to False

### Requirement: Source registry
The system SHALL provide a `dashboard.source` model that registers available data sources, auto-populated from installed metrics and service adapters.

#### Scenario: Auto-registration from metric
- **WHEN** a new metric "sales.net_revenue" is created
- **THEN** a dashboard.source record is automatically created, making it selectable in the dashboard builder
