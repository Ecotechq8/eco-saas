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


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    def _attendance_action_change(self, geo_information=None):
        self.ensure_one()
        action_date = fields.Datetime.now()

        if self.attendance_state != 'checked_in':
            vals = {
                'employee_id': self.id,
                'check_in': action_date,
            }
            if geo_information:
                vals.update({
                    'in_latitude': geo_information.get('latitude'),
                    'in_longitude': geo_information.get('longitude'),
                    'in_city': geo_information.get('city'),
                    'in_country_name': geo_information.get('country_name'),
                    'in_ip_address': geo_information.get('ip_address'),
                    'in_browser': geo_information.get('browser'),
                    'in_mode': geo_information.get('mode'),
                })
            return self.env['hr.attendance'].create(vals)

        attendance = self.env['hr.attendance'].search([
            ('employee_id', '=', self.id),
            ('check_out', '=', False),
        ], limit=1)

        if not attendance:
            raise exceptions.UserError(_(
                'Cannot perform check out on %(empl_name)s, could not find corresponding check in.',
                empl_name=self.sudo().name
            ))

        vals = {'check_out': action_date}
        if geo_information:
            vals.update({
                'out_latitude': geo_information.get('latitude'),
                'out_longitude': geo_information.get('longitude'),
                'out_city': geo_information.get('city'),
                'out_country_name': geo_information.get('country_name'),
                'out_ip_address': geo_information.get('ip_address'),
                'out_browser': geo_information.get('browser'),
                'out_mode': geo_information.get('mode'),
            })
        attendance.write(vals)
        return attendance
