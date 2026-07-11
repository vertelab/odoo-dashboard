## ADDED Requirements

### Requirement: SKILL.md shipped with core module
The system SHALL include a SKILL.md file in the dashboard_vrtl module root, providing AI agents with the knowledge to build dashboards from natural language.

#### Scenario: AI loads skill
- **WHEN** an AI agent with access to dashboard_vrtl/SKILL.md receives a dashboard-building request
- **THEN** the skill provides Odoo model knowledge, taxonomy lookups, visualization rules, and metric creation patterns

### Requirement: Five-phase dashboard creation workflow
The SKILL.md SHALL guide AI through five phases: Understand → Design → Metrics → Validate → Persist.

#### Scenario: Natural language dashboard request
- **WHEN** user says "Skapa en försäljningsdashboard med omsättning per månad och topp 5 produkter"
- **THEN** AI identifies domain (sale.order, sale.order.line), designs layout (KPI + line + bar), creates metrics (net_revenue, top_products), validates against database, and persists as YAML

#### Scenario: AI asks clarifying questions
- **WHEN** user request is ambiguous (e.g., "visa intäkter" without specifying date field)
- **THEN** AI asks: "Ska intäkterna baseras på orderdatum eller fakturadatum?"

### Requirement: Adapter creation mode
The SKILL.md SHALL include an adapter mode for creating new data sources from existing AbstractModel methods or custom SQL.

#### Scenario: Create adapter for existing report
- **WHEN** user wants to make an existing financial report available as a dashboard source
- **THEN** AI generates an adapter implementing dashboard.source.mixin with get_schema() and get_data(), registering it as a dashboard.source

#### Scenario: Create adapter with SQL optimization
- **WHEN** user asks to create an adapter and the original implementation has N+1 performance issues
- **THEN** AI generates an optimized implementation using _read_group() or security-bridged SQL instead of just delegating

### Requirement: SKILL.md knowledge domains
The SKILL.md SHALL cover: Odoo models and fields (sale, account, stock, hr, project), taxonomy concepts (taxonomier.se), visualization rules (data type → chart type), security rules (read_group first, ID-bridge for SQL, company filter), and composite metrics.

#### Scenario: Model knowledge lookup
- **WHEN** AI needs to find the model for "försäljning"
- **THEN** SKILL.md maps it to sale.order with key fields: amount_total, date_order, state, partner_id

#### Scenario: Visualization rules
- **WHEN** AI designs charts for "omsättning per månad"
- **THEN** SKILL.md recommends line chart (time series), 12 data points (rolling year), with a KPI summary tile

### Requirement: Validation before persistence
The SKILL.md SHALL require AI to test-run each metric against the database and verify results before saving.

#### Scenario: Metric validation
- **WHEN** AI creates metric "sales.net_revenue"
- **THEN** AI executes a test query with default filters, checks the result is non-empty and within reasonable magnitude, and shows the value to the user for confirmation

#### Scenario: Validation failure
- **WHEN** a test query returns empty results or an error
- **THEN** AI reports the issue and suggests corrections (e.g., check domain filters, verify account_type mapping)
