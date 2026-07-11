## MODIFIED Requirements

### Requirement: Kanban chart type
The system SHALL support `kanban` as a chart type in `dashboard.chart`, rendered as a card-based view with configurable fields, state-based coloring, icons, and inline actions. When `kanban_draggable` is enabled on the metric, cards SHALL be draggable between group columns.

#### Scenario: Kanban chart on dashboard
- **WHEN** a chart is created with `chart_type = "kanban"` referencing a metric that returns kanban-formatted rows
- **THEN** the dashboard renders a grid of kanban cards, each displaying the card's title, subtitle, state badge, and icon

#### Scenario: Kanban card click opens drill-down
- **WHEN** user clicks a kanban card that has drill_enabled=True and the underlying source supports get_drill_action()
- **THEN** the system navigates to the resource (e.g., opens account.journal form view or account.move tree view filtered by journal)

#### Scenario: Kanban chart respects group access
- **WHEN** a kanban chart has chart_group_ids set to ["Accounting Managers"]
- **THEN** only users in that group see the kanban cards; other users see remaining charts on the dashboard

#### Scenario: Draggable kanban card
- **WHEN** a kanban chart references a metric with `kanban_draggable = True` and `kanban_drag_group_field = "journal_id"`
- **THEN** cards are draggable between group columns; dropping writes `journal_id` on the card's record via `orm.write()`

#### Scenario: Non-draggable kanban (default)
- **WHEN** a kanban chart references a metric without `kanban_draggable`
- **THEN** cards are static, clickable for drill-down/filter, but not draggable
