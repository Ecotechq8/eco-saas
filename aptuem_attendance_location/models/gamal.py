# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import fields, models
import logging

_logger = logging.getLogger(__name__)

from odoo import fields, models, api

class ResCompany(models.Model):
    _inherit = 'res.company'
    
    company_latitude = fields.Float(string='Company Latitude', digits=(16, 6),
                                   help='Set Company Latitude here')
    company_longitude = fields.Float(string='Company Longitude', digits=(16, 6),
                                    help='Set Company Longitude here')
    allowed_distance = fields.Float(
        string='Allowed Distance (M)', digits=(16, 0),
        help='Set the allowed distance for check-in or check-out in kilometers. Example: 2.5 for 2.5 kilometers.'
    )

    attendance_location_ids = fields.One2many(
        'company.attendance.location',
        'company_id',
        string="Allowed Attendance Locations"
    )

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    company_latitude = fields.Float(string='Company Latitude', related='company_id.company_latitude', readonly=False)
    company_longitude = fields.Float(string='Company Longitude', related='company_id.company_longitude', readonly=False)
    allowed_distance = fields.Float(string='Allowed Distance (km)', related='company_id.allowed_distance', readonly=False)
    attendance_location_ids = fields.One2many(
        related='company_id.attendance_location_ids',
        readonly=False
    )

    def execute(self):
        res = super(ResConfigSettings, self).execute()
        _logger.info(f"company Latitude: {self.company_latitude}, company Longitude: {self.company_longitude}, Allowed Distance: {self.allowed_distance}")
        return res

class CompanyAttendanceLocation(models.Model):
    _name = 'company.attendance.location'
    _description = 'Company Attendance Allowed Locations'

    name = fields.Char(required=True)
    latitude = fields.Float(digits=(16, 6), required=True)
    longitude = fields.Float(digits=(16, 6), required=True)
    company_id = fields.Many2one('res.company', required=True, ondelete='cascade')