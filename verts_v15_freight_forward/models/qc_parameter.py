# -*- coding: utf-8 -*-
# Copyright 2021 Verts Services India Pvt Ltd.
# http://www.verts.co.in

from odoo import api,fields,models, _
from odoo.exceptions import UserError


class QcParameter(models.Model):
    _name = "qc.parameter"
    _description = 'Qc Parameter'
    
    name = fields.Char('Quality Parameter')