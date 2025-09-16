{
    "name": "Construction  Management ",
    "version": '0.1',
    "category": "Construction",
    "sequence": 20,
    "summary": """
        This module allows you to manage the Construction projects
    """,
    "description": """ 
        This module allows you to manage the Construction projects .
    """,
    "author": "Ahmed Elkhadrawy",
    "depends": ['base', 'project', 'crm','sale_crm','check_management','sale'],
    "license": "OPL-1",
    "data": [
        'security/ir.model.access.csv',
        'security/construction_groups.xml',
        "wizard/create_po_view.xml",
        "wizard/so_payment_view.xml",
        "report/report_contracting_business.xml",
        "views/crm_lead_view.xml",
        "views/request_quoation_view.xml",
        "views/project_views.xml",
        "views/sale_order_views.xml",
        "views/purchase_order_views.xml",
        "views/account.move.xml",
        "views/res_config_settings_views.xml",
        "views/res_partner_views.xml",
        "views/guarantee_letter_views.xml",


    ],

    "installable": True,
    "auto_install": False,
    "application": True,

}
