from odoo import models, fields
from markupsafe import Markup


class Users(models.Model):
    _inherit = 'res.users'

    def _init_odoobot(self):
        message = Markup("%s<br/>%s<br/><b>%s</b> <span class=\"o_odoobot_command\">:)</span>") % (
            _("Hello,"),
            _("Eco Pro's chat helps employees collaborate efficiently. I'm here to help you discover its features."),
            _("Try to send me an emoji")
        )
        channel = super()._init_odoobot()
        channel.message = message
        return channel
        