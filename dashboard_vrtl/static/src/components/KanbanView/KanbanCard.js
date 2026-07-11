/** @odoo-module **/

import { Component, useRef } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

/**
 * KanbanCard — renders a single kanban card with title, subtitle,
 * state badge, body KPI badges, footer, and action buttons.
 * Supports HTML5 drag-and-drop when config.kanban_draggable is true.
 */
export class KanbanCard extends Component {
    static template = "dashboard_vrtl.KanbanCard";
    static props = {
        card: Object,
        config: Object,
        onCardClick: Function,
        onActionClick: Function,
        onDragStart: { optional: true, type: Function },
        onDragEnd: { optional: true, type: Function },
    };

    setup() {
        this.action = useService("action");
        this.cardRef = useRef("card");
    }

    get isDraggable() {
        return this.props.config.kanban_draggable === true ||
               this.props.config.kanban_draggable === "true" ||
               this.props.config.kanban_draggable === "True";
    }

    // ── Computed display properties ──

    get title() {
        const field = this.props.config.card_title_field;
        if (field && this.props.card.columns[field] !== undefined) {
            return this.props.card.columns[field];
        }
        const cols = this.props.card.columns;
        for (const key of Object.keys(cols)) {
            if (typeof cols[key] === "string" && key !== "id") return cols[key];
        }
        return this.props.card.id || "";
    }

    get subtitle() {
        const field = this.props.config.card_subtitle_field;
        if (field && this.props.card.columns[field] !== undefined) {
            return this.props.card.columns[field];
        }
        return "";
    }

    get stateValue() {
        const field = this.props.config.state_field;
        if (field && this.props.card.columns[field] !== undefined) {
            return this.props.card.columns[field];
        }
        return "";
    }

    get stateColor() {
        const colors = this._parseJson(this.props.config.state_colors);
        const state = this.stateValue;
        return (colors && colors[state]) || "#e9ecef";
    }

    get stateIcon() {
        const icons = this._parseJson(this.props.config.state_icons);
        const state = this.stateValue;
        return (icons && icons[state]) || "";
    }

    get stateLabel() {
        return this.stateValue.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
    }

    get bodyFields() {
        const fields = this._parseJson(this.props.config.card_body_fields);
        if (!Array.isArray(fields)) return [];
        return fields.map((name) => ({
            name,
            value: this.props.card.columns[name],
            unit: this.props.card.units?.[name],
        }));
    }

    get footerFields() {
        const fields = this._parseJson(this.props.config.card_footer_fields);
        if (!Array.isArray(fields)) return [];
        return fields.map((name) => ({
            name,
            value: this.props.card.columns[name],
        }));
    }

    get visibleActions() {
        const actions = this._parseJson(this.props.config.card_actions);
        if (!Array.isArray(actions)) return [];
        return actions.slice(0, 2);
    }

    get moreActions() {
        const actions = this._parseJson(this.props.config.card_actions);
        if (!Array.isArray(actions) || actions.length <= 3) return [];
        return actions.slice(2);
    }

    get hasMoreActions() {
        return this.moreActions.length > 0;
    }

    formatValue(value, unit) {
        if (value === undefined || value === null) return "—";
        if (unit === "monetary") {
            const num = parseFloat(value);
            return isNaN(num) ? value : num.toLocaleString("sv-SE") + " kr";
        }
        if (unit === "percentage") {
            const num = parseFloat(value);
            return isNaN(num) ? value : num.toFixed(1) + "%";
        }
        if (unit === "integer") {
            const num = parseInt(value, 10);
            return isNaN(num) ? value : num.toLocaleString("sv-SE");
        }
        return value;
    }

    // ── Event handlers ──

    handleClick() {
        this.props.onCardClick(this.props.card);
    }

    handleActionClick(ev, actionDef) {
        ev.stopPropagation();
        this.props.onActionClick(actionDef, this.props.card);
    }

    // ── Drag & Drop ──

    handleDragStart(ev) {
        if (!this.isDraggable) return;
        ev.dataTransfer.setData("text/plain", JSON.stringify({
            id: this.props.card.id,
            columns: this.props.card.columns,
        }));
        ev.dataTransfer.effectAllowed = "move";
        // Reduce opacity of source card
        const el = this.cardRef.el;
        if (el) {
            el.style.opacity = "0.4";
            // Defer adding dragging class to next frame for ghost effect
            requestAnimationFrame(() => {
                if (el) el.classList.add("o_kanban_card_dragging");
            });
        }
        if (this.props.onDragStart) {
            this.props.onDragStart(this.props.card);
        }
    }

    handleDragEnd(ev) {
        const el = this.cardRef.el;
        if (el) {
            el.style.opacity = "";
            el.classList.remove("o_kanban_card_dragging");
        }
        if (this.props.onDragEnd) {
            this.props.onDragEnd(this.props.card);
        }
    }

    _parseJson(raw) {
        if (!raw) return {};
        if (typeof raw === "object") return raw;
        try {
            return JSON.parse(raw);
        } catch {
            return {};
        }
    }
}
