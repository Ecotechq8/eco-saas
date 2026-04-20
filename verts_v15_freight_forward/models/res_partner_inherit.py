# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class ResPartner(models.Model):
    _inherit = "res.partner"

    airline_code = fields.Char(string='Airline Code')
    is_shipping_line = fields.Boolean(string='Is Shipping Line', default=False)
    is_airline = fields.Boolean(string='Is Airline', default=False)
