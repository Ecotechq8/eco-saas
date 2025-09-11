# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from dateutil.relativedelta import relativedelta

class GetAttendanceWizard(models.TransientModel):
    _name = 'get.attendance'
    _description = 'get attendance wizard'

    device_id = fields.Many2one('attendance.device')
    start_date = fields.Datetime(default=lambda self: fields.Date.today())
    end_date = fields.Datetime(default=lambda self: fields.Date.today())

    def get_attendance(self):
        if self.device_id:
            self.device_id.action_attendance_download(self.start_date,self.end_date)