# -*- coding: utf-8 -*-

{
    'name': 'Employee Religion Field',
    'version': '18.0',
    'summary': """Employee Religion Field""",
    'description': """This module adds a religion field to the employee form.""",
    'category': 'Human Resources/Employees',
    'author': 'ahmed emara',
    'license': 'AGPL-3',

    'depends': ['hr'],

    'data': [
        'data/religions.xml',
        'security/ir.model.access.csv',
        'views/hr_religion_view.xml',
        'views/res_employee.xml',
    ],

    'images': ['static/description/banner.gif'],

    'installable': True,
    'auto_install': False,
    'application': True,
}