## Why

Odoo-dashboard (`dashboard_vrtl`) saknar idag tre kritiska funktioner för att bli en fullvärdig BI-plattform som ersätter Odoos standard-menyer:

1. **Meny-integration** — Dashboards kan bara vara undermenyer, inte förstasidor. En CFO som klickar "Accounting" ska kunna landa direkt på sin dashboard.
2. **Drag-and-drop kanban** — Dashboard-kanban är read-only. Odoos native kanban för `account.move` (dra faktura mellan journaler) måste fungera inuti dashboarden.
3. **Multi-persona redovisningsdashboards** — Endast `cfo_daily.yaml` finns. CEO, avdelningschef, projektledare, säljchef, och bokförare saknar sina vyer. De 57 finansiella rapporterna från `mn_finance_insights` är adapterade men ingen dashboard använder dem i praktiken. Gap-analyser för entreprenad (`plan/odoo-project`) och field service (`plan/odoo-management-system`) identifierar projekt-P&L, WIP, och fältarbete som saknade dashboard-vyer.

## What Changes

### A. Meny-egenskap — Dashboard som förstasida
- **Nytt fält `menu_mode`** på `dashboard.dashboard`: `submenu` (default) eller `replace`
- **Nytt fält `replaces_menu_id`**: pekar på huvudmenyn som ska ersättas
- **`create_update_menu()` uppdateras**: vid `replace` sätts menyns action till dashboardens `ir.actions.client`

### B. Drag-and-drop på kanban-kort
- **Nytt fält `kanban_draggable`** (bool) på `dashboard.metric` — default False
- **Nytt fält `kanban_drag_group_field`** (char) — fältet som ändras vid drop (t.ex. `journal_id`)
- **HTML5 drag-and-drop i `KanbanCard`**: `dragstart`, `dragover`, `drop`, `dragend`
- **Vid drop**: `orm.write(res_model, [card_id], {drag_group_field: target_value})` + re-fetch
- **Visuell feedback**: ghost-element, drop zone-highlight

### C. Multi-persona redovisningsdashboards (alla i en modul)
7 dashboards som auto-installeras med `dashboard_vrtl_finance`, valbara via Settings:

| Persona | Dashboard | Charts | Metrics | Källa |
|---------|-----------|--------|---------|-------|
| CEO | `ceo_overview` | 12 | 11 | financial_ratios, cash_position, burn_rate, multi_year, free_cash_flow, working_capital, three_statement, recurring_revenue, customer_concentration, cash_flow_forecast |
| CFO Daily | `cfo_daily` (uppdaterad) | 18 | 15 | cfo_command, income_expense_donut, aged_receivable, bank_reconciliation, late_invoices, negative_balance, daily_sales, top_movements, anomalous_transactions |
| CFO Monthly | `cfo_monthly` | 20 | 17 | budget_heatmap, tax_dashboard, tax_reconciliation, aging_combined, pl_forecast, liquidity_stress, currency_exposure, journal_audit, year_end_checklist, credit_notes_audit, vendor_* |
| Avd.chef | `department_spend` | 8 | 5 | analytic_pl, expense_analytics, budget_heatmap, vendor_spend, top_discounts |
| **Bokförare** | `bookkeeper_workspace` | 10 | 5 | account.journal (kanban draggable), bank_reconciliation, journal_audit, anomalous_transactions, late_invoices, negative_balance |
| Projektledare | `project_manager` | 10 | 8 | analytic_pl, product_profitability, margin_stability + NYA: project_margin, project_wip, project_budget |
| Säljchef | `sales_manager` | 15 | 13 | sales_analytics, daily_sales, aov_trend, customer_ltv, customer_profitability, customer_churn, customer_risk, customer_cohort, acquisition_velocity, margin_salesperson, pricing_power, refund_rate, cross_sell + NY: crm_forecast |

### D. Nya source-adaptrar
- **`dashboard.source.crm.forecast`** — CRM-viktad funnel → revenue forecast (i `dashboard_vrtl_source_crm`)
- **`dashboard.source.project.margin`** — Projekt-P&L via `account.analytic.line` (i `dashboard_vrtl_source_project`)
- **`dashboard.source.project.wip`** — WIP aging (ofakturerade timmar/kostnader)
- **`dashboard.source.project.budget`** — Budget vs utfall per projekt

### E. Bokförar-dashboard med funktionell kanban
- Journal-kanban med **drag-and-drop** (`kanban_draggable=True`, `drag_group_field=journal_id`)
- Kort = `account.move` (fakturor, verifikationer), grupperade per journal
- Drag en draft-faktura från Bank till Sales → `journal_id` uppdateras
- Klickbara kort → öppnar formulär
- Matchar Odoos standard accountant-arbetsflöde

### F. Settings — välj aktiva dashboards
- Ny inställningsvy under Accounting → Configuration → Dashboards
- Checkbox per persona-dashboard — vilka som ska visas i menyn
- Default: alla aktiva vid installation

## Capabilities

### New Capabilities
- `dashboard-menu-integration`: Dashboard kan ersätta huvudmeny som förstasida
- `kanban-drag-drop`: Drag-and-drop på kanban-kort med skriv-operationer
- `multi-persona-finance`: 7 rollbaserade redovisningsdashboards (CEO, CFO, Avd.chef, Bokförare, Projekt, Sälj)
- `crm-forecast-adapter`: CRM-viktad funnel → revenue forecast
- `project-adapters`: Projekt-P&L, WIP, budget adaptrar för entreprenad

### Modified Capabilities
- `kanban-chart`: Kanban-kort får `kanban_draggable` + `kanban_drag_group_field` för configurerbar drag-and-drop
- `dashboard-as-code`: YAML-schema utökas med `menu_mode`, `replaces_menu`, `kanban_draggable`, `kanban_drag_group_field`
- `source-interface`: Nya adaptrar för CRM forecast och project

## Impact

- **dashboard_vrtl/models/dashboard.py**: +2 fält (`menu_mode`, `replaces_menu_id`), uppdaterad `create_update_menu()`
- **dashboard_vrtl/models/dashboard_metric.py**: +2 fält (`kanban_draggable`, `kanban_drag_group_field`)
- **dashboard_vrtl/views/dashboard_metric_views.xml**: Kanban-tab uppdaterad med drag-fält
- **dashboard_vrtl/views/dashboard_views.xml**: Menu integration-fält
- **dashboard_vrtl/static/src/components/KanbanView/**: HTML5 drag-and-drop i KanbanCard + KanbanView
- **dashboard_vrtl_finance/data/dashboards/**: 7 YAML-filer (cfo_daily uppdateras, 6 nya)
- **dashboard_vrtl_finance/views/**: Settings-vy för dashboard-val
- **dashboard_vrtl_source_crm/**: Ny modul med `dashboard.source.crm.forecast`
- **dashboard_vrtl_source_project/**: Ny modul med 3 adaptrar
- **dashboard_vrtl/SKILL.md**: Uppdaterad med drag-and-drop, meny-integration, persona-mönster
