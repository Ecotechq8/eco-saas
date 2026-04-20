/** @odoo-module **/

import { Component, onMounted, onWillUpdateProps, useRef, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

/**
 * Color field widget for Odoo 18
 *
 * Migrated from Odoo 15 legacy widget
 * Original module: verts_v15_print_template
 * 
 * Uses HTML5 native color picker for better compatibility
 */

export class FieldColor extends Component {
    static template = "verts_v15_print_template.FieldColor";
    static props = {
        ...standardFieldProps,
    };

    setup() {
        super.setup();
        this.inputRef = useRef("colorInput");
        this.state = useState({
            colorValue: this.props.value || "#FFFFFF",
        });

        onMounted(() => {
            if (this.inputRef.el) {
                this.inputRef.el.value = this.state.colorValue;
            }
        });

        onWillUpdateProps((nextProps) => {
            if (nextProps.value !== this.props.value) {
                this.state.colorValue = nextProps.value || "#FFFFFF";
                if (this.inputRef.el) {
                    this.inputRef.el.value = this.state.colorValue;
                }
            }
        });
    }

    onColorInput(event) {
        const value = event.target.value.toUpperCase();
        this.state.colorValue = value;
        this.props.update(value);
    }

    get isReadonly() {
        return this.props.readonly;
    }
}

// Register the field (check if already registered to avoid duplicates)
if (!registry.category("fields").get("color", { onMissing: "ignore" })) {
    registry.category("fields").add("color", FieldColor);
}
