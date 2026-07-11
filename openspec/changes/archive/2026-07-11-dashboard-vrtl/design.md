## Context

Odoo saknar ett fullvärdigt BI-dashboardsystem. Befintliga lösningar:

- **Synconics BI Dashboard** (AGPL-3): 18 chart-typer via amCharts 5, drag-drop-layout. Brister: Python-loopar för aggregering (N+1-prestanda), inget semantiskt lager, ingen cross-chart-interaktivitet, säkerhetsmodell med luckor.
- **Cybrosys Dynamic Dashboard** (AGPL-3): Raw SQL → bra prestanda men monkey-patch-arkitektur, endast 5 chart-typer, ingen säkerhetsbrygga för ir.rule.
- **Odoo CE/EE Spreadsheet**: Spreadsheet-baserat, ingen generisk BI, CE readonly.
- **mn_finance_insights** (LGPL-3): 57 finansiella rapporter med _read_group()-mönster. Bra prestanda men hårdkodade, isolerade från generisk dashboard-funktionalitet.

Målet är en ny modul (`dashboard_vrtl`) som kombinerar Synconics UI (amCharts 5) med korrekt datahantering (_read_group + security bridge), ett semantiskt lager (metrics + taxonomier.se), och plattformstänk (adapters, as-code, AI-skill).

## Goals / Non-Goals

**Goals:**
- Skapa en BI-plattform som hanterar både generiska Odoo-modeller och specialiserade beräkningar
- Återanvända Synconics amCharts 5-komponenter men med ny datapipeline
- Implementera threshold-baserad alerting (saknas i alla Odoo dashboard-system)
- Möjliggöra dashboard-as-code via YAML för versionshantering och deployment
- Leverera en AI-skill (SKILL.md) som bygger dashboards från naturligt språk
- Integrera svenska XBRL-taxonomier (taxonomier.se) för juridiskt korrekta finansiella definitioner

**Non-Goals:**
- Inte ersätta Synconics — dashboard_vrtl är en ny modul, Synconics kan samexistera
- Inte bygga en generisk SQL-editor (som Superset SQL Lab) — fokus är Odoo-modeller
- Inte implementera externa datakällor (API:er, andra databaser) — endast Odoo-modeller + adapters
- Inte bygga mobilapp — responsiv webb räcker
- Inte ersätta interaktiva verktyg (bank_reconciliation, journal_audit) — dessa är inte dashboard-material

## Decisions

### D1: Bygg på Synconics, inte från grunden

**Val**: Återanvänd Synconics amCharts 5-bibliotek och chart-komponenter.

**Alternativ övervägt**: ECharts (Apache 2.0, fler chart-typer, WebGL). Förkastat pga ~150h portningskostnad av 14+ komponenter.

**Rationale**: amCharts 5 är redan integrerat. Fyra moduler är laddade men oanvända (flow.js, hierarchy.js) — ger 6-8 nya chart-typer utan extra beroenden. Licensen (AGPL-3) är kompatibel.

### D2: _read_group() för 80% av queries, SQL-brygga för resten

**Val**: Tre-stegs datapipeline:
1. read_group() för enkel aggregering (ORM hanterar säkerhet automatiskt)
2. ORM-ID-brygga för komplex SQL: `Model.search() → IDs → WHERE id = ANY($ids)`
3. Full SQL endast när ID-bryggan inte räcker (>100k IDs)

**Alternativ övervägt**: Raw SQL direkt (Cybrosys). Förkastat pga säkerhetsrisk — ir.rule, company-filter, active-fält ignoreras.

**Rationale**: read_group() kör GROUP BY i databasen — lika snabbt som raw SQL för aggregering, men 100% ORM-säkert.

### D3: Metric-system med tre lager

**Val**: Separera data-definition (metric) från visualisering (chart):
1. dashboard.taxonomy_concept — officiella begrepp från taxonomier.se
2. dashboard.metric — implementation (model/sql/service/composite)
3. dashboard.chart — visualisering

**Rationale**: En metric definieras EN gång, återanvänds över många charts. Ändras definitionen → alla charts uppdateras. Taxonomi-kopplingen ger revisionsbara definitioner med lagreferenser.

### D4: Plugin-baserade datakällor via AbstractModel

**Val**: dashboard.source.mixin (AbstractModel) med get_schema() + get_data().

**Rationale**: Möjliggör adaptrar för mn_finance_insights (52 rapporter) och framtida domäner. Adaptrar ÄGER sin implementation — kan delegera till original eller implementera om optimerat.

### D5: Alerting via Odoo notification + activity (inte email/Slack)

**Val**: Två kanaler — mail.channel (notification) och mail.activity (kräver åtgärd).

**Alternativ övervägt**: Email + Slack + webhook. Förkastat för v1 — Odoo-nativa kanaler täcker de viktigaste användningsfallen utan externa beroenden.

**Rationale**: Activity kräver åtgärd (inte bara passiv notifiering). State machine med acknowledgement.

### D6: Caching i tre lager med user-aware nycklar

**Val**: Request-cache (dict, per HTTP-anrop) → Session-cache (ORM, TTL 30s-60min) → Shared cache (endast safe_for_shared_cache metrics).

**Rationale**: 95-99% reduktion av databasfrågor. user_id i cache-nyckel förhindrar dataläckage via ir.rule.

### D7: Filter-infrastruktur som grund för cross-chart + drill-down

**Val**: Globala filter med per-chart filter_mapping (compatible + param_mapping). Cross-chart emit:ar filter-event. Drill-down använder drill_stack med brödsmulor.

**Rationale**: Samma infrastruktur driver både horisontell (cross-chart) och vertikal (drill-down) interaktivitet.

### D8: YAML som dashboard-as-code-format

**Val**: En dashboard = en YAML-fil med metrics + charts + filters + alerts. Domänspecifika Odoo-moduler (dashboard_vrtl_sales, _finance) levererar färdiga YAML-definitioner.

**Rationale**: Git-vänligt, diff-bart, versionshanterat. Separat från deployment (Salt).

## Risks / Trade-offs

- **[Prestanda] SQL-bryggan fungerar inte för ir.rule med computed/related fields** → Fallback: använd alltid read_group() om möjligt. SQL endast när det är säkert.
- **[Licens] amCharts 5 är AGPL** → OK för dashboard_vrtl (också AGPL-3). Vid kommersiell distribution utan källkod → krävs amCharts kommersiell licens.
- **[Underhåll] Adapter-kod för 52 finansiella rapporter** → Adaptrar är tunna (~50 rader var). Delegerar till originalet. Endast 7 adaptrar implementerar om logiken (prestandafix).
- **[Komplexitet] 18 modeller i core** → Modellerna är fokuserade. Många är enkla (cache, filter_mapping). Komplexiteten ligger i datapipelinen, inte i antalet modeller.
- **[Beroende] Taxonomier.se kan ändra format** → Import sker vid modul-installation/uppgradering, inte runtime. Validering vid import.
