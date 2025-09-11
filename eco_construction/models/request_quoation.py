from odoo import fields, models, api

import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError, RedirectWarning, ValidationError


class RequestQuotation(models.Model):
    _name = 'request.quotation'
    _description = 'Request Lines CRM'
    _order = 'lead_id, id'

    lead_id = fields.Many2one('crm.lead', string='Opportunity')
    project_id = fields.Many2one('project.project', string='Project')
    sequence = fields.Integer(string='Sequence', default=10)
    product_id = fields.Many2one('product.product', string='Product', domain=[('sale_ok', '=', True)],
                                 change_default=True, ondelete='restrict', required=False)
    product_uom_qty = fields.Float(string='Quantity', digits=dp.get_precision('Product Unit of Measure'), required=True,
                                   default=1.0)
    # product_uom = fields.Many2one('product.uom', string='Unit of Measure', required=True)
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure', )
    qty_onhand = fields.Float(string="Quantity on Hand")
    custom_order_line_id = fields.Many2one('sale.order.line', string="Sale Order Line", copy=False, )
    custom_order_id = fields.Many2one('sale.order', string="Sale Order", copy=False,
                                      related='custom_order_line_id.order_id')
    price_unit = fields.Float(string='Price Unit', readonly=False, required=True)
    cost = fields.Float(string='Cost', store=True, readonly=True, precompute=True,
                        compute='_get_last_price')

    display_type = fields.Selection(
        selection=[
            ('line_section', "Section"),
            ('line_note', "Note"),
        ],
        default=False)
    name = fields.Text(
        string="Description",
        compute='_compute_name',
        store=True, readonly=False, required=True, precompute=True)

    #    @api.multi #odoo13
    @api.onchange('product_id')
    def product_id_change(self):
        for rec in self:
            rec.product_uom = rec.product_id.uom_id.id
            if rec.product_id:
                rr = rec.product_id._compute_quantities_dict(lot_id=False, owner_id=False, package_id=False)
                rec.qty_onhand = rr[rec.product_id.id]['qty_available']

    @api.depends('product_id')
    def _get_last_price(self):
        for rec in self:
            if not rec.product_id.seller_ids:
                rec.cost = rec.product_id.lst_price
            else:
                rec.cost = rec.product_id.seller_ids.mapped('price')[-1]

    @api.depends('product_id')
    def _compute_name(self):
        for line in self:
            if not line.product_id:
                continue
            name = line.product_id.get_product_multiline_description_sale()
            line.name = name
