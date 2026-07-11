## MODIFIED Requirements

### Requirement: YAML dashboard format
The system SHALL support a YAML format for defining complete dashboards including metadata, metrics, filters, charts, alerts, and schedules. The dashboard section SHALL also support `menu_mode` and `replaces_menu` for menu integration.

#### Scenario: Complete YAML dashboard
- **WHEN** a YAML file defines a dashboard with 4 charts, 2 metrics, 1 filter, and 1 alert
- **THEN** loading the YAML creates/updates the corresponding ORM records (dashboard, metric, chart, filter, alert)

#### Scenario: Chart references metric by key
- **WHEN** a YAML chart references `metric: sales.net_revenue`
- **THEN** the chart is linked to the metric with key "sales.net_revenue"; if the metric doesn't exist, it is created from the YAML definition

#### Scenario: Dashboard with menu_mode: replace
- **WHEN** a YAML dashboard defines `menu_mode: replace` and `replaces_menu: account.menu_finance`
- **THEN** the loaded dashboard replaces the Accounting menu's action with this dashboard

#### Scenario: Dashboard with menu_mode: submenu
- **WHEN** a YAML dashboard defines `menu_mode: submenu` and `parent_menu: account.menu_finance`
- **THEN** the loaded dashboard creates a child menu under Accounting

#### Scenario: Kanban metric with drag-and-drop in YAML
- **WHEN** a YAML metric defines `kanban: {draggable: true, drag_group_field: journal_id}`
- **THEN** the metric record has `kanban_draggable = True` and `kanban_drag_group_field = "journal_id"`

### Requirement: YAML to ORM sync
The system SHALL provide a load_from_yaml() method on dashboard.dashboard that parses YAML and creates or updates ORM records, including menu_mode and kanban_draggable fields.

#### Scenario: First-time load
- **WHEN** load_from_yaml() runs on a YAML file with a new dashboard key
- **THEN** dashboard.dashboard, dashboard.metric, and dashboard.chart records are created; ir.actions.client and ir.ui.menu are created with the configured menu_mode

#### Scenario: Update existing dashboard
- **WHEN** load_from_yaml() runs on a YAML file with an existing dashboard key
- **THEN** existing records are updated (not duplicated). Charts with customized=True are NOT overwritten.

#### Scenario: Export ORM to YAML
- **WHEN** export_to_yaml() is called on a dashboard
- **THEN** it generates a YAML file matching the dashboard-as-code format, including menu_mode, replaces_menu, and kanban_draggable fields, suitable for version control
