# -*- coding: utf-8 -*-
#########################################################################
#                                                                       #
#   STRANBYS.COM                                                        #
#                                               #
#   GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3)                         #
#                                                                       #
#########################################################################

{
    "name": "Facility Management",
    "description": """Facility Management by Stranbys""",
    "category": "Operations",
    "version": "18.0.0.0.0",
    'author': 'Stranbys Info Solutions',
    'company': 'Stranbys Info Solutions',
    'maintainer': 'Stranbys Info Solutions',
    'website': "https://www.stranbys.com",
    "depends": ['base', 'account', 'crm', 'purchase', 'stock', 'contacts'],
    "data": [
        'security/ir.model.access.csv',
        'views/noupdate.xml',
        'views/views.xml',
        'views/masters.xml',
        'views/res_config_view.xml',
        'views/menus.xml',
        'wizards/create_invoice_wizard.xml',
    ],
    'images': ['static/description/banner.png',],
    'license': 'LGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
    # 'post_init_hook': 'post_init_hook',
}
