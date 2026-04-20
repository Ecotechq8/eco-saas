# -*- coding: utf-8 -*-
# Copyright 2021 VERTS Services India Pvt. Ltd.
# http://www.verts.co.in

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class OceanVoyage(models.Model):
    _name = "ocean.voyage"
    _description = 'Ocean Voyage'

    name = fields.Char(string="Name")
    shipping_line = fields.Many2one('res.partner', string="Shipping Line")
    desc = fields.Text(string="Description")
    estimated_arrival = fields.Char("Estimated time of Arrival")
    estimated_sail = fields.Char("Estimate time of Sail")
    booking_cut_off = fields.Char("Special Booking Cut-off")
    vgm_cut_off = fields.Char("VGM Cut-off")
    port_cust_off = fields.Char("Port Cut-off")
    si_cut_off = fields.Char("SI Cut-off")
    cargo_order_ids = fields.One2many("cargo.order", "voyage_id", "Cargo Orders")
