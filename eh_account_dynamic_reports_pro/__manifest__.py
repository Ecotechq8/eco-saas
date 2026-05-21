# -*- encoding: utf-8 -*-
##############################################################################
#
# ERP Heritage
# Copyright (C) 2026 (https://www.erpheritage.com.au/)
#
##############################################################################
{
 'name': "Dynamic Reports Pro",
 'summary': "Premium upgrade to Dynamic Accounting Reports: drag and drop custom report builder, scheduled email delivery, multi period forecasting, and budget vs actual scenario comparison.",
 'description': """
Dynamic Accounting Reports Pro
==============================

Premium extensions to the free Dynamic Accounting Reports module.

Pro features:

* Custom report builder. Drag and drop UI to compose new reports without writing
 Python or XML. Define lines, columns, expressions, drill down rules visually.
* Scheduled email delivery. Any report can be scheduled to email a PDF or XLSX
 to a recipient list on a cron (daily, weekly, monthly, period close).
* Multi period forecasting. Project P&L and Cash Flow forward using configurable
 growth or seasonality rules; compare baseline vs scenarios.
* Saved report views. Per user saved filter sets (date ranges, comparatives,
 drill down state) shareable across teams.

Requires:

* eh_account_dynamic_reports (free, install first).

Optional integrations:

* eh_account_budget_pro.

Search keywords
---------------

Accounting, Full Accounting, Full Accounting for Community, Odoo 19
Community accounting, accounting suite, accounting modules, financial
reporting, period close, accounts receivable, accounts payable, journal
entries, double entry bookkeeping.


    """,
 'author': "ERP Heritage",
 'website': "https://www.erpheritage.com.au/",
 'license': 'LGPL-3',
 'category': 'Accounting/Accounting',
 'version': '0.1',
 'depends': [
 'eh_account_dynamic_reports',
 ],
 'data': [
 'security/ir.model.access.csv',
 'security/eh_isolation_rules.xml',
 'data/cron.xml',
 'views/saved_view_views.xml',
 'views/schedule_views.xml',
 'views/forecast_views.xml',
 'views/builder_views.xml',
 'data/menus.xml',
 ],
 'demo': [
 'demo/pro_demo.xml',
 ],
 'images': ['static/description/banner.png'],
 'installable': True,
 'application': False,
 'auto_install': False,
}
