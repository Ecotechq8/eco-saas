{
    "name": "Real estate | Property management | Sale and Rental Contract management",
    "version": '0.1',
    "category": "Real Estate",
    "sequence": 20,
    "summary": """
        This module allows you to manage the real estate project, sell and rental property contracts, and calculate broker commission and many more.
        Advanced Property Sale & Rental Management | Property Sales | Property Rental 
    """,
    "description": """ 
        This module allows you to manage the real estate project, sell and rental property contracts, and calculate broker commission and many more.
        Advanced Property Sale & Rental Management | Property Sales | Property Rental 
    """,
    "author": "Ahmed Elkhadrawy",
    "depends": ['base', 'project', 'sale_project', 'account'],
    "license": "OPL-1",
    "data": [
        "data/ir_sequence.xml",
        "wizard/reservation_cancel_reason_view.xml",
        'security/ir.model.access.csv',
        "views/res_partner_views.xml",
        "views/project_views.xml",
        "views/view_property.xml",
        "views/property_reservation_views.xml",
        "views/account_payment_views.xml",
        "views/configuration_views.xml",
        "views/installment_line_views.xml",
        "views/account_payment_term.xml",
        "views/sale_order_views.xml",
        "views/menu_items.xml",
        "report/payment_reservation_report.xml",
        "report/reservation_form_printout.xml",
    ],

    "installable": True,
    "auto_install": False,
    "application": True,

}
