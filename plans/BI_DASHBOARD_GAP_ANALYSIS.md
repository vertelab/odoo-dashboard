# Gapanalys: Odoo Dashboard-system vs Marknadsledande BI-verktyg

> Datum: 2026-07-11 | Uppdrag: Jämför Odoo Enterprise Dashboard, CE Dashboard, Synconics BI Dashboard mot ledande BI-system

---

## 1. Systemöversikt — Odoo Dashboard-alternativ

### 1.0 Cybrosys Dynamic Dashboard (AGPL-3, Vertel-fork)

| Egenskap | Status |
|----------|--------|
| **Motor** | Chart.js 2.8 + raw SQL-frågor via `get_query()` |
| **Modeller** | `dashboard.menu`, `dashboard.block`, `dashboard.block.line` |
| **Chart-typer** | 5 typer: Bar, Radar, Pie, Line, Doughnut |
| **Tile-typer** | 1 tile-typ: värde med ikon, färg och formatering (K/M/G-suffix) |
| **Layout** | Bootstrap grid (col-lg-4/6/12), fasta rader |
| **Datakälla** | SQL-genererat direkt mot PostgreSQL (`BaseModel.get_query()` monkey-patch) |
| **Aggregering** | Count, Sum, Average — direkt i SQL |
| **Filter** | Odoo-domän-filter per block |
| **Group By** | Valbart fält — endast en nivå, ingen tidsaggregering |
| **Redigering** | Block skapas via popup/backend-formulär, ej drag-drop |
| **Export** | ❌ Saknas |
| **E-post** | ❌ Saknas |
| **Åtkomst** | Per-meny gruppbaserad (arvs från `ir.ui.menu`), ingen per-block access |
| **Teman** | ❌ Inga teman |
| **Auto-refresh** | ❌ Saknas |
| **Sub-group by** | ❌ Saknas — endast en nivå
| **Datumfilter** | ❌ Saknas — inga datumintervall eller period-jämförelser |
| **Drill-down** | ✅ Tile-klick öppnar lista med filter |
| **Prestanda** | ✅ Rå SQL — snabbare än ORM för aggregerade frågor |
| **Mobilt** | ⚠️ Bootstrap-responsive, ej optimerad |
| **Dashboard-per-model** | ✅ Skapa dashboard som meny under valfri Odoo-modell |

Arkitektur:
- `domain_to_sql.py`: Monkey-patchar `BaseModel.get_query()` — konverterar Odoo-domäner till SQL och kör aggregerade frågor direkt mot PostgreSQL
- `dashboard_menu.py`: Skapar `ir.actions.client` + `ir.ui.menu` för varje dashboard
- `dashboard_block.py`: Hanterar block (tile/graph), hämtar data via SQL
- JS-frontend: Owl-agnostisk widget-baserad (`AbstractAction`), Chart.js-rendering

Plats: `/tmp/pi-github-repos/CAPW-Servicios-Tecnicos/odoo_dynamic_dashboard/` (Vertel-fork: `https://github.com/vertelab/odoo-cybro-utility/tree/18.0/odoo_dynamic_dashboard`)

---

### 1.1 Odoo CE Spreadsheet Dashboard (Core, LGPL-3)

| Egenskap | Status |
|----------|--------|
| **Motor** | o-spreadsheet (Odoos egenutvecklade JS-bibliotek, Chart.js-baserat) |
| **Modeller** | `spreadsheet.dashboard`, `spreadsheet.dashboard.group` |
| **Dashboard-typer** | Fördefinierade, readonly spreadsheets i grupper (Försäljning, Lager, Redovisning, m.fl.) |
| **Datakälla** | Pivot-tabeller, diagram inbäddade i spreadsheet-celler |
| **Formler** | Ja — fullt kalkylbladsformelspråk (`ODOO.LIST`, `ODOO.PIVOT` m.fl.) |
| **Redigering** | ❌ Readonly i CE (måste redigeras via XML/datafiler) |
| **Export** | PDF via utskrift |
| **Realtid** | Begränsad — uppdateras vid omladdning |
| **Styling** | Spreadsheet-baserad formatering (cellstorlek, färg, fonter) |

