## ADDED Requirements

### Requirement: Project margin source adapter
The system SHALL provide a `dashboard.source.project.margin` adapter in module `dashboard_vrtl_source_project` that computes project P&L from `account.analytic.line`.

#### Scenario: Project margin calculation
- **WHEN** `dashboard.source.project.margin.get_data()` is called with a project filter
- **THEN** it queries `account.analytic.line` for the project, sums credits as revenue and debits as cost, and returns margin (revenue - cost) and margin_percentage

#### Scenario: Project margin by month
- **WHEN** project margin is fetched with `group_by = "date:month"`
- **THEN** rows show monthly revenue, cost, and margin for the selected project(s)

#### Scenario: Project margin schema
- **WHEN** `get_schema()` is called
- **THEN** it returns measures: revenue, cost, margin, margin_pct; dimensions: project, month; chart_types: ["bar_chart", "line_chart", "kpi", "table"]

### Requirement: Project WIP source adapter
The system SHALL provide a `dashboard.source.project.wip` adapter that computes Work In Progress (unbilled hours and costs) per project.

#### Scenario: WIP calculation from timesheet
- **WHEN** `dashboard.source.project.wip.get_data()` is called
- **THEN** it queries `account.analytic.line` with `timesheet_invoice_id = False` (not yet invoiced), groups by project, and returns unbilled hours and unbilled cost

#### Scenario: WIP aging
- **WHEN** WIP data is fetched
- **THEN** rows include aging buckets: current_month, 30_days, 60_days, 90_days, 90plus based on the line's date

#### Scenario: WIP schema
- **WHEN** `get_schema()` is called
- **THEN** it returns measures: unbilled_hours, unbilled_cost; dimensions: project, aging_bucket; chart_types: ["bar_chart", "table", "kpi"]

### Requirement: Project budget source adapter
The system SHALL provide a `dashboard.source.project.budget` adapter that computes budget vs actual per project using `account.analytic.line` and project budget data.

#### Scenario: Budget vs actual
- **WHEN** `dashboard.source.project.budget.get_data()` is called
- **THEN** it compares `project.analytic_account_id` budget lines against actual `account.analytic.line` debits/credits, returning budget_amount, actual_amount, variance, variance_pct

#### Scenario: Budget schema
- **WHEN** `get_schema()` is called
- **THEN** it returns measures: budget, actual, variance, variance_pct; dimensions: project, account; chart_types: ["bar_chart", "waterfall", "kpi", "table"]
