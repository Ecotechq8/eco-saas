from odoo import models, fields

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_commission_applicable = fields.Boolean(string='Is Commission Applicable')

class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    commission_loaded = fields.Boolean(string="Commission Loaded", default=False, copy=False)
