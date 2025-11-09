from odoo import fields, models, api, _


class HrPayslipInputType(models.Model):
    _inherit = 'hr.payslip.input.type'

    is_penalty = fields.Boolean()


class HrPayslipInput(models.Model):
    _inherit = 'hr.payslip.input'

    penalty_payment_id = fields.Many2one('penalty.request.payment')
    is_penalty = fields.Boolean()
