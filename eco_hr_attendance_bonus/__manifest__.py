{
    'name': 'HR Attendance Bonus',
    'version': '18.0.0.0',
    'category': 'Human Resources',
    'summary': 'HR Attendance Bonus ',
    'description': 'HR Attendance Bonus ',
    'depends': ['base', 'hr_attendance','om_hr_payroll', 'rm_hr_attendance_sheet'],
    'author': "Eco-Tech, Zaynab Ibrahim",
    'website': "https://ecotech.com",
    'data': [
        'security/ir.model.access.csv',

        'views/eco_hr_attendance_bonus.xml',
        'views/menus.xml',

    ],
}
