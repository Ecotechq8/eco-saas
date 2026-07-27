# -*- coding: utf-8 -*-
{
    'name': 'Eco Base Fixes',
    'version': '18.0.1.0.0',
    'category': 'Technical',
    'summary': 'Resets base action domains and fixes lingering issues after uninstalling custom modules',
    'author': 'Ahmed Emara',
    'website': 'https://ecopro-mena.com',
    'license': 'LGPL-3',
    'depends': ['base'],
    'data': [
        'views/res_users_views.xml',
    ],
    'installable': True,
    'auto_install': False,
}
