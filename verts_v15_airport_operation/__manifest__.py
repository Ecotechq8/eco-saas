# -*- coding: utf-8 -*-
{
    'name': 'Airport Operation',
    'version': '18.0.1.0.0',
    'summary': 'airport operation',
    'license': "AGPL-3",
    'category': 'Services',
    'author': 'Verts Services India Pvt. Ltd.',
    'website': 'https://www.verts.co.in',
    'sequence': '3',
    'depends': ['base', 'account', 'purchase', 'verts_v15_freight_forward'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/sequence_data.xml',
        'views/inbound_flight_view.xml',
        # 'views/configuration.xml',
        # 'views/gsa_invoice.xml',
        # 'views/gsa_invoice_account.xml',
        # 'views/gsa_invocie_commision_view.xml',
        'views/product_template_view.xml',
        'reports/gsa_invoice_report.xml',
        'reports/gsa_invoice_commission_report.xml',
        'views/menu.xml',

    ],
    'license': 'AGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}

