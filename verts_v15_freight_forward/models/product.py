# -*- coding: utf-8 -*-
# Copyright 2021 Verts Services India Pvt Ltd.
# http://www.verts.co.in

from odoo import fields, models, _


class UomUom(models.Model):
    _inherit = "uom.uom"

    freight_forward_forms = fields.Boolean(string='Freight Forward Forms')

class ProductTemplate(models.Model):
    _inherit = "product.template"
    
    is_export_expense = fields.Boolean(string='Is Export Expense')
    is_standard_expense = fields.Boolean(string='Is Standard Expense', default=False, help="This is the expense which will be added in all of the quotations by default such as Bill of Lading Charges, CHA charges etc. These are common charges which will be applied irrespective of the location where you are shipping.")
    export_pro_categ_id = fields.Many2one('export.product.category', string='Export Product Category ')
    is_export = fields.Boolean(string='Is Export')
    charge_code = fields.Char(string='Charges Code')