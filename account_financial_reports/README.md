# account_financial_reports — Odoo 18 Community

Enterprise-style financial reports for **Odoo 18 Community Edition** (no `account_reports` dependency required).

## Reports Included

| Report | Description |
|---|---|
| **General Ledger** | All posted journal entries grouped by account, with running balance |
| **Trial Balance** | Opening balance + period movements + closing balance per account |
| **Balance Sheet** | Assets / Liabilities / Equity snapshot |
| **Profit & Loss** | Income vs Expenses with net profit/loss |

## Features

- **Journal filter** — multi-select, leave empty for all journals
- **Analytic Account filter** — multi-select, filters by `analytic_distribution` JSON field
- **Date range filter** — From / To date
- **In-browser HTML preview** — rendered in a full OWL client action
- **Export to Excel** — professionally styled `.xlsx` with frozen panes, colour-coded rows, negative values in red

---

## Requirements

| Item | Details |
|---|---|
| Odoo | 18.0 Community |
| Python | `xlsxwriter >= 3.0` — install with `pip install xlsxwriter` |
| Odoo modules | `account`, `analytic` (both standard Community modules) |

---

## Installation

```bash
# 1. Install the Python dependency
pip install xlsxwriter

# 2. Copy the module to your addons path
cp -r account_financial_reports /path/to/odoo/custom_addons/

# 3. Restart Odoo
sudo systemctl restart odoo   # or however you restart

# 4. Activate developer mode in Odoo settings
# 5. Apps → Update Apps List → search "Financial Reports" → Install
```

---

## Usage

1. Go to **Accounting → Reporting → Custom Financial Reports**
2. Click any of the four report menu items
3. In the wizard dialog, choose:
   - **Date range** (From / To)
   - **Journals** (leave empty = all)
   - **Analytic Accounts** (leave empty = all)
4. Click **View Report** — the report opens in the browser
5. Click **Export to Excel** to download the `.xlsx` file

---

## File Structure

```
account_financial_reports/
├── __manifest__.py
├── __init__.py
├── models/
│   └── financial_report_engine.py   ← SQL queries for all 4 reports
├── wizard/
│   ├── financial_report_wizard.py   ← TransientModel with filters
│   └── financial_report_wizard_views.xml
├── controllers/
│   └── main.py                      ← /financial_reports/data (JSON)
│                                       /financial_reports/export_xlsx (download)
├── views/
│   └── menu_views.xml
├── security/
│   └── ir.model.access.csv
└── static/src/
    ├── js/financial_report.js       ← OWL client action component
    ├── xml/financial_report.xml     ← OWL templates (all 4 layouts)
    └── scss/financial_report.scss   ← Styling
```

---

## How Analytic Filtering Works

Odoo 17/18 stores analytic distribution as a **PostgreSQL JSONB** field on `account.move.line`:

```json
{ "42": 60.0, "17": 40.0 }   ← analytic_account_id: percentage
```

The filter uses the PostgreSQL `?` operator to match lines that contain any of the selected account IDs as a key:

```sql
aml.analytic_distribution ? '42'
```

---

## Troubleshooting

| Issue | Fix |
|---|---|
| "xlsxwriter not installed" on export | `pip install xlsxwriter` on your server |
| Empty report | Check that `account.move` records have `state = 'posted'` |
| Menu not visible | Ensure user has **Accountant** or **Adviser** role |
| JS errors in console | Run `?debug=assets` to rebuild assets |
| `account.account_type` error | Module uses `internal_group` field (Odoo 16+); verify your chart of accounts is configured |
