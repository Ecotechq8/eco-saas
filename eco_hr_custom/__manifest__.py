{
    'name': 'HR Custom ',
    'version': '18.0.0.0',
    'category': 'Human Resources',
    'summary': 'HR Custom  ',
    'description': 'HR Custom ',
    'depends': ['base', 'hr','hr_enhancement','hr_contract'],
    'author': "Eco-Tech, Zaynab Ibrahim",
    'website': "https://ecotech.com",
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',

        'views/hr_employee_views.xml',
        'views/hr_department.xml',
        'views/hr_contract.xml'

    ],
}
