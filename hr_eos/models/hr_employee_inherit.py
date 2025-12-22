# coding: utf-8
from dateutil.relativedelta import relativedelta
from collections import defaultdict
from datetime import datetime, timedelta, date
from pytz import utc

from odoo import api, fields, models, _
from odoo.tools import float_utils

# This will generate 16th of days
ROUNDING_FACTOR = 16


class HrEmployeeInherit(models.Model):
    _inherit = 'hr.employee'

    all_leaves_count = fields.Float(string="Number of Leaves")
    all_leaves_from_report = fields.Float(string="Number of Leaves")
    annual_leave_compute_type = fields.Selection(string="Annual Leave Compute Type",
                                                 selection=[('all_leaves', 'All Leaves Computed'),
                                                            ('some_leaves', 'Some Leaves Computed')])
    sick_leave_remaining_days = fields.Float(string="Sick Leave Remaining Days")

    termination_amount = fields.Float(string="Termination Amount", digits=(12, 3), compute='get_termination_amount')
    resignation_amount = fields.Float(string="Resignation Amount", digits=(12, 3), compute='get_resignation_amount')
    rule_id = fields.Many2one('hr.config.rules', string="Rule Name")
    leaves_count = fields.Float('Number of Time Off', compute='_compute_remaining_leaves')
    indemnity_liability = fields.Float(string="Indemnity Liability")

    leave_balance = fields.Float(compute='get_leave_balance', string='Leave Provision', digits=(12, 3))
    related_leave_balance = fields.Float(related='leave_balance', string='Leave Provision', digits=(12, 3))
    total_leave_provision = fields.Float(string='Net Leave Days', digits=(12, 3))
    remaining_leave_provision = fields.Float(string='Remaining Leave Provision', digits=(12, 3))
    def get_resignation_amount(self):
        for item in self:
            item.resignation_amount = 0.0
            resignation_request = self.env['hr.resignation.request'].search([('employee_id', '=', item.id),
                                                                             ('state', '=', 'resigned')],
                                                                            order='id asc', limit=1)
            if resignation_request:
                resignation_request.get_employee_resignation()
            else:
                hr_contract_obj = item.contract_id
                resignation_rule_obj = item.contract_id.rule_id
                if hr_contract_obj:
                    total_period = item.get_period(item.id)
                    total_years = round(
                        total_period['years'] + total_period['months'] / 12 + (total_period['days'] / 26) / 12, 3)
                    salary_per_day = hr_contract_obj.eos_amount / 26
                    resignation_amount = 0.0
                    if resignation_rule_obj:
                        for resignation in resignation_rule_obj.resignation_rule_ids:
                            if resignation.resignation_rang_start <= total_years < resignation.resignation_rang_end:
                                if total_years <= 10:
                                    # 5 YEARS
                                    days_per_year = resignation_rule_obj.resignation_rule_ids[
                                        0].resignation_days_per_year
                                    first_5_years = (((days_per_year * resignation_rule_obj.resignation_rule_ids[
                                        0].resignation_rang_end) * salary_per_day) * resignation.deduction_amount)

                                    # After 5 Years
                                    first_years_ends = resignation_rule_obj.resignation_rule_ids[0].resignation_rang_end
                                    after_5years = resignation_rule_obj.resignation_rule_ids[1].resignation_rang_end
                                    remaining_after_5 = after_5years if total_years - first_years_ends > after_5years else total_years - first_years_ends
                                    resignation_amount = first_5_years + (
                                            (resignation.resignation_days_per_year * remaining_after_5)
                                            * salary_per_day) * resignation.deduction_amount

                                elif total_years > 10:
                                    # 5 YEARS
                                    days_per_5_year = resignation_rule_obj.resignation_rule_ids[
                                        0].resignation_days_per_year
                                    res_years_rang_end = resignation_rule_obj.resignation_rule_ids[
                                        0].resignation_rang_end
                                    first_5_years = (((days_per_5_year * res_years_rang_end) * salary_per_day)
                                                     * resignation.deduction_amount)

                                    # After 5 Years
                                    first_years_ends = resignation_rule_obj.resignation_rule_ids[0].resignation_rang_end
                                    after_5years = resignation_rule_obj.resignation_rule_ids[1].resignation_rang_end
                                    remaining_after_5 = after_5years if total_years - first_years_ends > after_5years else total_years - first_years_ends
                                    days_per_after_5_year = resignation_rule_obj.resignation_rule_ids[
                                        1].resignation_days_per_year
                                    after_5_years = (((days_per_after_5_year * remaining_after_5) * salary_per_day)
                                                     * resignation.deduction_amount)

                                    # Remaining YEARS
                                    remaining_years = total_years - ((resignation_rule_obj.resignation_rule_ids[
                                                                          0].resignation_rang_end) + remaining_after_5)
                                    resignation_amount = first_5_years + after_5_years + \
                                                         ((resignation.resignation_days_per_year * remaining_years)
                                                          * salary_per_day) * resignation.deduction_amount
                    item.resignation_amount = resignation_amount

    def get_termination_amount(self):
        for item in self:
            item.termination_amount = 0.0
            termination_request = self.env['hr.termination.request'].search([('employee_id', '=', item.id),
                                                                             ('state', '=', 'terminated')],
                                                                            order='id asc', limit=1)
            if termination_request:
                termination_request.get_employee_termination()
            else:
                termination_rule_obj = item.contract_id.rule_id
                hr_contract_obj = item.contract_id
                if hr_contract_obj:
                    total_period = item.get_period(item.id)
                    total_years = round(
                        total_period['years'] + total_period['months'] / 12 + (total_period['days'] / 26) / 12, 3)
                    salary_per_day = hr_contract_obj.eos_amount / 26
                    termination_amount = 0.0
                    if termination_rule_obj:
                        for termination in termination_rule_obj.terminations_rule_ids:
                            if termination.termination_rang_start <= total_years < termination.termination_rang_end:
                                if total_years <= 5:
                                    termination_amount = ((termination.termination_days_per_year * total_years)
                                                          * salary_per_day) * termination.deduction_amount
                                if total_years > 5:
                                    # 5 YEARS
                                    deduction_amount = termination_rule_obj.terminations_rule_ids.search(
                                        [('termination_rang_start', '>=', 0),
                                         ('termination_rang_end', '<=', 5),
                                         ('termination_config_id', '=', hr_contract_obj.rule_id.id)]).deduction_amount
                                    days_per_year = termination_rule_obj.terminations_rule_ids.search(
                                        [('termination_rang_start', '>=', 0),
                                         ('termination_rang_end', '<=', 5),
                                         ('termination_config_id', '=',
                                          hr_contract_obj.rule_id.id)]).termination_days_per_year
                                    first_5_years = (((days_per_year * 5) * salary_per_day) * deduction_amount)

                                    # Remaining YEARS
                                    remaining_years = total_years - 5
                                    termination_amount = first_5_years + \
                                                         ((termination.termination_days_per_year * remaining_years)
                                                          * salary_per_day) * termination.deduction_amount
                    item.termination_amount = termination_amount

    def get_period(self, employee_id):
        leaves_obj = self.env['hr.leave']
        if self.contract_id.date_start:
            first_date = self.contract_id.date_start
            current_date = date.today()
            leave = sum(leaves_obj.search([('holiday_status_id.calculate_in_ter_resi', '=', True),
                                           ('state', '=', 'validate'),
                                           ('employee_id', '=', self.id)]).mapped('number_of_days'))
            if leave:
                current_date -= timedelta(days=leave)
            diff = relativedelta(current_date, first_date)
            years = diff.years
            months = diff.months
            days = diff.days
            return {'years': years, 'months': months, 'days': days}

    def get_leave_balance(self):
        for line in self:
            # defaults
            line.leave_balance = 0.0
            line.total_leave_provision = 0.0
            line.remaining_leave_provision = 0.0

            if not line.contract_id:
                continue
            salary_per_day = 0.0
            try:
                salary_per_day = (line.contract_id.total_amount or 0.0) / 26.0
            except Exception:
                salary_per_day = 0.0

            allocations = self.env['hr.leave.allocation'].search([
                ('employee_id', '=', line.id),
                ('state', '=', 'validate'),
                ('holiday_status_id.annual_leave', '=', True),
            ])

            total_number_of_days = sum(allocations.mapped('number_of_days_display')) if allocations else 0.0
            if not total_number_of_days:
                total_number_of_days = sum(allocations.mapped('number_of_days'))

            line.total_leave_provision = total_number_of_days

            taken_leaves = self.env['hr.leave'].search([
                ('employee_id', '=', line.id),
                ('state', '=', 'validate'),
                ('holiday_status_id.annual_leave', '=', True),
            ])

            taken_days = sum(taken_leaves.mapped('number_of_days')) if taken_leaves else 0.0

            # compute remaining and monetary balance
            line.remaining_leave_provision = total_number_of_days - taken_days
            if line.remaining_leave_provision < 0:
                line.remaining_leave_provision = 0.0

            line.leave_balance = (total_number_of_days - taken_days) * salary_per_day if salary_per_day else 0.0

    @api.model
    def get_employee_annual_leave(self):
        for rec in self.env['hr.employee'].search([]):
            contract_obj = self.env['hr.contract'].search([('id', '=', rec.contract_id.id), ('state', '=', 'open')],
                                                          limit=1)
            rec.all_leaves_count += (contract_obj.annual_leave_per_day / 365)

    def get_work_days_data(self, from_datetime, to_datetime, compute_leaves=True, calendar=None, domain=None):
        """
            By default the resource calendar is used, but it can be
            changed using the `calendar` argument.

            `domain` is used in order to recognise the leaves to take,
            None means default value ('time_type', '=', 'leave')

            Returns a dict {'days': n, 'hours': h} containing the
            quantity of working time expressed as days and as hours.
        """
        resource = self.resource_id
        calendar = calendar or self.resource_calendar_id

        # naive datetimes are made explicit in UTC
        if not from_datetime.tzinfo:
            from_datetime = from_datetime.replace(tzinfo=utc)
        if not to_datetime.tzinfo:
            to_datetime = to_datetime.replace(tzinfo=utc)

        # total hours per day: retrieve attendances with one extra day margin,
        # in order to compute the total hours on the first and last days
        from_full = from_datetime - timedelta(days=1)
        to_full = to_datetime + timedelta(days=1)
        intervals = calendar._attendance_intervals_batch(from_full, to_full, resource)
        day_total = defaultdict(float)
        for start, stop, meta in intervals:
            day_total[start.date()] += (stop - start).total_seconds() / 3600

        # actual hours per day
        if compute_leaves:
            intervals = calendar._work_intervals(from_datetime, to_datetime, resource, domain)
        else:
            intervals = calendar._attendance_intervals_batch(from_datetime, to_datetime, resource)
        day_hours = defaultdict(float)
        for start, stop, meta in intervals:
            day_hours[start.date()] += (stop - start).total_seconds() / 3600

        # compute number of days as quarters
        days = sum(
            float_utils.round(ROUNDING_FACTOR * day_hours[day] / day_total[day]) / ROUNDING_FACTOR
            for day in day_hours
        )
        return {
            'days': days,
            'hours': sum(day_hours.values()),
        }

    @api.model
    def get_employee_termination_and_resignation_amount(self):
        employee_obj = self.env['hr.employee'].search([])
        rule_obj = self.env['hr.config.rules'].search([])
        if rule_obj:
            rule_obj = self.env['hr.config.rules'].search([])[0]
        for rec in employee_obj:
            hr_contract_objs = self.env['hr.contract'].search(
                [('employee_id', '=', rec.id), ('state', 'not in', ['close', 'cancel'])])
            for hr_contract_obj in hr_contract_objs:
                if hr_contract_obj:
                    contract_start_year = (hr_contract_obj.date_start).year
                    contract_start_month = (hr_contract_obj.date_start).month
                    current_year = datetime.now().year
                    current_month = datetime.now().month
                    diff_years = current_year - contract_start_year
                    diff_month = current_month - contract_start_month
                    diff_years += diff_month / 12
                    salary_per_day = hr_contract_obj.eos_amount / 26
                    total = 0
                    diff = 0
                    total_regis = 0
                    if rule_obj:
                        for termination in rule_obj.terminations_rule_ids:
                            if termination.termination_rang_start <= diff_years < termination.termination_rang_end:
                                newdiff = diff_years - diff
                                second_rule_value = (
                                                            termination.termination_days_per_year * newdiff * salary_per_day) * termination.deduction_amount
                                second_rule_value += total

                                hr_contract_obj.employee_id.update({'termination_amount': second_rule_value})
                                # rec.state = 'terminated'
                            else:
                                diff += (termination.termination_rang_end - termination.termination_rang_start)
                                diff2 = (termination.termination_rang_end - termination.termination_rang_start)
                                total += (
                                                termination.termination_days_per_year * diff2 * salary_per_day) * termination.deduction_amount
                    if rule_obj:
                        counter = 0
                        diff_regis22 = 0
                        for resignation in rule_obj.resignation_rule_ids:
                            if resignation.resignation_rang_start <= diff_years < resignation.resignation_rang_end:

                                newdiff = diff_years - diff_regis22
                                second_regis_value = (resignation.resignation_days_per_year * newdiff)
                                second_regis_value += total_regis
                                final_regis_value = second_regis_value * salary_per_day * resignation.deduction_amount
                                hr_contract_obj.employee_id.update({'resignation_amount': final_regis_value})
                                # rec.state = 'resigned'
                                break
                            else:
                                if counter > 0:
                                    diff_regis = resignation.resignation_rang_end
                                    diff_regis2 = resignation.resignation_rang_end
                                    diff_regis22 += resignation.resignation_rang_end
                                    total_regis += (resignation.resignation_days_per_year * diff_regis)

                                else:
                                    counter += 1

    @api.model
    def get_employee_indemnity_liability(self):
        for rec in self.env['hr.employee'].search([]):
            if rec.contract_id:
                worked_months = 0.0
                contract_start = rec.contract_id.date_start
                salary_per_day = rec.contract_id.eos_amount / 26

                # Get related termination request
                related_termination_request = self.env['hr.termination.request'].search([('employee_id', '=', rec.id)],
                                                                                        order='last_date desc', limit=1)
                if related_termination_request:
                    termination_date = related_termination_request.last_date

                    # Remove leave from calculation
                    leave = sum(self.env['hr.leave'].search([('holiday_status_id.calculate_in_ter_resi', '=', True),
                                                             ('state', '=', 'validate'),
                                                             ('employee_id', '=', rec.id)]).mapped('number_of_days'))
                    if leave:
                        termination_date -= timedelta(days=leave)

                    diff = relativedelta(termination_date, contract_start)
                    years = diff.years
                    months = diff.months
                    days = diff.days

                    termination_year = related_termination_request.last_date.year
                    diff_years = termination_year - rec.contract_id.date_start.year

                    if related_termination_request.rule_id:
                        if years > 0:
                            worked_months = 12 * years
                        if months:
                            worked_months += months

                        for termination in related_termination_request.rule_id.terminations_rule_ids:
                            if termination.termination_rang_start <= diff_years < termination.termination_rang_end:
                                if days:
                                    worked_months += (termination.termination_days_per_year / 12) / 30 * days
                                amount = (termination.termination_days_per_year / 12) * worked_months * salary_per_day
                                rec.contract_id.employee_id.update({'indemnity_liability': amount})


