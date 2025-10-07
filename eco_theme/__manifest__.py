{
    'name': 'EcoTech-Theme',
    'summary': 'Odoo Community Backend Theme',
    'description': '''
        This module offers a mobile compatible design for Odoo Community. 
        Furthermore it allows the user to define some design preferences.
    ''',
    'version': '18.0.1.2.4',
    'category': 'Themes/Backend',
    'license': 'LGPL-3',
    'author': 'Ezzat Mohsen (EcoTech.co)',
    'website': 'http://www.mukit.at',
    'live_test_url': 'https://my.mukit.at/r/f6m',
    'contributors': [
        'Mathias Markl <mathias.markl@mukit.at>',
    ],
    'depends': [
        'base',
        'mail',
        'muk_web_chatter',
        'muk_web_dialog',
        'muk_web_appsbar',
        'muk_web_colors',
        'web',
        'crm',
        'stock',
        'web_tour',
        'auth_signup'

    ],
    'excludes': [
        'web_enterprise',
    ],
    'data': [
        'security/ir.model.access.csv',
        'templates/web_layout.xml',
        'views/res_config_settings.xml',
        'views/remove_odoo_templates.xml',
        # 'wizard/wizard.xml',
    ],
    'assets': {
        'web._assets_primary_variables': [
            (
                'after',
                'web/static/src/scss/primary_variables.scss',
                'eco_theme/static/src/scss/colors.scss'
            ),
            (
                'after',
                'web/static/src/scss/primary_variables.scss',
                'eco_theme/static/src/scss/variables.scss'
            ),
        ],
        'web.assets_backend': [
            'eco_theme/static/src/webclient/**/*.xml',
            'eco_theme/static/src/webclient/**/*.scss',
            'eco_theme/static/src/webclient/**/*.js',
            'eco_theme/static/src/views/**/*.scss',
        ],
    },
    'images': [
        'static/description/banner.png',
        'static/description/theme_screenshot.png'
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'post_init_hook': '_setup_module',
    'uninstall_hook': '_uninstall_cleanup',
}
