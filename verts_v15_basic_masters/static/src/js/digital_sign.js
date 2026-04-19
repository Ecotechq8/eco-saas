/** @odoo-module **/

import { Component, useRef, onMounted, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { useService } from "@web/core/utils/hooks";

/**
 * Digital signature field widget for Odoo 18
 * 
 * Migrated from Odoo 15 legacy widget
 * Original module: verts_v15_basic_masters.verts_v15_basic_masters
 * 
 * ⚠️ NEEDS HUMAN REVIEW: This is a skeleton migration.
 * The original widget used jQuery, _rpc, and session APIs which are all removed in OWL 2.
 * Business logic must be manually ported.
 */

export class FieldSignature extends Component {
    static template = "verts_v15_basic_masters.FieldSignature";
    static props = {
        ...standardFieldProps,
    };

    setup() {
        super.setup();
        this.orm = useService("orm");
        this.root = useRef("root");
        this.state = useState({
            signatureUrl: null,
        });
        
        onMounted(async () => {
            // ⚠️ Migrate the original init/render logic here
            // Original used: self._rpc({ model, method, args })
            // Replace with: await this.orm.call(model, method, args)
            await this._loadSignature();
        });
    }

    async _loadSignature() {
        // ⚠️ Migrate from:
        // self._rpc({ model: this.model, method: 'read', args: [this.res_id, [field_name]] })
        // To:
        // const result = await this.orm.call(this.props.record.resModel, 'read', [this.props.record.resId, ['signature_field']]);
    }

    _clearSignature() {
        // ⚠️ Migrate from the original sign_clean logic
    }
}

// Register the field
registry.category("fields").add("signature", FieldSignature);
