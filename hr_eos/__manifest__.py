# See LICENSE file for full copyright and licensing details.

{
    'name': 'Eco : HR EOS',
    'version': '0.1',
    'summary': 'Add resignation and termination and its rules.',
    'author': 'Omnya Rashwan',
    'description': """Add resignation and termination and its rules.""",
    'depends': ['base', 'hr_contract', 'hr', 'hr_holidays', 'ejabi_contract_enhancement'],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_config_rules_view.xml',
        'views/hr_termination_request.xml',
        'views/hr_resignation_request.xml',
        'views/hr_leave_type_inherit.xml',
        'views/hr_employee_inherit.xml',
        'views/end_of_service_recognition.xml',
        'views/res_config_setting.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
