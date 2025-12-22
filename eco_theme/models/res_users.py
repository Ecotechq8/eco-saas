from odoo import models, fields
from markupsafe import Markup

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
        