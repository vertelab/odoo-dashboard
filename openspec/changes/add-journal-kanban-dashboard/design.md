## Context

`dashboard_vrtl` renders charts via AmCharts through OWL components dispatched in `ChartComponent`. The current architecture handles 23 chart types (kpi, bar, line, pie, table, etc.) — all visualization-focused. There is no card/kanban view. Users needing a journal overview must leave the dashboard and use Odoo's native `account.journal` kanban.

The existing data pipeline (`dashboard.metric` → `get_data()` → `{rows: [{col: val}, ...]}` already supports row-based data, which maps naturally to kanban cards. The main gap is rendering, card configuration, and a journal-specific source adapter.

### Constraints
- Must work within the existing grid-stack layout system (charts are grid items)
- Must respect the existing filter → chart → drill-down interaction pattern
- Must support dashboard-as-code YAML format
- Must not break existing chart types
- Odoo 18 OWL (not legacy widget system)

## Goals / Non-Goals

**Goals:**
- Add `kanban` as a first-class chart type in the dashboard grid
- Build OWL components (`KanbanView`, `KanbanCard`) that render card grids with grouping, states, and actions
- Extend `dashboard.metric` with kanban configuration fields (card layout, state mapping, actions)
- Create `dashboard_vrtl_source_account` module with a journal adapter
- Support kanban in dashboard-as-code YAML format
- Integrate kanban with existing cross-chart filtering and drill-down

**Non-Goals:**
- Replacing Odoo's native kanban view system globally
- Drag-and-drop card reordering within kanban columns
- Inline editing of card fields (read-only display)
- Kanban as a replacement for tree/form views — this is a dashboard visualization only
- Generic adapter builder for arbitrary Odoo models as kanban (that's a future concern)

## Decisions

### Decision 1: OWL-based rendering, not AmCharts
**Choice**: Build `KanbanView` as a standalone OWL component, not an AmCharts plugin.
**Rationale**: AmCharts is a charting library, not a card/grid framework. Kanban cards are DOM-native (HTML/CSS with flexbox/grid), not SVG/canvas. Building in OWL gives full control over card rendering, event handling, and Odoo integration (field widgets, t-call templates).
**Alternative considered**: Use AmCharts' "force-directed" or custom renderer. Rejected — too much abstraction inversion for DOM-native content.

### Decision 2: Kanban config stored on dashboard.metric, not dashboard.chart
**Choice**: Card layout fields (card_title_field, state_field, state_colors, card_actions, group_by) live on `dashboard.metric`.
**Rationale**: The metric defines the data shape — which columns exist and what they mean. The chart only selects chart_type and position. This is consistent with how group_by already works (it's on chart, but the column reference is metric-aware). Kanban config describes how to interpret the metric's output, so it belongs on the metric.
**Alternative considered**: Put all kanban config on `dashboard.chart`. Rejected — would duplicate config for every chart referencing the same metric, and violates separation of data definition (metric) vs presentation choice (chart).

### Decision 3: New module `dashboard_vrtl_source_account` for journal adapter
**Choice**: Create a separate Odoo module for account-specific sources, following the pattern of `dashboard_vrtl_source_hr`.
**Rationale**: Keeps the core `dashboard_vrtl` module account-agnostic. Users without `account` installed get no errors. Domain adapters are independently installable. Consistent with existing architecture (hr source module already exists).
**Alternative considered**: Put journal adapter directly in `dashboard_vrtl`. Rejected — creates hard dependency on `account` in the core module.

### Decision 4: Kanban data format uses standard rows, not custom structure
**Choice**: Kanban cards read from the existing `rows` array in get_data() output, with convention-based column naming.
**Rationale**: No need to change the source interface contract. Kanban is just another consumer of the same data format. Columns like `name`, `state`, `icon` are conventions the adapter declares via get_schema().
**Alternative considered**: New `cards` key in get_data() output. Rejected — adds complexity to the interface for a presentation concern.

### Decision 5: Grouping uses metric's group_by, not a new field
**Choice**: Kanban column grouping reads from the data's grouped structure (if the metric was called with group_by) or from a kanban-specific group field.
**Rationale**: The existing data pipeline already supports group_by. When a metric's data is fetched with `group_by: "type"`, the rows come back with type as a column. The kanban view groups cards by that column value.
**Alternative considered**: Separate kanban_group_field. Accepted as an additional option — kanban_group_field on the metric explicitly declares the grouping dimension, decoupling it from the metric's default aggregation group_by.

### Decision 6: Card actions use ir.actions system, not custom JS
**Choice**: Card action buttons trigger standard Odoo actions (act_window, act_url, etc.) via the action service.
**Rationale**: Consistent with Odoo's action framework. No custom routing logic. Actions are declarative in YAML/metric config.
**Alternative considered**: Custom JS event handlers per card. Rejected — harder to configure, not YAML-friendly, breaks Odoo's action security model.

## Risks / Trade-offs

- **[Risk] Kanban cards in a grid-stack item may have limited vertical space** → Mitigation: Kanban charts default to a taller grid item (3 rows instead of 2). Configurable min-height.
- **[Risk] Performance with many cards (100+ journals)** → Mitigation: Virtual scrolling or pagination if card count exceeds 50. Initial release targets <100 cards (realistic for account.journal).
- **[Risk] State color conflicts with dashboard theme** → Mitigation: State colors are configurable per metric. Default palette uses accessible contrast ratios.
- **[Trade-off] No drag-and-drop** → Explicitly out of scope. Keeps implementation simple and avoids conflict with grid-stack's own drag behavior.
- **[Trade-off] Read-only cards** → Cards display data but don't support inline editing. Users click through to the actual record. Simplifies state management and avoids data consistency issues.
