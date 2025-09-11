from odoo import api, fields, models
import dateutil.parser
from datetime import datetime, timedelta


class SaleOrderRental(models.Model):
    _inherit = "sale.order"

    is_rental_order = fields.Boolean(string="Rental Order")
    is_late_picked_up = fields.Boolean(string="Late Picked Up")
    is_late_returned = fields.Boolean(string="Late Returned")
    next_pickup_date = fields.Date(string="Next Pickup", store=True)
    next_pickup_datetime = fields.Datetime(string="Next Pickup Time", store=True)
    next_return_date = fields.Date(string="Next Return", store=True)
    next_return_datetime = fields.Datetime(string="Next Return Time", store=True)
    is_partial_return_boolean = fields.Boolean(string="Partial Return Boolean",
                                               compute="_compute_partial_return_boolean")
    rental_state = fields.Selection([
        ('draft', 'Quotation'),
        ('sent', 'Quotation Sent'),
        ('signed', 'Signed'),
        ('confirm', 'Confirmed'),
        ('pickup', 'Picked Up'),
        ('return', 'Returned'),
        ('late_pickup', 'Late Pickup'),
        ('late_return', 'Late Return'),
        ('cancel', 'Cancelled'),
    ], default='draft', store=True, tracking=True)

    def _compute_partial_return_boolean(self):
        for rec in self:
            qty = []
            qty_delivered = []
            qty_rd_list = []
            for line in rec.order_line.search([('is_rental_line', '=', True), ('order_id', '=', rec.id)]):
                qty_rd = line.qty_delivered - line.qty_returned
                qty_rp = line.qty_returned - line.product_uom_qty
                qty.append(qty_rd)
                qty.append(qty_rp)
                qty_delivered.append(line.qty_delivered)
                qty_rd_list.append(qty_rd)
            result1 = all(element == 0.0 for element in qty)
            result2 = all(element == 0.0 for element in qty_delivered)
            result3 = all(element == 0.0 for element in qty_rd_list)
            if result1 or result2 or result3:
                rec.is_partial_return_boolean = False
            else:
                rec.is_partial_return_boolean = True

    @api.depends('order_line')
    def calculate_rental_state(self):
        for rec in self:
            rental_order_lines = rec.order_line.search([('is_rental_line', '=', True), ('order_id', '=', rec.id)])
            picked_lines = rental_order_lines.filtered(lambda line: line.is_picked_up)
            returned_lines = rental_order_lines.filtered(lambda line: line.is_returned)
            if (rec.next_pickup_datetime and (rec.next_pickup_datetime + timedelta(hours=1)) < datetime.now()
                    and len(rental_order_lines) != len(picked_lines)
                    and len(rental_order_lines) != len(returned_lines)):
                rec.rental_state = 'late_pickup'
            elif len(rental_order_lines) == len(picked_lines) and len(rental_order_lines) != len(returned_lines):
                rec.rental_state = 'pickup'
                if (rec.next_return_datetime and (rec.next_return_datetime + timedelta(hours=1)) < datetime.now()
                        and rec.rental_state == 'pickup'):
                    rec.rental_state = 'late_return'
            elif len(rental_order_lines) == len(returned_lines) and len(rental_order_lines) == len(picked_lines):
                rec.rental_state = 'return'
            else:
                rec.rental_state = 'confirm'

    def action_pickup(self):
        vals = []
        for line in self.order_line:
            if line.is_rental_line and not line.is_picked_up:
                qty_delivered = line.product_uom_qty - line.qty_delivered \
                    if line.product_template_id.tracking == 'none' else 0.0
                vals.append({
                    'order_line_id': line.id,
                    'product_id': line.product_id.id,
                    'qty_reserved': line.product_uom_qty - line.qty_delivered,
                    'qty_delivered': qty_delivered,
                    'product_template_id': line.product_template_id.id,
                })
        return {
            'name': 'Validate a Pick Up',
            'type': 'ir.actions.act_window',
            'res_model': 'rental.wizard',
            'view_id': self.env.ref('sttl_sale_rental.rental_pickup_wizard_view_form').id,
            'view_mode': 'form',
            'context': {
                'default_rental_line_ids': vals,
            },
            'target': 'new'
        }

    def action_return(self):
        vals = []
        for line in self.order_line:
            if (line.is_rental_line and line.qty_delivered - line.qty_returned != 0.0
                    and not line.is_returned and (line.is_picked_up or line.is_partial_pickup)):
                vals.append({
                    'order_line_id': line.id,
                    'product_id': line.product_id.id,
                    'qty_to_return': line.qty_delivered - line.qty_returned,
                    'qty_returned': line.qty_delivered - line.qty_returned,
                    'product_template_id': line.product_template_id.id,
                    'lot_ids': line.lot_ids.ids,
                })
        return {
            'name': 'Validate a Return',
            'type': 'ir.actions.act_window',
            'res_model': 'rental.wizard',
            'view_id': self.env.ref('sttl_sale_rental.rental_return_wizard_view_form').id,
            'view_mode': 'form',
            'context': {
                'default_rental_line_ids': vals,
            },
            'target': 'new'
        }

    def action_draft(self):
        self.rental_state = 'draft'
        res = super(SaleOrderRental, self).action_draft()
        return res

    def action_send_mail(self):
        self.rental_state = 'sent'
        res = super(SaleOrderRental, self).action_send_mail()
        return res

    def action_confirm(self):
        res = super(SaleOrderRental, self).action_confirm()
        self.calculate_rental_state()
        return res

    def action_cancel(self):
        self.rental_state = 'cancel'
        res = super(SaleOrderRental, self).action_cancel()
        return res

    @api.onchange('order_line')
    def calculate_next_pickup_return(self):
        for rec in self:
            picked_lines = rec.order_line.filtered(lambda l: not l.is_picked_up and l.is_rental_line)
            returned_lines = rec.order_line.filtered(lambda l: not l.is_returned and l.is_rental_line)
            pickup_dates = [line.pickup_date for line in picked_lines if line.pickup_date]
            return_dates = [line.return_date for line in returned_lines if line.return_date]
            min_pickup_date = min(pickup_dates) if pickup_dates else False
            min_return_date = min(return_dates) if return_dates else False
            if min_pickup_date:
                rec.next_pickup_date = dateutil.parser.parse(str(min_pickup_date)).date()
                rec.next_pickup_datetime = min_pickup_date
            else:
                rec.next_pickup_date = 0
                rec.next_pickup_datetime = 0
            if min_return_date:
                rec.next_return_date = dateutil.parser.parse(str(min_return_date)).date()
                rec.next_return_datetime = min_return_date
            else:
                rec.next_return_date = 0
                rec.next_return_datetime = 0
            if rec.rental_state == 'return':
                rec.next_pickup_date = 0
                rec.next_pickup_datetime = 0
                rec.next_return_date = 0
                rec.next_return_datetime = 0
