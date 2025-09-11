# -*- coding: utf-8 -*-
{
    'name': 'HR Operations (Portal)',
    'summary': 'Manage HR Operations From Portal',
    'description': """Manage HR Operations From Portal""",
    'version': '1.0.0',
    'author': "Eco-Tech, Omar Amr",
    'website': "https://ecotech.com",
    'category': 'Human Resources',

    # any module necessary for this one to work correctly
    'depends': ['eco_hr_operation', 'portal'],

    "assets": {
        "web.assets_frontend": [
            "hr_portal_operation/static/src/js/operation_portal.js",
            "hr_portal_operation/static/src/js/cancel_op.js",
        ]
    },

    # always loaded
    'data': [
        'views/templates.xml',
    ],
}
