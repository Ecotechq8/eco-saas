/** @odoo-module **/
// ============================================================================
// ERP Heritage
// Copyright (C) 2026 (https://www.erpheritage.com.au/)
// ============================================================================
//
// Dynamic Report viewer.
//
// A client action that renders any registered eh.account.dynamic.report
// interactively in the Odoo backend. The action context provides the
// report_code; the component fetches the report record, calls render() to
// get the JSON payload, and lays it out as a hierarchical table with a
// comprehensive filter pane above.
//
// Filters: date mode (range, as-of, this/last month/quarter/year),
// comparison toggle (none, previous_period, previous_year), companies,
// journals, partners, accounts, account types, analytic plans and
// analytic accounts. Posted-only and show-zero stay as quick checkboxes.
//
// Currency: every payload carries a currency block resolved server side
// from the company scope. The viewer renders amounts with the right
// symbol, decimal places, position. Multi-currency scopes mark the
// payload as such and the cells render numbers without a symbol.
//
// Hierarchy: lines flagged unfoldable can be expanded / collapsed; the
// component tracks the expanded set in state so re-renders preserve it.

import { Component, onWillStart, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { user } from "@web/core/user";

function todayStr() {
    const d = new Date();
    return d.toISOString().slice(0, 10);
}

function isoDate(d) {
    return d.toISOString().slice(0, 10);
}

function firstOfMonthStr() {
    const d = new Date();
    return isoDate(new Date(d.getFullYear(), d.getMonth(), 1));
}

function shiftMonths(date, count) {
    const d = new Date(date.getFullYear(), date.getMonth() + count, date.getDate());
    return d;
}

function startOfQuarter(date) {
    const q = Math.floor(date.getMonth() / 3);
    return new Date(date.getFullYear(), q * 3, 1);
}

function endOfQuarter(date) {
    const q = Math.floor(date.getMonth() / 3);
    return new Date(date.getFullYear(), q * 3 + 3, 0);
}

function endOfMonth(date) {
    return new Date(date.getFullYear(), date.getMonth() + 1, 0);
}

const PRESET_RANGES = {
    this_month: () => {
        const today = new Date();
        return [isoDate(new Date(today.getFullYear(), today.getMonth(), 1)),
                isoDate(endOfMonth(today))];
    },
    last_month: () => {
        const today = new Date();
        const start = new Date(today.getFullYear(), today.getMonth() - 1, 1);
        return [isoDate(start), isoDate(endOfMonth(start))];
    },
    this_quarter: () => {
        const today = new Date();
        return [isoDate(startOfQuarter(today)), isoDate(endOfQuarter(today))];
    },
    last_quarter: () => {
        const today = new Date();
        const last = shiftMonths(today, -3);
        return [isoDate(startOfQuarter(last)), isoDate(endOfQuarter(last))];
    },
    this_year: () => {
        const today = new Date();
        return [`${today.getFullYear()}-01-01`, `${today.getFullYear()}-12-31`];
    },
    last_year: () => {
        const today = new Date();
        const y = today.getFullYear() - 1;
        return [`${y}-01-01`, `${y}-12-31`];
    },
};

const ACCOUNT_TYPE_CHOICES = [
    { code: "asset_receivable", label: "Receivable" },
    { code: "asset_cash", label: "Cash" },
    { code: "asset_current", label: "Current Asset" },
    { code: "asset_non_current", label: "Non-current Asset" },
    { code: "asset_prepayments", label: "Prepayments" },
    { code: "asset_fixed", label: "Fixed Asset" },
    { code: "liability_payable", label: "Payable" },
    { code: "liability_credit_card", label: "Credit Card" },
    { code: "liability_current", label: "Current Liability" },
    { code: "liability_non_current", label: "Non-current Liability" },
    { code: "equity", label: "Equity" },
    { code: "equity_unaffected", label: "Current Year Earnings" },
    { code: "income", label: "Income" },
    { code: "income_other", label: "Other Income" },
    { code: "expense", label: "Expense" },
    { code: "expense_depreciation", label: "Depreciation" },
    { code: "expense_direct_cost", label: "Cost of Revenue" },
    { code: "off_balance", label: "Off-balance" },
];

function formatCurrency(value, currency, figureType) {
    if (value === null || value === undefined || value === "") {
        return "";
    }
    if (typeof value !== "number") {
        return String(value);
    }
    if (figureType === "integer") {
        return Math.trunc(value).toLocaleString();
    }
    if (figureType === "percentage") {
        return (value * 100).toFixed(2) + "%";
    }
    if (figureType === "float") {
        const fixed = Math.abs(value).toLocaleString(undefined, {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        });
        return value < 0 ? "(" + fixed + ")" : fixed;
    }
    if (figureType !== "monetary") {
        return String(value);
    }
    const decimals = (currency && currency.decimal_places !== undefined)
        ? currency.decimal_places : 2;
    const fixed = Math.abs(value).toLocaleString(undefined, {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals,
    });
    let body;
    if (currency && currency.symbol && !currency.multi_currency) {
        if (currency.position === "before") {
            body = currency.symbol + " " + fixed;
        } else {
            body = fixed + " " + currency.symbol;
        }
    } else {
        body = fixed;
    }
    return value < 0 ? "(" + body + ")" : body;
}

export class EhDynamicReportViewer extends Component {
    static template = "eh_account_dynamic_reports.DynamicReportViewer";
    static props = { "*": true };

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");
        this.dialog = useService("dialog");
        this.user = user;

        const ctx = (this.props.action && this.props.action.context) || {};
        this.reportCode = ctx.report_code;

        this.state = useState({
            loading: true,
            error: null,
            reportId: null,
            reportName: "",
            payload: null,
            filtersExpanded: false,
            expandedLines: [],
            savedViews: [],
            currentSavedViewId: null,
            choices: {
                companies: [],
                journals: [],
                partners: [],
                accounts: [],
                accountTypes: ACCOUNT_TYPE_CHOICES,
                analyticPlans: [],
                analyticAccounts: [],
            },
            options: {
                date: {
                    mode: "range",
                    date_from: firstOfMonthStr(),
                    date_to: todayStr(),
                },
                company_ids: [],
                journal_ids: [],
                partner_ids: [],
                account_ids: [],
                account_type_ids: [],
                analytic_account_ids: [],
                analytic_plan_ids: [],
                posted_only: true,
                show_zero: false,
                comparison: "none",
            },
        });

        onWillStart(async () => {
            await this.bootstrap();
        });
    }

    async bootstrap() {
        if (!this.reportCode) {
            this.state.loading = false;
            this.state.error = "No report_code in action context.";
            return;
        }
        const allowed = (this.user && this.user.context
            && this.user.context.allowed_company_ids) || [];
        if (allowed.length) {
            this.state.options.company_ids = allowed.slice();
        }
        const records = await this.orm.searchRead(
            "eh.account.dynamic.report",
            [["code", "=", this.reportCode]],
            ["id", "name"],
            { limit: 1 },
        );
        if (!records.length) {
            this.state.loading = false;
            this.state.error =
                "No registered report with code: " + this.reportCode;
            return;
        }
        this.state.reportId = records[0].id;
        this.state.reportName = records[0].name;
        await this.loadFilterChoices();
        await this.loadSavedViews();
        await this.refresh();
    }

    async loadSavedViews() {
        try {
            const views = await this.orm.call(
                "eh.account.report.saved_view", "list_for",
                [this.reportCode],
            );
            this.state.savedViews = views || [];
        } catch (e) {
            this.state.savedViews = [];
        }
    }

    async onSavedViewChange(event) {
        const viewId = parseInt(event.target.value, 10);
        if (!viewId) {
            this.state.currentSavedViewId = null;
            return;
        }
        try {
            const opts = await this.orm.call(
                "eh.account.report.saved_view", "load",
                [[viewId]],
            );
            if (opts) {
                // Merge: keep keys we know about, replace with the loaded
                // values; unknown keys in the saved view are dropped.
                const cur = this.state.options;
                for (const key of Object.keys(cur)) {
                    if (key in opts) {
                        cur[key] = opts[key];
                    }
                }
                this.state.currentSavedViewId = viewId;
                this.refresh();
            }
        } catch (e) {
            this.notification.add(
                "Failed to load saved view: "
                + ((e && e.message) || String(e)),
                { type: "danger" },
            );
        }
    }

    async onSaveCurrentView() {
        const name = window.prompt(
            "Save current filters as a view name:",
            "My filters",
        );
        if (!name) return;
        const shared = window.confirm(
            "Share with everyone in this company? Cancel for personal.",
        );
        try {
            const newId = await this.orm.call(
                "eh.account.report.saved_view", "save_view",
                [name, this.reportCode, this.state.options, shared],
            );
            this.state.currentSavedViewId = newId;
            this.notification.add(
                "Saved view: " + name, { type: "success" },
            );
            await this.loadSavedViews();
        } catch (e) {
            this.notification.add(
                (e && e.message) || String(e), { type: "danger" },
            );
        }
    }

    async onDeleteSavedView() {
        if (!this.state.currentSavedViewId) return;
        if (!window.confirm("Delete this saved view?")) return;
        try {
            await this.orm.unlink(
                "eh.account.report.saved_view",
                [this.state.currentSavedViewId],
            );
            this.state.currentSavedViewId = null;
            await this.loadSavedViews();
        } catch (e) {
            this.notification.add(
                (e && e.message) || String(e), { type: "danger" },
            );
        }
    }

    async loadFilterChoices() {
        // Companies, journals: bounded sets, fetch all.
        const [companies, journals, partners, accounts, plans, analyticAccounts] = await Promise.all([
            this.orm.searchRead("res.company", [], ["id", "name"], { limit: 50, order: "name" }),
            this.orm.searchRead("account.journal", [], ["id", "name", "code"], { limit: 200, order: "name" }),
            this.orm.searchRead(
                "res.partner",
                [["customer_rank", ">", 0], ["parent_id", "=", false]],
                ["id", "name"],
                { limit: 100, order: "name" },
            ),
            this.orm.searchRead("account.account", [], ["id", "code", "name"], { limit: 200, order: "code" }),
            this.tryFetch("account.analytic.plan", [], ["id", "name"], { limit: 50, order: "name" }),
            this.tryFetch("account.analytic.account", [], ["id", "name"], { limit: 100, order: "name" }),
        ]);
        this.state.choices.companies = companies;
        this.state.choices.journals = journals.map((j) => ({
            ...j, name: j.code ? `${j.code} ${j.name}` : j.name,
        }));
        this.state.choices.partners = partners;
        this.state.choices.accounts = accounts;
        this.state.choices.analyticPlans = plans;
        this.state.choices.analyticAccounts = analyticAccounts;
    }

    async tryFetch(model, domain, fields, opts) {
        // Analytic models may not be installed in some setups; tolerate.
        try {
            return await this.orm.searchRead(model, domain, fields, opts);
        } catch (e) {
            return [];
        }
    }

    async refresh() {
        if (!this.state.reportId) {
            return;
        }
        this.state.loading = true;
        this.state.error = null;
        try {
            const payload = await this.orm.call(
                "eh.account.dynamic.report",
                "render",
                [[this.state.reportId], this.state.options],
            );
            this.state.payload = payload;
        } catch (exc) {
            this.state.error = (exc && exc.message) || String(exc);
        } finally {
            this.state.loading = false;
        }
    }

    async onRefresh() {
        await this.refresh();
    }

    async onExportXlsx() {
        if (!this.state.reportId) return;
        try {
            const action = await this.orm.call(
                "eh.account.dynamic.report",
                "export_xlsx_attachment",
                [[this.state.reportId], this.state.options],
            );
            await this.action.doAction(action);
        } catch (exc) {
            this.notification.add(
                (exc && exc.message) || String(exc), { type: "danger" },
            );
        }
    }

    async onPrintPdf() {
        if (!this.state.reportId) return;
        try {
            const action = await this.orm.call(
                "eh.account.dynamic.report",
                "export_pdf_attachment",
                [[this.state.reportId], this.state.options],
            );
            await this.action.doAction(action);
        } catch (exc) {
            this.notification.add(
                (exc && exc.message) || String(exc), { type: "danger" },
            );
        }
    }

    async onLineClick(line) {
        if (!this.state.reportId) return;
        try {
            const drillAction = await this.orm.call(
                "eh.account.dynamic.report",
                "get_drilldown_for_line",
                [[this.state.reportId], this.state.options, line.id],
            );
            if (drillAction) {
                await this.action.doAction(drillAction);
            }
        } catch (exc) {
            console.warn("eh_dynamic_report drilldown failed", exc);
        }
    }

    // ---- filter handlers ----

    onToggleFilters() {
        this.state.filtersExpanded = !this.state.filtersExpanded;
    }

    onDateModeChange(event) {
        const mode = event.target.value;
        this.state.options.date.mode = mode;
        if (PRESET_RANGES[mode]) {
            const [from, to] = PRESET_RANGES[mode]();
            this.state.options.date.date_from = from;
            this.state.options.date.date_to = to;
            this.refresh();
        } else if (mode === "as_of") {
            this.state.options.date.date_from = "0001-01-01";
        }
    }

    onDateFromChange(event) {
        this.state.options.date.date_from = event.target.value;
    }

    onDateToChange(event) {
        this.state.options.date.date_to = event.target.value;
    }

    onComparisonChange(event) {
        this.state.options.comparison = event.target.value;
        this.refresh();
    }

    onPostedOnlyToggle(event) {
        this.state.options.posted_only = event.target.checked;
        this.refresh();
    }

    onShowZeroToggle(event) {
        this.state.options.show_zero = event.target.checked;
        this.refresh();
    }

    onMultiSelectChange(event, key) {
        const ids = Array.from(event.target.selectedOptions).map(
            (o) => parseInt(o.value, 10),
        );
        this.state.options[key] = ids;
        this.refresh();
    }

    onMultiSelectChangeStr(event, key) {
        const codes = Array.from(event.target.selectedOptions).map((o) => o.value);
        this.state.options[key] = codes;
        this.refresh();
    }

    onClearAllFilters() {
        this.state.options.journal_ids = [];
        this.state.options.partner_ids = [];
        this.state.options.account_ids = [];
        this.state.options.account_type_ids = [];
        this.state.options.analytic_account_ids = [];
        this.state.options.analytic_plan_ids = [];
        this.state.options.comparison = "none";
        this.refresh();
    }

    async openManyToManyPicker(model, optionKey, label) {
        // Lightweight picker via search dialog. Falls back to the basic
        // multi-select if the dialog service is unavailable in the host.
        try {
            const ids = await new Promise((resolve, reject) => {
                this.action.doAction({
                    type: "ir.actions.act_window",
                    name: "Pick " + label,
                    res_model: model,
                    views: [[false, "list"]],
                    target: "new",
                    domain: [],
                }, {
                    onClose: (result) => resolve(result && result.ids ? result.ids : null),
                });
            });
            if (ids && ids.length) {
                const merged = new Set(
                    [...(this.state.options[optionKey] || []), ...ids]
                        .map((i) => parseInt(i, 10)),
                );
                this.state.options[optionKey] = Array.from(merged);
                this.refresh();
            }
        } catch (e) {
            this.notification.add(
                "Use the multi-select; full picker unavailable.",
                { type: "warning" },
            );
        }
    }

    activeFilterCount() {
        const opts = this.state.options;
        let n = 0;
        if (opts.journal_ids.length) n++;
        if (opts.partner_ids.length) n++;
        if (opts.account_ids.length) n++;
        if ((opts.account_type_ids || []).length) n++;
        if (opts.analytic_account_ids.length) n++;
        if (opts.analytic_plan_ids.length) n++;
        if (opts.comparison && opts.comparison !== "none") n++;
        return n;
    }

    activeChips() {
        const chips = [];
        const opts = this.state.options;
        if (opts.comparison && opts.comparison !== "none") {
            chips.push({
                label: "Compare: " + opts.comparison.replace("_", " "),
                key: "comparison",
            });
        }
        const named = [
            ["journal_ids", this.state.choices.journals, "Journal"],
            ["partner_ids", this.state.choices.partners, "Partner"],
            ["account_ids", this.state.choices.accounts, "Account"],
            ["analytic_plan_ids", this.state.choices.analyticPlans, "Analytic plan"],
            ["analytic_account_ids", this.state.choices.analyticAccounts, "Analytic"],
        ];
        for (const [key, src, label] of named) {
            for (const id of opts[key] || []) {
                const rec = src.find((r) => r.id === id);
                chips.push({
                    label: `${label}: ${rec ? (rec.code ? rec.code + " " : "") + rec.name : id}`,
                    key, id,
                });
            }
        }
        for (const code of opts.account_type_ids || []) {
            const t = ACCOUNT_TYPE_CHOICES.find((x) => x.code === code);
            chips.push({
                label: "Type: " + (t ? t.label : code),
                key: "account_type_ids", id: code,
            });
        }
        return chips;
    }

    onRemoveChip(chip) {
        if (chip.key === "comparison") {
            this.state.options.comparison = "none";
        } else if (chip.id !== undefined) {
            this.state.options[chip.key] = this.state.options[chip.key].filter(
                (x) => x !== chip.id,
            );
        }
        this.refresh();
    }

    // ---- presentation helpers ----

    valueColumnDefs() {
        if (!this.state.payload) return [];
        return this.state.payload.columns.slice(1);
    }

    formatLineValue(line, valueIndex) {
        const colDef = this.valueColumnDefs()[valueIndex];
        if (!colDef) return "";
        const lineCol = line.columns ? line.columns[valueIndex] : null;
        if (!lineCol) return "";
        return formatCurrency(
            lineCol.value, this.state.payload.currency, colDef.figure_type,
        );
    }

    cellClass(line, valueIndex) {
        const colDef = this.valueColumnDefs()[valueIndex];
        const classes = [];
        if (colDef && ["monetary", "integer", "float", "percentage"].includes(
            colDef.figure_type,
        )) {
            classes.push("text-end");
        }
        const lineCol = line.columns ? line.columns[valueIndex] : null;
        if (lineCol && typeof lineCol.value === "number" && lineCol.value < 0) {
            classes.push("eh_dr_negative");
        }
        return classes.join(" ");
    }

    rowClass(line) {
        const meta = line.meta || {};
        const classes = [];
        if (line.level === 0) classes.push("eh_dr_section_row");
        else classes.push("eh_dr_data_row");
        if (meta.kind === "section_header") classes.push("eh_dr_header");
        if (meta.kind === "section_total") classes.push("eh_dr_total");
        if (meta.kind === "balance_check") classes.push("eh_dr_check");
        if (meta.kind === "net_profit"
            || meta.kind === "net_change"
            || meta.kind === "computed_total") {
            classes.push("eh_dr_computed");
        }
        return classes.join(" ");
    }

    nameStyle(line) {
        const indentEm = (line.level || 0) * 1.5;
        return indentEm ? "padding-left: " + indentEm + "em;" : "";
    }

    isExpanded(line) {
        return this.state.expandedLines.includes(line.id);
    }

    onToggleLine(line) {
        if (this.isExpanded(line)) {
            this.state.expandedLines = this.state.expandedLines.filter(
                (id) => id !== line.id,
            );
        } else {
            this.state.expandedLines = [...this.state.expandedLines, line.id];
        }
    }

    hasHierarchy() {
        return !!(this.state.payload && this.state.payload.lines.some(
            (l) => l.unfoldable,
        ));
    }

    onExpandAll() {
        if (!this.state.payload) return;
        this.state.expandedLines = this.state.payload.lines
            .filter((l) => l.unfoldable).map((l) => l.id);
    }

    onCollapseAll() {
        this.state.expandedLines = [];
    }

    visibleLines() {
        if (!this.state.payload) return [];
        // Hide rows whose parent_id is collapsed; otherwise show.
        const expanded = new Set(this.state.expandedLines);
        const result = [];
        for (const line of this.state.payload.lines) {
            const parentId = line.parent_id;
            if (parentId && !expanded.has(parentId)) continue;
            result.push(line);
        }
        return result;
    }
}

registry.category("actions").add(
    "eh_account_dynamic_report", EhDynamicReportViewer,
);
