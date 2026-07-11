## Why

Odoo saknar ett fullvärdigt BI-dashboardsystem. Synconics BI Dashboard är den bästa tillgängliga lösningen men har fundamentala brister: Python-loopar för aggregering (N+1-prestanda), inget semantiskt lager för återanvändbara metrics, ingen threshold-baserad alerting, isolerade charts utan cross-chart-interaktivitet, och ett säkerhetslager med luckor (chart.group_ids är endast runtime-filter, inte ir.rule). Samtidigt finns 57 specialiserade finansiella rapporter i mn_finance_insights som är byggda med rätt mönster (_read_group) men som lever i en separat värld utan integration med generisk dashboard-funktionalitet.

## What Changes

- **dashboard_vrtl**: Ny Odoo core-modul (AGPL-3) som ersätter Synconics som BI-plattform. Bygger vidare på Synconics amCharts 5-komponenter men med ny arkitektur för datahantering, säkerhet och interaktivitet.
- **Metric-system**: Återanvändbara datadefinitioner med stöd för model/sql/service/composite-källor, integrerat med svenska XBRL-taxonomier från taxonomier.se.
- **Plugin-baserade datakällor**: AbstractModel-gränssnitt (dashboard.source.mixin) som möjliggör adaptrar för specialiserade beräkningar. 52 av 57 finansiella rapporter adapterbara direkt.
- **Säkerhetsmodell**: Förstärkt 4-lagers modell med ir.rule för chart.group_ids, server-side roll-check för write/create/unlink, och row-level security per source_type (model/sql/service).
- **Alerting**: Threshold-baserad alerting via Odoo notification och activity, med anti-flood (cooldown, state machine).
- **Caching**: Tre lager (request → session → shared) med user-aware cache-nycklar för row-level security.
- **Globala filter + cross-chart + drill-down**: Enhetlig filter-infrastruktur. Charts reagerar på varandras klick. Multi-level drill med brödsmulor.
- **Dashboard-as-code**: YAML-definierade dashboards, versionshanterade i git. Domänspecifika moduler (sales, finance, hr) levererar färdiga dashboards.
- **AI-skill (SKILL.md)**: En språkmodell som bygger dashboards från naturligt språk — översätter domänspråk till Odoo-metrics via taxonomi-uppslag.

## Capabilities

### New Capabilities

- `core-models`: Dashboard, chart, metric, source, filter, alert, cache — komplett datamodell för BI-plattformen.
- `source-interface`: AbstractModel-gränssnitt (dashboard.source.mixin) med get_schema()/get_data()/get_drill_action(). Builtin model-source via _read_group().
- `metric-system`: Återanvändbara metrics med source_type (model/sql/service/composite), taxonomi-integration (taxonomier.se), och auto-detektion av row-level security.
- `security-model`: 4-lagers säkerhet (grupper → model-access → ir.rule → runtime-filter). Per-chart group access med ir.rule. Server-side roll-check.
- `adapter-architecture`: Plugin-baserade datakällor. Adaptrar för mn_finance_insights (52 rapporter) och framtida domäner (HR, lager, projekt).
- `global-filters`: Dashboard-filter med source-kompatibilitet. Filter stackas och propageras till kompatibla charts.
- `cross-chart-interactivity`: Charts emitterar filter-event vid klick. Dashboard propagerar till alla kompatibla charts.
- `drill-down`: Tre typer — group-by drill (hierarkisk), cross-chart drill (navigera till detalj-chart), action drill (öppna Odoo-vy). Brödsmulor och URL-state.
- `alerting`: Threshold-baserade alerts med condition-språk (value/delta). Två kanaler: Odoo notification + activity. Anti-flood via cooldown och state machine.
- `caching`: Tre lager (request/session/shared). User-aware cache-nycklar. TTL per dashboard-typ. Cron-baserad cleanup.
- `dashboard-as-code`: YAML-format för kompletta dashboards (metrics + charts + filters + alerts). Domänspecifika Odoo-moduler levererar färdiga YAML-definitioner.
- `taxonomy-integration`: Import av svenska XBRL-taxonomier. dashboard.taxonomy_concept records med lagreferenser. Mappning taxonomy → account_type → metric.
- `ai-skill`: SKILL.md för AI-driven dashboard-byggare. Fem faser: förstå → design → metrics → validera → persistera.

### Modified Capabilities

Inga — detta är en ny modul. Befintliga Synconics-komponenter (amCharts 5) återanvänds men dashboard_vrtl har sin egen datamodell.

## Impact

- **Ny kod**: ~18 modeller, ~25 Owl-komponenter, ~2000 rader Python, ~1000 rader JS, ~500 rader SKILL.md
- **Beroenden**: web, mail, base (core). Valfria: account, sale, crm, mn_finance_insights (domain/adapters)
- **Återanvändning**: Synconics amCharts 5-bibliotek och chart-komponenter återanvänds. Synconics befintliga modul påverkas EJ — dashboard_vrtl är en ny modul som körs parallellt.
- **Nya amCharts-moduler**: stock.js, wordcloud.js laddas för nya chart-typer (candlestick, word cloud). flow.js och hierarchy.js är redan laddade av Synconics men oanvända — aktiveras för Sankey, Treemap, Sunburst.
- **Taxonomi**: Nytt beroende på XBRL-filer från taxonomier.se (publik resurs, ingen runtime-beroende).
