/** @odoo-module */

// import publicWidget from 'web.public.widget';
import publicWidget from "@web/legacy/js/public/public_widget";


publicWidget.registry.PortalHomeCounters.include({
    _getCountersAlwaysDisplayed() {
        return this._super(...arguments).concat(['penalty_count']);
    },
});
