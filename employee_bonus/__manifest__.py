# -*- coding: utf-8 -*-
{
    "name": "Employee Bonus",
    "version": "18.0.0.0",
    'category': 'Human Resources',
    'summary': '',
    "description": """""",
    "author": "Eco-Tech, Omnya Rashwan",
    "depends": ['hr', 'om_hr_payroll_account', 'eco_contract_enhancement', 'rm_hr_attendance_sheet'],
    "data": [
        'security/ir.model.access.csv',
        'data/data.xml',
        'views/bonus_type_view.xml',
        'views/employee_bonus_view.xml',
        'views/input_type.xml'
    ],
    "auto_install": False,
    "installable": True,
}
