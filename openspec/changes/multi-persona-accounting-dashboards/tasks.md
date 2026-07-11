## 1. Menu integration fields on dashboard.dashboard

- [x] 1.1 Add `menu_mode` (Selection: submenu/replace, default submenu) field to `dashboard.dashboard`
- [x] 1.2 Add `replaces_menu_id` (Many2one: ir.ui.menu) field to `dashboard.dashboard`
- [x] 1.3 Add `_original_menu_action` (Char) computed/stored field for original action ref
- [x] 1.4 Update `create_update_menu()` to handle `menu_mode = "replace"`: set parent menu's action to dashboard action, store original
- [x] 1.5 Update `action_delete_menu()` / `unlink()` to restore original menu action when dashboard is deleted
- [x] 1.6 Update dashboard form view with menu integration section
- [x] 1.7 Update `_yaml_to_dashboard_vals()` and `_dashboard_to_yaml_dict()` for menu_mode/replaces_menu

## 2. Drag-and-drop fields on dashboard.metric

- [x] 2.1 Add `kanban_draggable` (Boolean, default False) field to `dashboard.metric`
- [x] 2.2 Add `kanban_drag_group_field` (Char) field to `dashboard.metric`
- [x] 2.3 Update `_yaml_to_metric_vals()` and `_metric_to_yaml_dict()` for kanban draggable fields
- [x] 2.4 Update metric form view (Kanban tab) with draggable fields
- [x] 2.5 Update `_get_kanban_config()` to include `kanban_draggable` and `kanban_drag_group_field`

## 3. HTML5 drag-and-drop in KanbanCard/KanbanView OWL

- [x] 3.1 Add `draggable` attribute + `dragstart` handler to KanbanCard when config.kanban_draggable is true
- [x] 3.2 Add `dragover` + `drop` handlers to KanbanView group columns
- [x] 3.3 Implement ghost element (semi-transparent clone following cursor during drag)
- [x] 3.4 Implement drop zone highlighting (dashed border on valid targets)
- [x] 3.5 Implement `orm.write()` call on successful drop: update `kanban_drag_group_field` on card's record
- [x] 3.6 Implement post-drop data re-fetch (call metric pipeline to refresh view)
- [x] 3.7 Add CSS for drag states (dragging, drag-over, invalid-target)
- [x] 3.8 Handle edge cases: drop on same column (no-op), drop outside (snap back), rapid drags (debounce)

## 4. CEO Dashboard YAML

- [x] 4.1 Create `dashboards/ceo_overview.yaml` in `dashboard_vrtl_finance`
- [x] 4.2 Define metrics: financial_ratios, cash_position, burn_rate, multi_year, free_cash_flow, working_capital, three_statement, recurring_revenue, customer_concentration, cash_flow_forecast
- [x] 4.3 Create KPI row: Revenue MTD, Gross Margin %, EBITDA, Cash Balance, Burn Rate
- [x] 4.4 Create trend charts: Revenue 12M, Working Capital Cycle, Customer Concentration Pareto, Free Cash Flow
- [x] 4.5 Add global period + company filters

## 5. CFO Daily Dashboard (update existing)

- [x] 5.1 Expand `cfo_daily.yaml`: add bank_reconciliation, aged_receivable, late_invoices, negative_balance, daily_sales, top_movements, anomalous_transactions metrics
- [x] 5.2 Add KPI row: Revenue, Expenses, Bank Balance, AR Total, AP Total
- [x] 5.3 Add charts: Revenue vs Expenses (line), AR Aging (bar), Late Invoices (table), Bank Reconciliation (status cards), Anomalous Transactions (list)
- [x] 5.4 Add alert: negative balance > 0

## 6. CFO Monthly Dashboard YAML

- [x] 6.1 Create `dashboards/cfo_monthly.yaml` in `dashboard_vrtl_finance`
- [x] 6.2 Define metrics: budget_heatmap, tax_dashboard, tax_reconciliation, aging_combined, pl_forecast, liquidity_stress, currency_exposure, journal_audit, year_end_checklist, credit_notes_audit, vendor_concentration, vendor_payment_schedule, payment_method_mix, days_to_pay, invoice_cycle_time, receivables_forecast, account_velocity, cash_efficiency, vendor_reliability
- [x] 6.3 Create KPI row: Net Income, Gross Margin %, OpEx, EBITDA Margin
- [x] 6.4 Create charts: P&L (stacked bar), Budget vs Actual (heatmap), AR/AP Combined Aging (bar), Tax Summary (table), Vendor Concentration (Pareto), Cash Conversion Efficiency (gauge)
- [x] 6.5 Add global period, company, department filters

## 7. Department Head Dashboard YAML

- [x] 7.1 Create `dashboards/department_spend.yaml` in `dashboard_vrtl_finance`
- [x] 7.2 Define metrics: analytic_pl, expense_analytics, budget_heatmap, vendor_spend, top_discounts
- [x] 7.3 Create KPI row: Budget Remaining, Expenses MTD, Variance %, Headcount
- [x] 7.4 Create charts: Expenses by Category (treemap), Budget vs Actual (waterfall), Monthly Trend (line), Vendor Spend (bar)
- [x] 7.5 Add department (analytic account) filter as primary global filter

## 8. Bookkeeper Workspace Dashboard YAML

