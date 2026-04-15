# -*- coding: utf-8 -*-

{
    'name': "Project Assignment to Employees",
    'version': '18.0.1.0.0',
    'author': 'ECO',
    'category': 'Project',
    'summary': 'Assign projects to employees',
    'depends': [
        'hr',
        'project',
        'hr_attendance',
    ],
    'data': [
        'views/hr_employee_views.xml',
        'views/hr_attendance_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
