# -*- coding: utf-8 -*-
{
    'name': 'Financial Reports (Community)',
    'version': '18.0.1.0.0',
    'category': 'Accounting/Accounting',
    'summary': 'Balance Sheet, P&L, Trial Balance, General Ledger with Journal & Analytic filters + Excel export',
    'description': """
        Provides Enterprise-style financial reports for Odoo 18 Community:
        - Balance Sheet
        - Profit & Loss
        - Trial Balance
        - General Ledger

        Features:
        - Filter by Journal(s)
        - Filter by Analytic Account(s)
        - Date range filter
        - In-browser preview (HTML)
        - Export to Excel (.xlsx)
    """,
    'author': 'Custom',
    'depends': ['account', 'analytic'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/financial_report_wizard_views.xml',
        'views/menu_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'account_financial_reports/static/src/scss/financial_report.scss',
            'account_financial_reports/static/src/js/financial_report.js',
            'account_financial_reports/static/src/xml/financial_report.xml',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}
