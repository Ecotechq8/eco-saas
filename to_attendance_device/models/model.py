from odoo import models, fields, api, _


class ResCompany(models.Model):
    _inherit = 'res.company'
    _description = 'Res Company'
    
    attendance_methode = fields.Selection([
        ('by_device', 'By Device'),
        ('one_by_one', 'One By One'),
        ('filo', 'First In - Last Out'),
    ],default='filo', required=True) 

class ResourceCalendarAttendance(models.Model):
    _inherit = "resource.calendar.attendance"

    start_shift = fields.Float(required=True, default=0.0)
    end_shift = fields.Float(required=True, default=0.0)
    
    def is_btween(self,hour):
        return hour >= self.start_shift and hour < self.end_shift

    def is_in_shift(self,datetime):
        day = datetime.weekday()
        hour = datetime.hour + datetime.minute / 60.0
        return self.is_btween(hour)
    
    def get_state(self,hour):
        if self.end_shift <= hour:
            return 1
        else:
            return None

class ResourceCalendar(models.Model):
    _inherit = "resource.calendar"

    def get_resource_line(self,datetime):
        day = datetime.weekday()
        hour = datetime.hour + datetime.minute / 60.0
        line_ids = self.attendance_ids.filtered(lambda r: r.dayofweek == str(day))
        for line in line_ids:
            check = line.is_btween(hour)
            if check:
                return line
        return False

    def get_status(self,datetime):
        day = datetime.weekday()
        hour = datetime.hour + datetime.minute / 60.0
        attendance_ids = self.attendance_ids.filtered(lambda r: r.dayofweek == str(day))
        for attendance in attendance_ids:
            state = attendance.get_state(hour)
            if state != None:
                return state