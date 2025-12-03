from odoo import api, fields, models, _
from odoo.exceptions import UserError

class HrPayslipEmployees(models.TransientModel):
    _name = 'hr.payslip.employees'
    _description = 'Generate payslips for all selected employees'

    employee_ids = fields.Many2many(
        'hr.employee', 'hr_employee_group_rel', 'payslip_id', 'employee_id', 'Employees'
    )

    def compute_sheet(self):
        [data] = self.read()
        active_id = self.env.context.get('active_id')
        if not data['employee_ids']:
            raise UserError(_("You must select employee(s) to generate payslip(s)."))
        if not active_id:
            raise UserError(_("No active payslip run found."))

        run = self.env['hr.payslip.run'].browse(active_id)
        from_date = run.date_start
        to_date = run.date_end

        payslips = self.env['hr.payslip']

        for employee in self.env['hr.employee'].browse(data['employee_ids']):
            contract = employee.contract_id
            if not contract:
                raise UserError(_("Employee %s has no contract." % employee.name))

            payslip_vals = {
                'employee_id': employee.id,
                'contract_id': contract.id,
                'struct_id': contract.struct_id.id,
                'date_from': from_date,
                'date_to': to_date,
                'payslip_run_id': active_id,
                'company_id': employee.company_id.id,
            }

            payslip = self.env['hr.payslip'].create(payslip_vals)
            payslips |= payslip

        payslips.compute_sheet()

        return {'type': 'ir.actions.act_window_close'}
