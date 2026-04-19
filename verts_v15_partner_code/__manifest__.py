# -*- coding: utf-8 -*-
# Copyright 2020 Verts Services India Pvt Ltd.
# http://www.verts.co.in

{
    'name': "Verts - Partner Code",
    'summary': """Partner Code""",
    'description': """
       Partner Code
    """,
    'author': "Verts Technologies",
    'website': "http://www.verts.co.in",
    'category': 'Sales/CRM',
    'version': '18.0.1.0.0',
    'depends': ['base', 'project'],
    # always loaded
    'data': [
        # 'security/security.xml',
        'security/ir.model.access.csv',
        'views/partner_code_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}
