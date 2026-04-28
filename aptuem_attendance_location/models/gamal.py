from odoo import fields, models
import logging

_logger = logging.getLogger(__name__)


class ResCompany(models.Model):
    _inherit = 'res.company'

    attendance_location_ids = fields.One2many(
        'company.attendance.location',
        'company_id',
        string="Allowed Attendance Locations"
    )


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    attendance_location_ids = fields.One2many(
        related='company_id.attendance_location_ids',
        readonly=False
    )


class CompanyAttendanceLocation(models.Model):
    _name = 'company.attendance.location'
    _description = 'Company Attendance Allowed Locations'

    name = fields.Char(required=True)
    latitude = fields.Float(string="Latitude", digits=(16, 6), required=True)
    longitude = fields.Float(string="Longitude", digits=(16, 6), required=True)
    company_id = fields.Many2one('res.company', required=True, ondelete='cascade')
    allowed_distance = fields.Float(
        string="Allowed Distance (meters)",
        required=True,
        default=100.0,
        help="Maximum allowed distance from this location in meters."
    )