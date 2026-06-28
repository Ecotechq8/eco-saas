# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
import pytz
from odoo.http import request
import requests


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    e_modified_time = fields.Datetime('Modified Check in', readonly=1)
    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('confirmed', 'Confirmed'),
        ],
        string='Status',
        default='draft',
        required=True,
        copy=False,
    )

    @api.model
    def _ensure_custom_schema(self):
        """Repair databases where this addon code was deployed before upgrade."""
        registry_flag = '_eco_hr_attendance_custom_schema_checked'
        if getattr(self.env.registry, registry_flag, False):
            return

        self.env.cr.execute("""
            SELECT column_name
              FROM information_schema.columns
             WHERE table_schema = 'public'
               AND table_name = 'hr_attendance'
               AND column_name IN ('state', 'e_modified_time')
        """)
        existing_columns = {column for (column,) in self.env.cr.fetchall()}
        schema_was_complete = {'state', 'e_modified_time'} <= existing_columns

        if 'state' not in existing_columns:
            self.env.cr.execute("""
                ALTER TABLE hr_attendance
                    ADD COLUMN state varchar
            """)

        self.env.cr.execute("""
            UPDATE hr_attendance
               SET state = 'draft'
             WHERE state IS NULL
        """)

        if 'e_modified_time' not in existing_columns:
            self.env.cr.execute("""
                ALTER TABLE hr_attendance
                    ADD COLUMN e_modified_time timestamp
            """)

        if schema_was_complete:
            setattr(self.env.registry, registry_flag, True)

    def init(self):
        self._ensure_custom_schema()

    def _check_attendance_confirm_action_allowed(self):
        if not self.env.user.has_group('eco_hr_attendance_custom.group_attendance_confirmation_actions'):
            raise UserError(_('You are not allowed to confirm attendance records.'))

    def action_confirm_attendance(self):
        self._ensure_custom_schema()
        self._check_attendance_confirm_action_allowed()
        self.filtered(lambda attendance: attendance.state != 'confirmed').write({
            'state': 'confirmed',
        })

    def action_set_attendance_to_draft(self):
        self._ensure_custom_schema()
        self._check_attendance_confirm_action_allowed()
        self.filtered(lambda attendance: attendance.state != 'draft').write({
            'state': 'draft',
        })

    @api.constrains('check_in', 'check_out')
    def _check_no_future_attendance_dates(self):
        now = fields.Datetime.now()
        for attendance in self:
            if attendance.check_in and attendance.check_in > now:
                raise ValidationError(_(
                    'You cannot create or import attendance records with a future Check In date.'
                ))
            if attendance.check_out and attendance.check_out > now:
                raise ValidationError(_(
                    'You cannot create or import attendance records with a future Check Out date.'
                ))

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
        self._ensure_custom_schema()
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
        self._ensure_custom_schema()
        if {'check_in', 'check_out'} & set(vals):
            locked_attendances = self.filtered(
                lambda attendance: attendance.state == 'confirmed' and vals.get('state', attendance.state) == 'confirmed'
            )
            if locked_attendances:
                raise UserError(_(
                    'You cannot modify Check In or Check Out on confirmed attendance records. '
                    'Set the attendance back to Draft first.'
                ))

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