- [x] 8.1 Create `dashboards/bookkeeper_workspace.yaml` in `dashboard_vrtl_finance`
- [x] 8.2 Define account.move kanban metric with `kanban_draggable: true, kanban_drag_group_field: journal_id`
- [x] 8.3 Create kanban chart: account.move cards grouped by journal_id, state colors per move state (draft/posted/cancel)
- [x] 8.4 Create supporting charts: Bank Reconciliation status, Late Invoices table, Anomalous Transactions list, Negative Balance alerts
- [x] 8.5 Add journal type filter (bank, sale, purchase, etc.)
- [x] 8.6 Configure card actions: "Open Move" (form), "Post" (action), "Reset to Draft"

## 9. Project Manager Dashboard YAML

- [x] 9.1 Create `dashboards/project_manager.yaml` in `dashboard_vrtl_finance`
- [x] 9.2 Define metrics: analytic_pl, product_profitability, margin_stability + new project adapters (project.margin, project.wip, project.budget)
- [x] 9.3 Create KPI row: Project Margin %, Billable Hours, WIP Total, Cost to Complete
- [x] 9.4 Create charts: Project Margin by Month (stacked bar), Billable vs Non-billable (pie), WIP Aging (table), Budget vs Actual (waterfall)
- [x] 9.5 Add project + period global filters

## 10. Sales Manager Dashboard YAML

- [x] 10.1 Create `dashboards/sales_manager.yaml` in `dashboard_vrtl_finance`
- [x] 10.2 Define metrics: sales_analytics, daily_sales, aov_trend, customer_ltv, customer_profitability, customer_churn, customer_risk, customer_cohort, acquisition_velocity, margin_salesperson, pricing_power, refund_rate, cross_sell + new crm.forecast adapter
- [x] 10.3 Create KPI row: Pipeline Value, Weighted Forecast, Win Rate %, Avg Deal Size
- [x] 10.4 Create charts: Funnel by Stage, Forecast vs Quota (gauge), Win/Loss Trend (line), Rep Performance (bar), Customer LTV (bar), Pipeline Velocity (table)
- [x] 10.5 Add team + period global filters

## 11. CRM Forecast source module (dashboard_vrtl_source_crm)

- [x] 11.1 Create module skeleton: `__manifest__.py`, `__init__.py`, models, security, data
- [x] 11.2 Implement `dashboard.source.crm.forecast` adapter (extends `dashboard.source.mixin`)
- [x] 11.3 Implement `get_schema()` with forecast measures and dimensions
- [x] 11.4 Implement `get_data()`: query crm.lead, weight by stage.probability, group by date_deadline:month
- [x] 11.5 Implement pipeline velocity metric (avg days per stage from message history)
- [x] 11.6 Implement `get_drill_action()` returning crm.lead tree view for drill-down
- [x] 11.7 Register source in dashboard.source registry
- [x] 11.8 Add `dashboard_vrtl` and `crm` as dependencies

## 12. Project source module (dashboard_vrtl_source_project)

- [x] 12.1 Create module skeleton: `__manifest__.py`, `__init__.py`, models, security, data
- [x] 12.2 Implement `dashboard.source.project.margin` adapter
- [x] 12.3 Implement `dashboard.source.project.wip` adapter
- [x] 12.4 Implement `dashboard.source.project.budget` adapter
- [x] 12.5 Implement `get_schema()` for each adapter
- [x] 12.6 Implement `get_data()` using account.analytic.line _read_group()
- [x] 12.7 Implement `get_drill_action()` for each (project.task or project.project form)
- [x] 12.8 Register all 3 sources in dashboard.source registry
- [x] 12.9 Add `dashboard_vrtl`, `project`, `hr_timesheet` as dependencies

## 13. Dashboard activation settings

- [x] 13.1 Create `res.config.settings` fields for each of the 7 dashboards (boolean, default True)
- [x] 13.2 Create settings view (Accounting → Configuration → Dashboards) with checkboxes
- [x] 13.3 Implement save logic: set `menu_active` on each dashboard based on checkbox state
- [x] 13.4 Add settings action and menu item

## 14. YAML load/export completeness

- [x] 14.1 Update `dashboard_vrtl_finance/__manifest__.py` to include all 7 YAML data files
- [x] 14.2 Update `_post_init_load_dashboards()` to load all YAML files on module install
- [x] 14.3 Test YAML round-trip for each dashboard (load → export → compare)

## 15. SKILL.md and manifest updates

- [x] 15.1 Update SKILL.md with: menu integration patterns, drag-and-drop kanban configuration, persona-to-dashboard mapping, CRM forecast and project adapter references
- [x] 15.2 Add kanban draggable + menu_mode to visualization rules table
- [x] 15.3 Update `dashboard_vrtl/__manifest__.py` if needed for new dependencies

## 16. Testing and verification

- [x] 16.1 Verify menu_mode "replace": Accounting menu opens dashboard
- [x] 16.2 Verify menu_mode "submenu": dashboard appears as child under Accounting
- [x] 16.3 Verify original menu action restored on dashboard delete
- [x] 16.4 Verify kanban drag-and-drop: drag card between columns, verify orm.write
- [x] 16.5 Verify non-draggable kanban does not accept drags
- [x] 16.6 Verify post-drop data refresh shows card in new column
- [x] 16.7 Verify all 7 dashboards load without errors
- [x] 16.8 Verify CEO dashboard KPIs display reasonable values
- [x] 16.9 Verify CFO Monthly budget vs actual heatmap renders
- [x] 16.10 Verify bookkeeper kanban show account.move cards grouped by journal
- [x] 16.11 Verify project margin adapter returns revenue, cost, margin
- [x] 16.12 Verify CRM forecast returns weighted pipeline value
- [x] 16.13 Verify settings checkbox toggles dashboard visibility
- [x] 16.14 Verify YAML round-trip for a dashboard with menu_mode=replace + kanban_draggable
