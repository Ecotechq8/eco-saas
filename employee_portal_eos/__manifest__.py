# See LICENSE file for full copyright and licensing details.

{
    'name': 'Eco: HR EOS Portal',
    'version': '18.0',
    'summary': 'Add resignation in portal.',
    'author': 'Omnya Rashwan',
    'description': """Add resignation in portal.""",
    'depends': ['base', 'hr', 'portal', 'custom_portal_account_page', 'hr_eos'],
    'data': [
        'views/resignation_web_template.xml',
    ],
    "assets": {
        "web.assets_frontend": [
            "employee_portal_eos/static/src/js/reg_portal.js",
        ]
    },
    'installable': True,
    'auto_install': False,
    'application': False,
}
