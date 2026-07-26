# -*- coding: utf-8 -*-
# Copyright 2021 Verts Services India Pvt Ltd.
# http://www.verts.co.in

{
    "name": "verts_v15_freight_purchase",
    "version": "18.0.1.0.0",
    "author": "VERTS Services India Pvt. Ltd.",
    "description": """This module adds the features of finance localization related to India""",
    "website": "http://www.verts.co.in",
    "depends": ['purchase', 'verts_v15_freight_forward'],
    "category": "Generic Modules",
    "init_xml": [],
    "demo_xml": [],
    "data": [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/sequence.xml',
        'views/quote_comparision.xml',
        'views/purchase_views.xml',
        'wizards/wiz_change_pol_qty.xml',
        'views/request_for_quotation.xml',
        'views/res_company_view.xml',
        'wizards/purchase_config_wiz_view.xml'
    ],
    'test': [],
    'installable': True,
    'active': False,
    'certificate': '',
}
