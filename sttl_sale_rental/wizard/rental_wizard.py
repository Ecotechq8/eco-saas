from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class RentalPickupWizard(models.TransientModel):
    _name = "rental.wizard"
    _description = "Rental Wizard"

    rental_line_ids = fields.One2many('rental.line', 'rental_wizard_id', string="Rental line ids")

    def pickup_validate(self):
        pickable_lines = self.rental_line_ids.filtered(lambda l: l.order_line_id.pickup_date < datetime.now())
        if pickable_lines:
            for rec in pickable_lines:
                if rec.order_line_id.product_id.type == 'product' and rec.order_line_id.product_id.qty_available <= 0:
                    raise ValidationError(_("There is no quantity available for renting."))
                elif not rec.order_line_id.pickup_date and not rec.order_line_id.return_date:
                    raise ValidationError(
                        _("Pickup and Return Dates for the renting period of a product must be selected."))
                elif not rec.order_line_id.pickup_date and rec.order_line_id.return_date:
                    raise ValidationError(_("Return Date for the renting period of a product must be selected."))
                elif rec.order_line_id.pickup_date and not rec.order_line_id.return_date:
                    raise ValidationError(_("Pickup Date for the renting period of a product must be selected."))
                else:
                    line = rec.order_line_id
                    if rec.qty_reserved < rec.qty_delivered:
                        raise ValidationError(_("Delivered Quantity cannot be more than Reserved Quantity."))
                    else:
                        line.lot_ids += rec.lot_ids
                        if rec.qty_delivered < 0.0:
                            rec.qty_delivered = 0.0
                        line.qty_delivered += rec.qty_delivered
                        vals = {
                            'date': line.pickup_date,
                            'origin': line.order_id.name,
                            'product_id': line.product_id.id,
                            'product_uom': line.product_uom.id,
                            'location_id': line.order_id.warehouse_id.lot_stock_id.id,
                            'location_dest_id': self.env.ref('stock.stock_location_customers').id,
                            'state': 'done',
                            'name': "Rental Product Delivered",
                            'company_id': self.env.context.get('allowed_company_ids')[0],
                            'lot_ids': rec.lot_ids,
                        }
                        move = self.env["stock.move"].create(vals)
                        if line.product_template_id.tracking == 'none':
                            move._set_quantity_done(rec.qty_delivered)
                            move._action_assign()
                            move._action_done()
                    if line.qty_delivered == line.product_uom_qty:
                        line.is_picked_up = True
                    else:
                        line.is_picked_up = False
                    rec.order_line_id.order_id.is_partial_return_boolean = True
                    rec.order_line_id.order_id.calculate_rental_state()
                    rec.order_line_id.order_id.calculate_next_pickup_return()
        else:
            raise ValidationError(_("You cannot pickup the product on "
                                    "an earlier date than previously decided pickup date."))

    def return_validate(self):
        returnable_lines = self.rental_line_ids.filtered(lambda l: l.order_line_id.return_date < datetime.now())
        if returnable_lines:
            for rec in returnable_lines:
                line = rec.order_line_id
                if rec.qty_to_return < rec.qty_returned:
                    raise ValidationError(_("Returned Quantity cannot be more than Delivered Quantity."))
                else:
                    if rec.qty_returned < 0.0:
                        rec.qty_returned = 0.0
                    line.qty_returned += rec.qty_returned
                    line.lot_ids -= rec.lot_ids
                    vals = {
                        'date': line.return_date,
                        'origin': line.order_id.name,
                        'product_id': line.product_id.id,
                        'product_uom': line.product_uom.id,
                        'location_id': self.env.ref('stock.stock_location_customers').id,
                        'location_dest_id': line.order_id.warehouse_id.lot_stock_id.id,
                        'state': 'done',
                        'name': "Rental Product Returned",
                        'company_id': self.env.context.get('allowed_company_ids')[0],
                        'lot_ids': rec.lot_ids,
                    }
                    move = self.env["stock.move"].create(vals)
                    if line.product_template_id.tracking == 'none':
                        move._set_quantity_done(rec.qty_returned)
                        move._action_assign()
                        move._action_done()
                    rec.order_line_id._compute_late_return()
                if line.qty_delivered == line.qty_returned and line.is_picked_up:
                    line.is_returned = True
                else:
                    line.is_returned = False
                rec.order_line_id.order_id.is_partial_return_boolean = False
                rec.order_line_id.order_id.calculate_rental_state()
                rec.order_line_id.order_id.calculate_next_pickup_return()
        else:
            raise ValidationError(_("You cannot return the product on an "
                                    "earlier date than previously decided return date."))


class RentalProductLine(models.TransientModel):
    _name = "rental.line"
    _description = "Rental Line"

    order_line_id = fields.Many2one('sale.order.line', string="Order Id")
    line_lot_ids = fields.Many2many(related="order_line_id.lot_ids", string="line_lot_ids")
    product_id = fields.Many2one('product.product', string="Product")
    qty_reserved = fields.Float(string="Reserved")
    qty_delivered = fields.Float(string="Picked Up")
    qty_to_return = fields.Float(string="Return")
    qty_returned = fields.Float(string="Returned")
    product_template_id = fields.Many2one('product.template')
    rental_wizard_id = fields.Many2one('rental.wizard', string="Rental Id")
    tracking = fields.Selection(related='product_id.tracking')
    lot_ids = fields.Many2many('stock.lot',
                               string="Serial No.",
                               domain="[('product_id', '=', product_id)]")

    @api.onchange('lot_ids')
    def _onchange_lot_ids(self):
        for rec in self:
            q_deliver = 0.0
            for lot in rec.lot_ids:
                q_deliver += lot.product_qty
            rec.qty_delivered = q_deliver
            rec.qty_returned = len(rec.lot_ids)
