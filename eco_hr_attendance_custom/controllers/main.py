import requests
from odoo import http, _
from odoo.http import request
from odoo.exceptions import UserError
from odoo.tools import float_round
from odoo.tools.image import image_data_uri


class HrAttendanceAccurateController(http.Controller):

    def _get_real_city_name(self, lat, lon):
        try:
            url = f"https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat={lat}&lon={lon}"
            headers = {'User-Agent': 'OdooAttendanceFix/1.0'}
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code == 200:
                address = response.json().get('address', {})
                return address.get('city') or address.get('town') or address.get('suburb') or _('Unknown')
        except:
            pass
        return _('Unknown Location')

    def _prepare_geo_data(self, mode, lat, lon):
        if not lat or not lon or lat in (False, 'false', None):
            raise UserError(_("High Precision GPS is required. Please allow location access."))

        real_city = self._get_real_city_name(lat, lon)
        return {
            'city': real_city,
            'country_name': _('Egypt'),
            'latitude': float(lat),
            'longitude': float(lon),
            'ip_address': request.httprequest.remote_addr,
            'browser': request.httprequest.user_agent.browser,
            'mode': mode,
        }

    def _get_employee_info_response(self, employee):
        """ This is REQUIRED for Odoo 18 UI to work correctly after check-in """
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