Basmoduler:
- `/usr/share/core-odoo/addons/spreadsheet/` — Grundmotor
- `/usr/share/core-odoo/addons/spreadsheet_dashboard/` — Dashboard-funktionalitet
- `/usr/share/core-odoo/addons/board/` — Användargränssnitt för dashboards
- `/usr/share/core-odoo/addons/spreadsheet_dashboard_sale/`, `..._stock_account/`, `..._account/` m.fl.

### 1.2 Odoo Enterprise Spreadsheet Dashboard (EE, OEEL-1)

| Egenskap | Status |
|----------|--------|
| **Motor** | o-spreadsheet + Enterprise-tillägg |
| **Extra över CE** | Full redigering, versionshistorik, kollaborativ redigering |
| **Redigering** | ✅ GUI-editor med revisionshantering (`spreadsheet_revision_ids`) |
| **Dashboard-moduler** | 14+ vertikalspecifika dashboards (CRM, Helpdesk, MRP, HR, m.fl.) |
| **Export** | PDF, utskrift |

Enterprise-tillägg:
- `~/odooext-odoo-enterprise/spreadsheet_edition/` — Redigeringsmotor
- `~/odooext-odoo-enterprise/spreadsheet_dashboard_edition/` — Dashboard-redigering
- `~/odooext-odoo-enterprise/spreadsheet_dashboard_crm/`, `..._stock/`, `..._hr_payroll/`, m.fl.

### 1.3 Synconics BI Dashboard (OPL-1, Community & Enterprise)

| Egenskap | Status |
|----------|--------|
| **Motor** | amCharts 5 (JS-bibliotek) + Gridstack layout |
| **Modeller** | `dashboard.dashboard`, `dashboard.chart` |
| **Chart-typer** | 18 typer: KPI, Tile, Bar, Column, Doughnut, Area, Funnel, Pyramid, Line, Pie, Radar, StackedColumn, Radial, Scatter, Map, Meter, To Do, List View |
| **Layout** | Drag-and-drop grid (12-kolumners Gridstack) |
| **Datakälla** | ORM direkt mot valfri Odoo-modell (ej SQL) |
| **Aggregering** | Count, Sum, Average |
| **Filter** | 🔥 26 datumfilter-optioner, Odoo-domän-filter per chart |
| **Group By** | Valbart fält + tidsintervall (dag/vecka/månad/kvartal/år) |
| **Sub Group By** | Sekundär gruppering för multi-series charts |
| **Jämförelser** | KPI: sum/ratio/percentage mot andra KPI, targets, progress bars |
| **Tidigare period** | Jämförelse mot tidigare period (%, värde) |
| **Multiplier** | Per-fält multiplikatorer |
| **Export** | CSV, Excel (xlsxwriter), KPI-bilder för e-post |
| **E-post** | Schemalagd e-post med chart-bilder |
| **Åtkomst** | Grupp/användarbaserad, per dashboard och per chart |
| **Import/Export** | JSON-import/export av hel dashboard |
| **Drill-down** | Item View Actions för nedbrytning |
| **Teman** | 6 amCharts-teman |
| **Auto-refresh** | 15s–5 min konfigurerbart |

Plats: `~/odooext-synconics-bi-dashboard/`

### 1.4 OCA MIS Builder (AGPL-3)

| Egenskap | Status |
|----------|--------|
| **Fokus** | Finansiell rapportering, ej generell BI |
| **Datakälla** | Redovisningskonton (account.move.line) |
| **Layout** | Matris: perioder som kolumner, konton/uttryck som rader |
| **Formler** | Accounting Expression Processor (AEP) |
| **Budget** | Budget-jämförelser |
| **Export** | XLSX, QWeb PDF |

Plats: `/usr/share/odooext-OCA-mis-builder/mis_builder/`

### 1.5 OCA Spreadsheet Dashboard OCA (AGPL-3)

| Egenskap | Status |
|----------|--------|
| **Syfte** | Överbrygga CE/EE-gapet — ger redigering till CE dashboards |
| **Motor** | Samma som Odoo CE spreadsheet |
| **Extra** | `spreadsheet_oca` ger GUI-redigering, import/export av spreadsheets |

Plats: `/usr/share/odooext-OCA-spreadsheet/`

---

## 2. Marknadsledande BI-system — Referensfunktioner

### 2.1 Power BI (Microsoft)

