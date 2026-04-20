# -*- coding: utf-8 -*-

{
    'name': 'Printouts & Reports Settings',
    'version': '18.0.1.0.0',
    'author': 'VERTS Services India Pvt. Ltd.',
    'category': 'Reporting',
    'depends': ['base'],
    'website': 'https://www.verts.co.in/',
    'description': '''Printout & Reports related configurations such as Logos, Border Colors, Font Colors etc.
''',
    'summary': 'Prinouts & Reports Related Configurations',
    'data': [
        ##'views/web_widget_color_view.xml',
        # 'views/res_company_view.xml',
    ],
    'images': [],
    'installable': True,
    'auto_install': False,
    'assets': {
        'web.assets_backend': [
            'verts_v15_print_template/static/src/js/**/*',
        ],
        'web.qweb_suite_reports': [
            'verts_v15_print_template/static/src/xml/widget_color.xml',
        ],
    },
    'license': 'LGPL-3',
}
