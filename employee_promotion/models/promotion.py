# -*- coding: utf-8 -*-


from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import date
# from pandas.tseries import offsets
from email.utils import formataddr


class EmployeePromotion(models.Model):
    _name = 'hr.promotion'
    _description = "Promotion"

    _inherit = ['mail.thread', 'mail.activity.mixin']

    @api.onchange('employee_id')
    def get_employee_company(self):
        for rec in self:
            rec.company_id = rec.employee_id.company_id.id

    housing_allowance = fields.Monetary(string='Housing Allowance', compute="_compute_contract_data", store=True)
    transportation_allowance = fields.Monetary(string='Transportation Allowance', compute="_compute_contract_data",
                                               store=True)
    other_allowances = fields.Monetary(string='Other Allowances', compute="_compute_contract_data", store=True)
    wage = fields.Monetary('Contract Wage', compute="_compute_contract_data", store=True)

    @api.depends('employee_id')
    def _compute_contract_data(self):
        for record in self:
            if record.employee_id:
                contract = self.env['hr.contract'].search([
                    ('employee_id', '=', record.employee_id.id),
                    ('state', '=', 'open')], limit=1)
                record.wage = contract.wage
                record.housing_allowance = contract.housing_allowance
                record.transportation_allowance = contract.transportation_allowance
                record.other_allowances = contract.other_allowances
            else:
                record.wage = 0
                record.housing_allowance = 0
                record.transportation_allowance = 0
                record.other_allowances = 0

    promotion_done = fields.Boolean(string='Promotion', default=False)
    name = fields.Char(string='Promotion', default='Promotion', track_visibility='onchange')
    comment = fields.Text(string='Comment', track_visibility='onchange')
    date = fields.Date(string='Date', required=True, default=lambda self: fields.Date.today(),
                       track_visibility='onchange')
    employee_id = fields.Many2one('hr.employee', string='Employee', track_visibility='onchange')
    manager_id = fields.Many2one('hr.employee', string='Manager', track_visibility='onchange', readonly=True)
    new_manager_id = fields.Many2one('hr.employee', string='Direct Manager', track_visibility='onchange')
    department_id = fields.Many2one('hr.department', 'Department', track_visibility='onchange', readonly=True)
    new_department_id = fields.Many2one('hr.department', 'Department', track_visibility='onchange')
    job_id = fields.Many2one('hr.job', 'Job Position', track_visibility='onchange', readonly=True)
    contract_id = fields.Many2one('hr.contract', readonly=True, string="Contract", track_visibility='onchange')
    new_contract_id = fields.Many2one('hr.contract', string="Contract", track_visibility='onchange')
    coach_id = fields.Many2one('hr.employee', 'Coach', track_visibility='onchange', readonly=True)
    new_coach_id = fields.Many2one('hr.employee', 'Coach', track_visibility='onchange')
    new_job_id = fields.Many2one('hr.job', 'Job Position', track_visibility='onchange')
    company_id = fields.Many2one('res.company', track_visibility='onchange')
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', store=True)
    state = fields.Selection([('new', 'New'), ('requested', 'Promotion Requested'),
                              ('approved', 'Approved'), ('cancel', 'Cancelled')], string='Status', readonly=True,
                             copy=False, index=True, default='new', track_visibility='onchange')
    is_regular = fields.Boolean(string='Regular User', default=lambda self: True if self.env.user.has_group(
        'manager_security.hr_regular_employee') else False)
    increase_types = fields.Selection([('amount', 'Amount'), ('percent', 'Percent'),
                                       ('adj', 'Salary Adjustment')], string='Increase Type')
    inc_amount = fields.Monetary(string='Amount')
    inc_housing_allowance = fields.Monetary(string='Housing Allowance Amount')
    inc_transportation_allowance = fields.Monetary(string='Transportation allowance Amount')
    inc_other_allowances = fields.Monetary(string='Other Allowances Amount')

    inc_percent = fields.Float(string='Percent')
    inc_housing_allowance_percent = fields.Float(string='Housing Allowance Percent')
    inc_transportation_allowance_percent = fields.Float(string='Transportation allowance Percent')
    inc_other_allowances_percent = fields.Float(string='Other Allowances Percent')

    gross_salary = fields.Monetary('Gross Salary')
    old_gross_salary = fields.Monetary('Previous Gross Salary')

    new_housing_allowance = fields.Monetary('New Housing  Allowance')
    old_housing_allowance = fields.Monetary('Previous Housing  Allowance')

    new_transportation_allowance = fields.Monetary('New Transportation Allowance')
    old_transportation_allowance = fields.Monetary('Previous Transportation Allowance')

    new_other_allowances = fields.Monetary('New Other Alowances')
    old_other_allowances = fields.Monetary('Previous Other Alowances')

    @api.onchange('increase_types')
    def get_gross_salary(self):
        for rec in self:
            rec.gross_salary = 0
            if rec.increase_types == 'adj':
                rec.gross_salary = rec.employee_id.contract_id.wage

    @api.onchange('employee_id', 'date')
    @api.constrains('employee_id', 'date')
    def get_employee_date(self):
        self.department_id = self.employee_id.department_id.id
        self.manager_id = self.department_id.manager_id.id
        self.job_id = self.employee_id.job_id.id

    @api.onchange('is_regular')
    def get_department_domain(self):
        for rec in self:
            if rec.is_regular == True:
                emp = self.env['hr.employee'].search([('user_id', '=', self.env.uid)])
                rec.new_department_id = emp.department_id.id
            else:
                domain = {'domain': {'new_department_id': [('id', '!=', False)]}}
                return domain

    def button_promotion_request(self):
        self.state = 'requested'

    def button_approve_request(self):
        for rec in self:
            rec.state = 'approved'
            if rec.increase_types == 'amount' and rec.inc_amount > 0:
                rec.employee_id.contract_id.wage += rec.inc_amount
                rec.employee_id.contract_id.housing_allowance += rec.inc_housing_allowance
                rec.employee_id.contract_id.transportation_allowance += rec.inc_transportation_allowance
                rec.employee_id.contract_id.other_allowances += rec.inc_other_allowances

            elif rec.increase_types == 'percent' and rec.inc_percent > 0:
                rec.employee_id.contract_id.wage = (rec.employee_id.contract_id.wage * (
                        rec.inc_percent / 100)) + rec.employee_id.contract_id.wage

                rec.employee_id.contract_id.housing_allowance = (rec.employee_id.contract_id.housing_allowance * (
                        rec.inc_housing_allowance_percent / 100)) + rec.employee_id.contract_id.housing_allowance

                rec.employee_id.contract_id.transportation_allowance = (
                                                                               rec.employee_id.contract_id.transportation_allowance * (
                                                                               rec.inc_transportation_allowance_percent / 100)) + rec.employee_id.contract_id.transportation_allowance

                rec.employee_id.contract_id.other_allowances = (rec.employee_id.contract_id.other_allowances * (
                        rec.inc_other_allowances_percent / 100)) + rec.employee_id.contract_id.other_allowances

            elif rec.increase_types == 'adj' and rec.gross_salary > 0:
                rec.old_gross_salary = rec.employee_id.contract_id.wage
                rec.old_housing_allowance = rec.employee_id.contract_id.housing_allowance
                rec.old_transportation_allowance = rec.employee_id.contract_id.transportation_allowance
                rec.old_other_allowances = rec.employee_id.contract_id.other_allowances
                # rec.old_gross_salary = rec.employee_id.contract_id.wage
                # rec.old_gross_salary = rec.employee_id.contract_id.wage

                rec.employee_id.contract_id.wage = rec.gross_salary
                rec.employee_id.contract_id.housing_allowance = rec.new_housing_allowance
                rec.employee_id.contract_id.transportation_allowance = rec.new_transportation_allowance
                rec.employee_id.contract_id.other_allowances = rec.new_other_allowances

            rec.wage = rec.employee_id.contract_id.wage
            rec.housing_allowance = rec.employee_id.contract_id.housing_allowance
            rec.other_allowances = rec.employee_id.contract_id.other_allowances
            rec.transportation_allowance = rec.employee_id.contract_id.transportation_allowance

            rec.employee_id.department_id = rec.new_department_id.id
            rec.employee_id.parent_id = rec.new_manager_id.id
            rec.employee_id.job_id = rec.new_job_id.id

    def button_submit_change(self):
        self.ensure_one()
        template_id = self.env.ref('employee_promotion.promotion_email_template')
        try:
            compose_form_id = self.env.ref('mail.email_compose_message_wizard_form').id
        except ValueError:
            compose_form_id = False
        ctx = {
            'default_model': 'hr.promotion',
            # 'default_res_id': self.ids[0],
            'default_use_template': bool(template_id.id),
            'default_template_id': template_id.id,
            'default_composition_mode': 'comment',
            'default_promotion_id': self.id,
            'mark_so_as_sent': True,
            'proforma': self.env.context.get('proforma', False),
            'force_email': True
        }

        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }

    def button_back_to_draft(self):
        self.state = 'new'

    def button_cancel_request(self):
        self.state = 'cancel'

    def unlink(self):
        for record in self:
            if record.state != 'new':
                raise UserError("Sorry , you are not allowed to delete promotion not in state draft")
        res = super(EmployeePromotion, self).unlink()
        return res
