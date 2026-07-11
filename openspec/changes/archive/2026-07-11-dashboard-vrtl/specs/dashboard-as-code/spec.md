## ADDED Requirements

### Requirement: YAML dashboard format
The system SHALL support a YAML format for defining complete dashboards including metadata, metrics, filters, charts, alerts, and schedules.

#### Scenario: Complete YAML dashboard
- **WHEN** a YAML file defines a dashboard with 4 charts, 2 metrics, 1 filter, and 1 alert
- **THEN** loading the YAML creates/updates the corresponding ORM records (dashboard, metric, chart, filter, alert)

#### Scenario: Chart references metric by key
- **WHEN** a YAML chart references `metric: sales.net_revenue`
- **THEN** the chart is linked to the metric with key "sales.net_revenue"; if the metric doesn't exist, it is created from the YAML definition

### Requirement: YAML to ORM sync
The system SHALL provide a load_from_yaml() method on dashboard.dashboard that parses YAML and creates or updates ORM records.

#### Scenario: First-time load
- **WHEN** load_from_yaml() runs on a YAML file with a new dashboard key
- **THEN** dashboard.dashboard, dashboard.metric, and dashboard.chart records are created; ir.actions.client and ir.ui.menu are created

#### Scenario: Update existing dashboard
- **WHEN** load_from_yaml() runs on a YAML file with an existing dashboard key
- **THEN** existing records are updated (not duplicated). Charts with customized=True are NOT overwritten.

#### Scenario: Export ORM to YAML
- **WHEN** export_to_yaml() is called on a dashboard
- **THEN** it generates a YAML file matching the dashboard-as-code format, suitable for version control

### Requirement: Domain-specific dashboard modules
The system SHALL support Odoo modules that deliver pre-built dashboards as YAML data files.

#### Scenario: Sales domain module
- **WHEN** dashboard_vrtl_sales is installed
- **THEN** 3 dashboards (Sales Executive, Sales Pipeline, Team Performance) appear in the menu with all charts pre-configured

#### Scenario: Finance domain module
- **WHEN** dashboard_vrtl_finance is installed and account module is present
- **THEN** 4 dashboards (CFO Daily, CFO Monthly, AR Aging, AP Aging) appear in the menu

### Requirement: Dashboard-as-code key-based references
The system SHALL use string keys (not database IDs) for cross-references in YAML, ensuring portability across instances.

#### Scenario: Metric referenced by key across instances
- **WHEN** a YAML dashboard defining metric key "sales.net_revenue" is loaded into a different Odoo instance
- **THEN** the metric is created with that key; charts reference it by key regardless of database ID differences

#### Scenario: Idempotent loading
- **WHEN** the same YAML file is loaded twice
- **THEN** the second load is a no-op (upsert by key); no duplicate records are created
