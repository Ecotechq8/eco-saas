# -*- coding: utf-8 -*-
{
    'name': "EOS History Report",
    'summary': "EOS History Report",
    'description': """EOS History Report""",
    'author': "Omar Amr, Eco-tech",
    'website': "https://ecotech.com",
    'category': 'Human Resources',
    'version': '18.0',
    # any module necessary for this one to work correctly
    'depends': ['hr_eos', 'eco_contract_enhancement', "hr_customization", 'report_xlsx'],

    'data': [
        'security/ir.model.access.csv',
        'reports/eos_history.xml',
        'actions/cron.xml',
        'views/balance_history.xml',
        'views/hr_contract.xml',
        'wizard/config_settings.xml',
        'views/hr_resignation_request.xml',
        'views/hr_termination_request.xml',
    ],
}
