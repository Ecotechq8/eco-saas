# -*- coding: utf-8 -*-

{
    'name': "ECO Data Cleanup - Delete All Transactions",
    'version': '18.0.1.0.0',
    'author': 'Ezzat Mohsen',
    'category': 'Tools',
    'website': '',
    'license': 'LGPL-3',
    'summary': '''
    Action server to delete all transactions from Purchase, Sales, Inventory, Projects, and Accounting.
    ''',
    'description': '''
    This module adds an action server in the Inventory module that allows administrators
    to delete all transactions from:
    - Purchase Orders
    - Sales Orders
    - Inventory (Stock Moves, Pickings, etc.)
    - Projects & Tasks
    - Accounting (Journal Entries, Invoices, Payments, etc.)
    
    WARNING: This is a DESTRUCTIVE operation. All transaction data will be permanently deleted.
    Master data (products, partners, etc.) will be preserved.
    ''',
    'depends': [
        'stock',
        'sale',
        'purchase',
        'project',
        'account',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/data_cleanup_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
