# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AccountPayment(models.Model):
    _inherit = "account.payment"

    project_id = fields.Many2one("project.project", "Project")
    property_id = fields.Many2one("product.template", "Property No.")

    reservation_id = fields.Many2one("property.reservation", "Reservation")
    reservation_seq  = fields.Char(string='Reservation Sequence', readonly=True)
    check_no = fields.Char(string='Check Number')

    def submit_reservation_seq(self):
        if self.reservation_seq == 'New' or not self.reservation_seq:
            self.reservation_seq = self.env["ir.sequence"].next_by_code("reservation.payment")
