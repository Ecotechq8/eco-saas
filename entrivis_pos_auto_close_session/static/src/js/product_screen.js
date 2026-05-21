/** @odoo-module **/

import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { _t } from "@web/core/l10n/translation";
import { patch } from "@web/core/utils/patch";

patch(ProductScreen.prototype, {
    async _onClickPay() {
        const posSessionState = this.pos.pos_session?.state;
        if (posSessionState === "closed") {
            this.dialog.add(AlertDialog, {
                title: _t("This Session is Already Closed"),
                body: _t(
                    "As per configuration this session is opened from decided hours. Click Okay to close the Screen."
                ),
            });
            return;
        }
        await super._onClickPay(...arguments);
    },
});
