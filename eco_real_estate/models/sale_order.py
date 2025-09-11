# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    project_id = fields.Many2one("project.project", "Project")
    property_id = fields.Many2one("product.template", "Property No.")

    reservation_id = fields.Many2one("property.reservation", "Reservation")

    cancel_payment_id = fields.Many2one('account.payment', 'Cancel payment ')
    cancel_reason = fields.Text('Cancel Reason')
    state = fields.Selection(selection_add=[ ("property_delivery", "Delivered")])
    payment_strategy_line_ids = fields.Many2many(
        comodel_name='payment.strategy.line',
        string="Payment Strategies",
        compute="_compute_payment_strategy_line_ids",
        store=True
    )

    @api.depends('reservation_id')
    def _compute_payment_strategy_line_ids(self):
        for order in self:
            if order.reservation_id:
                order.payment_strategy_line_ids = order.reservation_id.payment_strategy_line_ids
            else:
                order.payment_strategy_line_ids = [(5, 0, 0)]  # clear the field


    def action_property_delivered(self):
            self.write({'state': 'property_delivery'})
            self.property_id.write({'state': 'deliver'})
