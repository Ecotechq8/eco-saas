# -*- coding: utf-8 -*-
{
    'name': "Integrate Check Management with Real Estate",
    "version": "0.1",
    'category': 'Accounting',
    'summary': """ Check Management  """,
    "description": """
        This Module is used for check \n
        It includes creation of check receipt ,check cycle ,Holding ....... \n
    """,
    "author": "EcoTech by Khadrawy",
    "depends": ['check_management',
                'eco_real_estate',
                ],
    "data": [
        "views/normal_payments_views.xml",
        "views/property_reservation_views.xml"
    ],
    "auto_install": False,
    "installable": True,
}
