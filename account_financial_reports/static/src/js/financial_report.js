/** @odoo-module **/
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, useState, onWillStart } from "@odoo/owl";

class FinancialReportPreview extends Component {
    static template = "account_financial_reports.ReportPreview";

    setup() {
        this.notification = useService("notification");
        this.state = useState({
            data: null,
            options: this.props.action.params.options,
            loading: true
        });

        onWillStart(async () => {
            await this.load();
        });
    }

    async load() {
        this.state.loading = true;
        try {
            const response = await fetch("/financial_reports/data", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    jsonrpc: "2.0",
                    method: "call",
                    params: { options: this.state.options }
                })
            });
            const res = await response.json();
            if (res.result) {
                this.state.data = res.result;
            } else {
                this.notification.add("Error loading report data", { type: "danger" });
            }
        } catch (err) {
            console.error(err);
        } finally {
            this.state.loading = false;
        }
    }

    // Helper to allow template to use Object.keys
    get Object() {
        return Object;
    }

    fmt(v) {
        if (v === undefined || v === null) return "0.00";
        return new Intl.NumberFormat('en-US', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }).format(v);
    }

    exportXlsx() {
        const optionsStr = encodeURIComponent(JSON.stringify(this.state.options));
        const url = `/financial_reports/export_xlsx?options=${optionsStr}`;
        window.location.href = url;
    }

    get periodLabel() {
        if (!this.state.options) return "";
        const from = this.state.options.date_from || "Start";
        const to = this.state.options.date_to || "Today";
        return `${from} → ${to}`;
    }
}

registry.category("actions").add("financial_report_preview", FinancialReportPreview);