# -*- coding: utf-8 -*-
{
    "name": "Contract Enhancement",
    "version": "0.1",
    'category': 'Human Resources',
    'summary': '',
    "description": """ Add some fields on contract form view """,
    "author": "Eco-Tech, Omnya Rashwan",
    "depends": ['hr_contract'],
    "data": [
        'security/ir.model.access.csv',
        'views/hr_contract_inh_view.xml',
        'views/insurance_company_view.xml',
    ],
    "auto_install": False,
    "installable": True,
}
