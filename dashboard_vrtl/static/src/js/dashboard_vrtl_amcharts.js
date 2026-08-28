/** @odoo-module **/

import { Component, onWillStart, onMounted, onWillUnmount, useState, useRef } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { standardActionServiceProps } from "@web/webclient/actions/action_service";
import { DashboardChartItem } from "../components/DashboardChartItem/DashboardChartItem";

export class DashboardVrtlAmcharts extends Component {
    static template = "dashboard_vrtl.DashboardAmcharts";
    static components = { DashboardChartItem };
    static props = { ...standardActionServiceProps };

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
            many2oneOptions: {},   // filterKey -> [[id, display_name], ...]
            name: "",
            editable: false,
        });

        this.activeFilters = {};   // {filterKey: {value, label}}
        this.globalFilters = {};   // {date_from, date_to, ...} global filter values

        onWillStart(async () => {
            await this.applyBrandContext();
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
            const [duration, charts, name, filterDefs] = await this.orm.call(
                "dashboard.dashboard", "get_charts_details",
                [this.props.action.params.record, {
                    global: this.globalFilters,
                    cross: this.crossFilterValues,
                }]
            );
            this.state.charts = charts || [];
            this.state.name = name || "";
            this.autoReloadDuration = duration || 300000;
            if (Array.isArray(filterDefs)) {
                this.state.filterBar = filterDefs;
                this.initGlobalFilterDefaults(filterDefs);
                for (const fd of filterDefs) {
                    if (fd.type === "many2one") {
                        this.loadMany2oneOptions(fd);
                    }
                }
            }
            // Capture PNGs for charts referenced by active email schedules.
            this.scheduleMailImageCapture();
        } catch (e) {
            console.error("Failed to load dashboard:", e);
        } finally {
            this.state.loading = false;
        }
    }

    get crossFilterValues() {
        const out = {};
        for (const [key, f] of Object.entries(this.activeFilters)) {
            if (f && f.value !== undefined && f.value !== "" && f.value !== null) {
                out[key] = f.value;
            }
        }
        return out;
    }

    initGlobalFilterDefaults(filterDefs) {
        for (const fd of filterDefs) {
            if (fd.type !== "date_range") continue;
            if (!this.globalFilters.date_from && fd.default_from) {
                this.globalFilters.date_from = this.resolveShortcut(fd.default_from);
            }
            if (!this.globalFilters.date_to && fd.default_to) {
                this.globalFilters.date_to = this.resolveShortcut(fd.default_to);
            }
        }
    }

    onGlobalDateRange(which, value) {
        if (which === "from") this.globalFilters.date_from = value;
        else this.globalFilters.date_to = value;
        this.loadDashboard();
    }

    async applyBrandContext() {
        // When the dashboard is opened from the brand kanban (or with a brand
        // injected in the action params), pre-set the brand filter and the
        // session brand context so all brand-aware data scopes to it.
        const brandId = this.props.action.params.brand_id;
        if (!brandId) return;
        this.globalFilters["brand_id"] = brandId;
        try {
            await this.orm.call(
                "dashboard.dashboard", "action_set_brand_context",
                [this.props.action.params.record, brandId]
            );
        } catch (e) {
            console.error("Failed to set brand context:", e);
        }
    }

    async loadMany2oneOptions(gfilter) {
        if (this.state.many2oneOptions[gfilter.key] || !gfilter.model) return;
        try {
            const records = await this.orm.call(
                gfilter.model, "name_search", [""], { limit: 100 }
            );
            this.state.many2oneOptions[gfilter.key] = records || [];
        } catch (e) {
            this.state.many2oneOptions[gfilter.key] = [];
        }
    }

    async onGlobalMany2oneChange(gfilter, value) {
        if (value) {
            this.globalFilters[gfilter.field] = value;
        } else {
            delete this.globalFilters[gfilter.field];
        }
        // Brand filters also set the session brand context so ALL brand-aware
        // data (plans, posts, documents, ...) scope to the selected brand.
        if (gfilter.field === "brand_id") {
            try {
                await this.orm.call(
                    "dashboard.dashboard", "action_set_brand_context",
                    [this.props.action.params.record, value || 0]
                );
            } catch (e) {
                console.error("Failed to set brand context:", e);
            }
        }
        await this.loadDashboard();
    }

    onGlobalShortcut(gfilter, sc) {
        this.globalFilters.date_from = this.resolveShortcut(sc.from);
        this.globalFilters.date_to = this.resolveShortcut(sc.to);
        this.loadDashboard();
    }

    resolveShortcut(expr) {
        if (!expr) return "";
        const now = new Date();
        const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
        const iso = (d) => d.toISOString().slice(0, 10);
        const map = {
            today: () => iso(today),
            this_month_start: () => iso(new Date(today.getFullYear(), today.getMonth(), 1)),
            this_quarter_start: () => iso(new Date(today.getFullYear(), Math.floor(today.getMonth() / 3) * 3, 1)),
            this_year_start: () => iso(new Date(today.getFullYear(), 0, 1)),
            last_7_days: () => iso(new Date(today.getTime() - 7 * 86400000)),
            last_30_days: () => iso(new Date(today.getTime() - 30 * 86400000)),
            last_90_days: () => iso(new Date(today.getTime() - 90 * 86400000)),
            last_365_days: () => iso(new Date(today.getTime() - 365 * 86400000)),
            "12_months_ago": () => iso(new Date(today.getFullYear() - 1, today.getMonth(), today.getDate())),
        };
        return (map[expr] && map[expr]()) || expr;
    }

    startAutoRefresh() {
        if (this.timer) clearInterval(this.timer);
        // Guard against setInterval(..., undefined) which would fire ~every 4ms
        // when the first loadDashboard() failed before setting the duration.
        this.autoReloadDuration = this.autoReloadDuration || 300000;
        this.timer = setInterval(() => this.loadDashboard(), this.autoReloadDuration);
    }

    // ── Layout Editing (drag & drop) ──

    toggleEdit() {
        this.state.editable = !this.state.editable;
        if (this.grid) {
            this.grid.setStatic(!this.state.editable);
            this.grid.enableMove(this.state.editable);
            this.grid.enableResize(this.state.editable);
        }
    }

    async cancelEdit() {
        this.state.editable = false;
        if (this.grid) {
            this.grid.setStatic(true);
            this.grid.enableMove(false);
            this.grid.enableResize(false);
        }
        // Reload to revert any drag changes back to the saved layout
        await this.loadDashboard();
    }

    async saveLayout() {
        if (!this.grid) return;
        const items = this.grid.save(false) || [];
        const layout = items.map((item) => ({
            chartId: parseInt(item.id, 10),
            x: item.x, y: item.y, w: item.w, h: item.h,
        }));
        try {
            await this.orm.call(
                "dashboard.dashboard", "action_save_layout",
                [this.props.action.params.record, layout]
            );
            this.state.editable = false;
            if (this.grid) {
                this.grid.setStatic(true);
                this.grid.enableMove(false);
                this.grid.enableResize(false);
            }
            await this.loadDashboard();
        } catch (e) {
            console.error("Failed to save layout:", e);
        }
    }

    // ── Cross-Chart Filtering ──

    onChartFilter(ev) {
        // Called when a chart emits a filter (single-click)
        const { filterKey, value, label, sourceChart } = ev.detail || ev;

        if (!filterKey) return;

        // Toggle: clicking the same value again removes the filter
        const existing = this.activeFilters[filterKey];
        if (existing && String(existing.value) === String(value)) {
            delete this.activeFilters[filterKey];
        } else {
            this.activeFilters[filterKey] = { value, label, sourceChart };
        }

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

    // ── Email Chart Image Capture ──

    async scheduleMailImageCapture() {
        // Debounce: at most once per 5 minutes per session.
        const now = Date.now();
        if (this._lastMailCapture && now - this._lastMailCapture < 5 * 60 * 1000) return;
        try {
            const chartIds = await this.orm.call(
                "dashboard.dashboard", "get_mail_capture_chart_ids",
                [this.props.action.params.record]
            );
            if (!chartIds || !chartIds.length) return;
            // Let amCharts finish rendering before serializing the SVG.
            setTimeout(() => this.captureMailImages(chartIds), 2500);
        } catch (e) {
            console.error("Failed to resolve mail capture targets:", e);
        }
    }

    async captureMailImages(chartIds) {
        let captured = 0;
        for (const chartId of chartIds) {
            const item = this.rootRef.el?.querySelector(
                `.grid-stack-item[gs-id="${chartId}"]`
            );
            if (!item) continue;
            const svg = item.querySelector("svg");
            if (!svg) continue; // HTML-based types (kpi/tile/list/...) use the email summary fallback
            try {
                const dataUri = await this.svgToPng(svg);
                const b64 = dataUri.replace(/^data:image\/png;base64,/, "");
                await this.orm.call("dashboard.chart", "set_image", [chartId, b64]);
                captured += 1;
            } catch (e) {
                console.error("Chart image capture failed:", chartId, e);
            }
        }
        if (captured) this._lastMailCapture = Date.now();
    }

    svgToPng(svg) {
        return new Promise((resolve, reject) => {
            const xml = new XMLSerializer().serializeToString(svg);
            const svg64 =
                "data:image/svg+xml;base64," +
                btoa(unescape(encodeURIComponent(xml)));
            const img = new Image();
            img.onload = () => {
                try {
                    const rect = svg.getBoundingClientRect();
                    const scale = 2;
                    const canvas = document.createElement("canvas");
                    canvas.width = Math.max(1, Math.round(rect.width * scale));
                    canvas.height = Math.max(1, Math.round(rect.height * scale));
                    const ctx = canvas.getContext("2d");
                    ctx.fillStyle = "#ffffff";
                    ctx.fillRect(0, 0, canvas.width, canvas.height);
                    ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
                    resolve(canvas.toDataURL("image/png"));
                } catch (e) {
                    reject(e);
                }
            };
            img.onerror = () => reject(new Error("SVG image load failed"));
            img.src = svg64;
        });
    }

    // ── Chart Registration ──

    registerChart(chartId, ref) {
        this.chartRefs[chartId] = ref;
    }
}

registry.category("actions").add("dashboard_vrtl_amcharts", DashboardVrtlAmcharts);
