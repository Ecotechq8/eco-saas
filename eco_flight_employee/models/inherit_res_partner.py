from odoo import fields, models, api


class ResPartner(models.Model):
    _inherit = 'res.partner'
    is_flight_agent = fields.Boolean(
        string='Flight Agent',
        required=False
    )
