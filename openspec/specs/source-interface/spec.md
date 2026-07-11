## ADDED Requirements

### Requirement: Source interface contract
The system SHALL define `dashboard.source.mixin` as an AbstractModel requiring three methods: get_schema(), get_data(), and get_drill_action().

#### Scenario: get_schema declaration
- **WHEN** a source implements get_schema()
- **THEN** it returns a dict with measures (name, label, type), dimensions, filters (name, type, default), chart_types, drill_enabled, and filter_compatibility

#### Scenario: get_data with filters
- **WHEN** get_data() is called with measures=["revenue"], dimensions=["month"], filters={date_from: "2026-01-01", date_to: "2026-06-30"}
- **THEN** it returns {labels: [...], series: [{name, values, color}], rows: [...], currency: {...}}

#### Scenario: get_drill_action
- **WHEN** get_drill_action() is called with context from a clicked chart element
- **THEN** it returns an Odoo action dict (act_window) or None if drill is not supported

### Requirement: Builtin model source
The system SHALL provide a builtin source implementation (source_type="model") that uses _read_group() for aggregation and automatically respects ir.rule.

#### Scenario: Simple aggregation via read_group
- **WHEN** a metric with source_type="model" calls get_data() for sale.order with aggregation="sum"
- **THEN** the source calls _read_group(domain, fields=["amount_total:sum"], groupby=[...]) and returns aggregated results

#### Scenario: Model source respects ir.rule
- **WHEN** user with regional access restriction calls get_data() on sale.order
- **THEN** _read_group() automatically applies the user's ir.rule domain and only returns authorized data

### Requirement: Adapter architecture
The system SHALL support plugin Odoo modules that register adapters implementing dashboard.source.mixin for specialized data sources.

#### Scenario: Finance adapter
- **WHEN** dashboard_vrtl_source_finance is installed
- **THEN** 52 dashboard.source records are registered, one per financial report, each delegating to the corresponding mn_finance_insights AbstractModel

#### Scenario: Adapter with optimized implementation
- **WHEN** an adapter for customer_ltv is implemented with its own SQL query (replacing the original's 301-query N+1 pattern)
- **THEN** get_data() returns results in 2 queries instead of 301, with identical output structure

### Requirement: Source filter compatibility
The system SHALL allow each source to declare which global filter types it supports via filter_compatibility in get_schema().

#### Scenario: Compatible filter
- **WHEN** a source declares filter_compatibility: {period: {compatible: true, mapping: {from: "date_from", to: "date_to"}}}
- **THEN** the global period filter is applied as date_from/date_to parameters to get_data()

#### Scenario: Incompatible filter
- **WHEN** a source declares filter_compatibility: {customer: {compatible: false}}
- **THEN** the global customer filter is silently ignored for this source; the chart retains its data unchanged
