/** @odoo-module **/
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, useState, onWillStart } from "@odoo/owl";

class FinancialReportPreview extends Component {
    static template = "account_financial_reports.ReportPreview";
    setup() {
        this.orm = useService("orm");
        this.state = useState({ data: null, options: this.props.action.params.options });
        onWillStart(async () => { await this.load(); });
    }
    async load() {
        const response = await fetch("/financial_reports/data", {
            method: "POST", headers: {"Content-Type": "application/json"},
            body: JSON.stringify({jsonrpc: "2.0", method: "call", params: {options: this.state.options}})
        });
        const res = await response.json();
        this.state.data = res.result;
    }
    fmt(v) { return new Intl.NumberFormat('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2}).format(v); }
    exportXlsx() {
        const url = `/financial_reports/export_xlsx?options=${encodeURIComponent(JSON.stringify(this.state.options))}`;
        window.location.href = url;
    }
    get periodLabel() { return `${this.state.options.date_from || ''} → ${this.state.options.date_to || ''}`; }
}
registry.category("actions").add("financial_report_preview", FinancialReportPreview);