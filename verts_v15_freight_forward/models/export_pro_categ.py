# -*- coding: utf-8 -*-
# Copyright 2021 Verts Services India Pvt Ltd.
# http://www.verts.co.in


from odoo import api,fields,models, _
from odoo.exceptions import UserError


class ExportProductCategory(models.Model):
    _name = "export.product.category"
    _description = 'Export Product Category'

    name = fields.Char('Name', help="Export Product Category on which exports related processes & expenses might be applicable.  As per international norms, Such as Dry Chilly Powder will come Chilly Product Category")
    hs_code = fields.Char('HS code')


