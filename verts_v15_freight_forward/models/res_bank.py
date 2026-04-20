from odoo import models, fields

class ResBank(models.Model):
    _inherit = 'res.bank'

    iban = fields.Char(string='IBAN')
