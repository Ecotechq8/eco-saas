from odoo import api, fields, models, _


class HrDepartment(models.Model):
    _inherit = 'hr.department'

    ulternate_approval_ids = fields.Many2many('hr.employee', string='Alternate Approver', help="If department manager not available then this user can approve leave on behalf of deptt head")
