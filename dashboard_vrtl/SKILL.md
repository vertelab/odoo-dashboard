# SKILL: Dashboard Builder — AI-Assisted Odoo BI Development

Du är en Odoo dashboard-arkitekt. Din uppgift är att bygga kompletta BI-dashboards från naturligt språk med modulen `dashboard_vrtl`.

## Fas 1: Förstå

Identifiera domän, målgrupp och databehov.

1. **Identifiera domänen** från användarens beskrivning:
   - Försäljning → `sale.order`, `sale.order.line`, `crm.lead`
   - Redovisning → `account.move`, `account.move.line`, `account.account`
   - HR → `hr.employee`, `hr.leave`, `hr.contract`, `hr.payslip`
   - Lager → `stock.quant`, `stock.picking`, `product.product`
   - Projekt → `project.task`, `account.analytic.line`

2. **Ställ klargörande frågor vid osäkerhet:**
   - "Ska intäkter inkludera kreditnotor?"
   - "Används orderdatum eller fakturadatum för period?"
   - "Vilka grupper ska se dashboarden?"

## Fas 2: Design

Matcha data till rätt visualisering.

| Data | Chart-typ |
|------|-----------|
| Enkelt värde | KPI / Tile |
| Tidsserie (månad, vecka) | Line / Area / Bar |
| Kategorier (topplista) | Bar / Table |
| Fördelning (andelar) | Pie / Doughnut |
| Flöde / pipeline | Funnel / Sankey |
| Hierarki (kategoriträd) | Treemap / Sunburst |
| Mål vs utfall | Gauge / Meter |
| Geografisk data | Map |
| Korrelation | Scatter |
| Detaljlista | Table |
| Status-översikt, kortvy | Kanban |

**Layout-principer:**
- KPI:er överst (max 4-6 per rad)
- Huvuddiagram mitt (w=6, h=4)
- Kompletterande höger (w=3, h=4)
- Tabeller nederst

## Fas 3: Metrics

Skapa återanvändbara datadefinitioner.

1. **Slå upp i taxonomi**: Om användaren använder svenska redovisningsbegrepp, slå upp i `dashboard.taxonomy.concept`.

2. **Välj source_type:**
   - `model`: Enkel SUM/COUNT/AVG på en Odoo-modell → använd _read_group()
   - `sql`: Komplex beräkning → SQL med security bridge
   - `service`: Finns som adapter → delegera
   - `composite`: Kombination av andra metrics → formel

3. **Regler:**
   - Alltid company_id-filter på monetära metrics
   - `_read_group()` först, SQL endast vid behov
   - Vid SQL: alltid `Model.search() → authorized_ids → WHERE id = ANY()`

**Nyckelfält per modell:**
- `sale.order`: amount_total, date_order, state, partner_id, user_id
- `account.move.line`: debit, credit, balance, date, account_id, partner_id
- `stock.quant`: quantity, value, product_id, location_id
- `hr.employee`: name, department_id, job_id, gender, marital, children, create_date, active
- `hr.contract`: wage, state, date_start, date_end, employee_id, department_id
- `hr.leave`: date_from, date_to, state, holiday_status_id, employee_id
- `hr.leave.allocation`: number_of_days, date_from, date_to, state, holiday_status_id, employee_id
- `hr.payslip`: date_from, date_to, state, employee_id, struct_id
- `hr.payslip.line`: total, code, slip_id, salary_rule_id
- `crm.lead`: expected_revenue, stage_id, user_id, team_id

**Vanliga domän-filter:**
- Exkludera utkast: `[state, not in, [draft, cancel]]`
- Bokförda poster: `[parent_state, =, posted]`
- Exkludera tomma: `[partner_id, !=, False]`

## Fas 4: Validera

1. Kör en test-query för varje metric
2. Verifiera att data returneras (inte tomt)
3. Kontrollera storleksordning
4. Visa resultat för användaren: "Nettoomsättning senaste 30 dagar: 1 247 350 kr. OK?"

## Fas 5: Persistera

Fråga användaren:
- YAML-fil (versionshanterad) → skapa `.yaml` med dashboard-definition
- ORM-records (direkt i Odoo) → skapa `dashboard.dashboard` + `dashboard.metric` + `dashboard.chart`
- Båda → YAML som källa, ORM som runtime

## Adapter-läge

För att skapa en ny datakälla:

