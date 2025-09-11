from odoo import models, fields, api
from datetime import datetime, timedelta

class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    e_is_automatic_checkout = fields.Boolean('Automatic Checkout')

    @api.model
    def auto_checkout_employees(self):
        now = fields.Datetime.now()

        # Get all employees with a check-in but no check-out today
        attendances = self.sudo().search([
            ('check_in', '!=', False),
            ('check_out', '=', False), ('employee_id.has_shifts', '!=', True)
        ])

        for att in attendances:
            employee = att.employee_id

            # Get employee's working hours
            resource_calendar = employee.resource_calendar_id
            if not resource_calendar:
                continue  # Skip if no schedule assigned

            # Determine the day of the week
            weekday = att.check_in.weekday()  # 0 = Monday

            # Find matching attendance rule
            calendar_attendances = resource_calendar.attendance_ids.filtered(
                lambda a: int(a.dayofweek) == weekday
            )
            if not calendar_attendances:
                continue

            # Get the latest "hour_to" as scheduled checkout
            max_hour_to = max([a.hour_to for a in calendar_attendances])
            min_hour_from = min([a.hour_from for a in calendar_attendances])
            start_minutes = int(min_hour_from * 60)
            end_minutes = int(max_hour_to * 60)
            # Difference in minutes
            diff_minutes = end_minutes - start_minutes
            scheduled_checkout = att.check_in + timedelta(minutes=diff_minutes)

            # If the scheduled checkout time is in the past, update check-out
            if scheduled_checkout < now:
                att.check_out = scheduled_checkout
                att.e_is_automatic_checkout = True
