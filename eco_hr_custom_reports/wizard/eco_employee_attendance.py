# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from email.policy import default

from odoo import api, fields, models, _
import json
from odoo.exceptions import ValidationError
import io
import xlsxwriter
import base64
from datetime import date, timedelta, datetime
from dateutil.relativedelta import relativedelta


def get_count_holidays(emp, start_date, end_date):
    working_days_weekdays = list(set(emp.resource_calendar_id.attendance_ids.mapped('dayofweek')))
    holiday_weekdays = list({'0', '1', '2', '3', '4', '5', '6'} ^ set(working_days_weekdays))
    current_date = start_date
    weekdays = 0
    while current_date <= end_date:
        if str(current_date.weekday()) in holiday_weekdays:
            weekdays += 1
        current_date += timedelta(days=1)
    return weekdays


def get_dates_between(start_date_str, end_date_str, date_format="%Y-%m-%d"):
    start_date = datetime.strptime(start_date_str, date_format)
    end_date = datetime.strptime(end_date_str, date_format)

    delta = end_date - start_date
    return [(start_date + timedelta(days=i)).strftime(date_format) for i in range(delta.days + 1)]


class EcoEmployeeAttendance(models.TransientModel):
    _name = 'eco.employee.attendance'

    date_start = fields.Date('Start Date', required=1)
    date_end = fields.Date('End Date', required=1)
    department_id = fields.Many2one('hr.department')
    company_id = fields.Many2one(comodel_name='res.company')
    employee_ids = fields.Many2many('hr.employee')

    def get_leave_days(self, employee_id, start_date, end_date):
        """
        Get the number of leave days for an employee between two dates.

        :param employee_id: Employee's ID
        :param start_date: Start date in 'YYYY-MM-DD' format
        :param end_date: End date in 'YYYY-MM-DD' format
        :return: Number of leave days between the given period
        """
        # Search for leave records within the specified date range
        leaves = self.env['hr.leave'].search([
            ('employee_id', '=', employee_id.id),
            ('state', '=', 'validate'),  # Ensure that the leave is approved
            ('request_date_from', '>=', start_date),
            ('request_date_to', '<=', end_date)
        ])

        # Calculate total leave days
        total_leave_days = 0
        for leave in leaves:
            # Ensure that the leave period is fully within the given range
            request_date_from = datetime.strptime(str(leave.request_date_from), '%Y-%m-%d')
            request_date_to = datetime.strptime(str(leave.request_date_to), '%Y-%m-%d')
            leave_start = max(request_date_from, start_date)
            leave_end = min(request_date_to, end_date)

            # Ensure it's a valid leave period
            if leave_start <= leave_end:
                total_leave_days += (leave_end - leave_start).days + 1

        return total_leave_days

    def attendance_report(self, employees, date_start, date_end):
        emps_info = []
        for emp in employees:
            actual_working_days = self.env['hr.attendance'].sudo().search(
                [('employee_id', '=', emp.id), ('check_in', '>=', date_start),
                 ('check_in', '<=', date_end)])
            actual_working_days = actual_working_days.mapped('check_in')
            actual_working_days = list(set([d.strftime('%m-%d-%Y') for d in actual_working_days]))
            actual_working_days_count = len(actual_working_days)

            # working_days = \
            #     emp.resource_calendar_id.get_work_duration_data(date_start, date_end, compute_leaves=True,
            #                                                     domain=None)['days'] + 1
            week_holidays = get_count_holidays(emp, self.date_start, self.date_end)

            holidays_date = []
            holidays = self.env['hr.public.holiday'].sudo().search(
                [('date_from', '>=', self.date_start), ('date_to', '<=', self.date_end)])
            for holiday in holidays:
                holidays_date.extend(get_dates_between(str(holiday.date_from), str(holiday.date_to)))

            difference = date_end - date_start
            num_days = difference.days

            time_off_days = self.get_leave_days(emp, date_start, date_end)
            # actual_working_days = working_days - time_off_days
            emps_info.append({'name': emp.name,
                              'holidays': len(holidays_date),
                              'actual_working_days': actual_working_days_count,
                              'time_off_days': time_off_days,
                              'absence_days': num_days + 1 - len(holidays_date) - week_holidays})
        report_vals = {'date_start': self.date_start,
                       'date_end': self.date_end,
                       'department_id': self.department_id.name if self.department_id else '',
                       'company_id': self.company_id.name if self.company_id else '',
                       'employees_info': emps_info}
        return report_vals

    def absent_report(self, employees, date_start, date_end):
        emps_info = []
        for emp in employees:
            dayofwork = list(set(emp.resource_calendar_id.attendance_ids.mapped('dayofweek')))

            days = []
            delta = date_end - date_start  # returns timedelta
            for i in range(delta.days + 1):
                day = date_start + timedelta(days=i)
                if str(day.weekday()) in dayofwork:
                    days.append(day.strftime('%m-%d-%Y'))
            emp_attendance = self.env['hr.attendance'].sudo().search(
                [('employee_id', '=', emp.id), ('check_in', '>=', date_start), ('check_in', '<=', date_end+timedelta(days=1))])
            emp_attendance = emp_attendance.mapped('check_in')
            emp_attendance = [d.strftime('%m-%d-%Y') for d in emp_attendance]

            absence_days = [item for item in days if item not in emp_attendance]
            for abs_day in absence_days:
                emps_info.append({'department': emp.department_id.name,
                                  'name': emp.name,
                                  'date': abs_day})
        report_vals = {'date_start': self.date_start,
                       'date_end': self.date_end,
                       'department_id': self.department_id.name if self.department_id else '',
                       'company_id': self.company_id.name if self.company_id else '',
                       'employees_info': emps_info}
        return report_vals

    def get_months(self, date_start, date_end):
        arabic_months = [
            'يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو',
            'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر'
        ]
        date_start, date_end = sorted([date_start, date_end])
        count = (date_end.year - date_start.year) * 12 + date_end.month - date_start.month + 1
        months = [[(date_start + relativedelta(months=i)).month, arabic_months[(date_start.month + i - 1) % 12]]
                  for i in range(count)]
        return months

    def monthly_attendance_report(self, employees, date_start, date_end):
        months = self.get_months(date_start, date_end)
        month_names = []
        for month_number, month_name in months:
            month_names.append(month_name)
        employees_info = []
        for emp in employees:
            emp_list = []
            emp_list.append(emp.name)
            actual_working_days = self.env['hr.attendance'].sudo().search(
                [('employee_id', '=', emp.id), ('check_in', '>=', date_start),
                 ('check_in', '<=', date_end)])
            num_of_att_months = 0
            for month_number, month_name in months:
                first_day = datetime(2025, month_number, 1)
                last_day = (first_day + relativedelta(months=1, days=-1))
                current_month_att = actual_working_days.filtered(
                    lambda e: e.check_in >= first_day and e.check_in <= last_day)
                current_month_att = current_month_att.mapped('check_in')
                current_month_att = list(set([d.strftime('%m-%d-%Y') for d in current_month_att]))
                count = len(current_month_att)
                if count>0:
                    num_of_att_months += 1


                emp_list.append(count)
            emp_list.append(num_of_att_months)

            employees_info.append(emp_list)
        report_vals = {'date_start': self.date_start,
                       'date_end': self.date_end,
                       'department_id': self.department_id.name if self.department_id else '',
                       'company_id': self.company_id.name if self.company_id else '',
                       'months': month_names,
                       'employees_info': employees_info}
        print('ttt', report_vals)

        return report_vals

    def prepare_report_values(self):
        employees = self.env['hr.employee'].sudo().search([])
        if self.department_id:
            employees = employees.filtered(lambda e: e.department_id.id == self.department_id.id)
        if self.company_id:
            employees = employees.filtered(lambda e: e.company_id.id == self.company_id.id)
        if self.employee_ids:
            employees = employees.filtered(lambda e: e.id in self.employee_ids.ids)

        date_start = datetime.strptime(str(self.date_start), '%Y-%m-%d')
        date_end = datetime.strptime(str(self.date_end), '%Y-%m-%d')

        if self.env.context.get('absent_report'):
            report_vals = self.absent_report(employees, date_start, date_end)

        elif self.env.context.get('monthly_attendance_report'):
            report_vals = self.monthly_attendance_report(employees, date_start, date_end)

        else:
            report_vals = self.attendance_report(employees, date_start, date_end)

        return report_vals

    def action_print_pdf(self):
        """Mark lead as lost and apply the loss reason"""
        self.ensure_one()
        if self.env.context.get('absent_report'):
            res = self.env.ref('eco_hr_custom_reports.employee_absent_report_action').report_action(self)

        elif self.env.context.get('monthly_attendance_report'):
            res = self.env.ref('eco_hr_custom_reports.employee_monthly_attendance_report_action').report_action(self)

        else:
            res = self.env.ref('eco_hr_custom_reports.employee_attendance_report_action').report_action(self)

        return res
