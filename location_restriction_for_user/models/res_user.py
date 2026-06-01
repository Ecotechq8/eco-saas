from odoo import fields, api, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    allow_location_ids = fields.Many2many('stock.location')

