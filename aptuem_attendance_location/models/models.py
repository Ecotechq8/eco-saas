from math import radians, sin, cos, sqrt, atan2
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    @api.model
    def create(self, values):
        attendance = super(HrAttendance, self).create(values)
        attendance._check_company_range()
        return attendance

    def write(self, values):
        res = super(HrAttendance, self).write(values)
        self._check_company_range()
        return res

    def _compute_distance(self, lat1, lon1, lat2, lon2):
        # Radius of the earth in kilometers
        R = 6371.0

        # Convert latitude and longitude from degrees to radians
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

        # Calculate the change in coordinates
        dlon = lon2 - lon1
        dlat = lat2 - lat1

        # Apply Haversine formula
        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        distance = R * c

        return distance

    def _check_company_range(self):
        company = self.env.company

        for attendance in self:

            if not (attendance.in_latitude and attendance.in_longitude):
                raise UserError(_("Location access is required to check in/out."))

            employee_lat = attendance.in_latitude
            employee_lon = attendance.in_longitude

            match_found = False

            for location in company.attendance_location_ids:

                distance = self._compute_distance(
                    employee_lat,
                    employee_lon,
                    location.latitude,
                    location.longitude
                )

                _logger.info(f"Distance from {location.name}: {distance} km")

                if distance <= location.allowed_distance:
                    match_found = True
                    break

            if not match_found:
                raise UserError(_(
                    "You are outside the allowed range for attendance."
                ))