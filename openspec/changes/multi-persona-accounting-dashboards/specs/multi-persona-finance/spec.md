## ADDED Requirements

### Requirement: Seven persona-based dashboards
The system SHALL provide 7 pre-built dashboards in `dashboard_vrtl_finance` targeting CEO, CFO (Daily + Monthly), Department Head, Bookkeeper, Project Manager, and Sales Manager personas.

#### Scenario: All dashboards installable
- **WHEN** `dashboard_vrtl_finance` is installed
- **THEN** 7 dashboard YAML files are loaded: `ceo_overview`, `cfo_daily` (updated), `cfo_monthly`, `department_spend`, `bookkeeper_workspace`, `project_manager`, `sales_manager`

#### Scenario: Dashboard visibility configurable
- **WHEN** an admin navigates to Accounting → Configuration → Dashboards
- **THEN** a checkbox list shows all 7 dashboards; unchecked dashboards are deactivated (menu hidden but records preserved)

### Requirement: CEO dashboard
The system SHALL provide a `ceo_overview` dashboard with high-level KPIs: Revenue MTD, Gross Margin %, EBITDA, Cash Balance, Burn Rate, and trends for revenue, working capital, and customer concentration.

#### Scenario: CEO dashboard KPIs
- **WHEN** the CEO dashboard is loaded
- **THEN** it displays 5 KPI cards (Revenue, Gross Margin, EBITDA, Cash, Burn Rate) and 4 trend charts (Revenue 12M, Working Capital Cycle, Customer Concentration Pareto, Free Cash Flow)

#### Scenario: CEO dashboard sources
- **WHEN** the CEO dashboard fetches data
- **THEN** it uses metrics from: financial_ratios, cash_position, burn_rate, multi_year, free_cash_flow, working_capital, three_statement, recurring_revenue, customer_concentration, cash_flow_forecast

### Requirement: CFO Daily dashboard (updated)
The system SHALL update the existing `cfo_daily` dashboard to include 18 charts covering: bank reconciliation, aged receivables, late invoice tracking, daily sales, anomalous transaction detection, and negative balance alerts.

#### Scenario: Expanded CFO Daily
- **WHEN** CFO Daily is loaded
- **THEN** it displays KPI row (Revenue, Expenses, Bank Balance, AR Total, AP Total), revenue vs expenses trend, AR aging bars, late invoice tracker table, and anomalous transactions list

### Requirement: CFO Monthly dashboard
The system SHALL provide a `cfo_monthly` dashboard with 20 charts: P&L by month, budget vs actual heatmap, tax summary, liquidity stress test, currency exposure, journal audit, vendor concentration, and year-end checklist.

#### Scenario: CFO Monthly P&L
- **WHEN** CFO Monthly is loaded
- **THEN** it displays Net Income KPI, P&L by month (stacked bar: revenue + expenses), Budget vs Actual heatmap, AR/AP combined aging, and Tax Reconciliation summary

### Requirement: Department Head dashboard
The system SHALL provide a `department_spend` dashboard filtered by cost center (analytic account) with: budget remaining KPI, expenses MTD by category, vendor spend analysis, and top discount recipients.

#### Scenario: Department spend with cost center filter
- **WHEN** Department Head dashboard is loaded and a cost center filter is applied
- **THEN** all charts show data scoped to the selected analytic account

### Requirement: Bookkeeper workspace dashboard
The system SHALL provide a `bookkeeper_workspace` dashboard featuring a draggable journal kanban (account.move cards grouped by journal), bank reconciliation status, journal audit trail, and late invoice alerts.

#### Scenario: Bookkeeper kanban with drag-and-drop
- **WHEN** bookkeeper drags a draft invoice card from "Bank" to "Sales" column
- **THEN** the account.move record's journal_id is updated, and the card moves to the new column

#### Scenario: Bookkeeper kanban click opens record
- **WHEN** bookkeeper clicks a kanban card
- **THEN** the account.move form view opens for that record

### Requirement: Project Manager dashboard
The system SHALL provide a `project_manager` dashboard using `dashboard_vrtl_source_project` adapters with: project margin %, billable hours, WIP total, cost to complete, and project budget vs actual.

#### Scenario: Project margin trend
- **WHEN** Project Manager dashboard is loaded with a project filter
- **THEN** it displays project margin KPI (revenue - cost), billable vs non-billable hours stacked bar, WIP aging table, and budget vs actual waterfall

### Requirement: Sales Manager dashboard
The system SHALL provide a `sales_manager` dashboard with CRM-weighted revenue forecast, pipeline velocity, sales analytics, customer LTV, churn risk, and margin by salesperson.

#### Scenario: CRM-weighted revenue forecast
- **WHEN** Sales Manager dashboard is loaded
- **THEN** it displays weighted pipeline value KPI, forecast vs quota gauge chart, funnel by stage, win/loss trend, and rep performance bar chart

### Requirement: Dashboard activation settings
The system SHALL provide a configuration view under Accounting → Configuration → Dashboards where admin can toggle which persona dashboards are active.

#### Scenario: Deactivate a dashboard
- **WHEN** admin unchecks "CEO Overview" in dashboard settings and saves
- **THEN** the CEO dashboard menu is hidden (menu_active=False), charts and metrics are preserved
