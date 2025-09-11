{
    'name': 'HR Operations',
    'version': '18.0.0.0',
    'category': 'Human Resources',
    'summary': 'Manage HR Operations and Types',
    'description': 'A module to manage operation types and HR operations.',
    'depends': ['base', 'hr_contract'],
    'author': "Eco-Tech, Omar Amr",
    'website': "https://ecotech.com",
    'data': [
        'security/ir.model.access.csv',
        'views/hr_operation_type.xml',
        'views/hr_operation.xml',
    ],
}
