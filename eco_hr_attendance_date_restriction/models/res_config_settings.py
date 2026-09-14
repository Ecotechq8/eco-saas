from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    attendance_restrict_past_days = fields.Boolean(
        related='company_id.attendance_restrict_past_days',
        readonly=False,
        string="Restrict Past Attendance Entries",
    )
    attendance_max_past_days = fields.Integer(
        related='company_id.attendance_max_past_days',
        readonly=False,
        string="Maximum Past Days Allowed",
    )
    attendance_allow_manager_bypass = fields.Boolean(
        related='company_id.attendance_allow_manager_bypass',
        readonly=False,
        string="Allow Attendance Managers to Bypass",
    )