| Funktion | Beskrivning |
|----------|-------------|
| **Semantisk modell** | Stjärnschema, relationer, DAX-beräkningar |
| **Datakällor** | 200+ connectors (SQL, APIs, filer, molntjänster) |
| **Visualiseringar** | 30+ inbyggda + custom visuals marketplace |
| **Interaktivitet** | Cross-filtering, drill-through, bookmarks, tooltips |
| **AI/ML** | Q&A (naturligt språk), decomposition tree, key influencers, anomaly detection |
| **Mobilt** | Native-appar (iOS, Android) |
| **Delning** | App workspaces, row-level security, embed |
| **Schemalagd uppdatering** | Ja, med gateway |
| **Export** | PDF, PowerPoint, Excel, CSV |
| **Realtid** | Streaming datasets, push datasets |
| **Samarbete** | Kommentarer, co-authoring |

### 2.2 Tableau (Salesforce)

| Funktion | Beskrivning |
|----------|-------------|
| **Visualisering** | Branschledande, "best in class" visualiseringar |
| **Datakällor** | 100+ connectors |
| **Interaktivitet** | Dashboard actions, parameters, sets, LOD expressions |
| **AI/ML** | Ask Data, Explain Data, forecasting |
| **Mobilt** | Tableau Mobile, device designer |
| **Storytelling** | Tableau Stories, presentation mode |

### 2.3 Metabase (Open Source)

| Funktion | Beskrivning |
|----------|-------------|
| **Enkelhet** | GUI query builder för icke-tekniska användare |
| **SQL** | Native SQL för avancerade användare |
| **Dashboard** | Grid-baserad, filter, subscriptions |
| **Embedding** | Inbäddningsbar via iframe/JWT |
| **Alert** | Pulse alerts via e-post/slack |
| **Modellering** | Models, metrics, segments |

### 2.4 Looker (Google)

| Funktion | Beskrivning |
|----------|-------------|
| **Semantisk modell** | LookML — versionshanterad, kodbaserad semantisk modell |
| **Datakälla** | In-database (ingen dataförflyttning) |
| **Dashboard** | Dashboard filters, cross-filtering, schedules |
| **Embedding** | Looker Embed SDK, signed embedding |
| **AI** | Looker Assist, automated insights |

### 2.5 Grafana

| Funktion | Beskrivning |
|----------|-------------|
| **Fokus** | Time-series, DevOps, infrastruktur |
| **Datakällor** | 100+ (Prometheus, InfluxDB, SQL, m.fl.) |
| **Dashboard** | Variables (templating), annotations, alert rules |
| **Visualisering** | Time series, heatmaps, histograms, geomaps, stat panels |
| **Alert** | Avancerat alerts-system med kanaler |
| **Provisioning** | Dashboard-as-code (JSON, Terraform) |

### 2.6 Apache Superset (Open Source)

| Funktion | Beskrivning |
|----------|-------------|
| **Datakällor** | SQLAlchemy-baserade (40+ databaser) |
| **Semantisk modell** | Virtual datasets, calculated columns, metrics |
| **Visualisering** | 40+ charts, deck.gl geospatial, custom viz plugins |
| **Dashboard** | Filter boxes, native filters, cross-filtering |
| **SQL Lab** | SQL editor med resultatutforskning |
| **Alert** | Alerts & reports |
| **API** | Full REST API |

---

## 3. Gapanalys — Odoo vs Marknadsledande BI

### 3.1 Odoo CE Spreadsheet Dashboard

| Område | Betyg | Gap |
|--------|-------|-----|
| **Datakällor** | ⚠️ Svag | Endast Odoo-modeller via pivot. Inga externa datakällor, ingen SQL. |
| **Visualisering** | ⚠️ Medel | Chart.js-baserat, begränsat till spreadsheet-diagram. Få diagramtyper. |
| **Interaktivitet** | ❌ Svag | Ingen cross-filtering, drill-down, parameterisering. |
| **Redigering** | ❌ Saknas | Readonly i CE. Kräver utvecklare för att skapa/ändra dashboards. |
| **AI/ML** | ❌ Saknas | Ingen AI, forecasting eller natural language query. |
| **Externa datakällor** | ❌ Saknas | Endast Odoos interna modeller. |
| **Schemalagd uppdatering** | ⚠️ Begränsad | Ingen explicit schemaläggning; uppdateras vid sidladdning. |
| **Export** | ⚠️ Begränsad | Endast PDF via utskrift. Ingen CSV/Excel export. |
| **Alerting** | ❌ Saknas | Inga alert-regler eller notifieringar. |
| **Realtid** | ❌ Saknas | Ingen streaming eller push-baserad uppdatering. |
| **Dashboard-as-code** | ✅ Bra | XML-definierade dashboards, versionshanteringsbart. |
| **Säkerhet/Åtkomst** | ✅ Bra | Gruppbaserad åtkomst på dashboard-nivå. |

