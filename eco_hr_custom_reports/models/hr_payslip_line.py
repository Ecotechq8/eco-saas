# -*- coding: utf-8 -*-
from odoo import models, fields, api


class HrPayslipLine(models.Model):
    _inherit = 'hr.payslip.line'

    number_of_days = fields.Float(
        string='Number of Working Days',
        compute='_compute_payslip_days_and_hours',
        store=True,
        help='Number of working days from the payslip worked days lines.'
    )
    number_of_absence_days = fields.Float(
        string='Number of Days of Absence',
        compute='_compute_payslip_days_and_hours',
        store=True,
        help='Number of absence days from the payslip worked days lines.'
    )
    number_of_hours = fields.Float(
        string='Number of Hours',
        compute='_compute_payslip_days_and_hours',
        store=True,
        help='Number of working hours from the payslip worked days lines.'
    )

    @api.depends(
        'slip_id',
        'slip_id.worked_days_line_ids',
        'slip_id.worked_days_line_ids.number_of_days',
        'slip_id.worked_days_line_ids.number_of_hours',
        'slip_id.worked_days_line_ids.code',
    )
    def _compute_payslip_days_and_hours(self):
        for line in self:
            slip = line.slip_id
            if not slip or not slip.worked_days_line_ids:
                normal_work_days = getattr(slip, 'normal_work_days', 0.0) if slip else 0.0
                leave_days = getattr(slip, 'number_of_leave_days', 0.0) if slip else 0.0
                line.number_of_days = normal_work_days
                line.number_of_absence_days = leave_days
                line.number_of_hours = normal_work_days * 8.0
                continue

            worked_lines = slip.worked_days_line_ids.filtered(
                lambda w: w.code == 'WORK100' or (hasattr(w, 'work_entry_type_id') and w.work_entry_type_id and w.work_entry_type_id.code == 'WORK100')
            )
            absence_lines = slip.worked_days_line_ids.filtered(
                lambda w: w.code in ('ABS', 'ATTSHAB') or
                          (hasattr(w, 'work_entry_type_id') and w.work_entry_type_id and w.work_entry_type_id.code in ('ABS', 'ATTSHAB')) or
                          getattr(w, 'is_unpaid', False)
            )

            # Working Days & Working Hours
            if worked_lines:
                work_days = sum(w.number_of_days for w in worked_lines)
                work_hours = sum(w.number_of_hours for w in worked_lines)
            else:
                non_absence_lines = slip.worked_days_line_ids - absence_lines
                work_days = sum(w.number_of_days for w in non_absence_lines) if non_absence_lines else getattr(slip, 'normal_work_days', 0.0)
                work_hours = sum(w.number_of_hours for w in non_absence_lines) if non_absence_lines else work_days * 8.0

            # Absence Days
            if absence_lines:
                absence_days = sum(abs(w.number_of_days) for w in absence_lines)
            else:
                absence_days = getattr(slip, 'number_of_leave_days', 0.0)

            line.number_of_days = work_days
            line.number_of_absence_days = absence_days
            line.number_of_hours = work_hours
