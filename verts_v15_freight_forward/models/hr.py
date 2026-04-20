# -*- coding: utf-8 -*-
# Copyright 2025 Verts Services India Pvt Ltd.
# http://www.verts.co.in

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class HrEmployee(models.Model):
    _inherit = "hr.employee"
    
    employee_code = fields.Char("Employee Code", size=64, required=True, default='/')


    @api.model
    def create(self, values):
        if values.get('employee_code', '/') == '/':
            values['employee_code'] = self.env['ir.sequence'].next_by_code('employee.sequence') or '/'
        return super(HrEmployee, self).create(values)



