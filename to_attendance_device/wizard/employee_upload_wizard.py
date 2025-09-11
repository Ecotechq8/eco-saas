from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class EmployeeUploadWizard(models.TransientModel):
    _name = 'employee.upload.wizard'
    _description = 'Employee Upload Wizard'

    @api.model
    def _get_employee_ids(self):
        return self.env['hr.employee'].search([('id', 'in', self.env.context.get('active_ids', []))])

    device_ids = fields.Many2many('attendance.device', string='Devices', required=True)
    employee_ids = fields.Many2many('hr.employee', string='Employees to upload', default=_get_employee_ids, required=True)

    @api.onchange('employee_ids')
    def _onchange_employee_ids(self):
        if self.employee_ids:
            self.device_ids = self.employee_ids.mapped('unamapped_attendance_device_ids')

    def action_employee_upload(self):
        self.ensure_one()
        for device_id in self.device_ids:
            for employee_id in self.employee_ids:
                if not employee_id.barcode:
                    raise ValidationError(_('Employee %s has no Badge ID (employee barcode) set. Please set it on the employee profile.')
                                        % (employee_id.name))
                employee_id.action_load_to_attendance_device(device_id)
        self.device_ids.action_employee_map()

