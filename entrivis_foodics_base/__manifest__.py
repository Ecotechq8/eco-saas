# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) 2020-Today Entrivis Tech PVT. LTD. (<http://www.entrivistech.com>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
##############################################################################

{
    'name': "Foodics Integration",
    "description": "Foodics Integration.",
    "summary": """Foodics Integration.""",
    'version': "18.0.1.0.0",
    'category': 'Foodic',
    'website': "www.entrivistech.com",
    'author': 'Entrivis Tech Pvt. Ltd.',
    'maintainer': 'Entrivis Tech Pvt. Ltd.',
    'depends': ['purchase', 'point_of_sale', 'web'],
    'data': [
        'security/ir.model.access.csv',
        # 'data/ir_cron.xml',
        'views/foodic_connector_view.xml',
        'views/foodics_history_view.xml',
        'views/product_view.xml',
        'views/product_category_view.xml',
        'views/pos_config_view.xml',
        'views/res_users.xml',
        'views/res_partner_view.xml',
        'views/payment_method.xml',
        'views/account_tax_view.xml',
        'views/account_tax_group_view.xml',
        'views/pos_order_view.xml',
        # 'data/sync_data_cron.xml',
        'views/pos_session_view.xml',
        # 'views/order_tracking_view.xml',
        # 'views/sale_order_view.xml',
        # 'views/stock_picking_view.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
}
