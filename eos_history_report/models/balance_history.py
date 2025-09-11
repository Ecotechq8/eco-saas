from odoo import models, fields, api, _
from dateutil.relativedelta import relativedelta
from datetime import datetime
import calendar


class BalanceHistory(models.Model):
    _name = 'balance.history'
    _description = 'Leave Balance History'

    employee = fields.Many2one('hr.employee', string='Employee')
    joining_date = fields.Date(string='Joining Date')
    total_salary = fields.Float(string='Total Salary')
    date_from = fields.Date(string='Date From')
    date_to = fields.Date(string='Date To')
    eos_segment = fields.Many2one('hr.termination.rules', string='EOS Segmentation')
    leave_monthly = fields.Float(string='Leave Monthly')

    leave_monthly_value = fields.Float(string='Leave Monthly Value')

    opening_balance_leave_days = fields.Float()
    opening_balance_leave_amount = fields.Float()

    time_off_request_days = fields.Float()
    time_off_request_amount = fields.Float()

    opening_balance_eos_days = fields.Float()
    opening_balance_eos_amount = fields.Float()

    eos_allowance_days = fields.Float(string='EOS Allowance (Days)')
    eos_allowance_amount = fields.Float(string='EOS Allowance (Amount)')
    esb_paid_days = fields.Float()
    esb_paid_amount = fields.Float()

    ending_balance_leave_days = fields.Float()
    ending_balance_leave_amount = fields.Float()

    ending_balance_eos_days = fields.Float()
    ending_balance_eos_amount = fields.Float()

    def print_excel_report(self):
        data = {'ids': self.ids, 'model': self._name}
        report_action = self.env.ref('eos_history_report.balance_history_excel_report').report_action(self, data=data)
        report_action['close_on_report_download'] = True
        return report_action

    @api.model
    def create_balance_history(self):
        hr_config_rule = self.env['hr.config.rules'].search([], limit=1)
        contracts = self.env['hr.contract'].search([('state', '=', "open")])
        s = datetime.today() - relativedelta(months=1)
        for contract in contracts:
            yearly_amount = 0
            domain = [
                ("employee", '=', contract.employee_id.id),
                ('date_from', '=', s.replace(day=1, month=s.month)),
                ('date_to', '=', s.replace(day=calendar.monthrange(s.year, s.month)[1])),
            ]
            if not self.search(domain):
                balance_history_data = dict()
                day_amount = contract.total_amount / hr_config_rule.month_work_days
                delta = s.date() - contract.date_start
                years_num = delta.days / 365

                termination_rules = self.env['hr.termination.rules'].search([
                    ('termination_rang_start', "<=", years_num),
                    ('termination_rang_end', ">=", years_num)
                ], limit=1)
                if termination_rules:
                    yearly_amount = day_amount * termination_rules.termination_days_per_year
                    balance_history_data.update({
                        'eos_segment': termination_rules.id
                    })

                annual_leaves_per_month = self.env['hr.leave'].search([
                    ("employee_id", '=', contract.employee_id.id),
                    ('request_date_from', '<=', s.date()),
                    ('request_date_to', '>=', s.date()),
                    ('holiday_status_id.annual_leave', '=', True),
                    ('state', '=', 'validate')
                ])

                balance_history_data.update({
                    'employee': contract.employee_id.id,
                    'joining_date': contract.date_start,
                    'total_salary': contract.total_amount,
                    'date_from': s.replace(day=1),
                    'date_to': s.replace(day=calendar.monthrange(s.year, s.month)[1]),
                    'leave_monthly': contract.leave_monthly,
                    'leave_monthly_value': contract.leave_monthly_value,
                    'opening_balance_leave_days': contract.opening_balance_leave_days,
                    'opening_balance_leave_amount': contract.opening_balance_leave_amount,
                    'time_off_request_days': -sum(annual_leaves_per_month.mapped("number_of_days")),
                    'time_off_request_amount': sum(
                        annual_leaves_per_month.mapped("number_of_days")) * contract.day_value,
                    'ending_balance_leave_days': contract.opening_balance_leave_days + contract.leave_monthly - sum(
                        annual_leaves_per_month.mapped("number_of_days")),
                    'ending_balance_leave_amount': contract.opening_balance_leave_amount + contract.leave_monthly_value - (
                            sum(annual_leaves_per_month.mapped("number_of_days")) * contract.day_value),
                    'opening_balance_eos_days': contract.opening_balance_eos_days,
                    'opening_balance_eos_amount': contract.opening_balance_eos_amount,
                })

                daily_balance = yearly_amount / 365
                daily_balance * calendar.monthrange(s.year, s.month)[1]
                month_balance = yearly_amount / 12

                if self.env['ir.config_parameter'].sudo().get_param('eos_calculation_type') == "monthly":
                    balance_history_data.update({
                        "eos_allowance_amount": month_balance,  # قيمة
                        "eos_allowance_days": month_balance / contract.day_value if contract.day_value > 0 else 0,
                    })

                else:
                    daily_balance = (yearly_amount / 365) * calendar.monthrange(s.year, s.month)[1]
                    balance_history_data.update({
                        "eos_allowance_amount": daily_balance,  # قيمة
                        "eos_allowance_days": daily_balance / contract.day_value if contract.day_value > 0 else 0,
                    })

                resignation_req = self.env['hr.resignation.request'].search([
                    ('employee_id', '=', contract.employee_id.id),
                    ('state', '=', 'resigned'),
                ])

                if resignation_req:
                    balance_history_data.update({
                        'esb_paid_days': contract.opening_balance_eos_days + balance_history_data.get(
                            "eos_allowance_days", 0),
                        'esb_paid_amount': resignation_req.resignation_amount + resignation_req.other_allowance - resignation_req.other_deduction
                    })

                termination_req = self.env['hr.termination.request'].search([
                    ('employee_id', '=', contract.employee_id.id),
                    ('state', '=', 'terminated'),
                ])
                if termination_req:
                    balance_history_data.update({
                        'esb_paid_days': contract.opening_balance_eos_days + balance_history_data.get(
                            "eos_allowance_days", 0),
                        'esb_paid_amount': termination_req.termination_amount + termination_req.other_allowance - termination_req.other_deduction
                    })

                if balance_history_data.get("esb_paid_amount", 0) > 0:
                    balance_history_data.update({
                        'ending_balance_eos_days': 0,
                        'ending_balance_eos_amount': 0
                    })
                else:
                    balance_history_data.update({
                        'ending_balance_eos_days': contract.opening_balance_eos_days + balance_history_data.get(
                            "eos_allowance_days", 0),
                        'ending_balance_eos_amount': contract.opening_balance_eos_amount + balance_history_data.get(
                            "eos_allowance_amount", 0)
                    })

                self.create(balance_history_data)
