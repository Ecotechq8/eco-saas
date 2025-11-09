# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import date

class HrEmployee(models.Model):

    _inherit = 'hr.employee'

    age = fields.Integer(
        string="Age",
        compute='_compute_age',
        store=True,
        readonly=True
    )

    @api.depends('birthday')
    def _compute_age(self):
        today = date.today()
        for employee in self:
            if employee.birthday:
                birth_date = employee.birthday
                age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
                employee.age = age
            else:
                employee.age = 0