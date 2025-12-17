# -*- coding: utf-8 -*-


from odoo import models, fields, api
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta


class EOSRecognitionIndemnity(models.Model):
    _name = 'eos.recognition.indemnity'
    _description = "End Of Service Recognition Indemnity"

    eos_employee_id = fields.Many2one('eos.recognition', string="Eos Employee")
    employee_id = fields.Many2one('hr.employee', string="Employee")
    contract_id = fields.Many2one('hr.contract', string="Contract", related='employee_id.contract_id', readonly=1)
    contract_start_date = fields.Date(string="Contract Start Date", related='employee_id.contract_id.date_start',
                                      readonly=1)
    period = fields.Char(string="Period", compute='get_period')
    indemnity = fields.Float(string="Indemnity", related='employee_id.indemnity_liability', readonly=1)
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    employee_wage = fields.Monetary(string='Total Salary', related='employee_id.contract_id.total_amount')
    leave_balance = fields.Float(related='employee_id.leave_balance', string='Leave Provision', digits=(12, 3))
    total_leave_provision = fields.Float(related='employee_id.total_leave_provision', string='Net Leave Days',
                                         digits=(12, 3))

    @api.depends('employee_id', 'employee_id.contract_id', 'employee_id.contract_id.date_start')
    def get_period(self):
        leaves_obj = self.env['hr.leave']
        for rec in self:
            rec.period = ''
            if rec.contract_start_date:
                first_date = rec.contract_start_date
                current_date = date.today()
                leave = sum(leaves_obj.search([('holiday_status_id.calculate_in_ter_resi', '=', True),
                                               ('state', '=', 'validate'),
                                               ('employee_id', '=', rec.employee_id.id)]).mapped('number_of_days'))
                if leave:
                    current_date -= timedelta(days=leave)
                diff = relativedelta(current_date, first_date)
                years = diff.years
                months = diff.months
                days = diff.days
                rec.period = '{} years {} months {} days'.format(years, months, days)
