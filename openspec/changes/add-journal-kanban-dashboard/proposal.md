## Why

Odoo-användare inom redovisning navigerar dagligen mellan journaler för att granska, bokföra och följa upp verifikationer. Idag måste de lämna dashboard-vyn för att öppna Odoos standard-kanbanvy för `account.journal`. Genom att addera kanban som en inbyggd chart-typ i dashboard_vrtl kan användare få en samlad översikt över sina journaler direkt i dashboarden — med statusindikatorer, snabbnavigering och samma interaktiva kontext (filter, drill-down, alerts) som övriga charts.

## What Changes

- **Ny chart_type `kanban`** i `dashboard.chart` — renderas som kortvy med konfigurerbara fält, färgkodning, och statusikoner
- **Ny OWL-komponent `KanbanView`** — renderar kanban-kort i dashboard-griden, integrerat med befintlig chart-dispatch (`ChartComponent`)
- **Kanban-specifik datamodell** — metrics som levererar `rows` med `state`, `color`, `icon`, `avatar` och `actions` för varje kort
- **Source-adapter `dashboard_vrtl_source_account`** — ny domänmodul med minst en adapter: `dashboard.source.account.journals` som returnerar journal-data i kanban-format (status, antal moves, balans, senaste aktivitet)
- **Kanban-konfiguration i YAML** — stöd för `chart_type: kanban` i dashboard-as-code YAML-formatet med fältmappning, gruppering, och actiondefinitioner
- **Interaktivitet** — klick på kanban-kort → drill-down (öppna journalens moves), cross-chart filtering (klicka journal → filtrera andra charts), och inline-actions (skapa ny verifikation, öppna journal)

## Capabilities

### New Capabilities
- `kanban-chart`: Kanban chart type in dashboard — OWL rendering, card configuration, state-based coloring, inline actions, drill-down, and cross-chart filter integration

### Modified Capabilities
- `core-models`: Lägg till `kanban` som chart_type i `dashboard.chart`, utöka `dashboard.metric` med kanban-specifika konfigurationsfält (card_template, group_by_state, state_field, state_colors)

## Impact

- **dashboard_vrtl/models/dashboard_chart.py**: Nytt val `kanban` i `chart_type` selection
- **dashboard_vrtl/models/dashboard_metric.py**: Nya fält för kanban-konfiguration
- **dashboard_vrtl/static/src/js/**: Ny OWL-komponent `KanbanView` + `KanbanCard`
- **dashboard_vrtl/views/dashboard_templates.xml**: Ny dispatch i `ChartComponent`
- **dashboard_vrtl_source_account/**: Ny modul med `dashboard.source.account.journals` adapter
- **dashboard_vrtl/__manifest__.py**: Beroende på `account` (för journal-adaptern)
- **AI SKILL.md**: Uppdaterad med kanban-mönster, fältmappning, och rekommendationer
- **dashboard-as-code spec**: Utökad YAML-syntax för kanban-charts
