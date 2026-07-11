/** @odoo-module **/

import { Component, onWillStart, onMounted, onWillUnmount, useState, useRef } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { loadJS } from "@web/core/assets";

export class DashboardVrtlAmcharts extends Component {
    static template = "dashboard_vrtl.DashboardAmcharts";
    static props = { "*": true };

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.ui = useService("ui");

        this.rootRef = useRef("root");
        this.grid = false;
        this.timer = false;
        this.chartRefs = {};

        this.state = useState({
            loading: true,
            charts: [],
            filters: [],           // Active cross-chart filters
            drillStack: [],        // Drill-down breadcrumb stack
            filterBar: [],         // Global filter definitions
            name: "",
            editable: false,
        });

        this.activeFilters = {};   // {filterKey: {value, label}}

        onWillStart(async () => {
            await this.loadDashboard();
        });

        onMounted(() => {
            if (window.GridStack) {
                this.grid = window.GridStack.init({
                    staticGrid: true, float: false, styleInHead: true,
                    cellHeight: 90, width: 12, verticalMargin: 3,
                }, this.rootRef.el?.querySelector(".grid-stack"));
            }
            this.startAutoRefresh();
        });

        onWillUnmount(() => {
            if (this.timer) clearInterval(this.timer);
        });
    }

    // ── Data Loading ──

    async loadDashboard() {
        this.state.loading = true;
        try {
            const [duration, charts, name, editable] = await this.orm.call(
                "dashboard.dashboard", "get_charts_details",
                [this.props.action.params.record]
            );
            this.state.charts = charts || [];
            this.state.name = name || "";
            this.state.editable = editable;
            this.autoReloadDuration = duration || 300000;
        } catch (e) {
            console.error("Failed to load dashboard:", e);
        } finally {
            this.state.loading = false;
        }
    }

    startAutoRefresh() {
        if (this.timer) clearInterval(this.timer);
        this.timer = setInterval(() => this.loadDashboard(), this.autoReloadDuration);
    }

    // ── Cross-Chart Filtering ──

    onChartFilter(ev) {
        // Called when a chart emits a filter (single-click)
        const { filterKey, value, label, sourceChart } = ev.detail || ev;

        if (!filterKey) return;

        // Add to active filters
        this.activeFilters[filterKey] = { value, label, sourceChart };

        // Update filter bar display
        this.state.filters = Object.entries(this.activeFilters).map(([key, f]) => ({
            key, label: f.label, value: f.value,
        }));

        // Store in URL
        this.updateURL();

        // Propagate to all compatible charts
        this.refreshFilteredCharts();
    }

    removeFilter(filterKey) {
        delete this.activeFilters[filterKey];
        this.state.filters = Object.entries(this.activeFilters).map(([key, f]) => ({
            key, label: f.label, value: f.value,
        }));
        this.updateURL();
        this.refreshFilteredCharts();
    }

    refreshFilteredCharts() {
        // Trigger re-render of all charts with current filter context
        // Charts implement their own compatibility check
        this.loadDashboard();
    }

    // ── Drill-Down ──

    onChartDrill(ev) {
        // Called when a chart emits a drill-down event (double-click)
        const { field, value, label, chartType } = ev.detail || ev;
        if (!field || !value) return;

        const drillEntry = {
            level: this.state.drillStack.length + 1,
            field, value, label, chartType,
        };

        this.state.drillStack = [...this.state.drillStack, drillEntry];
        this.activeFilters[field] = { value, label, sourceChart: "drill" };

        this.updateURL();
        this.loadDashboard();
    }

    navigateDrill(level) {
        if (level < 0) {
            this.state.drillStack = [];
            this.activeFilters = {};
            this.state.filters = [];
        } else {
            this.state.drillStack = this.state.drillStack.slice(0, level + 1);
            // Rebuild filters from remaining drill levels
            this.activeFilters = {};
            for (const step of this.state.drillStack) {
                this.activeFilters[step.field] = {
                    value: step.value, label: step.label, sourceChart: "drill",
                };
            }
        }
        this.state.filters = Object.entries(this.activeFilters).map(([key, f]) => ({
            key, label: f.label, value: f.value,
        }));
        this.updateURL();
        this.loadDashboard();
    }

    openAction(ev) {
        // Drill-down action: open Odoo view
        const { action } = ev.detail || ev;
        if (action) {
            this.action.doAction(action);
        }
    }

    // ── URL State Persistence ──

    updateURL() {
        const params = new URLSearchParams(window.location.hash.slice(1));
        if (Object.keys(this.activeFilters).length > 0) {
            params.set("filters", Object.entries(this.activeFilters)
                .map(([k, v]) => `${k}:${v.value}`).join(","));
        } else {
            params.delete("filters");
        }
        if (this.state.drillStack.length > 0) {
            params.set("drill", this.state.drillStack
                .map(s => `${s.level}:${s.label}:${s.field}=${s.value}`).join("/"));
        } else {
            params.delete("drill");
        }
        window.location.hash = params.toString();
    }

    restoreFromURL() {
        const params = new URLSearchParams(window.location.hash.slice(1));
        const filterStr = params.get("filters");
        if (filterStr) {
            for (const part of filterStr.split(",")) {
                const [key, value] = part.split(":");
                if (key && value) {
                    this.activeFilters[key] = { value, label: key };
                }
            }
            this.state.filters = Object.entries(this.activeFilters).map(([key, f]) => ({
                key, label: f.label, value: f.value,
            }));
        }
    }

    // ── Chart Registration ──

    registerChart(chartId, ref) {
        this.chartRefs[chartId] = ref;
    }
}

registry.category("actions").add("dashboard_vrtl_amcharts", DashboardVrtlAmcharts);
