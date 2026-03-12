import requests
import logging
from odoo import http, _
from odoo.http import request
from odoo.exceptions import UserError
from odoo.tools import float_round
from odoo.tools.image import image_data_uri

_logger = logging.getLogger(__name__)


class HrAttendanceAccurateController(http.Controller):

    def _get_location_details(self, lat, lon):
        """
        Converts coordinates to City and Country.
        Handles Alexandria/Governorate structure specifically.
        """
        _logger.info("DEBUG: Fetching location for Lat: %s, Lon: %s", lat, lon)
        city = _('Unknown')
        country = _('Egypt')

        try:
            # Use a very specific User-Agent so the API doesn't block you
            url = f"https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat={lat}&lon={lon}"
            headers = {'User-Agent': 'Odoo_Attendance_Eco_Fix_v2'}
            response = requests.get(url, headers=headers, timeout=8)

            if response.status_code == 200:
                data = response.json()
                _logger.info("DEBUG: Full API Response: %s", data)
                address = data.get('address', {})

                # Egypt Specific Logic: Look for City, Town, or Governorate (Alexandria is a Governorate)
                city = (address.get('city') or
                        address.get('town') or
                        address.get('governorate') or
                        address.get('state') or
                        address.get('suburb') or
                        _('Unknown'))

                country = address.get('country', _('Egypt'))

                _logger.info("DEBUG: Found City: %s, Country: %s", city, country)
        except Exception as e:
            _logger.error("DEBUG: API Call Failed: %s", str(e))

        return city, country

    def _prepare_geo_data(self, mode, lat, lon):
        if not lat or not lon or lat in (False, 'false', None):
            raise UserError(_("High Precision GPS is required. Please allow location access."))

        # Get both City and Country from the API
        real_city, real_country = self._get_location_details(lat, lon)

        return {
            'city': real_city,
            'country_name': real_country,
            'latitude': float(lat),
            'longitude': float(lon),
            'ip_address': request.httprequest.remote_addr,
            'browser': request.httprequest.user_agent.browser,
            'mode': mode,
        }

    def _get_employee_info_response(self, employee):
        """ Required for Odoo UI to refresh correctly """
        return {
            'id': employee.id,
            'employee_name': employee.name,
            'employee_avatar': employee.image_256 and image_data_uri(employee.image_256),
            'attendance_state': employee.attendance_state,
            'hours_today': float_round(employee.hours_today, precision_digits=2),
            'last_attendance_worked_hours': float_round(employee.last_attendance_worked_hours, precision_digits=2),
            'last_check_in': employee.last_check_in,
            'kiosk_delay': employee.company_id.attendance_kiosk_delay * 1000,
            'display_overtime': employee.company_id.hr_attendance_display_overtime,
        }

    @http.route('/hr_attendance/systray_check_in_out', type='json', auth='user')
    def systray_attendance(self, latitude=False, longitude=False):
        employee = request.env.user.employee_id
        if not employee:
            raise UserError(_("No employee linked to this user."))
        geo_info = self._prepare_geo_data('systray', latitude, longitude)
        employee._attendance_action_change(geo_info)
        return self._get_employee_info_response(employee)

    @http.route('/hr_attendance/manual_selection', type='json', auth='public')
    def manual_selection(self, token, employee_id, pin_code, latitude=False, longitude=False):
        company = request.env['res.company'].sudo().search([('attendance_kiosk_key', '=', token)], limit=1)
        employee = request.env['hr.employee'].sudo().browse(int(employee_id))
        if not company or employee.company_id != company:
            return {}
        if company.attendance_kiosk_use_pin and employee.pin != pin_code:
            return {}

        geo_info = self._prepare_geo_data('kiosk', latitude, longitude)
        employee.sudo()._attendance_action_change(geo_info)
        return self._get_employee_info_response(employee)
