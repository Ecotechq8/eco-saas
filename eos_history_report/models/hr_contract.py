from odoo import models, fields, api


class HrContract(models.Model):
    _inherit = 'hr.contract'

    leave_monthly = fields.Float(compute='_compute_leave_monthly')
    leave_monthly_value = fields.Float(compute='_compute_leave_monthly_value')

    def _compute_leave_monthly(self):
        for contract in self:
            contract.leave_monthly = contract.annual_leave_per_day / 12 if contract.annual_leave_per_day else 0.0

    def _compute_leave_monthly_value(self):
        for contract in self:
            contract.leave_monthly_value = contract.leave_monthly * contract.day_value

    opening_balance_leave_days = fields.Float()
    opening_balance_leave_amount = fields.Float()
    opening_balance_eos_days = fields.Float()
    opening_balance_eos_amount = fields.Float()
