# -*- coding: utf-8 -*-
{
    'name': "Entrivis POS Auto Close Session",

    'summary': "Auto-close POS sessions after a configurable runtime, plus Foodics OAuth settings.",

    'description': """
Entrivis POS Auto Close Session
================================
* Cron that auto-closes any opened POS session whose runtime exceeds the
  configured number of hours.
* Settings page (Foodics tab) exposing the Foodics OAuth credentials:
  redirect URI, client ID, client secret.
* POS frontend guard that blocks payment if the active session has been
  closed server-side.
""",

    'author': "Entrivis Tech. Pvt. Ltd.",
    'website': "https://www.entrivistech.com",

    'category': 'Point of Sale',
    'version': '18.0.1.0.0',

    'depends': ['base', 'point_of_sale', 'entrivis_foodics_base'],

    # always loaded
    'data': [
        'data/pos_auto_close_cron.xml',
        'views/res_config_settings.xml',
    ],
    'assets': {
        'point_of_sale.assets_frontend': [
            'entrivis_pos_auto_close_session/static/src/js/*.js',
        ]
    },
    'license': 'LGPL-3',
}
