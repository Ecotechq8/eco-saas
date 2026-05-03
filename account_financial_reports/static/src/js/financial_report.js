/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, useState, onWillStart } from "@odoo/owl";

class FinancialReportPreview extends Component {
    static template = "account_financial_reports.ReportPreview";
    static props = ["*"];

    setup() {
        this.orm          = useService("orm");
        this.notification = useService("notification");

        this.state = useState({
            loading:    true,
            error:      null,
            data:       null,
            reportType: "",
            options:    {},
        });

        onWillStart(async () => {
            const params = this.props.action?.params || {};
            this.state.reportType = params.report_type || "";
            this.state.options    = params.options     || {};
            await this._loadReport();
        });
    }

    async _jsonRpc(route, params) {
        const response = await fetch(route, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                jsonrpc: "2.0",
                method:  "call",
                id:      1,
                params:  params,
            }),
        });
        const json = await response.json();
        if (json.error) {
            const msg = json.error.data?.message || json.error.message || "RPC error";
            throw new Error(msg);
        }
        return json.result;
    }

    async _loadReport() {
        this.state.loading = true;
        this.state.error   = null;
        try {
            const data = await this._jsonRpc("/financial_reports/data", {
                options: this.state.options,
            });
            if (data && data.error) {
                this.state.error = data.error;
            } else {
                this.state.data = data;
            }
        } catch (e) {
            this.state.error = e.message || String(e);
        } finally {
            this.state.loading = false;
        }
    }

    async exportXlsx() {
        const options = this.state.options;
        const form    = document.createElement("form");
        form.method   = "POST";
        form.action   = "/financial_reports/export_xlsx";
        form.style.display = "none";

        const add = (n, v) => {
            const input  = document.createElement("input");
            input.type   = "hidden";
            input.name   = n;
            input.value  = v;
            form.appendChild(input);
        };
        add("options",    JSON.stringify(options));
        add("csrf_token", odoo.csrf_token);

        document.body.appendChild(form);
        form.submit();
        document.body.removeChild(form);

        this.notification.add("Excel file download started…", {
            type: "success", sticky: false,
        });
    }

    // ─────────────────────────────────────────────────────────────────────────
    // NEW: Getters for Dynamic Journal Columns (Enterprise Style)
    // ─────────────────────────────────────────────────────────────────────────

    get journalColumns() {
        // Returns the list of journals found by the engine
        return this.state.data?.journal_columns || [];
    }

    getJournalBalance(account, journalName) {
        // Safe access for the specific journal balance in the UI
        if (!account.journal_balances) return 0;
        return account.journal_balances[journalName] || 0;
    }

    // ─────────────────────────────────────────────────────────────────────────
    // Helpers
    // ─────────────────────────────────────────────────────────────────────────

    get reportTitle() {
        return {
            general_ledger: "General Ledger",
            trial_balance:  "Trial Balance",
            balance_sheet:  "Balance Sheet",
            profit_loss:    "Profit & Loss",
        }[this.state.reportType] || "Financial Report";
    }

    fmt(val) {
        if (val === null || val === undefined) return "–";
        const n = parseFloat(val);
        if (isNaN(n)) return val;
        return new Intl.NumberFormat("en-US", {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        }).format(n);
    }

    fmtClass(val) {
        const n = parseFloat(val);
        if (isNaN(n)) return "";
        return n < 0 ? "fr-negative" : "";
    }

    get periodLabel() {
        const o = this.state.options;
        if (o.date_from && o.date_to)
            return `Period: ${o.date_from} → ${o.date_to}`;
        return o.date_to || o.date_from || "";
    }
}

registry.category("actions").add("financial_report_preview", FinancialReportPreview);
export { FinancialReportPreview };