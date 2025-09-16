from dateutil.relativedelta import relativedelta
from datetime import datetime

from odoo import api, fields, models, _
from odoo.tools.float_utils import float_round
from odoo.exceptions import ValidationError


class SaleOrderLineRental(models.Model):
    _inherit = "sale.order.line"

    qty_returned = fields.Float(string="Returned", readonly=True)
    pickup_date = fields.Datetime(string="Pick up Date")
    return_date = fields.Datetime(string="Return Date")
    is_rental_line = fields.Boolean(string="Rental Boolean")
    duration = fields.Char(string="Duration", store=True, compute="_calculate_unit_price")
    is_late_return = fields.Boolean(string="Late Return", default=False, compute="_compute_late_return")
    is_picked_up = fields.Boolean(string="Picked up Boolean")
    is_returned = fields.Boolean(string="Return Boolean")
    is_partial_pickup = fields.Boolean(string="Partial Pickup", compute="_compute_partial_pickup_return")
    is_partial_return = fields.Boolean(string="Partial Return", compute="_compute_partial_pickup_return")
    lot_ids = fields.Many2many('stock.lot', string="Serial No.")

    @api.onchange('product_id')
    def _onchange_product(self):
        if self.product_template_id.is_rent:
            self.is_rental_line = True
        else:
            self.is_rental_line = False

    @api.onchange('return_date')
    def _onchange_return_date(self):
        for line in self:
            if line.pickup_date and line.return_date:
                if line.return_date < line.pickup_date:
                    line.duration = False
                else:
                    # Calculate the difference in time
                    duration_diff = relativedelta(line.return_date, line.pickup_date)
                    # Check if the duration is less than 1 hour
                    if duration_diff.hours == 0 and duration_diff.minutes <= 59 and duration_diff.days == 0:
                        line.duration = False
                        line.price_unit = 0.0  # Optionally reset the price
                    else:
                        line._calculate_unit_price()

    @api.constrains('pickup_date', 'return_date')
    def _check_closing_date(self):
        for line in self:
            if line.return_date < line.pickup_date:
                raise ValidationError(_('Return date must be after the pickup date.'))

    @api.onchange('pickup_date', 'return_date', 'product_uom_qty')
    def _onchange__calculate_unit_price(self):
        self._calculate_unit_price()

    @api.depends('pickup_date', 'return_date', 'product_uom_qty')
    def _calculate_unit_price(self):
        for order in self:
            rental_prices = order.env['rental.price'].search([('product_template_id', '=', order.product_template_id.id)])
            duration_diff = relativedelta(order.return_date, order.pickup_date)
            days = (duration_diff.days + 1) if duration_diff.hours >= 23 else duration_diff.days
            hour_price = rental_prices.filtered(lambda p: p.unit_type == 'hour')
            day_price = rental_prices.filtered(lambda p: p.unit_type == 'day')
            week_price = rental_prices.filtered(lambda p: p.unit_type == 'week')
            month_price = rental_prices.filtered(lambda p: p.unit_type == 'month')

            if duration_diff.hours and not duration_diff.months and not duration_diff.days and not duration_diff.years:
                if hour_price:
                    self.price_unit = hour_price.price * duration_diff.hours
                    self.duration = "%d hours" % duration_diff.hours
                    return
                elif day_price:
                    # price = (duration_diff.hours * day_price.price) / 24
                    self.price_unit = day_price.price
                    self.duration = "%d hours" % duration_diff.hours
                    return

            if duration_diff.days and not duration_diff.months and not duration_diff.years:
                if week_price:
                    if duration_diff.weeks:
                        weeks = days / 7
                        remaining_days = days - (duration_diff.weeks * 7)
                        order.price_unit = float_round(week_price.price * weeks,
                                                      precision_rounding=order.product_id.uom_id.rounding)
                        order.duration = "%d weeks %d days" % (duration_diff.weeks, remaining_days)
                        return
                    elif day_price:
                        if duration_diff.hours and duration_diff.hours < 23:
                            days_with_hours = days + (duration_diff.hours / 24)
                            self.price_unit = float_round(day_price.price * days_with_hours,
                                                          precision_rounding=self.product_id.uom_id.rounding)
                            self.duration = "%d days %d hours" % (days, duration_diff.hours)
                            return
                        else:
                            self.price_unit = day_price.price * days
                            self.duration = "%d days" % days
                            return
                    else:
                        order.price_unit = float_round((week_price.price / 7) * days,
                                                      precision_rounding=order.product_id.uom_id.rounding)
                        order.duration = "%d days" % days
                        return
                elif day_price:
                    order.price_unit = day_price.price * days
                    order.duration = "%d days" % days
                    return
                elif month_price:
                    order.price_unit = (month_price.price / 30) * days
                    order.duration = "%d days" % days
                    return
            if duration_diff.months and not duration_diff.years:
                order.duration = "%d months %d days" % (duration_diff.months, days)
                if month_price:
                    months = duration_diff.months + days / 30
                    order.price_unit = float_round(month_price.price * months,
                                                  precision_rounding=order.product_id.uom_id.rounding)
                    return
                elif day_price:
                    month_days = duration_diff.months * 30 + days
                    order.price_unit = float_round(day_price.price * month_days,
                                                  precision_rounding=order.product_id.uom_id.rounding)
                    return
                elif week_price:
                    month_days = duration_diff.months * 30 + days
                    order.price_unit = float_round((week_price.price/7) * month_days,
                                                  precision_rounding=order.product_id.uom_id.rounding)
                    return
            if duration_diff.years:
                order.duration = "%d years %d months %d days" % (
                duration_diff.years, duration_diff.months, duration_diff.days)
                if month_price:
                    months = duration_diff.years * 12 + duration_diff.months + days / 30
                    order.price_unit = float_round(month_price.price * months,
                                                  precision_rounding=order.product_id.uom_id.rounding)
                    return
                elif day_price:
                    month_days = (duration_diff.years * 12 + duration_diff.months) * 30 + days
                    order.price_unit = float_round(day_price.price * month_days,
                                                  precision_rounding=order.product_id.uom_id.rounding)
                    return
                elif week_price:
                    month_days = (duration_diff.years * 12 + duration_diff.months) * 30 + days
                    order.price_unit = float_round((week_price.price/7) * month_days,
                                                  precision_rounding=order.product_id.uom_id.rounding)
                    return

    @api.onchange('product_id', 'product_uom_qty', 'price_unit')
    def _onchange_qty(self):
        if self.product_id.qty_available:
            if (self.product_id and self.product_uom_qty != 0
                    and self.product_uom_qty > self.product_id.qty_available):
                raise ValidationError(_("Ordered Quantity cannot be more than Available Quantity."))
        self._calculate_unit_price()

    def _compute_partial_pickup_return(self):
        for line in self:
            if (line.qty_delivered != line.product_uom_qty and
                    line.qty_delivered < line.product_uom_qty and line.qty_delivered != 0.0):
                line.is_partial_pickup = True
            else:
                line.is_partial_pickup = False
            if (line.qty_delivered != line.qty_returned and line.product_uom_qty != line.qty_returned and
                    line.qty_returned < line.qty_delivered and line.qty_returned != 0.0):
                line.is_partial_return = True
            else:
                line.is_partial_return = False

    @api.depends('return_date')
    def _compute_late_return(self):
        for line in self:
            if line.return_date:
                duration = relativedelta(datetime.now(), line.return_date)
                if line.return_date < datetime.now() and duration.days == 0:
                    line.is_late_return = True
                elif line.return_date < datetime.now() and duration.days > 0:
                    line.is_late_return = True
                else:
                    line.is_late_return = False
            else:
                line.is_late_return = False

    def _action_launch_stock_rule(self, previous_product_uom_qty=False):
        lines = self.search([('is_rental_line', '=', False)])
        res = super(SaleOrderLineRental, lines)._action_launch_stock_rule(previous_product_uom_qty)
        return res
