{
    'name': 'EcoTech-Advanced',
    'summary': 'Eco Advanced Modules',
    'description': '''
        Advanced modules bundle for eco tech saas
    ''',
    'version': '18.0.1.2.4',
    'category': 'Themes/Backend',
    'license': 'LGPL-3',
    'author': 'Ahmed Ismail (EcoTech.co)',

    'depends': [
        'eco_theme',
    ],
    'excludes': [
        'web_enterprise',
    ],
    'data': [
        'views/menu_overrides.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
