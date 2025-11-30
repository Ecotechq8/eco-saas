# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class HrPayslipEmployees(models.TransientModel):
    _name = 'hr.payslip.employees'
    _description = 'Generate payslips for all selected employees'

    employee_ids = fields.Many2many('hr.employee', 'hr_employee_group_rel', 'payslip_id', 'employee_id', 'Employees')

    def compute_sheet(self):
        payslips = self.env['hr.payslip']
        [data] = self.read()
        active_id = self.env.context.get('active_id')
        if active_id:
            [run_data] = self.env['hr.payslip.run'].browse(active_id).read(['date_start', 'date_end', 'credit_note'])
        from_date = run_data.get('date_start')
        to_date = run_data.get('date_end')
        if not data['employee_ids']:
            raise UserError(_("You must select employee(s) to generate payslip(s)."))
        for employee in self.env['hr.employee'].browse(data['employee_ids']):
            payslip = self.env['hr.payslip'].create({
                'employee_id': employee.id,
                'date_from': from_date,
                'date_to': to_date,
                'payslip_run_id': active_id,
            })
            payslip.onchange_employee_id()
            payslip.compute_sheet()
        payslips.compute_sheet()
        return {'type': 'ir.actions.act_window_close'}
