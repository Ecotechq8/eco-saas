
{
    'name': 'UnitSoft NavBar Branding Logo',
    'summary': 'Odoo Community NavBar Branding Logo',
    'version': '18.0.0.0.1',
    'category': 'Themes/Backend',
    'license': 'LGPL-3',
    'author': 'UnitSoft',
    'website': 'https://www.unitsoft.io',
    'description': """
        Odoo Community NavBar Branding Logo.
    """,
    'contributors': [
        'Suport <support@unitsoft.io>',
        ],
    'data': [
        ],
    'depends': [
        'eco_theme',
        ],
    'assets': {
        'web.assets_backend': [
            'us_navbar_branding_logo/static/src/webclient/navbar/navbar.xml',
        ],
    'images': [
        'static/images/description_screenshot.jpg',
        'static/description/banner.png',
        ], 
    },

    'installable': True,
    'application': False,
    'auto_install': False,
}
