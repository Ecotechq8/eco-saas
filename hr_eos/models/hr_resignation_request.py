# coding: utf-8
from odoo import models, fields, api, _
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta

from odoo.exceptions import AccessError, UserError, ValidationError, AccessDenied


class HrResignationRequest(models.Model):
    _name = 'hr.resignation.request'
    _rec_name = 'employee_id'

    def get_emp_with_contract(self):
        employees = []
        contract_objects = self.env['hr.contract'].sudo().search(
            [('employee_id', '!=', False), ('state', 'in', ['draft', 'open', 'pending'])])
        for contract in contract_objects:
            employees.append(contract.employee_id.id)
        return [('id', 'in', employees)]

    state = fields.Selection(string="State",selection=[
        ('draft', 'Draft'),
        ('emp_mang_submit', 'Manager Submit'),
        ('resigned', 'Resigned'),
        ('rejected', 'Rejected'), 
        ('canceled', 'Canceled')
    ],default='draft')

    def reject_button(self):
        for rec in self:
            rec.state = 'rejected'

    def hr_manager_approve(self):
        self.write({'state': 'resigned'})

    def employee_manager_approve(self):
        self.write({'state': 'emp_mang_submit'})


    employee_id = fields.Many2one('hr.employee', string="Employee", domain=get_emp_with_contract)
    rule_id = fields.Many2one('hr.config.rules', string="Rule Name", related='employee_id.contract_id.rule_id',
                              readonly=1)
    notes = fields.Text(string="Notes")
    last_date = fields.Date(string="Last Date")
    number_of_day = fields.Float(string="", required=False, )
    number_of_year = fields.Float(string="", required=False, )
    percentage_value = fields.Float(string="", required=False, )
    currency_id = fields.Many2one('res.currency', string='Currency', required=True, readonly=True,
                                  default=lambda self: self.env.company.currency_id.id)
    transferring_or_check_number = fields.Char(string='Transferring / Check Number')
    transferring_or_check_date = fields.Date(string='Transferring / Check Date')
    transferring_or_check_bank = fields.Many2one(comodel_name='res.bank', string='Transferring / Check Bank')

    @api.model
    def create_regfrom_portal(self, values):
        if not self.env.user.employee_id:
            raise AccessDenied()
        if not (values['last_date'] and values['request_notes']):
            return {
                'errors': _('All fields are required !')
            }
        values = {
            'employee_id': values.get('employee_id', self.env.user.employee_id.id),  # values['employee_id'],
            'last_date': values['last_date'],
            'notes': values['request_notes'],
        }
        tmp_resignation = self.env['hr.resignation.request'].sudo().new(values)
        values = tmp_resignation._convert_to_write(tmp_resignation._cache)
        myresignation = self.env['hr.resignation.request'].sudo().create(values)
        return {
            'id': myresignation.id
        }

    @api.onchange('last_date')
    @api.constrains('last_date')
    def onchange_get_num_of_year(self):
        for rec in self:
            hr_contract_obj = rec.employee_id.contract_id
            if hr_contract_obj:
                contract_start_days = hr_contract_obj.date_start
                termination_days = rec.last_date
                diff_dayes = termination_days - contract_start_days
                diff_years = diff_dayes.days / 365
                rec.number_of_year = round(diff_years, 1)
                rec.number_of_day = round(diff_dayes.days, 1)
                if rec.number_of_year < 3:
                    rec.percentage_value = 0.0
                elif 3 <= rec.number_of_year <= 5:
                    rec.percentage_value = 50
                elif 5 <= rec.number_of_year <= 10:
                    rec.percentage_value = 67
                elif rec.number_of_year > 10:
                    rec.percentage_value = 100

    def get_employee_resignation(self):
        for rec in self:
            hr_contract_obj = rec.employee_id.contract_id
            resignation_rule_obj = rec.rule_id
            if hr_contract_obj:
                total_period = rec.employee_id.get_period(rec.employee_id)
                total_years = round(
                    total_period['years'] + total_period['months'] / 12 + (total_period['days'] / 26) / 12, 3)
                # salary_per_day = hr_contract_obj.wage / 26
                salary_per_day = hr_contract_obj.eos_amount / 26
                resignation_amount = 0.0
                if resignation_rule_obj:
                    for resignation in resignation_rule_obj.resignation_rule_ids:
                        if resignation.resignation_rang_start <= total_years < resignation.resignation_rang_end:
                            if total_years <= 10:
                                # 5 YEARS
                                days_per_year = resignation_rule_obj.resignation_rule_ids[0].resignation_days_per_year
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
                                days_per_5_year = resignation_rule_obj.resignation_rule_ids[0].resignation_days_per_year
                                res_years_rang_end = resignation_rule_obj.resignation_rule_ids[0].resignation_rang_end
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

                        hr_contract_obj.employee_id.update({'resignation_amount': resignation_amount})
                        rec.state = 'resigned'

    def resignation_cancel(self):
        for rec in self:
            rec.state = 'canceled'

    period = fields.Char(string="Period", compute='get_period')

    @api.depends('employee_id', 'employee_id.contract_id', 'employee_id.contract_id.date_start')
    def get_period(self):
        leaves_obj = self.env['hr.leave']
        for rec in self:
            rec.period = ''
            if rec.employee_id.contract_id.date_start:
                first_date = rec.employee_id.contract_id.date_start
                leave = sum(leaves_obj.search([('holiday_status_id.calculate_in_ter_resi', '=', True),
                                               ('state', '=', 'validate'),
                                               ('employee_id', '=', rec.employee_id.id)]).mapped('number_of_days'))
                if leave:
                    rec.last_date -= timedelta(days=leave)
                diff = relativedelta(rec.last_date, first_date)
                years = diff.years
                months = diff.months
                days = diff.days
                rec.period = '{}-{}-{}'.format(years, months, days)

    contract_start_date = fields.Char(string="Contract Start Date", compute='get_contract_start_date')

    def get_contract_start_date(self):
        date = self.employee_id.contract_id.date_start
        self.contract_start_date = date.strftime('%Y') + '-' + date.strftime('%m') + '-' + date.strftime('%d')

    unpaid_leave_days = fields.Float(compute='get_unpaid_leave_balance')
    unpaid_leave_amount = fields.Float(compute='get_unpaid_leave_balance')

    def get_unpaid_leave_balance(self):
        for line in self:
            line.unpaid_leave_days, line.unpaid_leave_amount = 0.0, 0.0
            salary_per_day = line.employee_id.contract_id.total_amount / 26
            taken_leaves = self.env['hr.leave'].search([('employee_id', '=', line.employee_id.id),
                                                        ('state', '=', 'validate'),
                                                        ('holiday_status_id.is_unpiad_leave', '=', True)])
            if taken_leaves:
                line.unpaid_leave_days = sum(taken_leaves.mapped('number_of_days'))
                line.unpaid_leave_amount = (sum(taken_leaves.mapped('number_of_days'))) * salary_per_day

    annual_leave_days = fields.Float(related='employee_id.total_leave_provision', string='Annual Leave Days')
    annual_leave_amount = fields.Float(related='employee_id.leave_balance', string='Annual Leave Balance')
