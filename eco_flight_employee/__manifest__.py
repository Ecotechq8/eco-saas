# -*- coding: utf-8 -*-
{
    'name': "Air Ticket",
    'summary': "Air Flight Reservation",
    'description': """
        Air Flight Ticket
    """,
    'author': "Ezzat Mohsen (EchoTech inc",
    'website': "https://www.EcoTech.com",
    'category': 'Reservation',
    'version': '0.1',
    'depends': ['base',
                'hr_contract',
                'hr',
                'base',
                'account',
                'mail',
                'portal',
                'website'
                ],
    'data': [
        'data/flight_ticket_sequence.xml',
        'security/ir.model.access.csv',
        'views/inherit_hr_contract.xml',
        'views/air_ticket_line.xml',
        'views/flight_ticket_request.xml',
        'views/res_config.xml',
        'views/inherit_res_partner.xml',
        'views/flight_ticket_portal_templates.xml',
        'views/menus.xml'

    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