### 3.2 Odoo Enterprise Spreadsheet Dashboard

| Område | Betyg | Gap |
|--------|-------|-----|
| **Datakällor** | ⚠️ Svag | Samma som CE — endast Odoo-modeller. |
| **Visualisering** | ⚠️ Medel | Samma som CE. |
| **Interaktivitet** | ⚠️ Låg | Bättre än CE tack vare spreadsheet-funktionalitet men saknar cross-filtering. |
| **Redigering** | ✅ Bra | Full GUI-editor, versionshistorik, kollaborativ redigering. |
| **AI/ML** | ❌ Saknas | Ingen AI. |
| **Externa datakällor** | ❌ Saknas | Samma begränsning som CE. |
| **Schemalagd uppdatering** | ⚠️ Begränsad | Samma som CE. |
| **Export** | ⚠️ Begränsad | PDF, utskrift. |
| **Alerting** | ❌ Saknas | Inga alerts. |
| **Realtid** | ❌ Saknas | Ingen streaming. |
| **Samarbete** | ✅ Bra | Revisionshantering, fleranvändarredigering. |

### 3.3 Synconics BI Dashboard

| Område | Betyg | Gap |
|--------|-------|-----|
| **Datakällor** | ⚠️ Svag | Endast Odoo-modeller via ORM. Ingen SQL, inga externa källor. |
| **Visualisering** | ✅ Bra | 18 diagramtyper via amCharts 5, 6 teman, flexibla layouts (KPI, Tile). |
| **Interaktivitet** | ⚠️ Medel | Drill-down via Item Actions. Saknar cross-filtering mellan charts. |
| **Redigering** | ✅ Bra | GUI-konfigurator med live preview, drag-and-drop layout. |
| **AI/ML** | ❌ Saknas | Ingen AI eller prediktiv analys. |
| **Externa datakällor** | ❌ Saknas | Bara Odoo ORM. |
| **Schemalagd e-post** | ✅ Bra | Schemalagd e-post med chart-bilder (imgkit-rendering). |
| **Export** | ✅ Bra | CSV + Excel (xlsxwriter), KPI-bilder i e-post. |
| **Alerting** | ❌ Saknas | Inga threshold-baserade alerts. Endast schemalagd e-post. |
| **Realtid** | ⚠️ Begränsad | Auto-refresh 15s–5 min. Ingen push/WebSocket. |
| **Import/Export** | ✅ Bra | JSON-export/import av hela dashboard-konfigurationer. |
| **Dashboard-as-code** | ❌ Saknas | Ingen versionshantering av dashboards. GUI-only. |
| **Säkerhet/Åtkomst** | ✅ Bra | Per-dashboard och per-chart grupp- och användaraccess. |
| **Mobilt** | ❌ Saknas | Ingen responsiv eller mobiloptimerad vy. |
| **Prestanda** | ⚠️ Medel | All data hämtas i Python via ORM (N+1 risk). Ingen caching. |

---

## 4. Sammanfattande gaps per BI-kapacitet

### 4.1 Kritiska gaps (alla Odoo-system)

| Gap | CE | EE | Synconics | MIS Builder |
|-----|----|----|-----------|-------------|
| **Externa datakällor** (DB, API, filer) | ❌ | ❌ | ❌ | ❌ |
| **SQL-baserade frågor** | ❌ | ❌ | ❌ | ❌ |
| **Cross-chart interaktivitet** | ❌ | ❌ | ❌ | N/A |
| **Alerting/thresholds** | ❌ | ❌ | ❌ | ❌ |
| **Realtidsuppdatering** | ❌ | ❌ | ❌ | ❌ |
| **AI/prediktiv analys** | ❌ | ❌ | ❌ | ❌ |
| **Naturligt språk-frågor** | ❌ | ❌ | ❌ | ❌ |
| **Mobilapp/nativ mobil** | ❌ | ❌ | ❌ | ❌ |
| **Dashboard-as-code** | ✅ | ✅ | ❌ | ❌ |
| **Parameterisering** | ❌ | ❌ | ❌ | ✅ (perioder) |
| **Embedding** | ❌ | ❌ | ❌ | ❌ |

