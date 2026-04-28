from math import radians, sin, cos, sqrt, atan2
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    @api.model_create_multi
    def create(self, vals_list):
        attendances = super().create(vals_list)
        attendances._check_company_range(action='check_in')
        return attendances

    def write(self, values):
        res = super().write(values)

        # Validate only when checkout location is being written
        checkout_fields = {'check_out', 'out_latitude', 'out_longitude'}
        if checkout_fields.intersection(values.keys()):
            self._check_company_range(action='check_out')

        return res

    def _compute_distance_meters(self, lat1, lon1, lat2, lon2):
        """Return distance in meters using Haversine formula."""
        earth_radius_km = 6371.0

        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

        dlon = lon2 - lon1
        dlat = lat2 - lat1

        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))

        return earth_radius_km * c * 1000  # meters

    def _get_attendance_coordinates(self, action):
        self.ensure_one()

        if action == 'check_out':
            lat = self.out_latitude
            lon = self.out_longitude
            label = _("check out")
        else:
            lat = self.in_latitude
            lon = self.in_longitude
            label = _("check in")

        if lat is None or lon is None:
            raise UserError(_("Location access is required to %s.") % label)

        return lat, lon

    def _check_company_range(self, action='check_in'):
        company = self.env.company

        # If no allowed locations configured, do not block attendance
        if not company.attendance_location_ids:
            _logger.info("No attendance locations configured for company %s. Skipping range validation.", company.name)
            return True

        for attendance in self:
            employee_lat, employee_lon = attendance._get_attendance_coordinates(action)

            nearest_location = None
            nearest_distance = None
            match_found = False

            for location in company.attendance_location_ids:
                if location.latitude is None or location.longitude is None:
                    continue

                distance_m = attendance._compute_distance_meters(
                    employee_lat,
                    employee_lon,
                    location.latitude,
                    location.longitude
                )

                _logger.info(
                    "Attendance %s %s distance from %s: %.2f meters",
                    attendance.id,
                    action,
                    location.name,
                    distance_m
                )

                if nearest_distance is None or distance_m < nearest_distance:
                    nearest_distance = distance_m
                    nearest_location = location

                allowed_m = location.allowed_distance or 0.0
                if distance_m <= allowed_m:
                    match_found = True
                    break

            if not match_found:
                if nearest_location:
                    raise UserError(_(
                        "You are outside the allowed attendance range.\n\n"
                        "Nearest allowed location: %s\n"
                        "Your distance: %.2f meters\n"
                        "Allowed distance: %.2f meters"
                    ) % (
                                        nearest_location.name,
                                        nearest_distance,
                                        nearest_location.allowed_distance or 0.0
                                    ))
                else:
                    raise UserError(_("No valid attendance locations are configured."))

        return True


