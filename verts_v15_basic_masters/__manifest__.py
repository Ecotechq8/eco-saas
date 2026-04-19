# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


{
    "name": "Verts V15 Basic Masters",
    "version": "18.0.1.0.0",
    'author': 'VERTS Services India Pvt. Ltd.',
    "description": """""",
    "website": "http://www.verts.co.in",
    "depends": ['base', 'product', 'hr'],
    "category": "Generic Modules",
    "license": "LGPL-3",
    "data": [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/mode_transport_data.xml',
        'data/state_data.xml',
        'views/basic_masters_view.xml',
        # 'views/branch_master_view.xml',
        'views/res_branch_views.xml',
        'views/pin_code_view.xml',
        'views/res_users_view.xml',
        'views/product_view.xml',
        'views/customers_view.xml',
        'views/res_company_view.xml',
        'views/res_country_view.xml',
        'views/brand_view.xml',
        'views/partner_categ_view.xml',
        'views/business_classification_view.xml',
        'views/makers_view.xml',
        'views/term_and_condition_set_view.xml',
        'views/term_and_condition_view.xml',
        'views/term_and_condition_option_view.xml',
        'views/hr_department_view.xml',
        'data/cities_data.xml',
        'data/branch_data.xml',
        'data/container_type_data.xml',
        'data/internal_brand_data.xml',
        'data/external_brand_data.xml',
        'data/categories_demo_data.xml',
        'views/menu_view.xml',
    ],
    'installable': True,
    # 'assets': {
    #     'web.assets_backend': [
    #     #'verts_v15_basic_masters/static/src/js/**/*',
    #     ],
    #     'web.qweb_suite_reports': [
    #         'verts_v15_basic_masters/static/src/xml/digital_sign.xml',
    #     ],
    # },
}


