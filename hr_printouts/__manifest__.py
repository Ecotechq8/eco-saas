# -*- coding: utf-8 -*-
{
    'name': "Eco: HR Printouts",
    'summary': "Add some printouts",
    'description': """Add some printouts""",
    'author': "Eco-Tech, Omnya Rashwan",
    'website': "https://ecotech.com",
    'category': 'Human Resources',
    'version': '18.0',

    # any module necessary for this one to work correctly
    'depends': ['hr', 'eco_hr_operation'],

    # always loaded
    'data': [
        'reports/experience_certificate_report.xml',
        'reports/salary_details_certificate_report.xml',
        'reports/salary_certificate_report.xml',
        'reports/proceed_working_report.xml',
        'reports/final_release_report.xml',
        'reports/passport_request_report.xml',
        'reports/proceed_working_leave_report.xml',
        'reports/internal_investigation_report.xml',
        'reports/salary_continuity_certificate_report.xml'
    ],
}
