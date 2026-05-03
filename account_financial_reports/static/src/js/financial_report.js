/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, useState, onWillStart, onMounted, xml } from "@odoo/owl";

// ─────────────────────────────────────────────────────────────────────────────
// Main Report Preview Client Action
// ─────────────────────────────────────────────────────────────────────────────

class FinancialReportPreview extends Component {
    static template = "account_financial_reports.ReportPreview";
    static props = ["*"];

    setup() {
        this.rpc    = useService("rpc");
        this.notification = useService("notification");

        this.state = useState({
            loading:     true,
            error:       null,
            data:        null,
            reportType:  "",
            options:     {},
        });

        onWillStart(async () => {
            const params = this.props.action?.params || {};
            this.state.reportType = params.report_type || "";
            this.state.options    = params.options     || {};
            await this._loadReport();
        });
    }

    async _loadReport() {
        this.state.loading = true;
        this.state.error   = null;
        try {
            const data = await this.rpc("/financial_reports/data", {
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
        const options  = this.state.options;
        const form     = document.createElement("form");
        form.method    = "POST";
        form.action    = "/financial_reports/export_xlsx";
        form.style.display = "none";

        const add = (n, v) => {
            const i = document.createElement("input");
            i.type  = "hidden";
            i.name  = n;
            i.value = v;
            form.appendChild(i);
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

    get reportTitle() {
        return {
            general_ledger: "General Ledger",
            trial_balance:  "Trial Balance",
            balance_sheet:  "Balance Sheet",
            profit_loss:    "Profit & Loss",
        }[this.state.reportType] || "Financial Report";
    }

    // ── helpers for template ────────────────────────────────────────────────
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

    get filterSummary() {
        const o = this.state.options;
        const parts = [];
        if (o.journal_ids?.length)
            parts.push(`${o.journal_ids.length} journal(s)`);
        if (o.analytic_account_ids?.length)
            parts.push(`${o.analytic_account_ids.length} analytic account(s)`);
        return parts.length ? "Filtered by: " + parts.join(", ") : "No additional filters";
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// Register as a client action
// ─────────────────────────────────────────────────────────────────────────────
registry.category("actions").add("financial_report_preview", FinancialReportPreview);

export { FinancialReportPreview };
