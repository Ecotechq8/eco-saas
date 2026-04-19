# -*- coding: utf-8 -*-
# Copyright 2021 Verts Services India Pvt. Ltd.
# http://www.verts.co.in

from odoo import api, fields, models, tools, _


class PartnerCategories(models.Model):
    _name = "partner.categories"
    _description = 'Partner Categories'

    name = fields.Char(string='Category', required=True)
    # account_receivable = fields.Many2one('account.account', string='Account Receivable')
    # account_payable = fields.Many2one('account.account', string='Account Payable')
    prefix = fields.Char(string='Prefix', default='')
    suffix = fields.Char(string='Suffix', default='')
    sequence_size = fields.Integer(string='Sequence Size')
    next_no = fields.Integer(string='Next No')
    type = fields.Selection([('customer', 'Customer'), ('supplier', 'Supplier')], string="Type")

