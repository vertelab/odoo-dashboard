## ADDED Requirements

### Requirement: Kanban draggable configuration
The system SHALL support `kanban_draggable` (Boolean, default False) and `kanban_drag_group_field` (Char) fields on `dashboard.metric` to enable HTML5 drag-and-drop on kanban cards.

#### Scenario: Draggable kanban metric
- **WHEN** a metric defines `kanban_draggable = True` and `kanban_drag_group_field = "journal_id"`
- **THEN** kanban cards rendered from this metric are draggable, and dropping a card onto a different column writes the target group value to the card's record

#### Scenario: Non-draggable kanban (default)
- **WHEN** a metric has `kanban_draggable = False` (default)
- **THEN** kanban cards are not draggable and behave as read-only visualization

### Requirement: Drag-and-drop visual feedback
The system SHALL provide visual feedback during drag-and-drop operations: a semi-transparent ghost of the dragged card, highlight on valid drop zones, and an "invalid target" cursor on invalid drop zones.

#### Scenario: Card drag start
- **WHEN** user starts dragging a kanban card
- **THEN** a semi-transparent copy follows the cursor, the original card becomes opaque (opacity 0.4), and valid drop zones show a dashed border highlight

#### Scenario: Card dropped on valid target
- **WHEN** user drops a draggable kanban card onto a different group column
- **THEN** the card's `kanban_drag_group_field` value is written via `orm.write()`, the kanban re-fetches data, and the card appears in the new column

#### Scenario: Card dropped on same column
- **WHEN** user drops a draggable kanban card on the same column it originated from
- **THEN** no write operation occurs, and the card snaps back with no data re-fetch

#### Scenario: Card dropped on invalid target
- **WHEN** user drags a kanban card outside any valid drop zone and releases
- **THEN** the card snaps back to its original position with no write operation

### Requirement: Drop target res_model validation
The system SHALL validate that the dragged card's `res_model` matches the target column's expected model before allowing the drop.

#### Scenario: Drop model mismatch prevented
- **WHEN** user drags a `crm.lead` card onto a column expecting `account.move` records
- **THEN** the drop zone shows an "invalid" cursor and the drop is rejected

### Requirement: Post-drop data refresh
The system SHALL re-fetch the metric's data after a successful drop to reflect the updated group assignments.

#### Scenario: Data refresh after drop
- **WHEN** a card is dropped and `orm.write()` succeeds
- **THEN** the KanbanView component re-fetches data via the existing metric pipeline and re-renders with updated columns

### Requirement: Drag-and-drop in YAML
The system SHALL support `kanban_draggable` and `kanban_drag_group_field` in the YAML metric definition under the `kanban` section.

#### Scenario: YAML draggable kanban metric
- **WHEN** a YAML metric defines `kanban: {draggable: true, drag_group_field: journal_id}`
- **THEN** the loaded metric has `kanban_draggable = True` and `kanban_drag_group_field = "journal_id"`
