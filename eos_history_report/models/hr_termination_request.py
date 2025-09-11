from odoo import models, fields, api


class TerminationRequest(models.Model):
    _inherit = 'hr.termination.request'

    termination_amount = fields.Float(related="employee_id.termination_amount", store=True)
    other_allowance = fields.Float()
    other_deduction = fields.Float()
