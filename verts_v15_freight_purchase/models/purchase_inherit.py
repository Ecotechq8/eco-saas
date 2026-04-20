# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    req_quot_id = fields.Many2one('request.for.quotation', string='Request for Quotation')
    req_quot_line_id = fields.Many2one('request.for.quotation.line', string='RFQ Line')
    internal_product_type = fields.Selection([
        ('fg', 'FG'), ('rm', 'RM'), ('consu', 'Consumables'),
        ('service', 'Service'), ('semi_fg_wip', 'Semi FG/WIP'),
        ('gi', 'General Items'), ('fa', 'Fixed Assets'), ('mix', 'Mix')
    ], string='Internal Product Type')
    origin_type = fields.Char(string='Origin Type')
    type_of_po = fields.Selection([('VQ', 'Vendor Quote'), ('PO', 'Purchase Order')], string='Type of PO')
    readonly_qty = fields.Boolean(string='Readonly Quantity', default=False)
