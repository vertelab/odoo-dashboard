/** @odoo-module **/

import { Component, onMounted, useEffect, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { KanbanCard } from "./KanbanCard";

/**
 * KanbanView — renders kanban card grid from metric data.
 * Supports grouped columns or fluid grid, state-based coloring,
 * card click → drill-down/filter, HTML5 drag-and-drop between columns,
 * and inline action buttons.
 */
export class KanbanView extends Component {
    static template = "dashboard_vrtl.KanbanView";
    static components = { KanbanCard };
    static props = {
        chartId: String,
        name: String,
        isDirty: { optional: true, type: Boolean },
        data: { optional: true, type: Object },
        update_chart: { optional: true, type: Function },
        onFilterEvent: { optional: true, type: Function },
        onDrillEvent: { optional: true, type: Function },
        theme: String,
        recordSets: Object,
    };

    setup() {
        this.action = useService("action");
        this.orm = useService("orm");

        this.state = useState({
            isError: false,
            errorMessage: "",
            name: "",
            groups: {},
            noGroupCards: [],
            groupField: "",
            loading: false,
            dragState: null,       // {card, sourceGroup}
            dropTarget: null,      // target group key
            isDragging: false,
        });

        useEffect(
            () => {
                this.renderView();
            },
            () => [
                this.props.chartId,
                this.props.recordSets,
                this.props.isDirty,
                this.props.name,
                this.props.data,
            ],
        );

        onMounted(() => {
            this.renderView();
        });
    }

    get kanbanConfig() {
        const rs = this.props.recordSets;
        if (!rs) return {};
        return rs.kanban_config || {};
    }

    get isDraggable() {
        const config = this.kanbanConfig;
        return config.kanban_draggable === true ||
               config.kanban_draggable === "true" ||
               config.kanban_draggable === "True";
    }

    renderView() {
        const data = this.props.recordSets;
        if (!data) return;

        if (data.type === "error") {
            this.state.isError = true;
            this.state.errorMessage = data.message;
            return;
        }

        this.state.isError = false;
        this.state.name = data.name || this.props.name;
        this.state.loading = false;

        const cards = this._buildCards(data);
        this._groupCards(cards, data);
    }

    _buildCards(data) {
        const rows = data.rows || [];
        const columns = data.columns || [];
        const units = data.units || {};

        return rows.map((row, idx) => {
            const cardCols = {};
            if (columns.length > 0) {
                columns.forEach((col, i) => {
                    cardCols[col] = row[i] !== undefined ? row[i] : (Array.isArray(row) ? row[i] : row[col]);
                });
            } else if (typeof row === "object" && !Array.isArray(row)) {
                Object.assign(cardCols, row);
            } else if (Array.isArray(row)) {
                cardCols.id = row[0];
                cardCols._name = row[1] || "";
            }
            return {
                id: cardCols.id || `card_${idx}`,
                columns: cardCols,
                units,
            };
        });
    }

    _groupCards(cards, data) {
        const groupField = this.kanbanConfig.kanban_group_field || data.group_by;
        if (!groupField) {
            this.state.noGroupCards = cards;
            this.state.groups = {};
            this.state.groupField = "";
            return;
        }

        this.state.groupField = groupField;
        const groups = {};
        for (const card of cards) {
            const value = card.columns[groupField] || "Ungrouped";
            if (!groups[value]) groups[value] = [];
            groups[value].push(card);
        }
        this.state.groups = groups;
        this.state.noGroupCards = [];
    }

    // ── Event Handlers ──

    onCardClick(card) {
        if (this.state.isDragging) return;
        if (this.props.onDrillEvent) {
            this.props.onDrillEvent(card);
            return;
        }
        if (this.props.onFilterEvent) {
            this.props.onFilterEvent(card);
            return;
        }
        if (card.id && this.kanbanConfig._drill_model) {
            this.action.doAction({
                type: "ir.actions.act_window",
                res_model: this.kanbanConfig._drill_model,
                res_id: card.id,
                views: [[false, "form"]],
            });
        }
    }

    onActionClick(actionDef, card) {
        if (actionDef.confirm) {
            if (!window.confirm(actionDef.confirm)) return;
        }
        const params = { ...actionDef.params };
        if (params) {
            for (const key of Object.keys(params)) {
                if (typeof params[key] === "string") {
                    params[key] = params[key].replace(/\{(\w+)\}/g, (_, col) =>
                        card.columns[col] !== undefined ? card.columns[col] : `{${col}}`
                    );
                }
            }
        }
        this.action.doAction({
            type: actionDef.action || "ir.actions.act_window",
            res_model: actionDef.res_model || params?.res_model,
            res_id: card.id,
            views: actionDef.views || [[false, "form"]],
            context: { ...(params || {}), ...(actionDef.context || {}) },
            name: actionDef.label || actionDef.name,
        });
    }

    // ── Drag & Drop handlers ──

    onDragStart(card) {
        this.state.isDragging = true;
        this.state.dragState = { card };
    }

    onDragEnd(_card) {
        this.state.isDragging = false;
        this.state.dragState = null;
        this.state.dropTarget = null;
    }

    onDragOver(ev, groupKey) {
        if (!this.isDraggable) return;
        ev.preventDefault();
        ev.dataTransfer.dropEffect = "move";
        this.state.dropTarget = groupKey;
    }

    onDragLeave(_ev, _groupKey) {
        this.state.dropTarget = null;
    }

    async onDrop(ev, targetGroupKey) {
        ev.preventDefault();
        if (!this.isDraggable || !this.state.dragState) return;

        const dragCard = this.state.dragState.card;
        const dragGroupField = this.kanbanConfig.kanban_drag_group_field;
        const resModel = this.kanbanConfig._res_model;

        // Find source group
        const sourceGroupKey = Object.keys(this.state.groups).find(key =>
            this.state.groups[key].some(c => c.id === dragCard.id)
        );

        // No-op if dropping on same column
        if (sourceGroupKey === targetGroupKey) {
            this.state.dragState = null;
            this.state.dropTarget = null;
            this.state.isDragging = false;
            return;
        }

        // Write the group field value
        if (resModel && dragGroupField && dragCard.id) {
            try {
                await this.orm.write(resModel, [dragCard.id], {
                    [dragGroupField]: targetGroupKey,
                });
            } catch (e) {
                console.error("KanbanView: drag-and-drop write failed", e);
            }
        }

        // Reset drag state
        this.state.dragState = null;
        this.state.dropTarget = null;
        this.state.isDragging = false;

        // Re-render with updated data
        this.renderView();
    }

    // ── Card props helpers ──

    getCardConfig(card) {
        return this.kanbanConfig;
    }
}
