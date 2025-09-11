# coding: utf-8

from odoo import models, fields, api, _
from datetime import datetime, date, timedelta

from odoo.exceptions import AccessDenied


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

    state = fields.Selection(string="State",
                             selection=[('draft', 'Draft'), ('resigned', 'Resigned'), ('canceled', 'Canceled')],
                             default='draft')
    employee_id = fields.Many2one('hr.employee', string="Employee", domain=get_emp_with_contract)
    rule_id = fields.Many2one('hr.config.rules', string="Rule Name", related='employee_id.contract_id.rule_id',
                              readonly=1)
    notes = fields.Text(string="Notes")
    last_date = fields.Date(string="Last Date")
    his_notice_period = fields.Boolean()
    notice_period = fields.Integer(
        default=lambda self: self.env['ir.config_parameter'].sudo().get_param('max_notice_period'))

    @api.model
    def create_regfrom_rtal(self, values):
        if not self.env.user.employee_id:
            raise AccessDenied()
        user = self.env.user
        self = self.sudo()
        # and values['manager_id']
        if not (values['last_date'] and values['request_notes']):
            return {'errors': _('All fields are required !')}
        values = {
            'employee_id': values['employee_id'],
            'last_date': values['last_date'],
            'notes': values['request_notes'],
        }
        tmp_loan = self.env['hr.resignation.request'].sudo().new(values)
        # tmp_loan._compute_date_from_to()
        values = tmp_loan._convert_to_write(tmp_loan._cache)
        myloan = self.env['hr.resignation.request'].sudo().create(values)
        return {
            'id': myloan.id
        }

    def get_employee_resignation(self):
        for rec in self:
            hr_contract_obj = rec.employee_id.contract_id
            resignation_rule_obj = rec.rule_id
            if hr_contract_obj:
                total_period = rec.employee_id.get_period(rec.employee_id)
                total_years = round(
                    total_period['years'] + total_period['months'] / 12 + (total_period['days'] / 26) / 12, 3)
                salary_per_day = hr_contract_obj.wage / 26
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
