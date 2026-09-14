from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    attendance_restrict_past_days = fields.Boolean(
        string="Restrict Past Attendance Entries",
        default=True,
        help="If enabled, attendance records (Check In / Check Out) older than the allowed number of days cannot be created or imported.",
    )
    attendance_max_past_days = fields.Integer(
        string="Maximum Past Days Allowed",
        default=7,
        help="Number of days in the past from the current date for which attendance records can be created or imported.",
    )
    attendance_allow_manager_bypass = fields.Boolean(
        string="Allow Attendance Managers to Bypass",
        default=False,
        help="If enabled, users with the Attendance Manager role or 'Bypass Attendance Past Date Restriction' permission can create or import records beyond the limit.",
    )
