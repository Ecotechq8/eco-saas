from odoo import models, fields, api, _


class HrPayrollStructure(models.Model):
    _inherit = 'hr.payroll.structure'

    use_in_report = fields.Boolean()
