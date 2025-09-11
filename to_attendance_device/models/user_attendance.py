from odoo import models, fields, api, _


class UserAttendance(models.Model):
    _name = 'user.attendance'
    _description = 'User Attendance'
    _order = 'timestamp DESC, user_id, status, attendance_state_id, device_id'

    device_id = fields.Many2one('attendance.device', string='Attendance Device', required=True, ondelete='restrict', index=True)
    user_id = fields.Many2one('attendance.device.user', string='Device User', required=True, ondelete='cascade', index=True)
    timestamp = fields.Datetime(string='Timestamp', required=True, index=True)
    status = fields.Integer(string='Device Attendance State', required=True,
                            help='The state which is the unique number stored in the device to'
                            ' indicate type of attendance (e.g. 0: Checkin, 1: Checkout, etc)')
    attendance_state_id = fields.Many2one('attendance.state', string='Odoo Attendance State',
                                          help='This technical field is to map the attendance'
                                          ' status stored in the device and the attendance status in Odoo', required=True, index=True)
    activity_id = fields.Many2one('attendance.activity', related='attendance_state_id.activity_id', store=True, index=True)
    hr_attendance_id = fields.Many2one('hr.attendance', string='HR Attendance', ondelete='set null',
                                       help='The technical field to link Device Attendance Data with Odoo\' Attendance Data', index=True)

    type = fields.Selection([('checkin', 'Check-in'),
                            ('checkout', 'Check-out')], string='Activity Type', related='attendance_state_id.type', store=True)
    employee_id = fields.Many2one('hr.employee', string='Employee', related='user_id.employee_id', store=True, index=True)
    valid = fields.Boolean(string='Valid Attendance', index=True, readonly=True, default=False,
                           help="This field is to indicate if this attendance record is valid for HR Attendance Synchronization."
                           " E.g. The Attendances with Check out prior to Check in or the Attendances for users without employee"
                           " mapped will not be valid.")
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id,
                                 readonly=True, states={'draft': [('readonly', False)]})
    attendance_methode = fields.Selection(related='company_id.attendance_methode') 

    _sql_constraints = [
        ('unique_user_id_device_id_timestamp',
         'UNIQUE(user_id, device_id, timestamp)',
         "The Timestamp and User must be unique per Device"),
    ]

    @api.constrains('status', 'attendance_state_id')
    def constrains_status_attendance_state_id(self):
        for r in self:
            if r.status != r.attendance_state_id.code:
                raise(_('Attendance Status conflict! The status number from device must match the attendance status defined in Odoo.'))

    def get_valid(self,prev_att):
        if self.attendance_methode == 'filo':
            if not prev_att:
                valid = True
            elif self.type == 'checkin' and prev_att.type == 'checkout':
                valid = True
            elif self.type == 'checkout' and prev_att.type == 'checkout':
                valid = True
                prev_att.write({'valid': False})
            elif self.type == 'checkin' and prev_att.type == 'checkin':
                tz_timestamp = self.device_id.convert_utc_time_to_tz(prev_att.timestamp, self.device_id.tz)
                resource_line = self.employee_id.resource_calendar_id.get_resource_line(tz_timestamp)
                if resource_line:
                    prev_att_tz_timestamp = self.device_id.convert_utc_time_to_tz(prev_att.timestamp, self.device_id.tz)
                    check_prev_att = resource_line.is_in_shift(prev_att_tz_timestamp)
                    valid = not check_prev_att
                valid = False
            else:
                valid = False
        elif self.attendance_methode == 'one_by_one':
            if not prev_att:
                valid = self.type == 'checkin'
            else:
                valid = prev_att.type != self.type
        elif self.attendance_methode == 'by_device':
            if not prev_att:
                valid = self.type == 'checkin'
            else:
                valid = prev_att.type != self.attendance_state_id.type
        return valid
    
    def is_valid(self):
        self.ensure_one()
        if not self.employee_id:
            return False

        prev_att = self.search([('employee_id', '=', self.employee_id.id),
                                ('timestamp', '<', self.timestamp),
                                ('activity_id', '=', self.activity_id.id)], limit=1, order='timestamp DESC')
        return self.get_valid(prev_att)

    @api.model_create_multi
    def create(self, vals_list):
        attendances = super(UserAttendance, self).create(vals_list)
        valid_attendances = attendances.filtered(lambda att: att.is_valid())
        if valid_attendances:
            valid_attendances.write({'valid': True})
        return attendances
