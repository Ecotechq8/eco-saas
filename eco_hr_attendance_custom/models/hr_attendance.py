# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo import fields, models, api, _
import pytz
from odoo import models, api
from odoo.http import request
import requests


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    e_modified_time = fields.Datetime('Modified Check in', readonly=1)

    def action_modify_checkin_time(self):
        for rec in self:
            checkin_weekday = rec.check_in.weekday()
            modify_checkin_time = rec.employee_id.resource_calendar_id.attendance_ids.filtered(
                lambda e: e.dayofweek == str(checkin_weekday) and e.day_period == 'morning')
            if modify_checkin_time:
                rec.e_modified_time = rec.check_in

                modify_checkin_time = modify_checkin_time[0].hour_from
                hours, remainder = divmod(modify_checkin_time, 1)  # Get the hours as the integer part
                minutes = remainder * 60  # Convert the fractional part to minutes
                checkin = rec.check_in.astimezone(pytz.timezone(self.env.user.tz or 'UTC'))
                checkin = checkin.replace(hour=int(hours), minute=int(minutes), second=0)
                updated_utc = checkin.astimezone(pytz.utc)
                # Strip timezone to make it naive
                naive_utc = updated_utc.replace(tzinfo=None)
                rec.check_in = naive_utc

    def _get_ip_location(self):
        try:
            if not request:
                return {}

            ip = request.httprequest.remote_addr

            response = requests.get(
                f"http://ip-api.com/json/{ip}",
                timeout=3
            )

            data = response.json()

            if data.get("status") == "success":
                return {
                    "latitude": data.get("lat"),
                    "longitude": data.get("lon"),
                    "city": data.get("city"),
                    "country": data.get("country"),
                }

        except Exception:
            pass

        return {}


    @api.model
    def create(self, vals):
        location = self._get_ip_location()

        if location:
            vals.update({
                "in_latitude": location.get("latitude"),
                "in_longitude": location.get("longitude"),
                "in_city": location.get("city"),
                "in_country_name": location.get("country"),
            })

        return super().create(vals)


    def write(self, vals):

        # Detect if checkout is being written
        if "check_out" in vals:
            location = self._get_ip_location()

            if location:
                vals.update({
                    "out_latitude": location.get("latitude"),
                    "out_longitude": location.get("longitude"),
                    "out_city": location.get("city"),
                    "out_country_name": location.get("country"),
                })

        return super().write(vals)