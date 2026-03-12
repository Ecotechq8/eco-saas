# controllers/hr_attendance.py
from odoo import http, _
from odoo.http import request
from odoo.exceptions import UserError
from odoo.tools import float_round
from odoo.tools.image import image_data_uri
import datetime


class HrAttendanceAccurateController(http.Controller):

    @staticmethod
    def _get_company(token):
        return request.env['res.company'].sudo().search([
            ('attendance_kiosk_key', '=', token)
        ], limit=1)

    @staticmethod
    def _require_real_geo(mode, latitude=False, longitude=False):
        """
        Accept only real coordinates coming from the client.
        Never fallback to GeoIP.
        """
        if latitude in (False, None, '', 'false') or longitude in (False, None, '', 'false'):
            raise UserError(_("GPS location is required. Please enable location access and try again."))

        try:
            latitude = float(latitude)
            longitude = float(longitude)
        except Exception:
            raise UserError(_("Invalid GPS coordinates received. Please try again."))

        return {
            'city': _('Unknown'),
            'country_name': _('Unknown'),
            'latitude': latitude,
            'longitude': longitude,
            'ip_address': request.httprequest.remote_addr,
            'browser': request.httprequest.user_agent.browser,
            'mode': mode,
        }

    @staticmethod
    def _get_user_attendance_data(employee):
        response = {}
        if employee:
            response = {
                'id': employee.id,
                'hours_today': float_round(employee.hours_today, precision_digits=2),
                'hours_previously_today': float_round(employee.hours_previously_today, precision_digits=2),
                'last_attendance_worked_hours': float_round(employee.last_attendance_worked_hours, precision_digits=2),
                'last_check_in': employee.last_check_in,
                'attendance_state': employee.attendance_state,
                'display_systray': employee.company_id.attendance_from_systray,
            }
        return response

    @staticmethod
    def _get_employee_info_response(employee):
        response = {}
        if employee:
            response = {
                **HrAttendanceAccurateController._get_user_attendance_data(employee),
                'employee_name': employee.name,
                'employee_avatar': employee.image_256 and image_data_uri(employee.image_256),
                'total_overtime': float_round(employee.total_overtime, precision_digits=2),
                'kiosk_delay': employee.company_id.attendance_kiosk_delay * 1000,
                'attendance': {
                    'check_in': employee.last_attendance_id.check_in,
                    'check_out': employee.last_attendance_id.check_out,
                },
                'overtime_today': request.env['hr.attendance.overtime'].sudo().search([
                    ('employee_id', '=', employee.id),
                    ('date', '=', datetime.date.today()),
                    ('adjustment', '=', False),
                ], limit=1).duration or 0,
                'use_pin': employee.company_id.attendance_kiosk_use_pin,
                'display_overtime': employee.company_id.hr_attendance_display_overtime,
            }
        return response

    @http.route('/hr_attendance/manual_selection', type='json', auth='public')
    def manual_selection_with_geolocation(self, token, employee_id, pin_code, latitude=False, longitude=False):
        company = self._get_company(token)
        if not company:
            return {}

        employee = request.env['hr.employee'].sudo().browse(int(employee_id))
        if employee.company_id != company:
            return {}

        if company.attendance_kiosk_use_pin and employee.pin != pin_code:
            return {}

        geo_information = self._require_real_geo('kiosk', latitude=latitude, longitude=longitude)
        employee.sudo()._attendance_action_change(geo_information)
        return self._get_employee_info_response(employee)

    @http.route('/hr_attendance/attendance_barcode_scanned', type='json', auth='public')
    def scan_barcode(self, token, barcode, latitude=False, longitude=False):
        company = self._get_company(token)
        if not company:
            return {}

        employee = request.env['hr.employee'].sudo().search([
            ('barcode', '=', barcode),
            ('company_id', '=', company.id)
        ], limit=1)

        if not employee:
            return {}

        geo_information = self._require_real_geo('kiosk', latitude=latitude, longitude=longitude)
        employee._attendance_action_change(geo_information)
        return self._get_employee_info_response(employee)

    @http.route('/hr_attendance/systray_check_in_out', type='json', auth='user')
    def systray_attendance(self, latitude=False, longitude=False):
        employee = request.env.user.employee_id
        if not employee:
            raise UserError(_("No employee is linked to this user."))

        geo_information = self._require_real_geo('systray', latitude=latitude, longitude=longitude)
        employee._attendance_action_change(geo_information)
        return self._get_employee_info_response(employee)