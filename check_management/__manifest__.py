# -*- coding: utf-8 -*-
{
    'name': "Check Management",
    "version": "0.1",
    'category': 'Accounting',
    'summary': """ Check Management  """,
    "description": """
        This Module is used for check \n
        It includes creation of check receipt ,check cycle ,Holding ....... \n
    """,
    "author": "Omnya Rashwan",
    "depends": ['account',
                'om_account_accountant',
                'base'
                ],
    "data": [
        'security/ir.model.access.csv',
        'security/security.xml',
        # 'views/account_move.xml',
        'views/account_journal_view.xml',
        'views/checks_fields_view.xml',
        'views/check_payment.xml',
        'views/check_book.xml',
        'views/check_menus.xml',
        'wizard/check_cycle_wizard_view.xml',
        'views/payment_report.xml',
        'views/report_check_cash_payment_receipt_templates.xml',
        'data/action_servers.xml',
        'data/data.xml'
    ],
    "auto_install": False,
    "installable": True,
}
