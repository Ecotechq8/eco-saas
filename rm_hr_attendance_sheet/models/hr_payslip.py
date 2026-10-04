# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, date, time, timedelta
import pytz
import logging

_logger = logging.getLogger(__name__)


class Payslip(models.Model):
    _inherit = 'hr.payslip'

    def compute_sheet(self):
        for payslip in self:
            payslip.update_attendance_worked_days()
        return super().compute_sheet()

    def update_attendance_worked_days(self):
        self.ensure_one()
        if not self.employee_id or not self.date_from or not self.date_to:
            return

        contract = self.contract_id or (
            self.employee_id.contract_ids.filtered(lambda c: c.state == 'open')[:1]
        )
        if not contract:
            contract_ids = self.get_contract(self.employee_id, self.date_from, self.date_to)
            if contract_ids:
                contract = self.env['hr.contract'].browse(contract_ids[0])

        contract_id = contract.id if contract else False

        work_entry_obj = self.env['hr.work.entry.type']
        overtime_work_entry = work_entry_obj.search([('code', '=', 'ATTSHOT')], limit=1)
        latin_work_entry = work_entry_obj.search([('code', '=', 'ATTSHLI')], limit=1)
        absence_work_entry = work_entry_obj.search([('code', '=', 'ATTSHAB')], limit=1)
        difftime_work_entry = work_entry_obj.search([('code', '=', 'ATTSHDT')], limit=1)

        # 1. Look for existing attendance sheet
        sheet = self.env['attendance.sheet'].search([
            ('employee_id', '=', self.employee_id.id),
            ('date_from', '<=', self.date_to),
            ('date_to', '>=', self.date_from),
        ], limit=1)
        if not sheet and self.id and not isinstance(self.id, models.NewId):
            sheet = self.env['attendance.sheet'].search([('payslip_id', '=', self.id)], limit=1)

        # 2. If not found and contract has attendance policy, auto-create draft sheet
        if not sheet and contract and contract.att_policy_id:
            try:
                sheet = self.env['attendance.sheet'].create({
                    'employee_id': self.employee_id.id,
                    'date_from': self.date_from,
                    'date_to': self.date_to,
                    'contract_id': contract.id,
                    'att_policy_id': contract.att_policy_id.id,
                    'payslip_id': self.id if self.id and not isinstance(self.id, models.NewId) else False,
                })
                sheet.get_attendances()
            except Exception as e:
                _logger.warning("Could not auto-create attendance sheet: %s", e)
                sheet = False

        no_absence = 0
        tot_absence = 0.0
        no_overtime = 0
        tot_overtime = 0.0
        no_late = 0
        tot_late = 0.0
        no_difftime = 0
        tot_difftime = 0.0

        if sheet:
            if self.id and not isinstance(self.id, models.NewId) and (not sheet.payslip_id or sheet.payslip_id != self):
                sheet.payslip_id = self.id

            if sheet.state == 'draft':
                has_manual_notes = any(l.note for l in sheet.line_ids)
                if not sheet.line_ids or not has_manual_notes:
                    sheet.get_attendances()
                else:
                    sheet._compute_sheet_total()
            else:
                sheet._compute_sheet_total()

            no_absence = sheet.no_absence
            tot_absence = sheet.tot_absence
            no_overtime = sheet.no_overtime
            tot_overtime = sheet.tot_overtime
            no_late = sheet.no_late
            tot_late = sheet.tot_late
            no_difftime = sheet.no_difftime
            tot_difftime = sheet.tot_difftime
        else:
            att_data = self._calculate_attendance_absence_from_attendance(contract=contract)
            no_absence = att_data.get('no_absence', 0)
            tot_absence = att_data.get('tot_absence', 0.0)
            no_overtime = att_data.get('no_overtime', 0)
            tot_overtime = att_data.get('tot_overtime', 0.0)
            no_late = att_data.get('no_late', 0)
            tot_late = att_data.get('tot_late', 0.0)
            no_difftime = att_data.get('no_difftime', 0)
            tot_difftime = att_data.get('tot_difftime', 0.0)

        target_lines_data = [
            {
                'name': _("Overtime"),
                'code': 'OVT',
                'work_entry_type_id': overtime_work_entry.id if overtime_work_entry else False,
                'sequence': 30,
                'number_of_days': no_overtime,
                'number_of_hours': tot_overtime,
            },
            {
                'name': _("Absence"),
                'code': 'ABS',
                'work_entry_type_id': absence_work_entry.id if absence_work_entry else False,
                'sequence': 35,
                'number_of_days': no_absence,
                'number_of_hours': tot_absence,
            },
            {
                'name': _("Late In"),
                'code': 'LATE',
                'work_entry_type_id': latin_work_entry.id if latin_work_entry else False,
                'sequence': 40,
                'number_of_days': no_late,
                'number_of_hours': tot_late,
            },
            {
                'name': _("Difference time"),
                'code': 'DIFFT',
                'work_entry_type_id': difftime_work_entry.id if difftime_work_entry else False,
                'sequence': 45,
                'number_of_days': no_difftime,
                'number_of_hours': tot_difftime,
            },
        ]

        # Update saved records
        if self.id and not isinstance(self.id, models.NewId):
            for line_data in target_lines_data:
                code = line_data['code']
                matching = self.worked_days_line_ids.filtered(
                    lambda w: w.code == code or (
                        line_data['work_entry_type_id'] and getattr(w, 'work_entry_type_id', False) and w.work_entry_type_id.id == line_data['work_entry_type_id']
                    )
                )
                vals = {
                    'number_of_days': line_data['number_of_days'],
                    'number_of_hours': line_data['number_of_hours'],
                    'contract_id': contract_id,
                }
                if line_data['work_entry_type_id']:
                    vals['work_entry_type_id'] = line_data['work_entry_type_id']
                if matching:
                    matching.write(vals)
                else:
                    vals.update({
                        'payslip_id': self.id,
                        'name': line_data['name'],
                        'code': line_data['code'],
                        'sequence': line_data['sequence'],
                    })
                    self.env['hr.payslip.worked_days'].create(vals)
        else:
            # Onchange / NewId context
            existing_codes = {}
            for w in self.worked_days_line_ids:
                existing_codes[w.code] = w
                if getattr(w, 'work_entry_type_id', False) and w.work_entry_type_id:
                    existing_codes[w.work_entry_type_id.code] = w

            new_lines = []
            for line_data in target_lines_data:
                code = line_data['code']
                matching = existing_codes.get(code)
                if matching:
                    matching.number_of_days = line_data['number_of_days']
                    matching.number_of_hours = line_data['number_of_hours']
                    if line_data['work_entry_type_id']:
                        matching.work_entry_type_id = line_data['work_entry_type_id']
                else:
                    line_vals = dict(line_data, contract_id=contract_id)
                    new_lines.append((0, 0, line_vals))
            if new_lines:
                self.worked_days_line_ids = new_lines

    def _calculate_attendance_absence_from_attendance(self, contract=None):
        self.ensure_one()
        contract = contract or self.contract_id or (
            self.employee_id.contract_ids.filtered(lambda c: c.state == 'open')[:1]
        )
        if not contract or not contract.resource_calendar_id:
            return {'no_absence': 0, 'tot_absence': 0.0}

        calendar = contract.resource_calendar_id
        dayofwork = set(int(d) for d in calendar.attendance_ids.mapped('dayofweek'))
        hours_per_day = calendar.hours_per_day or (getattr(contract, 'workdays_hour', 0.0) or 8.0)

        tz_name = self.employee_id.tz or self.env.user.tz or 'UTC'
        try:
            tz = pytz.timezone(tz_name)
        except Exception:
            tz = pytz.utc

        # Check-in attendances
        attendances = self.env['hr.attendance'].sudo().search([
            ('employee_id', '=', self.employee_id.id),
            ('check_in', '>=', datetime.combine(self.date_from, time.min)),
            ('check_in', '<=', datetime.combine(self.date_to, time.max) + timedelta(days=1)),
        ])
        att_dates = set()
        for att in attendances:
            if att.check_in:
                local_dt = pytz.utc.localize(att.check_in).astimezone(tz)
                att_dates.add(local_dt.date())

        # Validated leaves
        leaves = self.env['hr.leave'].sudo().search([
            ('employee_id', '=', self.employee_id.id),
            ('state', '=', 'validate'),
            ('date_from', '<=', datetime.combine(self.date_to, time.max)),
            ('date_to', '>=', datetime.combine(self.date_from, time.min)),
        ])
        leave_dates = set()
        for l in leaves:
            l_from = l.date_from.date() if isinstance(l.date_from, datetime) else l.date_from
            l_to = l.date_to.date() if isinstance(l.date_to, datetime) else l.date_to
            cur = max(l_from, self.date_from)
            end = min(l_to, self.date_to)
            while cur <= end:
                leave_dates.add(cur)
                cur += timedelta(days=1)

        # Public holidays
        pub_holiday_dates = set()
        if 'hr.public.holiday' in self.env:
            hols = self.env['hr.public.holiday'].sudo().search([
                ('date_from', '<=', self.date_to),
                ('date_to', '>=', self.date_from),
            ])
            for h in hols:
                cur = max(h.date_from, self.date_from)
                end = min(h.date_to, self.date_to)
                while cur <= end:
                    pub_holiday_dates.add(cur)
                    cur += timedelta(days=1)

        absent_days_count = 0
        cur = self.date_from
        while cur <= self.date_to:
            if cur.weekday() in dayofwork:
                if cur not in att_dates and cur not in leave_dates and cur not in pub_holiday_dates:
                    absent_days_count += 1
            cur += timedelta(days=1)

        return {
            'no_absence': absent_days_count,
            'tot_absence': absent_days_count * hours_per_day,
            'no_overtime': 0,
            'tot_overtime': 0.0,
            'no_late': 0,
            'tot_late': 0.0,
            'no_difftime': 0,
            'tot_difftime': 0.0,
        }

    @api.onchange('employee_id', 'date_from', 'date_to')
    def onchange_employee(self):
        res = super().onchange_employee()
        for payslip in self:
            payslip.update_attendance_worked_days()
        return res

    @api.model
    def get_worked_day_lines(self, contracts, date_from, date_to):
        res = super().get_worked_day_lines(contracts, date_from, date_to)
        work_entry_obj = self.env['hr.work.entry.type']
        overtime_work_entry = work_entry_obj.search([('code', '=', 'ATTSHOT')], limit=1)
        latin_work_entry = work_entry_obj.search([('code', '=', 'ATTSHLI')], limit=1)
        absence_work_entry = work_entry_obj.search([('code', '=', 'ATTSHAB')], limit=1)
        difftime_work_entry = work_entry_obj.search([('code', '=', 'ATTSHDT')], limit=1)

        for contract in contracts:
            employee = contract.employee_id
            sheet = self.env['attendance.sheet'].search([
                ('employee_id', '=', employee.id),
                ('date_from', '<=', date_to),
                ('date_to', '>=', date_from),
            ], limit=1)
            no_absence, tot_absence = 0, 0.0
            no_overtime, tot_overtime = 0, 0.0
            no_late, tot_late = 0, 0.0
            no_difftime, tot_difftime = 0, 0.0

            if sheet:
                if sheet.state == 'draft':
                    has_manual_notes = any(l.note for l in sheet.line_ids)
                    if not sheet.line_ids or not has_manual_notes:
                        sheet.get_attendances()
                    else:
                        sheet._compute_sheet_total()
                else:
                    sheet._compute_sheet_total()
                no_absence, tot_absence = sheet.no_absence, sheet.tot_absence
                no_overtime, tot_overtime = sheet.no_overtime, sheet.tot_overtime
                no_late, tot_late = sheet.no_late, sheet.tot_late
                no_difftime, tot_difftime = sheet.no_difftime, sheet.tot_difftime
            else:
                dummy_payslip = self.new({
                    'employee_id': employee.id,
                    'date_from': date_from,
                    'date_to': date_to,
                    'contract_id': contract.id,
                })
                att_data = dummy_payslip._calculate_attendance_absence_from_attendance(contract=contract)
                no_absence = att_data.get('no_absence', 0)
                tot_absence = att_data.get('tot_absence', 0.0)

            res.extend([
                {
                    'name': _("Overtime"),
                    'code': 'OVT',
                    'contract_id': contract.id,
                    'work_entry_type_id': overtime_work_entry.id if overtime_work_entry else False,
                    'sequence': 30,
                    'number_of_days': no_overtime,
                    'number_of_hours': tot_overtime,
                },
                {
                    'name': _("Absence"),
                    'code': 'ABS',
                    'contract_id': contract.id,
                    'work_entry_type_id': absence_work_entry.id if absence_work_entry else False,
                    'sequence': 35,
                    'number_of_days': no_absence,
                    'number_of_hours': tot_absence,
                },
                {
                    'name': _("Late In"),
                    'code': 'LATE',
                    'contract_id': contract.id,
                    'work_entry_type_id': latin_work_entry.id if latin_work_entry else False,
                    'sequence': 40,
                    'number_of_days': no_late,
                    'number_of_hours': tot_late,
                },
                {
                    'name': _("Difference time"),
                    'code': 'DIFFT',
                    'contract_id': contract.id,
                    'work_entry_type_id': difftime_work_entry.id if difftime_work_entry else False,
                    'sequence': 45,
                    'number_of_days': no_difftime,
                    'number_of_hours': tot_difftime,
                },
            ])
        return res


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
