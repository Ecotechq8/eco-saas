from . import models
import base64
# from . import wizard
from odoo.tools import file_open


def _setup_module(env):
    if env.ref('base.main_company', False): 
        with file_open('web/static/img/favicon.ico', 'rb') as file:
            env.ref('base.main_company').write({
                'favicon': base64.b64encode(file.read())
            })
        with file_open('eco_theme/static/src/img/background.png', 'rb') as file:
            env.ref('base.main_company').write({
                'background_image': base64.b64encode(file.read())
            })
    bot_user = env.ref('base.user_root', raise_if_not_found=False)
    if bot_user:
        bot_user.sudo().write({'name': 'EcoPro Assistant'})

def _uninstall_cleanup(env):
    env['res.config.settings']._reset_theme_color_assets()