### 4.2 Styrkor per system

| System | Unik styrka |
|--------|-------------|
| **CE Spreadsheet** | Zero-cost, spreadsheet-gränssnitt, pivot-formler, versionshanteringsbara dashboards |
| **EE Spreadsheet** | GUI-redigering + CE-funktionalitet, kollaborativ redigering, 14+ vertikalspecifika dashboards |
| **Synconics BI** | Fristående BI-byggare, 18 charttyper, export, schemalagd e-post, drag-drop layout, JSON-import/export |
| **MIS Builder** | Finansiell rapportering, period-kolumner, budget-jämförelser, AEP-uttryck |

### 4.3 Närmast marknadsledande BI

| Förmåga | Bästa Odoo-alternativ | Närmsta BI-motsvarighet |
|---------|----------------------|------------------------|
| **Visualisering** | Synconics (18 typer, amCharts 5) | Metabase / Superset nivå |
| **Redigering** | EE Spreadsheet / Synconics | Under Metabase/Superset |
| **Export** | Synconics (CSV, Excel, bild) | Metabase-nivå |
| **Delning** | Synconics (e-post schemaläggning) | Metabase "pulses" |
| **Embedding** | Saknas helt | Power BI/Tableau/Looker standard |
| **Semantisk modell** | Saknas | Looker (LookML), Power BI (star schema) |
| **Alerting** | Saknas helt | Grafana > Superset > Metabase |
| **Realtid** | Saknas helt | Power BI streaming, Grafana |
| **AI** | Saknas helt | Power BI > Tableau > Looker |

---

## 5. Rekommendationer för att täppa gapen

### Prioritet 1 — Kritiska funktioner

1. **Alerting / Notifieringar** — Konfigurerbara thresholds per KPI med e-post/Slack/Teams-notifiering. Grafana och Metabase har starka referensimplementationer.
2. **Cross-chart interaktivitet** — När användaren klickar på ett diagram ska övriga diagram filtreras (Power BI/Tableau-standard).
3. **Dashboard filter/variables** — Globala filter som påverkar alla charts på en dashboard (som Metabase/Superset/Grafana).

### Prioritet 2 — Viktiga förbättringar

4. **Parameteriserbara dashboards** — Mall-dashboards där användare kan byta ut parametrar (datum, kund, produktkategori).
5. **Embedding** — Möjlighet att bädda in dashboards externt (iframe, JWT-signed). Looker och Metabase har starka referenser.
6. **Dashboard-as-code för Synconics** — Importera/exportera behöver kompletteras med versionshanteringsbart format + möjlighet att definiera via XML/YAML.

### Prioritet 3 — Framtida satsningar

7. **SQL/SQL Lab** — Möjlighet att definiera charts med egna SQL-frågor (Superset SQL Lab, Metabase native queries).
8. **Externa datakällor** — Ansluta externa databaser/API:er som datakälla för dashboards.
9. **AI-funktioner** — Forecasting, anomaly detection, natural language query (som Power BI Q&A).
10. **Realtid / WebSocket** — Push-baserad uppdatering av dashboards via bus/WebSocket (Grafana live mode).

---

## 6. Detaljerad jämförelse: Cybrosys Dynamic Dashboard vs Synconics BI Dashboard

### 6.1 Funktionsjämförelse sida vid sida

