# guarantee_letter/models/guarantee_letter.py
from odoo import models, fields, api
import odoo.addons.decimal_precision as dp

class GuaranteeLetterTransaction(models.Model):
    _name = 'guarantee.letter.transaction'

    letter_id = fields.Many2one('guarantee.letter',string='Letter_id', required=False)
    product_id = fields.Many2one('product.product', string='Product',
                                 change_default=True, ondelete='restrict', required=False)
    price_unit = fields.Float(string='Unit Price ', readonly=False,)
    date = fields.Date(string='Date', default=fields.Date.today())
    account_id = fields.Many2one('account.account',string='Account',related='product_id.property_account_expense_id')

    name = fields.Text(
        string="Description",
        compute='_compute_name',
        store=True, readonly=False, required=True, precompute=True)
    project_id = fields.Many2one('project.project', string='Project', related='letter_id.project_id')
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account',related='letter_id.project_id.analytic_account_id')
    taxes_ids = fields.Many2many('account.tax', string='Taxes')
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure', )
    product_uom_qty = fields.Float(string='Quantity', digits=dp.get_precision('Product Unit of Measure'), required=True,
                                   default=1.0)
    subtotal = fields.Float(string='Subtotal', compute='_compute_subtotal',store=True)


    @api.depends('product_id')
    def _compute_name(self):
        for line in self:
            if not line.product_id:
                continue
            name = line.product_id.get_product_multiline_description_sale()
            line.name = name

    @api.depends('product_uom_qty','price_unit')
    def _compute_subtotal(self):
        for line in self:
          line.subtotal = 0.0
          line.subtotal = line.product_uom_qty * line.price_unit
