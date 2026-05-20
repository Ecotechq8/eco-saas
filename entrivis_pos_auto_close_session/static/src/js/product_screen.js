/** @odoo-module **/

import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";

patch(ProductScreen.prototype, "entrivis_pos_auto_close_session.ProductScreen", {
    /**
     * Override _onClickPay to check session state before allowing payment
     */
    async _onClickPay() {
        const posSessionState = this.pos.pos_session.state;
        console.log("Pos Session State", posSessionState);

        if (posSessionState === "closed") {
            // Do not confirm the order and show error popup
            this.dialog.add("AlertDialog", {
                title: this.env._t("This Session is Already Closed"),
                body: this.env._t(
                    "As per configuration this session is opened from decided hours. Click Okay to close the Screen."
                ),
            });
            return;
        }

        // If session is open, call the original _onClickPay method
        await super._onClickPay(...arguments);
    },
});
