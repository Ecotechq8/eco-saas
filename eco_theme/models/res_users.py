from odoo import api, models, fields
from markupsafe import Markup

from odoo.modules import get_resource_path
from odoo.tools import _


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

                icon_path = get_resource_path(
                eco_module,
                'static', 'src', 'img', 'icons',f'{original_module}.png'
            )
                print(f"Checking icon path: {icon_path}")
                if icon_path:
                    icon = f'/{eco_module}/static/src/img/icons/{original_module}.png'
                    activity['icon'] = icon
                return activities
        return activities

       