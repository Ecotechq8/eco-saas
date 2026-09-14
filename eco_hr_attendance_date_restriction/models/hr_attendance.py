from datetime import timedelta
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    @api.constrains('check_in', 'check_out')
    def _check_attendance_past_days_limit(self):
        is_admin = self.env.is_superuser()

        for attendance in self:
            company = attendance.employee_id.company_id or self.env.company
            if not company.attendance_restrict_past_days:
                continue

            max_days = company.attendance_max_past_days
            if max_days < 0:
                continue

            if is_admin:
                continue

            user = self.env.user

            if user.has_group('eco_hr_attendance_date_restriction.group_hr_attendance_bypass_date_limit'):
                continue

            if company.attendance_allow_manager_bypass and user.has_group('hr_attendance.group_hr_attendance_manager'):
                continue

            today = fields.Date.context_today(attendance)
            cutoff_date = today - timedelta(days=max_days)

            if attendance.check_in:
                check_in_local_date = fields.Datetime.context_timestamp(attendance, attendance.check_in).date()
                if check_in_local_date < cutoff_date:
                    check_in_str = fields.Date.to_string(check_in_local_date)
                    cutoff_str = fields.Date.to_string(cutoff_date)
                    raise ValidationError(_(
                        "You cannot create or import attendance records with a Check In date older than %(days)s days from today.\n"
                        "• Employee: %(employee)s\n"
                        "• Check In Date: %(check_in)s\n"
                        "• Earliest Allowed Date: %(limit_date)s",
                        days=max_days,
                        employee=attendance.employee_id.display_name or _("Unknown"),
                        check_in=check_in_str,
                        limit_date=cutoff_str,
                    ))

            if attendance.check_out:
                check_out_local_date = fields.Datetime.context_timestamp(attendance, attendance.check_out).date()
                if check_out_local_date < cutoff_date:
                    check_out_str = fields.Date.to_string(check_out_local_date)
                    cutoff_str = fields.Date.to_string(cutoff_date)
                    raise ValidationError(_(
                        "You cannot create or import attendance records with a Check Out date older than %(days)s days from today.\n"
                        "• Employee: %(employee)s\n"
                        "• Check Out Date: %(check_out)s\n"
                        "• Earliest Allowed Date: %(limit_date)s",
                        days=max_days,
                        employee=attendance.employee_id.display_name or _("Unknown"),
                        check_out=check_out_str,
                        limit_date=cutoff_str,
                    ))