1. Implementera `dashboard.source.mixin`:
   ```python
   class MySource(models.AbstractModel):
       _name = "dashboard.source.my_source"
       _inherit = "dashboard.source.mixin"

       def get_schema(self):
           return {"name": "...", "measures": [...], ...}

       def get_data(self, measures, dimensions, filters, options=None):
           return {"labels": [...], "series": [...]}
   ```

2. Registrera via `dashboard.source` XML-data.

3. Prestandaregler: max 3 queries per get_data(), använd _read_group(), LIMIT alltid.

## Menu Integration

Dashboards kan integreras i Odoos menysystem på två sätt:

```yaml
dashboard:
  key: cfo_daily
  name: CFO Daily
  menu_mode: replace       # "submenu" (default) eller "replace"
  replaces_menu: account.menu_finance  # Endast vid menu_mode=replace
```

- **submenu**: Dashboarden visas som barn under `parent_menu_id` (standard)
- **replace**: Dashboarden ersätter huvudmenyns action. Klick på "Accounting" → öppnar dashboarden. Original-action sparas och återställs vid borttagning.

## Kanban chart type

`dashboard_vrtl` stödjer kanban-som chart-typ för kortbaserade vyer direkt i dashboarden.

### När använda kanban
- Översikt av objekt med status (journaler, projekt, anställda, ärenden)
- Snabbnavigering till underliggande records
- Grupperade kortvyer (per typ, status, ansvarig)
- Dashboard som startpunkt för dagligt arbete

### Kanban-konfiguration (YAML)

```yaml
metrics:
  - key: account.journals
    label: Account Journals
    source_type: service
    service_model: dashboard.source.account.journals
    service_method: get_data
    kanban:
      state_field: state           # Kolumn med statusvärde
      state_colors:                # Status → CSS färg
        active: "#28a745"
        locked: "#6c757d"
      state_icons:                 # Status → Font Awesome ikon
        active: fa-check-circle
        locked: fa-lock
      card_title_field: name       # Kolumn för korttitel
      card_subtitle_field: type    # Kolumn för underrubrik
      card_body_fields:            # KPI-badges på kortet
        - pending_moves
        - balance
      card_footer_fields:          # Footer-information
        - last_activity
      card_actions:                # Inline action-knappar
        - name: new_move
          label: New Entry
          icon: fa-plus
          action: ir.actions.act_window
          params:
            res_model: account.move
            context:
              default_journal_id: "{id}"
        - name: view_journal
          label: Open Journal
          icon: fa-book
          action: ir.actions.act_window
          params:
            res_model: account.journal
            res_id: "{id}"
      group_field: type            # Gruppera kort i kolumner

charts:
  - key: journals_kanban
    label: Journals
    metric: account.journals
    type: kanban
```

### Kanban-fält på dashboard.metric

| Fält | Typ | Beskrivning |
|------|-----|-------------|
| `state_field` | Char | Kolumnnamn för statusvärde (t.ex. "state") |
| `state_colors` | JSON | Mapping status → CSS färg |
| `state_icons` | JSON | Mapping status → Font Awesome icon |
| `card_title_field` | Char | Kolumn för kortets titel |
| `card_subtitle_field` | Char | Kolumn för kortets underrubrik |
| `card_body_fields` | JSON | Lista av kolumner att visa som KPI-badges |
| `card_footer_fields` | JSON | Lista av kolumner att visa i footer |
| `card_actions` | JSON | Lista av action-definitioner för knappar |
| `kanban_group_field` | Char | Kolumn för gruppering i kolumner |

### Card action format

```json
[
  {
    "name": "new_move",
    "label": "New Entry",
    "icon": "fa-plus",
    "action": "ir.actions.act_window",
    "params": { "res_model": "account.move", "context": { "default_journal_id": "{id}" } },
    "confirm": "Are you sure?"
  }
]
```

- `{id}`, `{name}` etc i params ersätts med kortets kolumnvärden
- `confirm` (valfritt): visar confirm-dialog före exekvering
- Max 2 actions visas som knappar, resten i "More" dropdown

### Account journal kanban source

Modulen `dashboard_vrtl_source_account` levererar:
- `dashboard.source.account.journals` — adapter för account.journal i kanban-format
- Dashboard YAML: `dashboards/journal_kanban.yaml`
- Kolumner: id, name, code, type, state, pending_moves, total_debit, total_credit, balance, last_activity
- Auto-installerar dashboard vid modulinstallation

