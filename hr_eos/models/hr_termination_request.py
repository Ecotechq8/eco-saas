# coding: utf-8
from odoo import models, fields, api, _
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta


class HrTerminationRequest(models.Model):
    _name = 'hr.termination.request'
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
        ('terminated', 'Terminated'), 
        ('rejected', 'Rejected'),
        ('canceled', 'Canceled')
    ],default='draft')

    def reject_button(self):
        for rec in self:
            rec.state = 'rejected'

    def hr_manager_approve(self):
        self.write({'state': 'terminated'})

    def employee_manager_approve(self):
        self.write({'state': 'emp_mang_submit'})


    employee_id = fields.Many2one('hr.employee', string="Employee", domaon=get_emp_with_contract)
    rule_id = fields.Many2one('hr.config.rules', string="Rule Name", related='employee_id.contract_id.rule_id',
                              readonly=1)
    notes = fields.Text(string="Notes")
    last_date = fields.Date(string="Last Date")
    number_of_day = fields.Float(string="", required=False, )
    number_of_year = fields.Float(string="", required=False, )
    percentage_value = fields.Float(string="", required=False, default=100, readonly=1)
    currency_id = fields.Many2one('res.currency', string='Currency', required=True, readonly=True,
                                  default=lambda self: self.env.company.currency_id.id)

    transferring_or_check_number = fields.Char(string='Transferring / Check Number')
    transferring_or_check_date = fields.Date(string='Transferring / Check Date')
    transferring_or_check_bank = fields.Many2one(comodel_name='res.bank', string='Transferring / Check Bank')

    notice_period = fields.Selection(selection=[('unpaid', 'UnPaid'), ('paid', 'Paid')])
    required_working_during_notice_period = fields.Selection(selection=[('no', 'No'), ('yes', 'Yes')])

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

    legal_affairs_statement = fields.Char()
    project_manager_notes = fields.Char()

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

    def get_employee_termination(self):
        for rec in self:
            termination_rule_obj = rec.rule_id
            hr_contract_obj = rec.employee_id.contract_id
            if hr_contract_obj:
                total_period = rec.employee_id.get_period(rec.employee_id)
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
                                     ('termination_rang_end', '<=', 5)]).deduction_amount
                                days_per_year = termination_rule_obj.terminations_rule_ids.search(
                                    [('termination_rang_start', '>=', 0),
                                     ('termination_rang_end', '<=', 5)]).termination_days_per_year
                                first_5_years = (((days_per_year * 5) * salary_per_day) * deduction_amount)

                                # Remaining YEARS
                                remaining_years = total_years - 5
                                termination_amount = first_5_years + \
                                                     ((termination.termination_days_per_year * remaining_years)
                                                      * salary_per_day) * termination.deduction_amount

                            hr_contract_obj.employee_id.update({'termination_amount': termination_amount})
                            rec.state = 'terminated'

    def termination_cancel(self):
        for rec in self:
            rec.state = 'canceled'

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
