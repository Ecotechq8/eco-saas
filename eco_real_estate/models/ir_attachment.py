from odoo import _, api, fields, models, tools


class ir_attachment(models.Model):
    _inherit = 'ir.attachment'

    property_pay_id = fields.Many2one('property.reservation', ' property payment ')
    property_legal_id = fields.Many2one('property.reservation', ' property legal ')
    payment_attach_type = fields.Selection(
        string='Payment Attachment Type',
        selection=[('deposit', 'Deposit'),
                   ('checks', 'Checks'),
                   ('signature', 'Signature'),
                   ('cancel', 'Cancellation'),

                   ],
        required=False, )
    property_legal_type = fields.Many2one(
        comodel_name='property.legal.type',
        string='Legal Type',
        required=False)
        
class property_legal_type(models.Model):

    _name= 'property.legal.type'
    name = fields.Char(string='Name', required=True)