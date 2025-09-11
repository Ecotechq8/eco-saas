# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo import fields, models, api, _
import pytz



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

