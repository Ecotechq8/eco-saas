# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo import fields, models, api, _
import pytz



class EcoHrAttendanceBonus(models.Model):
    _name = 'eco.hr.attendance.bonus'

    number_of_attendance_days = fields.Float()
    number_of_bonus_days = fields.Float()
    applied = fields.Boolean('Active', default=True)

    ### Salary Rule
    # num_of_added_days = 0
    # attendance_days = employee.env['hr.attendance'].sudo().search(
    #     [('employee_id', '=', employee.id), ('check_in', '>=', payslip.date_from), ('check_in', '<=', payslip.date_to)])
    # emp_attendance = attendance_days.mapped('check_in')
    # emp_attendance = list(set([d.strftime('%m-%d-%Y') for d in emp_attendance]))
    # num_of_emp_attendance_days = len(emp_attendance)
    # attendance_bonus = employee.env['eco.hr.attendance.bonus'].sudo().search(
    #     [('applied', '=', True), ('number_of_attendance_days', '>=', num_of_emp_attendance_days)],
    #     order='number_of_attendance_days desc', limit=1)
    # if attendance_bonus:
    #     num_of_added_days = attendance_bonus.number_of_bonus_days
    # salary_day_rate = contract.total_amount / 30
    # result = num_of_added_days * salary_day_rate