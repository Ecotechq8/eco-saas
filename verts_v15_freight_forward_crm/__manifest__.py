 # -*- coding: utf-8 -*-
# Copyright 2021 Verts Services India Pvt Ltd.
# http://www.verts.co.in

{
    "name": "verts_v15_freight_forward_crm",
    "version": "18.0.1.0.0",
    "author": "VERTS Services India Pvt. Ltd.",
    "description": """This module adds the features of finance localization related to India""",
    "website": "http://www.verts.co.in",
    "depends": ['crm', 'uom', 'verts_v15_freight_forward'],
    "category": "Generic Modules",
    "init_xml": [],
    "demo_xml": [],
    "data": [
        'security/ir.model.access.csv',
        "views/sequence.xml",
        "wizard/bulk_entry_wizard_view.xml",
        "wizard/sales_report.xml",
        "wizard/air_import_cargo_sales_report.xml",
        "wizard/cargo_sea_freight_report.xml",
        'data/data_view.xml',
        'views/config_view.xml',
        'views/crm_lead_view.xml',
        'views/menu.xml',
        'reports/price_request_report.xml',
        'views/mail_template_data.xml'
    ],
    'test': [],
    'installable': True,
    'application': True,
    'active': False,
    'certificate': '',
}