| Funktion | Cybrosys Dynamic Dashboard | Synconics BI Dashboard |
|----------|--------------------------|------------------------|
| **Chart-typer** | 5 (Bar, Radar, Pie, Line, Doughnut) | 18 (KPI, Tile, Bar, Column, Doughnut, Area, Funnel, Pyramid, Line, Pie, Radar, StackedColumn, Radial, Scatter, Map, Meter, To Do, List) |
| **Chart-bibliotek** | Chart.js 2.8 | amCharts 5 |
| **Tile-typer** | 1 enkel tile (värde + ikon) | 4 tile-layouter + 5 KPI-layouter |
| **Layout** | Bootstrap grid, 3 storlekar | Gridstack drag-and-drop, 12-kolumners |
| **Datakälla** | 🔥 Rå SQL (`get_query()`) | Odoo ORM (`search()` + Python-loopar) |
| **Prestanda** | ✅ SQL-aggregering i databasen | ⚠️ ORM N+1 risk, Python-aggregering |
| **Filter** | Odoo-domän | Odoo-domän + 26 datumfilter-optioner |
| **Group By** | 1 nivå, inget tidsintervall | 2 nivåer (group by + sub-group), dag/vecka/månad/kvartal/år |
| **Datumhantering** | ❌ Inget datumfilter | ✅ 26 datumfilter + periodjämförelser |
| **Jämförelser** | ❌ Saknas | KPI sum/ratio/percentage, targets, progress bars |
| **Redigering** | Skapa/redigera block via backend-formulär | GUI-konfigurator med live preview, drag-drop |
| **Layout-editor** | ❌ Fast grid, manuell ordning | ✅ Drag-and-drop, position sparas |
| **Export** | ❌ Saknas | CSV, Excel (xlsxwriter), KPI-bilder |
| **E-post** | ❌ Saknas | Schemalagd e-post med chart-bilder (imgkit) |
| **Teman** | ❌ Inga | 6 amCharts-teman |
| **Auto-refresh** | ❌ Saknas | 15s–5 min |
| **Åtkomst** | Per-meny (grupp) | Per-dashboard + per-chart (grupp/användare) |
| **Import/Export** | ❌ Saknas | JSON-export/import |
| **Drill-down** | ✅ Tile-klick → lista | ✅ Item View Actions (flernivå-drill) |
| **Multipliers** | ❌ Saknas | ✅ Per-fält multiplikatorer |
| **To Do / List** | ❌ Saknas | ✅ To Do (default/activity) + List View |
| **Map Chart** | ❌ Saknas | ✅ Geografisk karta |
| **Meter/Gauge** | ❌ Saknas | ✅ Meter chart med target |
| **Dashboard-per-model** | ✅ Per-modell meny | ✅ Fristående dashboard-meny |
| **Licens** | AGPL-3 | OPL-1 (proprietär, fri att använda) |
| **Kodstorlek** | ~300 rader Python + ~200 JS | ~3465 rader Python + omfattande JS/komponenter |

### 6.2 Cybrosys unika styrkor

1. **SQL-prestanda** — `get_query()` kör aggregeringar direkt i PostgreSQL. Detta är fundamentalt bättre än Synconics ORM-loopar för stora datamängder.
2. **Enkel arkitektur** — Liten kodbas (~500 rader), lätt att underhålla och förstå.
3. **AGPL-3** — Öppen källkod, ingen proprietär begränsning.
4. **Monkey-patch-metoden** — `BaseModel.get_query()` är elegant — alla modeller får SQL-frågegenerering automatiskt.
5. **Meny-integrerad** — Dashboards skapas direkt som menyalternativ under befintliga Odoo-menyträd.

### 6.3 Synconics unika styrkor

1. **18 chart-typer** vs 5 — inkluderar KPI, Map, Meter, Funnel, Pyramid, Scatter, List, To Do.
2. **Rik KPI-motor** — Jämförelser, targets, progress bars, tidigare period, dual-KPI ratio.
3. **Datumfilter** — 26 fördefinierade datumintervall ("Last 30 Days", "Year to Date", etc).
4. **Drag-and-drop layout** — Gridstack-baserad, positioner sparas.
5. **Export** — CSV, Excel, bild-rendering för e-post.
6. **E-post-schemaläggning** — Per-dashboard cron-jobb med chart-bilder.
7. **Drill-down** — Flernivå-actions med breadcrumbs.
8. **Live preview** — Ändra konfiguration och se resultat direkt i formuläret.

---

## 7. Analys: Bygga ut Cybrosys vs Bygga nytt

### 7.1 Vad krävs för att utöka Cybrosys med Synconics redigering och grafer?

För att nå Synconics-nivå på Cybrosys-plattformen krävs följande moduler:

