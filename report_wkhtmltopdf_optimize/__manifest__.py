# -*- coding: utf-8 -*-
{
    'name': 'Report Wkhtmltopdf Optimize',
    'summary': 'Optimize PDF rendering performance on resource-limited servers by splitting large print jobs (like Payslips) into batches and merging them in memory.',
    'version': '18.0.1.0.0',
    'category': 'Technical',
    'author': 'Ahmed Emara',
    'depends': ['base'],
    'data': [
        'views/ir_actions_report_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
