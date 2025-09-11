{
    'name': 'HR Custom Reports',
    'version': '18.0.0.0',
    'category': 'Human Resources',
    'summary': 'HR Custom Reports ',
    'description': 'HR Custom Reports ',
    'depends': ['base', 'hr', 'om_hr_payroll'],
    'author': "Eco-Tech, Zaynab Ibrahim",
    'website': "https://ecotech.com",
    'data': [
        'security/ir.model.access.csv',

        'reports/employee_attendance_report_template.xml',
        'reports/employee_attendance_report_action.xml',

        'reports/employee_absent_report_template.xml',
        'reports/employee_absent_report_action.xml',

        'reports/employee_monthly_attendance_report_template.xml',
        'reports/employee_monthly_attendance_report_action.xml',

        'wizard/eco_employee_attendance_views.xml',

        'views/menus.xml',
        'views/hr_payroll.xml',

    ],
}
