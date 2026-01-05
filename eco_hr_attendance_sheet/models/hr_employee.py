from odoo import api, fields, models
from datetime import datetime, date, timedelta


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    get_inf_from_planning = fields.Boolean(string="Planning Attendance Data", )
    auto_create_attendance = fields.Boolean()

    def get_workday(self, index):
        values = [('0', 'Monday'),
                  ('1', 'Tuesday'),
                  ('2', 'Wednesday'),
                  ('3', 'Thursday'),
                  ('4', 'Friday'),
                  ('5', 'Saturday'),
                  ('6', 'Sunday')]
        return str(dict(values)[(index)])

    def action_create_attendance(self):
        attend_obj = self.env['hr.attendance']
        for rec in self.search([('auto_create_attendance', '=', True)]):
            check_in, check_out = False, False
            today_day = datetime.strptime(str(date.today()) + ' 00:00:00', "%Y-%m-%d %H:%M:%S").strftime('%A')
            for line in rec.resource_calendar_id.attendance_ids:
                if today_day == self.get_workday(line.dayofweek):
                    check_in = datetime.strptime(str(date.today()) + ' 00:00:00', "%Y-%m-%d %H:%M:%S") + timedelta(
                        hours=line.hour_from) - timedelta(hours=3)
                    check_out = datetime.strptime(str(date.today()) + ' 00:00:00', "%Y-%m-%d %H:%M:%S") + timedelta(
                        hours=line.hour_to) - timedelta(hours=3)
            if not attend_obj.search([('employee_id', '=', rec.id), ('check_in', '=', check_in)]):
                attend_obj.create({
                    'employee_id': rec.id,
                    'check_in': check_in,
                    'check_out': check_out,
                })


class HrEmployeePublic(models.Model):
    _inherit = 'hr.employee.public'

    get_inf_from_planning = fields.Boolean(string="Planning Attendance Data")
    auto_create_attendance = fields.Boolean()
