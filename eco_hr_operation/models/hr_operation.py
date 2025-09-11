from odoo import models, fields, api
from datetime import datetime


class OperationType(models.Model):
    _name = 'hr.operation.type'
    _description = 'Operation Type'

    name = fields.Char(string='Name', required=True)
    is_portal = fields.Boolean()

    show_fields = fields.Selection([
        ('passport_withdrawal', 'passport withdrawal'),
        ('proceed_work', 'proceed work'),
        ('final_release', 'final release'),
        ('proceed_work_leave', 'proceed work leave'),
        ('investigation_call', 'investigation call'),
    ])


class HrOperation(models.Model):
    _name = 'hr.operation'
    _description = 'HR Operation'

    date = fields.Date(string='Date', required=True)
    responsible_id = fields.Many2one('hr.employee', string='Responsible')
    job_title = fields.Many2one('hr.job', related='employee_id.job_id', string='Job Title', store=True)
    type_id = fields.Many2one('hr.operation.type', string='Operation Type', required=True)

    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    identification_no = fields.Char(related='employee_id.identification_id', string='Identification No', store=True)
    nationality_id = fields.Many2one(related='employee_id.country_id', string='Nationality', store=True)
    manager_id = fields.Many2one(related='employee_id.parent_id', string='Manager', store=True)

    department_id = fields.Many2one(related='employee_id.department_id', string='Department', store=True)
    date_of_birth = fields.Date(related='employee_id.birthday', string='Date of Birth', store=True)
    contract_id = fields.Many2one('hr.contract', string='Contract', compute='_compute_contract', store=True)
    contract_start_date = fields.Date(string='Contract Start Date', compute='_compute_contract', store=True)
    contract_end_date = fields.Date(string='Contract End Date', compute='_compute_contract', store=True)
    currency_id = fields.Many2one('res.currency', string='Currency', required=True, readonly=True,
                                  default=lambda self: self.env.company.currency_id.id)

    final_release = fields.Boolean()
    last_work_date = fields.Date()

    proceed_work = fields.Boolean()
    to_mr_miss = fields.Char()

    investigation_call = fields.Boolean()
    calling_date = fields.Date()
    calling_time = fields.Char()

    passport_withdrawal = fields.Boolean()
    passport_delivery_date = fields.Date()
    passport_receive_date = fields.Date()
    number_of_days = fields.Char(compute='get_number_of_days')
    purpose_of_passport_withdrawal = fields.Text()

    proceed_work_leave = fields.Boolean()
    date_resumes_duty = fields.Date()
    reason_change_resume_date = fields.Text()

    cancellation_reason = fields.Text()

    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'confirmed'),
        ('cancelled', 'cancelled'),
    ], default="draft")

    show_fields = fields.Selection(related="type_id.show_fields")

    def action_confirm(self):
        for s in self:
            s.state = "confirmed"

    def action_cancel(self):
        for s in self:
            s.state = "cancelled"

    def get_number_of_days(self):
        for item in self:
            d1 = datetime.strptime(str(item.passport_receive_date), "%Y-%m-%d")
            d2 = datetime.strptime(str(item.passport_delivery_date), "%Y-%m-%d")
            item.number_of_days = abs((d2 - d1).days)

    @api.depends('employee_id', 'date', 'type_id')
    def _compute_display_name(self):
        for record in self:
            name_parts = []
            if record.date:
                name_parts.append(record.date.strftime('%Y-%m-%d'))
            if record.employee_id:
                name_parts.append(record.employee_id.name)
            if record.type_id:
                name_parts.append(record.type_id.name)
            record.display_name = ' - '.join(name_parts)

    @api.depends('employee_id')
    def _compute_contract(self):
        for record in self:
            record.contract_id = False
            record.contract_start_date = False
            record.contract_end_date = False
            if record.employee_id:
                contract = self.env['hr.contract'].search([('employee_id', '=', record.employee_id.id),
                                                           ('state', '=', 'open')], limit=1)
                record.contract_id = contract.id
                record.contract_start_date = contract.date_start
                record.contract_end_date = contract.date_end
