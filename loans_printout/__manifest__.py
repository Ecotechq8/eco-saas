# -*- coding: utf-8 -*-
{
    'name': "Eco: Loans Printout",
    'summary': "Add loan printout",
    'description': """Add loan printout""",
    'author': "Eco-Tech, Omnya Rashwan",
    'website': "https://ecotech.com",
    'category': 'Human Resources',
    'version': '18.0',

    # any module necessary for this one to work correctly
    'depends': ['hr', 'dev_hr_loan'],

    # always loaded
    'data': [
        'reports/loan_request_report.xml',
    ],
}