class HrEmployeesPublic(models.Model):
    _inherit = 'hr.employee.public'

    all_leaves_count = fields.Float(string="Number of Leaves")
    all_leaves_from_report = fields.Float(string="Number of Leaves")
    annual_leave_compute_type = fields.Selection(string="Annual Leave Compute Type",
                                                 selection=[('all_leaves', 'All Leaves Computed'),
                                                            ('some_leaves', 'Some Leaves Computed')])
    sick_leave_remaining_days = fields.Float(string="Sick Leave Remaining Days")

    termination_amount = fields.Float(string="Termination Amount", digits=(12, 3), compute='get_termination_amount')
    resignation_amount = fields.Float(string="Resignation Amount", digits=(12, 3), compute='get_resignation_amount')
    rule_id = fields.Many2one('hr.config.rules', string="Rule Name")
    leaves_count = fields.Float('Number of Time Off', compute='_compute_remaining_leaves')
    indemnity_liability = fields.Float(string="Indemnity Liability")

    total_leave_provision = fields.Float(string='Net Leave Days', digits=(12, 3))
    remaining_leave_provision = fields.Float(string='Remaining Leave Provision', digits=(12, 3))


class Contract(models.Model):
    _inherit = 'hr.contract'

    rule_id = fields.Many2one('hr.config.rules', string="Indemnity Rule Name")
    eos_amount = fields.Float(compute='get_eos_amount')
    pin = fields.Char(related='employee_id.pin', string='Employee PIN', store=True, readonly=True)
    e_insurance_number = fields.Char(string='Employee Insurance Number')


    def get_eos_amount(self):
        eos_amount = 0.0
        for item in self:
            if self.env['ir.config_parameter'].sudo().get_param('eos_with_wage'):
                eos_amount += item.wage
            if self.env['ir.config_parameter'].sudo().get_param('eos_with_allow1'):
                eos_amount += item.housing_allowance
            if self.env['ir.config_parameter'].sudo().get_param('eos_with_allow2'):
                eos_amount += item.transportation_allowance
            if self.env['ir.config_parameter'].sudo().get_param('eos_with_allow3'):
                eos_amount += item.other_allowances
            if self.env['ir.config_parameter'].sudo().get_param('eos_with_allow4'):
                eos_amount += item.food_allowance
            if self.env['ir.config_parameter'].sudo().get_param('eos_with_allow5'):
                eos_amount += item.fuel_allowance
            item.eos_amount = eos_amount
