## ADDED Requirements

### Requirement: CRM forecast adapter registration
The system SHALL register `dashboard.source.crm.forecast` as a dashboard.source when `dashboard_vrtl_source_crm` is installed.

#### Scenario: CRM forecast source available
- **WHEN** `dashboard_vrtl_source_crm` is installed
- **THEN** a `dashboard.source` record exists with `technical_name = "crm.forecast"`, `model_name = "dashboard.source.crm.forecast"`, `source_type = "service"`, `category = "CRM"`

### Requirement: Project adapters registration
The system SHALL register `dashboard.source.project.margin`, `dashboard.source.project.wip`, and `dashboard.source.project.budget` as dashboard.source records when `dashboard_vrtl_source_project` is installed.

#### Scenario: Project sources available
- **WHEN** `dashboard_vrtl_source_project` is installed
- **THEN** three `dashboard.source` records exist for project.margin, project.wip, and project.budget, each with `source_type = "service"`, `category = "Project"`
