# -*- coding: utf-8 -*-
{
    'name': "Eco: Leaves Printouts",
    'summary': "Add some printouts in leaves",
    'description': """Add some printouts in leaves""",
    'author': "Eco-Tech, Omnya Rashwan",
    'website': "https://ecotech.com",
    'category': 'Human Resources',
    'version': '17.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr_holidays', 'eco_contract_enhancement'],

    # always loaded
    'data': [
        'reports/sick_leave_form_report.xml',
        'reports/business_training_trip_report.xml',
        'reports/leave_entitlement_payment_report.xml'
    ],
}
