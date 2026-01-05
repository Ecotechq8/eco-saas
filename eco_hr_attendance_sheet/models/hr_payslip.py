from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class Payslip(models.Model):
    _inherit = 'hr.payslip'

    def _get_worked_day_lines(self):
        worked_days_line_ids = super()._get_worked_day_lines()

        for payslip in self:
            structure = payslip.struct_id
            if not structure.unpaid_work_entry_type_ids:
                continue

            unpaid_codes = structure.unpaid_work_entry_type_ids.mapped('code')
            for line in worked_days_line_ids:
                if line.code in unpaid_codes:
                    line.is_unpaid = True
        return worked_days_line_ids

    def _get_worked_day_lines_values(self, domain=None):
        self.ensure_one()
        res = []
        hours_per_day = self._get_worked_day_lines_hours_per_day()
        work_hours = self.contract_id._get_work_hours(self.date_from, self.date_to, domain=domain)
        work_hours_ordered = sorted(work_hours.items(), key=lambda x: x[1])
        biggest_work = work_hours_ordered[-1][0] if work_hours_ordered else 0
        add_days_rounding = 0
        for work_entry_type_id, hours in work_hours_ordered:
            work_entry_type = self.env['hr.work.entry.type'].browse(work_entry_type_id)
            days = round(hours / hours_per_day, 5) if hours_per_day else 0
            if days > 26 and work_entry_type_id == 1:
                days -= 1
            if work_entry_type_id == biggest_work:
                days += add_days_rounding
            day_rounded = self._round_days(work_entry_type, days)
            add_days_rounding += (days - day_rounded)
            attendance_line = {
                'sequence': work_entry_type.sequence,
                'work_entry_type_id': work_entry_type_id,
                'number_of_days': day_rounded,
                'number_of_hours': hours,
            }
            res.append(attendance_line)
        return res

    @api.onchange('employee_id')
    def onchange_employee_id(self):
        if not self.employee_id:
            return
        work_entry_obj = self.env['hr.work.entry.type']
        overtime_work_entry = work_entry_obj.search([('code', '=', 'ATTSHOT')])
        latin_work_entry = work_entry_obj.search([('code', '=', 'ATTSHLI')])
        absence_work_entry = work_entry_obj.search([('code', '=', 'ATTSHAB')])
        difftime_work_entry = work_entry_obj.search([('code', '=', 'ATTSHDT')])
        if not overtime_work_entry:
            raise ValidationError(_(
                'Please Add Work Entry Type For Attendance Sheet Overtime With Code ATTSHOT'))
        if not latin_work_entry:
            raise ValidationError(_(
                'Please Add Work Entry Type For Attendance Sheet Late In With Code ATTSHLI'))
        if not absence_work_entry:
            raise ValidationError(_(
                'Please Add Work Entry Type For Attendance Sheet Absence With Code ATTSHAB'))
        if not difftime_work_entry:
            raise ValidationError(_(
                'Please Add Work Entry Type For Attendance Sheet Diff Time With Code ATTSHDT'))

        overtime = [{
            'name': "Overtime",
            'code': 'OVT',
            'work_entry_type_id': overtime_work_entry[0].id,
            'sequence': 30,
            'number_of_days': 0.0,
            'number_of_hours': 0.0,
        }]
        absence = [{
            'name': "Absence",
            'code': 'ABS',
            'work_entry_type_id': absence_work_entry[0].id,
            'sequence': 35,
            'number_of_days': 0.0,
            'number_of_hours': 0.0,
        }]
        late = [{
            'name': "Late In",
            'code': 'LATE',
            'work_entry_type_id': latin_work_entry[0].id,
            'sequence': 40,
            'number_of_days': 0.0,
            'number_of_hours': 0.0,
        }]
        difftime = [{
            'name': "Difference time",
            'code': 'DIFFT',
            'work_entry_type_id': difftime_work_entry[0].id,
            'sequence': 45,
            'number_of_days': 0.0,
            'number_of_hours': 0.0,
        }]
        worked_days_lines = overtime + late + absence + difftime
        self.worked_days_line_ids = [(0, 0, x) for x in worked_days_lines]


class HrPayrollStructure(models.Model):
    _inherit = 'hr.payroll.structure'

    unpaid_work_entry_type_ids = fields.Many2many(
        'hr.work.entry.type',
        'hr_structure_unpaid_work_entry_rel',
        'structure_id',
        'work_entry_type_id',
        string="Unpaid Work Entry Types"
    )


class HrPayslipWorkedDays(models.Model):
    _inherit = 'hr.payslip.worked_days'

    is_unpaid = fields.Boolean("Unpaid", default=False)