### Integrationspunkter
- **Cross-chart filter**: Klicka på kanban-kort → filtrerar övriga charts
- **Drill-down**: Dubbelklicka / drill-klick → öppnar record (journal, move)
- **Inline actions**: Knappar på kortet öppnar Odoo actions
- **Access control**: Respekterar `chart_group_ids` och `dashboard.group_ids`

### Kanban drag-and-drop

Kort kan göras draggable mellan grupp-kolumner via metric-konfiguration:

```yaml
metrics:
  - key: account.moves_kanban
    kanban:
      draggable: true
      drag_group_field: journal_id   # Fältet som uppdateras vid drop
      group_field: journal_id        # Grupperingskolumn
```

När `draggable: true`:
- Kort får `draggable="true"`-attribut
- Dra mellan kolumner → `orm.write(res_model, [id], {drag_group_field: target_value})`
- Visuell feedback: drop zone-highlight, semi-transparent ghost
- No-op om kortet droppas på samma kolumn

**Användningsexempel:** Bokförarens journal-kanban — dra `account.move` mellan journaler för att byta journal.

## Persona Dashboard Catalog

Modulen `dashboard_vrtl_finance` levererar 7 rollbaserade dashboards:

| Dashboard | Key | Målgrupp | Charts |
|-----------|-----|----------|--------|
| CEO Overview | `ceo_overview` | VD / Ledning | 8 (6 KPI, 2 trend) |
| CFO Daily | `cfo_daily` | Ekonomichef daglig | 8 (6 KPI, 2 charts) |
| CFO Monthly | `cfo_monthly` | Ekonomichef månadsvis | 6 (4 KPI, 2 charts) |
| Department Spend | `department_spend` | Avdelningschef | 6 (4 KPI, 2 charts) |
| Bookkeeper Workspace | `bookkeeper_workspace` | Bokförare | 5 (3 KPI, 1 kanban, 1 table) |
| Project Manager | `project_manager` | Projektledare | 6 (4 KPI, 2 charts) |
| Sales Manager | `sales_manager` | Säljchef | 7 (4 KPI, 3 charts) |

**Aktivering:** Accounting → Configuration → Settings → Dashboard Personas (checkbox per dashboard)

**Nya källmoduler:**
- `dashboard_vrtl_source_crm` — `dashboard.source.crm.forecast` (viktad pipeline → revenue forecast)
- `dashboard_vrtl_source_project` — `project.margin`, `project.wip`, `project.budget`

## HR Domain Knowledge

**Available HR Sources** (dashboard_vrtl_source_hr):

| Source | Technical Name | Measures |
|--------|---------------|----------|
| Headcount Trend | hr.headcount | headcount, new_hires, departures |
| Department Distribution | hr.department_distribution | count, percentage |
| Gender Balance | hr.gender_balance | count, percentage |
| Payroll Cost Trend | hr.payroll_trend | gross_salary, contributions, total_cost |
| Salary Distribution | hr.salary_distribution | avg_salary, median_salary, employee_count |
| Absence Trend | hr.absence_trend | sick_days, vacation_days, other_leave, total_absence |
| Sick Leave by Dept | hr.sick_leave_by_dept | sick_days, sick_rate |
| Vacation Utilization | hr.vacation_utilization | allocated, taken, remaining, utilization_pct |

**HR-specific aggregation patterns:**
- Headcount: Count employees with `active=True` and `create_date` within period
- New hires: Count where `create_date` is within month
- Departures: Count where `active=False` and `write_date` within month
- Sick leave: `hr.leave` with `leave_validation_type='sick'`, overlapping month window
- Vacation: `hr.leave` with `leave_validation_type='leave'`, overlapping month window
- Payroll: `hr.payslip` with `state in ('done','paid')`, matching date_from/date_to range

**Common HR filters:**
- `department_ids` — filter by hr.department (many2many)
- `date_from`/`date_to` — period for trend analysis
- `year` — year for vacation utilization

**Gaps this module closes:**
1. **Workforce visibility** — Odoo HR has data but no BI dashboards → real-time KPIs
2. **Payroll cost analysis** — Payroll data locked in payslip → visualized trends
3. **Absence analytics** — Leave data fragmented → sick leave patterns, vacation tracking
4. **Compensation transparency** — Contract data isolated → salary distribution by department
5. **Cross-chart interactivity** — clicking a department filters all charts
6. **Alerting** — automatic notification when sick rate exceeds threshold
