# coding: utf-8
from odoo import models, fields, api, _
# from odoo.exceptions import AccessError, UserError, ValidationError
# from odoo.addons.resource.models.resource import float_to_time, HOURS_PER_DAY
from datetime import datetime
import calendar
from dateutil.relativedelta import relativedelta


class HrLeaveRequest(models.Model):
    _inherit = 'hr.leave'

    expected_leave = fields.Float(string="Expected Number Of leaves", compute='_compute_leaves_count', store=True)
    # duration_display = fields.Float()
    is_payed_in_advance = fields.Boolean(string="Is Payed in Advance")
    compute_full_days = fields.Boolean(string="Include Weekend Days", default=False)

    country_ids = fields.Many2many("res.country")
    flight_details_ids = fields.One2many("flight.details", 'leave_id')

    flight_tickets_unit = fields.Char(string="Flight Tickets Unit / Brand")
    flight_tickets_host = fields.Char(string="Flight Tickets Host")

    hotel_unit = fields.Char(string="Hotel Unit / Brand")
    hotel_host = fields.Char(string="Hotel Host")

    airport_pickup_unit = fields.Char(string="Airport Pickup/Drop Unit / Brand")
    airport_pickup_host = fields.Char(string="Airport Pickup/Drop Host")

    transportation_unit = fields.Char(string="Transportations Unit / Brand")
    transportation_host = fields.Char(string="Transportations Host")

    event_fees_unit = fields.Char(string="Event Fee(s) Unit / Brand")
    event_fees_host = fields.Char(string="Event Fee(s) Host")

    others_unit = fields.Char(string="Others Unit / Brand")
    others_host = fields.Char(string="Others Host")

    @api.depends('holiday_status_id', 'employee_id', 'request_date_to')
    def _compute_leaves_count(self):
        for rec in self:
            if rec.holiday_status_id.requires_allocation:
                diff = 0
                allocation_obj = self.env['hr.employee'].search([('id', '=', rec.employee_id.id)], limit=1)
                allocation_days = allocation_obj.remaining_leaves
                if rec.request_date_to:
                    diff = (rec.request_date_to - fields.Date.today()).days
                if allocation_days and diff:
                    rec.expected_leave = allocation_days + diff * (30 / 365)
                elif allocation_days:
                    rec.expected_leave = allocation_days
                elif diff:
                    rec.expected_leave = diff * (30 / 365)
            else:
                rec.expected_leave = 0

    # @api.constrains('state', 'number_of_days', 'holiday_status_id')
    # def _check_holidays(self):
    #     for holiday in self:
    #         if holiday.holiday_type != 'employee' or not holiday.employee_id:
    #             continue
    #         if holiday.number_of_days_display > holiday.expected_leave:
    #             raise ValidationError(_('The number of remaining leaves is not sufficient for this leave type.\n'
    #                                     'Please also check the leaves waiting for validation.'))

    def get_workday(self, index):
        values = [('0', 'Monday'),
                  ('1', 'Tuesday'),
                  ('2', 'Wednesday'),
                  ('3', 'Thursday'),
                  ('4', 'Friday'),
                  ('5', 'Saturday'),
                  ('6', 'Sunday')]
        return str(dict(values)[(index)])

    def get_week_ends_and_working_days(self, working_schedule=False):
        weekends = []
        working_days = []
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        if working_schedule:
            for attend_day in working_schedule[0].attendance_ids:
                if self.get_workday(attend_day.dayofweek) not in working_days:
                    working_days.append(self.get_workday(attend_day.dayofweek))
            weekends = list(set(days) - set(working_days))
        return [weekends, working_days]

    def _check_weekend_days(self, from_date, to_date, weekend_days):
        weekly_off_count = 0
        weekly_start_calc_dt = from_date
        while weekly_start_calc_dt <= to_date:
            if self.get_workday(str(weekly_start_calc_dt.weekday())) in weekend_days:
                weekly_off_count += 1
            weekly_start_calc_dt = weekly_start_calc_dt + relativedelta(days=1)
        return weekly_off_count

    # def _get_number_of_days_details(self, date_from, date_to, employee_id, compute_leaves=False):
    #     """ Returns a float equals to the timedelta between two dates given as string."""
    #     employee = self.env['hr.employee'].browse(employee_id)
    #     working_schedule = employee.resource_calendar_id
    #     week_end_days_count = self._check_weekend_days(date_from, date_to,
    #                                                    self.get_week_ends_and_working_days(
    #                                                        working_schedule=working_schedule)[0])
    #     if employee_id and compute_leaves == True:
    #         employee = self.env['hr.employee'].browse(employee_id)
    #         return employee._get_work_days_data_batch(date_from, date_to)[employee.id]['days'] + week_end_days_count
    #     if employee_id and compute_leaves == False:
    #         employee = self.env['hr.employee'].browse(employee_id)
    #         return employee._get_work_days_data_batch(date_from, date_to)[employee.id]['days']
    #     today_hours = self.env.company.resource_calendar_id.get_work_hours_count(
    #         datetime.combine(date_from.date(), time.min), datetime.combine(date_from.date(), time.max), False)
    #     hours = self.env.company.resource_calendar_id.get_work_hours_count(date_from, date_to)
    #     return {'days': hours / (today_hours or HOURS_PER_DAY), 'hours': hours}
    #
    # @api.depends('date_from', 'date_to', 'employee_id', 'compute_full_days')
    # @api.onchange('date_from', 'date_to', 'employee_id', 'compute_full_days')
    # def _onchange_leave_dates(self):
    #     for rec in self:
    #         if rec.employee_id and rec.date_from and rec.date_to and rec.compute_full_days:
    #             rec.number_of_days = self._get_number_of_days_details(rec.date_from, rec.date_to, rec.employee_id.id,
    #                                                                   compute_leaves=True)
    #         elif rec.employee_id and rec.date_from and rec.date_to:
    #             rec.number_of_days = self._get_number_of_days_details(rec.date_from, rec.date_to, rec.employee_id.id,
    #                                                                   compute_leaves=False)

    # else:
    #     rec.number_of_days = 0.0

    def calculate_sick_leave_deduction(self, role_number, current_month_days, previous_month_days):
        """Calculates the sick leave deduction for the current month, considering multiple rules.

        Args:
            role_number: The role number of the employee.
            current_month_days: The number of sick leave days taken in the current month.
            previous_month_days: The number of sick leave days taken in the previous month.

        Returns:
            A list of tuples, where each tuple contains the number of days and the corresponding deduction percentage.
        """
        total_sick_leave_days = current_month_days + previous_month_days
        if role_number == 1:
            remaining_days = current_month_days
            deductions = []
            rules = [(15, 0), (10, 25), (10, 50), (10, 75), (float('inf'), 100)]
            for rule_days, deduction_percentage in rules:
                days_in_rule = min(remaining_days, rule_days)
                deductions.append((days_in_rule, deduction_percentage))
                remaining_days -= days_in_rule
            return deductions

        elif 2 <= role_number <= 5:
            deductions = []
            rules = [(15, 0), (10, 25), (10, 50), (10, 75), (float('inf'), 100)]

            for rule_days, deduction_percentage in rules:
                days_in_rule = min(total_sick_leave_days, rule_days)
                deductions.append((days_in_rule, deduction_percentage))
                total_sick_leave_days -= days_in_rule

            return deductions
        else:
            # Handle other role numbers or default behavior
            return [(current_month_days, 0)]  # No deduction for other roles

    def get_sick_leave_days(self, date_from, date_to):
        for rec in self:
            total_sick_leave_days = 0.0
            if rec.date_from and rec.date_to and rec.employee_id:
                sick_leave_recs = self.env['hr.leave'].search([
                    ('employee_id', '=', rec.employee_id.id),
                    ('holiday_status_id.sick_leave', '=', True),
                    ('state', 'in', ['validate']),
                    '|',
                    '|',
                    '&',
                    ('date_from', '<=', date_from), ('date_to', '>=', date_from),
                    '&',
                    ('date_from', '<=', date_to), ('date_to', '>=', date_to),
                    '|',
                    '&',
                    ('date_from', '>=', date_from), ('date_to', '<=', date_to),
                    '&',
                    ('date_from', '<=', date_from), ('date_to', '>=', date_to),
                ])
                if sick_leave_recs:
                    for leave in sick_leave_recs:
                        total_sick_leave_days += leave.number_of_days
            return total_sick_leave_days

    def action_approve(self):
        res = super(HrLeaveRequest, self).action_approve()
        for item in self:
            days_list = []
            d1 = datetime.strptime(str(item.request_date_from), '%Y-%m-%d')
            d2 = datetime.strptime(str(item.request_date_to), '%Y-%m-%d')
            end_date = datetime(d1.year, d1.month, calendar.mdays[d1.month]).date()

            if d2.date() > end_date:
                start_date = datetime(d2.year, d2.month, 1).date()
                first_leave_days = (end_date - d1.date()).days + 1
                second_leave_days = (d2.date() - start_date).days + 1
                days_list.append({d1.date(): first_leave_days})
                days_list.append({start_date: second_leave_days})

            elif d2.date() < end_date:
                days_list.append({d1.date(): (d2.date() - d1.date()).days + 1})

            first_day_in_year = datetime.now().date().replace(month=1, day=1)
            last_day_in_year = datetime.now().date().replace(month=12, day=31)
            total_sick_leave_days = self.get_sick_leave_days(first_day_in_year, last_day_in_year)

            role_number = 1
            for emp_sick in item.employee_id.employee_sick_leave_ids:
                role_number = 5 if emp_sick.rule_5 > 0.0 else 4 if emp_sick.rule_4 > 0.0 else 3 if emp_sick.rule_3 > 0.0 else 2 if emp_sick.rule_2 > 0.0 else 1

            total_deduction = self.calculate_sick_leave_deduction(role_number, item.number_of_days,
                                                                  total_sick_leave_days)
            for days in days_list:
                for date, index in days.items():
                    deductions = self.calculate_sick_leave_deduction(role_number, index, total_sick_leave_days)

                    previous_rule = self.env['employee.sick.leave'].search([('employee_id', '=', item.employee_id.id)],
                                                                           order="id desc")
                    if previous_rule:
                        total_rule_1, total_rule_2, total_rule_3, total_rule_4, total_rule_5 = 0, 0, 0, 0, 0
                        for rule in previous_rule:
                            total_rule_1 += rule.rule_1
                            total_rule_2 += rule.rule_2
                            total_rule_3 += rule.rule_3
                            total_rule_4 += rule.rule_4
                            total_rule_5 += rule.rule_5

                        item.employee_id.employee_sick_leave_ids = [(0, 0, {
                            'date': date,
                            'rule_1': abs(total_rule_1 - total_deduction[0][0]),
                            'rule_2': abs(total_rule_2 - total_deduction[1][0]),
                            'rule_3': abs(total_rule_3 - total_deduction[2][0]),
                            'rule_4': abs(total_rule_4 - total_deduction[3][0]),
                            'rule_5': abs(total_rule_5 - total_deduction[4][0]),
                        })]
                    else:
                        item.employee_id.employee_sick_leave_ids = [(0, 0, {
                            'date': date,
                            'rule_1': deductions[0][0],
                            'rule_2': deductions[1][0],
                            'rule_3': deductions[2][0],
                            'rule_4': deductions[3][0],
                            'rule_5': deductions[4][0],
                        })]
        return res


class FlightDetails(models.Model):
    _name = 'flight.details'

    leave_id = fields.Many2one('hr.leave')
    date_from = fields.Date()
    date_to = fields.Date()
    airlines = fields.Char()
    flight_no = fields.Char()
    ticket_class = fields.Char()
    departure_date_time = fields.Datetime()
    arrival_date_time = fields.Datetime()


class HolidaysAllocationInherit(models.Model):
    _inherit = 'hr.leave.allocation'

    _sql_constraints = [
        ('type_value',
         "CHECK( (holiday_type='employee' AND employee_id IS NOT NULL) or "
         "(holiday_type='category' AND category_id IS NOT NULL) or "
         "(holiday_type='department' AND department_id IS NOT NULL) or "
         "(holiday_type='company' AND mode_company_id IS NOT NULL))",
         "The employee, department, company or employee category of this request is missing. Please make sure that your user login is linked to an employee."),
        ('duration_check', "CHECK ( 1=1 )", "The number of days must be greater than 0."),
        ('number_per_interval_check', "CHECK(number_per_interval > 0)",
         "The number per interval should be greater than 0"),
        ('interval_number_check', "CHECK(interval_number > 0)", "The interval number should be greater than 0"),
    ]
