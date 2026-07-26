# -*- coding: utf-8 -*-
# Copyright 2021 VERTS Services India Pvt. Ltd.
# http://www.verts.co.in

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class OceanVessel(models.Model):
    _name = "ocean.vessel"
    _description = 'Ocean Vessels'

    name = fields.Char(string="Name")
    shipping_line = fields.Many2one('res.partner', string="Shipping Line")
    desc = fields.Text(string="Description")
    imo_number = fields.Char("IMO NUmber")
    vessel_type = fields.Char("vessel Type")
    mmsi = fields.Char("MMSI")
    call_sign = fields.Char("Call Sign")
    flag = fields.Char("Flag")
    gross_tonnage = fields.Char("Gross Tonnage")
    summer_dwt = fields.Char("Summer DWT")
    length_overall = fields.Char("Length Overall x Breadth Extreme")
    year_built = fields.Char("Year Built")
    home_port = fields.Many2one("ports","Home Port")
