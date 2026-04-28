# -*- coding: utf-8 -*-
# Copyright 2021 VERTS Services India Pvt. Ltd.
# http://www.verts.co.in

from odoo import api,fields,models, _
from odoo.exceptions import UserError


class BillLadingType(models.Model):
    _name = "bill.lading.type"
    _description = 'Bill of Lading Type'

    name = fields.Char("Name")
    desc = fields.Text("Description")
