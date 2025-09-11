from odoo import models, fields, api, _


class EmployeeSickLeave(models.Model):
    _name = 'employee.sick.leave'

    date = fields.Date()
    rule_1 = fields.Integer(string='Rule1(0%)')  # 0%  ---- 0>15
    rule_2 = fields.Integer(string='Rule2(25%)')  # 25% ---- 16>25
    rule_3 = fields.Integer(string='Rule3(50%)')  # 50% ---- 26>35
    rule_4 = fields.Integer(string='Rule4(75%)')  # 75% ---- 36>45
    rule_5 = fields.Integer(string='Rule5(100%)')  # 100% --- 46>100

    payslip_id = fields.Many2one(comodel_name='hr.payslip', string='Payslip Name')
    employee_id = fields.Many2one(comodel_name='hr.employee')