#### A. Chart-motor (stor insats)
- Byt ut Chart.js 2.8 mot amCharts 5 (eller behåll Chart.js och bygg fler typer)
- Lägg till: Column, Area, Funnel, Pyramid, StackedColumn, Radial, Scatter, Map, Meter
- Bygg KPI-rendering (5 layouter + progress bars + jämförelse-pilar)
- Bygg Tile-layouter (4 varianter)
- Bygg List View och To Do View
- Lägg till teman (minst 4-6 st)
- **Uppskattad insats: 80-120h JS/frontend**

#### B. Datumfilter och perioder (medel insats)
- Bygg `get_date_filter_domain()` med 26 alternativ
- Lägg till period-jämförelser (previous period, same period previous years)
- Integrera i SQL-generatorn (`get_query()`)
- **Uppskattad insats: 20-30h Python**

#### C. Drag-and-drop layout (medel insats)
- Integrera Gridstack.js
- Spara/återställ positioner i `grid_stack_dimensions` JSON-fält
- Auto-positionering för nya block
- **Uppskattad insats: 15-25h JS/Python**

#### D. GUI-redigerare med live preview (stor insats)
- Bygg `form_dashboard_preview` widget som Synconics
- Realtidsuppdatering vid konfigurationsändring (isDirty-flödet)
- Bygg `dashboard_selection` widget för chart-typ-väljare
- **Uppskattad insats: 30-50h JS/Python**

#### E. Export och e-post (medel insats)
- CSV-export (Python csv-modul)
- Excel-export (xlsxwriter)
- Bildrendering för e-post (imgkit + HTML templates)
- Schemalagd e-post (ir.cron + mail.compose.message)
- **Uppskattad insats: 20-30h Python**

#### F. Sub-group by och avancerad aggregering (liten-medel insats)
- Utöka `get_query()` med sub-group by (kräver ny SQL-generering)
- Multiplier-stöd
- **Uppskattad insats: 10-15h Python**

#### G. Import/Export, Access control, Auto-refresh (liten insats)
- JSON-import/export
- Per-block access control
- Auto-refresh med JavaScript-timer
- **Uppskattad insats: 10-15h Python/JS**

#### Total uppskattad insats för att nå Synconics-nivå: **185-285 timmar**

### 7.2 Risker med att bygga ut Cybrosys

| Risk | Nivå | Kommentar |
|------|------|----------|
| **Chart.js-begränsningar** | Hög | Chart.js saknar Map, Meter/Gauge, Funnel, Pyramid, Radar (finns), Scatter. Kräver plugin eller byte till amCharts/ECharts. |
| **SQL-generatorns komplexitet** | Medel | Sub-group by, datumfilter i SQL är komplext men genomförbart. |
| **Monkey-patch-stabilitet** | Medel | `BaseModel.get_query()` är en monkey-patch — risk för konflikt med andra moduler. |
| **Ingen versionshantering** | Låg | Cybrosys saknar dashboard-as-code. Kan lösas med JSON import/export. |
| **Licens-kompatibilitet** | Låg | AGPL-3 → inga problem att bygga vidare. |

### 7.3 Rekommendation: Bygg nytt eller bygg ut?

#### Alternativ A: Bygg ut Cybrosys Dynamic Dashboard

**Fördelar:**
- Behåller SQL-prestandan (unik styrka)
- Liten, ren kodbas att bygga vidare på
- AGPL-3 — full frihet
- Redan fungerande meny-integration och grundläggande block

**Nackdelar:**
- Kräver ~200-300h för att nå Synconics-nivå
- Chart.js-begränsning kräver biblioteksbyte
- Monkey-patch riskerar konflikter
- Behöver i princip byggas om från grunden i JS-frontend

#### Alternativ B: Bygg ny egen dashboard-modul från grunden

**Fördelar:**
- Full kontroll över arkitektur och teknikval
- Kan designas rätt från början (modern Owl-kompatibel, rätt bibliotek)
- Kan inkorporera både SQL-prestanda OCH rik funktionalitet
- Dashboard-as-code från dag ett

**Nackdelar:**
- Större initial insats (~300-400h)
- All funktionalitet måste byggas från scratch
- Underhållsbörda på lång sikt

#### Alternativ C: Hybrid — Synconics som bas + SQL-injektion (REKOMMENDERAS)

