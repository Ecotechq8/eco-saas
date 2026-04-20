/** @odoo-module **/

import { Component } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

export class FieldColor extends Component {
    static template = "verts_v15_print_template.FieldColor";
    static props = {
        ...standardFieldProps,
    };

    get value() {
        return this.props.record.data[this.props.name];
    }

    get readonly() {
        return this.props.readonly;
    }

    get widgetClass() {
        return "oe_form_field";
    }
}

registry.category("fields").add("color", FieldColor);
