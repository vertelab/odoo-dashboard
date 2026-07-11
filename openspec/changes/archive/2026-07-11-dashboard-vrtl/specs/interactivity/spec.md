## ADDED Requirements

### Requirement: Global dashboard filters
The system SHALL support dashboard-level filters (date_range, many2one, companies, selection) that can be mapped to source-specific parameters per chart.

#### Scenario: Period filter with shortcuts
- **WHEN** a dashboard defines a date_range filter "Period" with shortcuts ["This Month", "Last Quarter", "Rolling 12M"]
- **THEN** the filter bar shows a dropdown with the shortcuts; selecting one updates all compatible charts

#### Scenario: Filter mapping per chart
- **WHEN** a chart has filter_mapping: {period: {compatible: true, mapping: {from: "date_from", to: "date_to"}}}
- **THEN** the global period filter is translated to date_from/date_to when calling that chart's source

#### Scenario: Incompatible filter silently skipped
- **WHEN** a chart has filter_mapping: {customer: {compatible: false}}
- **THEN** when the customer filter is activated, that chart retains its current data without error

### Requirement: Cross-chart interactivity
The system SHALL propagate filter events from one chart to all compatible charts on the same dashboard.

#### Scenario: Click chart to filter all
- **WHEN** user clicks the "Nord" segment in a Pie chart that emits filter {region: "Nord", region_id: 5}
- **THEN** all charts with filter_mapping.region.compatible=true refresh with region_id=5; charts without region support remain unchanged

#### Scenario: Stacked filters
- **WHEN** user clicks "Nord" then clicks "Product A"
- **THEN** both filters are active simultaneously; all compatible charts are filtered by region=Nord AND product=Product A

#### Scenario: Remove stacked filter
- **WHEN** user clicks ✕ on the "Nord" filter badge in the filter bar
- **THEN** "Nord" filter is removed; only "Product A" filter remains active; all charts re-query

### Requirement: Drill-down navigation
The system SHALL support three drill-down types: group-by drill (hierarchical), cross-chart drill (navigate to another chart), and action drill (open Odoo view).

#### Scenario: Group-by drill
- **WHEN** user double-clicks "Nord" in a chart with drill_path: [{field: product_id, label: "Produkt"}]
- **THEN** the dashboard zooms into Nord, showing products within Nord; a breadcrumb "Dashboard > Nord" appears

#### Scenario: Multi-level drill
- **WHEN** user double-clicks "Product A" from the Nord drill level with next drill_path: [{field: partner_id, label: "Kund"}]
- **THEN** breadcrumb shows "Dashboard > Nord > Product A"; drill_stack has two entries

#### Scenario: Action drill
- **WHEN** user clicks a row in a table chart with drill: {type: action, action: "res.partner.form", param_field: id}
- **THEN** the res.partner form view opens for the clicked record

#### Scenario: Browser back from drill
- **WHEN** user presses browser back while in a drill-down level
- **THEN** the drill_stack is popped; the previous level's data and breadcrumb are restored

### Requirement: Filter state persistence
The system SHALL persist active filter state in the URL hash and restore it on page load.

#### Scenario: Share filtered dashboard
- **WHEN** dashboard has active filters period=Q1-2026 and region=Nord
- **THEN** URL contains #filters=period:2026-Q1,region:5; sharing this URL shows the same filtered dashboard

#### Scenario: Drill state in URL
- **WHEN** user has drilled down to "Nord > Product A"
- **THEN** URL contains #drill=level1:Nord:region_id=5/level2:Product_A:product_id=42
