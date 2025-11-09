# -*- coding: utf-8 -*-
from odoo import api, fields, models


class NewModule(models.Model):
    _name = 'hr.religion'
    _description = 'Hr Religion'

    name = fields.Char(required=True)