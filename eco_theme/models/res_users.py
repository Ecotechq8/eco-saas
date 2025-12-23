from odoo import api, models
from markupsafe import Markup

from odoo.tools.misc import file_path
from odoo.tools import _
import logging


_logger = logging.getLogger(__name__)

class Users(models.Model):
    _inherit = 'res.users'

    def _init_odoobot(self):
        self.ensure_one()

        odoobot_id = self.env['ir.model.data']._xmlid_to_res_id("base.partner_root")
        channel = self.env['discuss.channel'].channel_get(
            [odoobot_id, self.partner_id.id]
        )

        message = Markup(
            "%s<br/>%s<br/><b>%s</b> <span class=\"o_odoobot_command\">:)</span>"
        ) % (
            _("Hello,"),
            _("Eco Pro's chat helps employees collaborate efficiently. I'm here to help you discover its features."),
            _("Try to send me an emoji"),
        )

        channel.sudo().message_post(
            author_id=odoobot_id,
            body=message,
            message_type="comment",
            silent=True,
            subtype_xmlid="mail.mt_comment",
        )

        self.sudo().odoobot_state = 'onboarding_emoji'
        return channel
    

    @api.model
    def _get_activity_groups(self):
        activities = super()._get_activity_groups()
        for activity in activities:
            module_name = activity.get('model','')
            Model = self.env[module_name]
            original_module = Model._original_module
            eco_modules = ['eco_theme','eco_advanced']
            for eco_module in eco_modules:
                icon_file = f'{eco_module}/static/src/img/icons/{original_module}.png'
                try:
                    path_exist = file_path(icon_file)
                except Exception:
                    path_exist = False
                icon_path = "/"+icon_file
                _logger.info(f"Checking icon path: {path_exist}")
                if path_exist:
                    activity['icon'] = icon_path
        return activities

       