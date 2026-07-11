## ADDED Requirements

### Requirement: Kanban chart type
The system SHALL support `kanban` as a chart type in `dashboard.chart`, rendered as a card-based view with configurable fields, state-based coloring, icons, and inline actions.

#### Scenario: Kanban chart on dashboard
- **WHEN** a chart is created with `chart_type = "kanban"` referencing a metric that returns kanban-formatted rows
- **THEN** the dashboard renders a grid of kanban cards, each displaying the card's title, subtitle, state badge, and icon

#### Scenario: Kanban card click opens drill-down
- **WHEN** user clicks a kanban card that has drill_enabled=True and the underlying source supports get_drill_action()
- **THEN** the system navigates to the resource (e.g., opens account.journal form view or account.move tree view filtered by journal)

#### Scenario: Kanban chart respects group access
- **WHEN** a kanban chart has chart_group_ids set to ["Accounting Managers"]
- **THEN** only users in that group see the kanban cards; other users see remaining charts on the dashboard

### Requirement: Kanban card state visualization
The system SHALL support state-based coloring and icon display on kanban cards via configurable state_field, state_colors, and state_icons mappings on the metric.

#### Scenario: State field mapping
- **WHEN** a metric defines `state_field = "journal_state"` with `state_colors = {"active": "#28a745", "locked": "#6c757d", "draft": "#ffc107"}`
- **THEN** each kanban card shows a colored ribbon or border matching the row's state value, and a state badge with the translated state label

#### Scenario: State icon display
- **WHEN** a metric defines `state_icons = {"active": "fa-check-circle", "locked": "fa-lock", "draft": "fa-pencil"}`
- **THEN** each kanban card renders the corresponding Font Awesome icon next to the state badge

#### Scenario: Missing state mapping
- **WHEN** a row has a state value not present in state_colors or state_icons
- **THEN** the card renders with a default neutral color (#e9ecef) and no icon, without error

### Requirement: Kanban card field layout
The system SHALL render kanban cards with a configurable field layout: title, subtitle, body fields, and footer fields, mapped from metric row columns.

#### Scenario: Card field mapping
- **WHEN** a metric's kanban config defines `card_title_field = "name"`, `card_subtitle_field = "code"`, `card_body_fields = ["pending_moves", "total_balance"]`, `card_footer_fields = ["last_activity"]`
- **THEN** each card shows the journal name as title, code as subtitle, pending_moves and total_balance as body KPI badges, and last_activity in the footer

#### Scenario: Card body KPI formatting
- **WHEN** a card_body_field references a numeric measure with defined unit (e.g., currency, count, percentage)
- **THEN** the value is formatted according to the unit (e.g., "125 000 kr" for currency, "42" for count, "3.2%" for percentage)

### Requirement: Kanban grouping
The system SHALL support grouping kanban cards into columns by a configurable group field, rendering column headers with group labels and counts.

#### Scenario: Group by journal type
- **WHEN** a kanban chart defines `group_by = "type"` on the metric, and the data contains journals of types "sale", "purchase", "bank", "cash", "general"
- **THEN** cards are arranged in labeled columns, one per journal type, with a count badge on each column header (e.g., "Bank (3)")

#### Scenario: No grouping
- **WHEN** a kanban chart has no group_by defined
- **THEN** all cards render in a single fluid grid, wrapping responsively based on available width

#### Scenario: Empty group
- **WHEN** a group has zero cards after filtering
- **THEN** the column header still renders with count "(0)" and an empty-state message "No records"

### Requirement: Kanban inline actions
The system SHALL support configurable inline action buttons on kanban cards, rendered in the card footer or as a dropdown menu.

#### Scenario: Inline action "New Entry"
- **WHEN** a kanban config defines `card_actions = [{"name": "new_move", "label": "New Entry", "icon": "fa-plus", "action": "ir.actions.act_window", "params": {"res_model": "account.move", "context": {"default_journal_id": "{id}"}}}]`
- **THEN** each card shows a "New Entry" button that opens account.move form with the journal pre-filled

#### Scenario: Action with confirmation
- **WHEN** a kanban config defines an action with `confirm = "Are you sure?"`
- **THEN** clicking the action button shows a confirmation dialog before executing

#### Scenario: Maximum visible actions
- **WHEN** a kanban config defines more than 3 card_actions
- **THEN** the first 2 actions render as inline buttons, remaining actions render in a "More" dropdown menu

### Requirement: Kanban cross-chart filtering
The system SHALL allow kanban cards to act as filter sources for other charts on the same dashboard, consistent with existing cross-chart interaction patterns.

#### Scenario: Click journal card filters other charts
- **WHEN** user clicks a kanban card (not an action button) and the dashboard has other charts with compatible filter_compatibility
- **THEN** a filter is applied to the dashboard (e.g., `journal_id = 5`), and all compatible charts re-fetch data with the filter

#### Scenario: Click kanban card in drill mode
- **WHEN** user is in drill-down mode (drill stack is active) and clicks a kanban card
- **THEN** the drill action takes priority over cross-chart filtering; the cross-chart filter is NOT applied

### Requirement: Kanban empty state
The system SHALL display a meaningful empty state when a kanban chart returns no data.

#### Scenario: No journals match filters
- **WHEN** a kanban chart for account.journal returns zero rows due to filter constraints
- **THEN** the chart area shows an empty state with message "No journals match the current filters" and a "Clear filters" button

#### Scenario: No kanban configuration
- **WHEN** a kanban chart is created but no metric is assigned
- **THEN** the chart area shows "Configure a metric to display kanban cards" with a configuration button
