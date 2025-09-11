# coding: utf-8
from odoo import models, fields, api, _


class HrLeaveType(models.Model):
    _inherit = 'hr.leave.type'

    annual_leave = fields.Boolean(string="Annual Leave")
    calculate_in_ter_resi = fields.Boolean(string='Cal. in Termination and Resignation')

    is_unpiad_leave = fields.Boolean(string="Is Unpaid Leave", )
    is_permission = fields.Boolean(string="Is Permission")