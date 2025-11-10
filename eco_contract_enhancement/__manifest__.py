# -*- coding: utf-8 -*-
{
    "name": "Eco: Contract Enhancement",
    "version": "18.0.0.0",
    'category': 'Human Resources',
    'summary': '',
    "description": """ Add some fields on contract form view.""",
    "author": "Eco-Tech, Omnya Rashwan",
    "depends": ['om_hr_contract'],
    "data": [
        'security/ir.model.access.csv',
        'views/hr_contract_inh_view.xml',
        'views/insurance_company_view.xml',
    ],
    "auto_install": False,
    "installable": True,
}
