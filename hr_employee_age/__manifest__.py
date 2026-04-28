# -*- coding: utf-8 -*-
{
    'name': 'HR Employee Age',
    'version': '18.0',
    'summary': "Automatically calculates and displays the employee's age.",
    'description': """
        This module extends the Human Resources application to add a new 'Age' field.
        The age is computed automatically based on the employee's date of birth.
    """,
    'category': 'Human Resources/Employees',
    'author': 'ahmed emara',
    'depends': [
        'hr',
    ],
    'data': [
        'views/hr_employee_view.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}