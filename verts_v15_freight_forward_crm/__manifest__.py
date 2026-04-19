 # -*- coding: utf-8 -*-
# Copyright 2021 Verts Services India Pvt Ltd.
# http://www.verts.co.in

{
    "name": "verts_v15_freight_forward_crm",
    "version": "18.0.1.0.0",
    "author": "VERTS Services India Pvt. Ltd.",
    "description": """This module adds the features of finance localization related to India""",
    "website": "http://www.verts.co.in",
    "license": "LGPL-3",
    "depends": ['crm', 'uom', 'verts_v15_freight_forward'],
    "category": "Generic Modules",
    "data": [
        'security/ir.model.access.csv',
        "wizard/bulk_entry_wizard_view.xml",
        'views/crm_lead_view.xml',
        'reports/price_request_report.xml',
        'views/mail_template_data.xml'
    ],
    'installable': True,
    'application': True,
}