1. Behåll Synconics BI Dashboard som bas (18 charttyper, drag-drop, export, etc.)
2. Bygg en tilläggsmodul `synconics_bi_dashboard_sql` som:
   - Ersätter ORM-anropen i `get_chart_data()` med SQL-frågor för aggregerade typer
   - Återanvänder Cybrosys `get_query()`-metodik men som en utility-funktion (ej monkey-patch)
   - Lägger till **dashboard-as-code** (XML/YAML-definitioner)
   - Lägger till **alerting** (thresholds + e-post/Slack)
   - Lägger till **cross-chart filter**
   - Lägger till **global dashboard filter/variables**
3. Resultat: Bästa av två världar — Synconics UI + SQL-prestanda + nya BI-funktioner

**Uppskattad insats för alternativ C: 80-120h**

| Moment | Timmar |
|--------|--------|
| SQL-query-injektion i `get_chart_data()` (ersätt ORM-loopar) | 20-30h |
| Dashboard-as-code (XML/YAML-import) | 15-20h |
| Alerting-system (thresholds + notifieringar) | 15-25h |
| Cross-chart filter | 15-20h |
| Globala dashboard-filters | 10-15h |
| Embedding-stöd (iframe/JWT) | 10-15h |
| **Totalt** | **85-125h** |

### 7.4 Slutrekommendation

**Alternativ C (Hybrid) rekommenderas** med följande motivering:

1. Synconics är redan ~80% av vägen till ett fullfjädrat BI-verktyg
2. De kritiska gapen (SQL-prestanda, alerting, cross-filtering, embedding) kan åtgärdas med relativt små tillägg
3. Att bygga om hela UI:t från grunden (Alternativ A/B) är inte kostnadseffektivt
4. Synconics proprietära licens (OPL-1) tillåter användning men inte vidaredistribution av modifierad kod — tilläggsmoduler med AGPL-3 är OK så länge de inte modifierar originalkoden direkt

**⚠️ Viktigt licens-påpekande:** Synconics är OPL-1 (Odoo Proprietary License). Detta innebär att man **inte får** modifiera, rebranda eller vidaredistribuera modifierade versioner. Tilläggsmoduler som importerar/ärver från Synconics utan att modifiera originalfilerna är däremot möjliga. Verifiera med Synconics legal innan vidareutveckling.

---

## 8. Källfilsreferenser

| System | Nyckelfil |
|--------|-----------|
| **Cybrosys Dynamic Dashboard** | `/tmp/pi-github-repos/CAPW-Servicios-Tecnicos/odoo_dynamic_dashboard/models/dashboard_block.py` |
| **Cybrosys SQL-generator** | `/tmp/pi-github-repos/CAPW-Servicios-Tecnicos/odoo_dynamic_dashboard/models/domain_to_sql.py` |
| **Cybrosys Dashboard Menu** | `/tmp/pi-github-repos/CAPW-Servicios-Tecnicos/odoo_dynamic_dashboard/models/dashboard_menu.py` |
| **Cybrosys JS** | `/tmp/pi-github-repos/CAPW-Servicios-Tecnicos/odoo_dynamic_dashboard/static/src/js/dynamic_dashboard.js` |
| CE Spreadsheet Dashboard | `/usr/share/core-odoo/addons/spreadsheet_dashboard/models/spreadsheet_dashboard.py` |
| CE Spreadsheet | `/usr/share/core-odoo/addons/spreadsheet/__manifest__.py` |
| CE Board | `/usr/share/core-odoo/addons/board/__manifest__.py` |
| EE Spreadsheet Edition | `~/odooext-odoo-enterprise/spreadsheet_edition/__manifest__.py` |
| EE Dashboard Edition | `~/odooext-odoo-enterprise/spreadsheet_dashboard_edition/models/spreadsheet_dashboard.py` |
| Synconics BI Dashboard (chart) | `~/odooext-synconics-bi-dashboard/models/dashboard_chart.py` (3465 rader) |
| Synconics Dashboard-modell | `~/odooext-synconics-bi-dashboard/models/dashboard.py` |
| OCA MIS Builder | `/usr/share/odooext-OCA-mis-builder/mis_builder/__manifest__.py` |
| OCA Spreadsheet OCA | `/usr/share/odooext-OCA-spreadsheet/spreadsheet_oca/__manifest__.py` |
| OCA Spreadsheet Dashboard OCA | `/usr/share/odooext-OCA-spreadsheet/spreadsheet_dashboard_oca/__manifest__.py` |
