# coding: utf-8
from odoo import models, fields, api, _
import datetime
from dateutil import relativedelta


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

    state = fields.Selection(string="State",
                             selection=[('draft', 'Draft'), ('terminated', 'Terminated'), ('canceled', 'Canceled')],
                             default='draft')
    employee_id = fields.Many2one('hr.employee', string="Employee", domaon=get_emp_with_contract)

    rule_id = fields.Many2one('hr.config.rules', string="Rule Name", related='employee_id.contract_id.rule_id',
                              readonly=1)
    notes = fields.Text(string="Notes")
    last_date = fields.Date(string="Last Date")

    his_notice_period = fields.Boolean()
    notice_period = fields.Integer(
        default=lambda self: self.env['ir.config_parameter'].sudo().get_param('max_notice_period'))

    def get_employee_termination(self):
        for rec in self:
            termination_rule_obj = rec.rule_id
            hr_contract_obj = rec.employee_id.contract_id
            notice_period_days = 0
            if hr_contract_obj:
                total_period = rec.employee_id.get_period(rec.employee_id)
                total_years = round(
                    total_period['years'] + total_period['months'] / 12 + (total_period['days'] / 26) / 12, 3)
                salary_per_day = hr_contract_obj.wage / 26
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

                            # if rec.employee_id.leave_balance > 0.0 and termination_amount > 0.0:
                            #     if rec.employee_id.related_leave_balance > 0.0:
                            #         termination_amount += rec.employee_id.related_leave_balance
                            #         rec.employee_id.update({'related_leave_balance': 0.0})

                            hr_contract_obj.employee_id.update({'termination_amount': termination_amount})
                            rec.state = 'terminated'

    def termination_cancel(self):
        for rec in self:
            rec.state = 'canceled'
