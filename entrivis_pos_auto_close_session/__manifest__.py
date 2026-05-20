# -*- coding: utf-8 -*-
{
    'name': "Entrivis POS Auto Close Session",

    'summary': """""",

    'description': """""",

    'author': "Entrivis Tech. Pvt. Ltd.",
    'website': "https://www.entrivistech.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/18.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '18.0.1.0.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'point_of_sale'],

    # always loaded
    'data': [
        'data/pos_auto_close_cron.xml',
        'views/res_config_settings.xml',
    ],
    'assets': {
        'point_of_sale.assets_frontend': [
            'entrivis_pos_auto_close_session/static/src/js/*.js',
        ]
    },
    'license': 'LGPL-3',
}
