# -*- coding: utf-8 -*-
# Copyright 2021 Verts Services India Pvt Ltd.
# http://www.verts.co.in

from odoo import api,fields,models, _
from odoo.exceptions import UserError


class SpiceBoardRateMaster(models.Model):
    _name = "spice.board.rate.master"
    _description = 'Spice Board Rate Master'
    _rec_name = 'country_id'

    country_id = fields.Many2one('res.country', required=True, string="Country")
    qc_id = fields.Many2one('qc.parameter', required=True, string="QC Parameter")
    # rate_small_five = fields.Float(string="Rate <=5mt (Rs. per MT)", required=True)
    # rate_greater_five = fields.Float(string="Rate > 5mt (Rs. per MT)", )
    product_id = fields.Many2one('product.product', string="Expense Name")
    # categ_id = fields.Many2one('product.category', string="Expense Category")
    spice_board_line = fields.One2many('spice.board.line', 'spice_id', string="Spice Board Line")


class SpiceBoardLine(models.Model):
    _name = "spice.board.line"
    _description = 'SpiceBoardLine'

    from_qty = fields.Float(string="From Qty")
    to_qty = fields.Float(string="To Qty")
    price = fields.Float(string="Price")
    spice_id = fields.Many2one('spice.board.rate.master', string="Spice ID")
    product_id = fields.Many2one('product.product', string="Product")
    categ_id = fields.Many2one('product.category', string="Product Category")

    # @api.onchange('product_id')
    # def onchange_product_id(self):
    #     if self.product_id:
    #         self.categ_id = self.product_id.categ_id.id
