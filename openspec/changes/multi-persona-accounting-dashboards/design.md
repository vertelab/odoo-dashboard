## Context

`dashboard_vrtl` har nu kanban-stöd (`add-journal-kanban-dashboard`) och 57 adapterade finansiella rapporter via `dashboard_vrtl_source_finance`. Men tre kärnfunktioner saknas för produktion: meny-integration, drag-and-drop kanban, och rollbaserade dashboards.

Gap-analyser från `plan/odoo-project` och `plan/odoo-management-system` identifierar entreprenad-specifika behov: projekt-P&L, WIP, SVA. Dessa kräver nya adaptrar.

### Constraints
- Alla dashboards i EN modul (`dashboard_vrtl_finance`), valbara via Settings
- Drag-and-drop endast på explicit konfigurerade metrics (inte alla kanban)
- Meny-integration måste vara reversibel (original-action sparas)
- CRM-forecast och project-adaptrar i separata moduler (beroendehantering)

## Goals / Non-Goals

**Goals:**
- Dashboard kan ersätta Odoo huvudmeny som förstasida (2 fält + logik i `create_update_menu`)
- Kanban-kort får configurerbar drag-and-drop (HTML5-events + `orm.write`)
- 7 rollbaserade dashboards: CEO, CFO Daily/Monthly, Avd.chef, Bokförare, Projekt, Sälj
- Bokförare-dashboard med funktionell draggable journal-kanban
- 3 nya source-adaptrar (crm.forecast, project.margin, project.wip, project.budget)
- Settings-vy för att toggla dashboards

**Non-Goals:**
- Drag-and-drop mellan OLIKA dashboards (endast inom samma kanban-vy)
- SVA (successiv vinstavräkning) — separat modul, utanför scope
- ÄTA-hantering i dashboard — hanteras av `contract_aaw`
- Projektdagbok — separat modul, utanför scope
- Offline-stöd för kanban
- Realtids-synkronisering mellan användare (collaborative drag-and-drop)

## Decisions

### Decision 1: Menu replacement via `replaces_menu_id` + original action storage
**Choice**: Lagra original-menyns action som textsträng (t.ex. `"ir.actions.act_window,123"`) på dashboarden, återställ vid borttagning.
**Rationale**: Enkelt, inga nya modeller. Action-ref är stabil. Vid `menu_mode=replace` sätts `ir.ui.menu.action` till dashboardens `ir.actions.client`-ref.
**Alternative considered**: Skapa en wrapper-action som redirectar. För komplext, risk för redirect-loopar.

### Decision 2: Drag-and-drop via HTML5 native events + Odoo ORM
**Choice**: Använd HTML5 `dragstart`, `dragover`, `drop`, `dragend` i KanbanCard + KanbanView OWL-komponenter. Vid drop: `useService("orm").write(res_model, [id], {field: value})`.
**Rationale**: Inga externa bibliotek. OWL-komponenter har redan tillgång till `orm`-servicen. HTML5 drag-and-drop fungerar i alla moderna webbläsare.
**Alternative considered**: SortableJS / interact.js. Mer flexibelt men tyngre beroende. Överkurs för enkel column-to-column drag.

### Decision 3: All dashboards i `dashboard_vrtl_finance`, adaptrar i egna moduler
**Choice**: Dashboard-YAML:er i `dashboard_vrtl_finance/data/dashboards/`. CRM-forecast i `dashboard_vrtl_source_crm`. Projekt-adaptrar i `dashboard_vrtl_source_project`.
**Rationale**: Separat beroendehantering. CRM-adaptern kräver `crm`, projekt-adaptern kräver `project` + `hr_timesheet`. Finance-dashboards kräver bara `account` + `mn_finance_insights`. Ingen mening att tvinga CRM/projekt-beroenden på alla.
**Alternative considered**: Allt i en modul. För brett beroendeträd, svårt att installera selektivt.

### Decision 4: Settings-vy via `res.config.settings`
**Choice**: Använd Odoos standard `res.config.settings` med boolean-fält per dashboard. Vid save: `dashboard.menu_active = bool` för respektive dashboard.
**Rationale**: Standard Odoo-mönster. Inga nya modeller. Enkelt att admin:ar förstår.
**Alternative considered**: Egen modell `dashboard.activation`. Överkurs för 7 boolean-fält.

### Decision 5: Bokförare-dashboard med `account.move` som kanban-kort
**Choice**: Bokförarens kanban visar `account.move`-rader grupperade per `journal_id`. `kanban_draggable=True`, `kanban_drag_group_field="journal_id"`. Klick öppnar `account.move`-formulär.
**Rationale**: Matchar Odoos standard accountant-arbetsflöde — flytta verifikationer mellan journaler.
**Alternative considered**: Visa journaler som kort med "pending moves" som siffror (befintligt mönster). Statiskt, ger inte arbetsflödet.

### Decision 6: CRM-forecast viktar med `stage.probability`
**Choice**: `crm.stage.probability` har prioritet över `crm.lead.probability`. Fallback-kedja: stage.probability → lead.probability → 0.
**Rationale**: Stage-baserade probabilities är standard i Odoo CRM. Lead.probability är manuell override.
**Alternative considered**: Endast lead.probability. Missar stage-övergripande konsistens.

### Decision 7: Projekt-adaptrar använder `account.analytic.line`
**Choice**: Alla tre adaptrar (margin, wip, budget) frågar `account.analytic.line` som primär datakälla.
**Rationale**: `account.analytic.line` är Odoos universella projekt-kostnadsmodell. Tid, material, expenses — allt landar här. `_read_group()` säkrar ir.rule.
**Alternative considered**: Direkta SQL-queries mot `account_move_line`. Bryter mot ir.rule-mönstret.

## Risks / Trade-offs

- **[Risk] Menu replacement kan förvirra användare** → Mitigation: Tydlig UI-text i dashboard-formuläret. Original-menyn visas som "Accounting (Classic)" när dashboard ersätter.
- **[Risk] Drag-and-drop + auto-refresh kan skapa race conditions** → Mitigation: Inaktivera auto-refresh under pågående drag-operation. Re-fetcha först efter `orm.write()` resolve:at.
- **[Risk] CRM-forecast kräver att stage.probability är ifylld** → Mitigation: Adaptern loggar en warning om `probability = 0` för icke-"won"/"lost" stages. Dashboard visar "Configure stage probabilities" om alla är 0.
- **[Risk] Projekt-adaptrar kräver `account.analytic.line`-data** → Mitigation: Adaptern returnerar tomt resultat med meddelande "No timesheet data found for this project" istället för error.
- **[Risk] 7 dashboards kan översvämma menyn** → Mitigation: Settings-vyn låter admin stänga av irrelevanta dashboards. Default: alla aktiva.
- **[Trade-off] Bokförare-kanban visar account.move, inte journaler** → Annorlunda än befintlig journal-kanban. Två olika vyer för olika syften (översikt vs arbetsflöde). Dokumenteras i SKILL.md.
