from odoo import fields, models, api, _


class HrPayslipInputType(models.Model):
    _inherit = 'hr.payslip.input.type'

    is_bonus = fields.Boolean()


class HrPayslipInput(models.Model):
    _inherit = 'hr.payslip.input'

    bonus_id = fields.Many2one('employee.bonus')
    is_bonus = fields.Boolean()
