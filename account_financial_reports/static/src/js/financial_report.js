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

        onWillStart(async () => { await this.load(); });
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
            this.state.data = res.result;
        } catch (err) {
            this.notification.add("Failed to load report", { type: "danger" });
        } finally {
            this.state.loading = false;
        }
    }

    get Object() { return Object; }

    fmt(v) {
        return new Intl.NumberFormat('en-US', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }).format(v || 0);
    }

    exportXlsx() {
        const opt = encodeURIComponent(JSON.stringify(this.state.options));
        window.location.href = `/financial_reports/export_xlsx?options=${opt}`;
    }
}

registry.category("actions").add("financial_report_preview", FinancialReportPreview);