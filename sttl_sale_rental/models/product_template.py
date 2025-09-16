from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = "product.template"

    is_rent = fields.Boolean(string="Can be Rented")
    rental_price_ids = fields.One2many("rental.price", "product_template_id", string="Rental Prices")
    rental_count = fields.Float(string="Rental Count", compute="_compute_rental_count")

    def action_view_rentals(self):
        self.ensure_one()
        ptl_id = self.id
        domain = [('is_rental_line', '=', True), ('product_template_id', '=', ptl_id)]
        return {
            'type': 'ir.actions.act_window',
            'name': 'Rental Product Timeline',
            'view_mode': 'timeline',
            'view_id': self.env.ref('sttl_sale_rental.sol_rental_timeline_action').id,
            'res_model': 'sale.order.line',
            'context': "{'create': False}",
            'domain': domain
        }

    def _compute_rental_count(self):
        for rec in self:
            if rec.is_rent:
                rented_product = self.env["sale.order.line"].search([('is_rental_line', '=', True), ('product_template_id', '=', rec.id)])
                delivered_count = sum(rented_product.mapped('qty_delivered'))
                returned_count = sum(rented_product.mapped('qty_returned'))
                rec.rental_count = delivered_count - returned_count
            else:
                rec.rental_count = 0.0

    @api.onchange('tracking')
    def _onchange_tracking(self):
        if self.tracking == 'lot':
            raise ValidationError(_("Tracking with Lots is not available for rental products."))


class RentalPrice(models.Model):
    _name = "rental.price"
    _description = "Rental Price"

    unit_type = fields.Selection([
        ('hour', 'Hourly'),
        ('day', 'Daily'),
        ('week', 'Weekly'),
        ('month', 'Monthly')
    ], string="Unit Duration", readonly=False, store=True)
    price = fields.Monetary(string="Price")
    currency_id = fields.Many2one(
        'res.currency', 'Currency',
        default=lambda self: self.env.company.currency_id.id,
        required=True)
    product_template_id = fields.Many2one("product.template", string="Product")


class ProductProduct(models.Model):
    _inherit = "product.product"

    def action_view_rentals(self):
        self.ensure_one()
        domain = [('is_rental_line', '=', True), ('product_id', '=', self.id)]
        return {
            'type': 'ir.actions.act_window',
            'name': 'Rental Product Timeline',
            'view_mode': 'timeline',
            'view_id': self.env.ref('sttl_sale_rental.sol_rental_timeline_action').id,
            'res_model': 'sale.order.line',
            'context': "{'create': False, 'edit': False}",
            'domain': domain
        }

    @api.onchange('tracking')
    def _onchange_tracking(self):
        if self.tracking == 'lot':
            raise ValidationError(_("Tracking with Lots is not available for rental products."))
