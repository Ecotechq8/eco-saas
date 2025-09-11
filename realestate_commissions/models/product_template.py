from odoo import fields, models, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_commission_product = fields.Boolean(
        string=' is_commission_product',
        required=False)
