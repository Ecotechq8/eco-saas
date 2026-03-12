from odoo import http
from odoo.http import request


class AttendanceController(http.Controller):

    @http.route('/attendance/check', type='json', auth='user')
    def attendance_check(self, latitude=None, longitude=None):
        employee = request.env.user.employee_id

        if not employee:
            return {"error": "Employee not found"}

        geo_information = {
            "latitude": latitude,
            "longitude": longitude,
            "city": request.geoip.city.name if request.geoip else None,
            "country": request.geoip.country.name if request.geoip else None,
            "ip_address": request.httprequest.remote_addr,
            "browser": request.httprequest.user_agent.browser,
            "mode": "manual",
        }

        attendance = employee._attendance_action_change(geo_information)

        return {
            "attendance_id": attendance.id,
            "state": employee.attendance_state
        }
