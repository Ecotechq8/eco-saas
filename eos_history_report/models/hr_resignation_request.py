from odoo import models, fields, api


class ResignationRequest(models.Model):
    _inherit = 'hr.resignation.request'

    resignation_amount = fields.Float(related="employee_id.resignation_amount", store=True)
    other_allowance = fields.Float()
    other_deduction = fields.Float()
