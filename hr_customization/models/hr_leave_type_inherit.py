# coding: utf-8
from odoo import models, fields, api, _


class HrLeaveType(models.Model):
    _inherit = 'hr.leave.type'

    pay_in_advance = fields.Boolean(string="Allow Pay in Advance")
    sick_leave = fields.Boolean(string="Sick Leave")

    sick_leave_rules_ids = fields.One2many('sick.leave.rule', 'leave_type_id',
                                           string="Sick Leave Rules")
    is_unpiad_leave = fields.Boolean(string="Is Unpaid Leave", )

    sick_leave_reset_date = fields.Date()

    def action_reset_sick_leave_lines(self):
        employee_sick_leaves = self.env['employee.sick.leave']
        for item in self.search([('sick_leave', '=', True)]):
            if item.sick_leave_reset_date == fields.Date.today():
                for line in employee_sick_leaves.search([]):
                    line.unlink()
