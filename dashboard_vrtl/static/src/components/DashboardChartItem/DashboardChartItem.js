/** @odoo-module **/

import { Component } from "@odoo/owl";

import { AreaChart } from "../AreaChart/AreaChart";
import { BarChart } from "../BarChart/BarChart";
import { ColumnChart } from "../ColumnChart/ColumnChart";
import { DoughnutChart } from "../DoughnutChart/DoughnutChart";
import { FunnelChart } from "../FunnelChart/FunnelChart";
import { KanbanView } from "../KanbanView/KanbanView";
import { KPIView } from "../KPIView/KPIView";
import { LineChart } from "../LineChart/LineChart";
import { ListView } from "../ListView/ListView";
import { MapChart } from "../MapChart/MapChart";
import { MeterChart } from "../MeterChart/MeterChart";
import { PieChart } from "../PieChart/PieChart";
import { PyramidChart } from "../PyramidChart/PyramidChart";
import { RadarChart } from "../RadarChart/RadarChart";
import { RadialChart } from "../RadialChart/RadialChart";
import { ScatterChart } from "../ScatterChart/ScatterChart";
import { StackedColumnChart } from "../StackedColumnChart/StackedColumnChart";
import { TileView } from "../TileView/TileView";
import { TodoView } from "../TodoView/TodoView";

// Chart types whose components consume an array of row objects
// (each row: {category, <seriesName>: value}).
const ARRAY_MULTI_TYPES = new Set([
    "bar_chart", "column_chart", "line_chart", "area_chart",
    "doughnut_chart", "stackedcolumn_chart", "radial_chart", "scatter_chart",
]);

// Chart types whose components consume an array with a single "value" field.
const ARRAY_VALUE_TYPES = new Set([
    "funnel_chart", "pyramid_chart", "map_chart", "radar_chart",
]);

/**
 * Convert the backend {labels, series} format into the row-array format
 * expected by the amCharts components.
 */
function toRowArray(data, valueOnly = false) {
    const labels = Array.isArray(data.labels) ? data.labels : [];
    const series = Array.isArray(data.series) ? data.series : [];
    return labels.map((label, i) => {
        if (valueOnly) {
            const s0 = series[0];
            return {
                category: label,
                value: s0 && Array.isArray(s0.values) ? s0.values[i] : 0,
            };
        }
        const row = { category: label };
        for (const s of series) {
            if (s && s.name !== undefined && Array.isArray(s.values)) {
                row[s.name] = s.values[i];
            }
        }
        return row;
    });
}

function firstValue(data) {
    const s0 = Array.isArray(data.series) ? data.series[0] : undefined;
    return s0 && Array.isArray(s0.values) ? s0.values[0] : 0;
}

function firstLabel(data, fallback) {
    if (data.name) {
        return data.name;
    }
    if (Array.isArray(data.labels) && data.labels[0]) {
        return data.labels[0];
    }
    return fallback;
}

/**
 * Normalize chart data to the shape expected by the target component.
 * The backend returns {labels, series, rows, ...} while the components
 * expect either an array of row objects or a rich dict (KPI/Tile/Todo/List).
 */
export function normalizeChartData(chart) {
    const data = chart.data;
    if (!data || data.type === "error") {
        return data;
    }
    const type = chart.chart_type;

    // Kanban: {columns, rows, units, kanban_config} — pass through
    if (type === "kanban") {
        return data;
    }

    // Meter gauge: expects a dict {current_value, target}
    if (type === "meter_chart") {
        if (data && typeof data === "object" && !Array.isArray(data) &&
            data.current_value !== undefined) {
            return data;
        }
        const value = firstValue(data);
        const target = data && data.target !== undefined ? data.target : value || 100;
        return { current_value: value, target: target };
    }

    // Array-based amCharts components
    if (ARRAY_MULTI_TYPES.has(type)) {
        if (Array.isArray(data)) {
            return data;
        }
        if (Array.isArray(data.labels) && Array.isArray(data.series)) {
            return toRowArray(data, false);
        }
        return [];
    }

    if (ARRAY_VALUE_TYPES.has(type)) {
        if (Array.isArray(data)) {
            return data;
        }
        if (Array.isArray(data.labels) && Array.isArray(data.series)) {
            return toRowArray(data, true);
        }
        return [];
    }

    // KPI
    if (type === "kpi") {
        if (data.layout_type) {
            return data; // rich format from service source
        }
        return {
            layout_type: "layout1",
            name: firstLabel(data, chart.name || "KPI"),
            count: firstValue(data),
            count2: 0,
            comparison: "none",
            background_color: chart.background_color || "#ffffff",
            font_color: "#343a40",
            font_size: 14,
            text_align: "left",
            icon_option: "custom",
            icon: "",
            default_icon: "",
            kpi_border_type: "border",
            is_kpi_border: false,
            kpi_border_width: 2,
            kpi_border_color: "#dee2e6",
            target: "",
            kpi_enable_target: false,
            kpi_view_type: "progress",
            color: "bg-success",
            progress: 0,
            tooltip_info: chart.name,
        };
    }

    // Tile
    if (type === "tile") {
        if (data.tile_layout_type) {
            return data;
        }
        return {
            tile_layout_type: "layout1",
            name: firstLabel(data, chart.name || "Tile"),
            count: firstValue(data),
            count2: 0,
            comparison: "none",
            background_color: chart.background_color || "#ffffff",
            font_color: "#343a40",
            font_size: 14,
            text_align: "left",
            icon_option: "custom",
            icon: "",
            default_icon: "",
            target: "",
        };
    }

    // List / Table
    if (type === "list" || type === "table") {
        if (data.columns && data.records) {
            return data;
        }
        let rows = data.rows;
        if (!rows && Array.isArray(data.labels)) {
            rows = toRowArray(data, false);
        }
        if (Array.isArray(rows)) {
            // Rows derived from {labels, series} carry no id (only category/
            // _value/series values). Give each row a stable, unique key so the
            // ListView t-foreach never sees duplicate/undefined record ids
            // ("Got duplicate key in t-foreach: undefined").
            rows = rows.map((r, i) => ({
                ...r,
                id: r.id !== undefined && r.id !== null
                    ? r.id
                    : (r._value !== undefined && r._value !== null ? `v_${r._value}` : `row_${i}`),
                currentIds: r.currentIds || (r.id !== undefined && r.id !== null ? [r.id] : []),
            }));
        }
        const columns = rows && rows.length
            ? Object.keys(rows[0])
                  .filter((k) => k !== "currentIds" && k !== "id")
                  .map((k) => ({ column_name: k, name: k, id: k }))
            : [];
        return { columns, records: rows || [], name: chart.name, model: data.model || "" };
    }

    // Todo and any other type: pass through (service sources provide the rich shape)
    return data;
}

export class DashboardChartItem extends Component {
    static template = "dashboard_vrtl.DashboardChartItem";
    static components = {
        AreaChart, BarChart, ColumnChart, DoughnutChart, FunnelChart,
        KanbanView, KPIView, LineChart, ListView, MapChart, MeterChart,
        PieChart, PyramidChart, RadarChart, RadialChart, ScatterChart,
        StackedColumnChart, TileView, TodoView,
    };
    static props = {
        chart: Object,
        editable: { type: Boolean, optional: true },
    };

    get displayData() {
        return normalizeChartData(this.props.chart);
    }

    get hasData() {
        const type = this.props.chart.chart_type;
        if (ARRAY_MULTI_TYPES.has(type) || ARRAY_VALUE_TYPES.has(type)) {
            return Array.isArray(this.displayData) && this.displayData.length > 0;
        }
        return Boolean(this.displayData);
    }
}
