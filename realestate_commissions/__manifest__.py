# -*- coding: utf-8 -*-
{
    'name': "Real Estate Sales Commissions",
    "version": "0.1",
    'category': 'Accounting',
    'summary': """ Sales Commissions """,
    "description": """
        This Module is used for Sales Commissions
    """,
    "author": "EcoTech by Khadrawy",
    "depends": ['eco_real_estate',],
    "data": [
        "security/sales_commission_groups.xml",
        "security/ir.model.access.csv",
        "views/commission_sales_views.xml",
        "views/commission_range_views.xml",
        "views/product_template_views.xml",
    ],
    "auto_install": False,
    "installable": True,
}
