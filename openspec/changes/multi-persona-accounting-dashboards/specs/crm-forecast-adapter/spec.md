## ADDED Requirements

### Requirement: CRM forecast source adapter
The system SHALL provide a `dashboard.source.crm.forecast` adapter in module `dashboard_vrtl_source_crm` that computes weighted revenue forecast from CRM pipeline data.

#### Scenario: Weighted forecast calculation
- **WHEN** `dashboard.source.crm.forecast.get_data()` is called
- **THEN** it queries `crm.lead` with `probability` and `expected_revenue`, computes `forecast = Σ(expected_revenue × probability / 100)`, and returns monthly forecast values with pipeline total

#### Scenario: Forecast grouped by month
- **WHEN** forecast data is requested with `group_by = "date_deadline:month"`
- **THEN** rows are grouped by expected close month, each with `forecast_value` (weighted) and `pipeline_value` (unweighted)

#### Scenario: Forecast schema
- **WHEN** `get_schema()` is called
- **THEN** it returns measures: forecast_value (monetary), pipeline_value (monetary), deal_count (integer), weighted_win_rate (percentage); chart_types: ["bar_chart", "line_chart", "funnel_chart", "kpi", "table"]

#### Scenario: CRM forecast respects stage
- **WHEN** CRM pipeline has stages with different probabilities
- **THEN** each lead's probability is taken from its `stage_id.probability`, fallback to `lead.probability`

#### Scenario: Pipeline velocity metric
- **WHEN** `dashboard.source.crm.forecast.get_data()` includes pipeline_velocity metric
- **THEN** it computes average days per stage from lead message history (date of stage change events)
