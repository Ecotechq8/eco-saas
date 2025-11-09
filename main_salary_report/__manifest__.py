{
    'name': 'Eco: Main Salary Report',
    'version': '18.0',
    'author': "Eco-Tech, Omnya Rashwan",
    'depends': ['base', 'hr', 'report_xlsx', 'hr_payroll'],
    'data': [
        'security/ir.model.access.csv',
        'reports/salary_report.xml',
        'wizard/salary_report_wiz_view.xml',
        'views/hr_payroll_structure_view.xml',
    ],
    'application': True,
    'installable': True,
}
