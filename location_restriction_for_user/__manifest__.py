# -*- coding: utf-8 -*-

{
    'name': 'Location Access Control',
    'description': """Warehouse Location Restriction""",
    'summary': "'Warehouse Restriction for all users convenience and inventory location management'",
    'version': '18.0.1.0.0',
    'category': 'Stock',
    'license': 'LGPL-3',
    'depends': ['base', 'stock', 'sale', 'sale_stock'],
    'data': [

        'views/res_user_inh_view.xml',
        'views/stock_picking_type_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True
}
