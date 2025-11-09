from odoo import fields, models, api, _
from datetime import date

from odoo.exceptions import UserError


class PenaltyRequest(models.Model):
    _inherit = 'penalty.request'

    penalty_rule_id = fields.Many2one(comodel_name='penalty.rule', required=True)
    penalty_type_of_approve = fields.Selection(related='penalty_rule_id.type_of_approval')
    contract_id = fields.Many2one(required=False, related="employee_id.contract_id")
    month = fields.Char(compute='get_month')
    input_type_id = fields.Many2one(related='penalty_rule_id.input_type_id')

    state = fields.Selection(selection_add=[
        ('emp_mang_submit', 'Manager Submit'),
        ('approved', 'Approved'), ('rejected',)])
    payslip_id = fields.Many2one(comodel_name='hr.payslip')

    @api.ondelete(at_uninstall=False)
    def _unlink_if_correct_states(self):
        for penalty in self:
            if penalty.state == 'approved':
                raise UserError(_('You cannot delete a penalty that is approved'))

    @api.depends('request_date')
    def get_month(self):
        for item in self:
            item.month = ''
            if item.request_date:
                item.month = item.request_date.month

    employee_cause_of_penalty = fields.Text()
    employee_approve_of_cause = fields.Text()
    employee_other_approve = fields.Text()
    emp_manager_feedback = fields.Text()
    emp_manager_opinion = fields.Selection(selection=[('approved', 'غير مخالف'), ('not_approved', 'مخالف')])
    hr_manager_feedback = fields.Text()
    no_of_repetition = fields.Integer()
    last_penalty_date = fields.Date(compute='get_last_penalty_date')

    @api.depends('employee_id')
    def get_last_penalty_date(self):
        for rec in self:
            rec.last_penalty_date = False
            if rec.employee_id:
                rec.last_penalty_date = self.env['penalty.request'].search(
                    [('employee_id', '=', rec.employee_id.id),
                     ('state', '=', 'approved')], order='id desc', limit=1).request_date

    @api.onchange('penalty_rule_id')
    def onchange_penalty_rule_id(self):
        for rec in self:
            if rec.penalty_rule_id:
                rec.penalty_type = rec.penalty_rule_id.penalty_type
                previous_same_penalty = self.env['penalty.request'].search_count(
                    [('employee_id', '=', rec.employee_id.id),
                     ('penalty_rule_id', '=', rec.penalty_rule_id.id), ('month', '=', date.today().month),
                     ('state', 'not in', ('draft', 'rejected'))])

                lines = [line.rate for line in rec.penalty_rule_id.line_ids]

                max_penalty_index = 4

                # Ensure `previous_same_penalty` is within bounds
                penalty_index = min(previous_same_penalty, max_penalty_index)

                # Check if `lines` has enough entries
                if len(lines) > penalty_index:
                    rec.penalty_amount_amount = lines[penalty_index]
                    rec.penalty_amount_days = lines[penalty_index]
                    rec.no_of_repetition = penalty_index if penalty_index > 0 else None

    @api.model
    def create(self, vals):
        res = super(PenaltyRequest, self).create(vals)
        users, users_manager = [], []
        users.append(res.employee_id.user_id.id)
        if res.employee_id.parent_id:
            users_manager.append(res.employee_id.parent_id.user_id.id)
        if users:
            template = self.env.ref('penalty_enhancement.mail_penalty_request_template')
            email_users = self.env['res.users'].sudo().search([('id', 'in', users)]).mapped('email')
            if email_users:
                if False in email_users:
                    email_users.remove(False)
            template.write({'email_to': ', '.join(email_users)})
            template.send_mail(res.id, force_send=True, raise_exception=False)
        if users_manager:
            m_template = self.env.ref('penalty_enhancement.mail_penalty_request_manager_template')
            m_email_users = self.env['res.users'].sudo().search([('id', 'in', users_manager)]).mapped('email')
            if m_email_users:
                if False in m_email_users:
                    m_email_users.remove(False)
            m_template.write({'email_to': ', '.join(m_email_users)})
            m_template.send_mail(res.id, force_send=True, raise_exception=False)

        if res.employee_id.user_id or res.employee_id.parent_id.user_id:
            todos = {
                'res_id': res.id,
                'res_model_id': self.env['ir.model'].search([('model', '=', 'penalty.request')]).id,
                'user_id': res.employee_id.parent_id.user_id.id,
                'summary': 'Penalty Request',
                'note': 'Need your approve on penalty request',
                'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                'date_deadline': res.request_date,
            }
            self.env['mail.activity'].create(todos)
        return res

    def confirm_button(self):
        res = super(PenaltyRequest, self).confirm_button()
        users, users_manager = [], []
        users.append(self.employee_id.user_id.id)
        if self.employee_id.parent_id:
            users_manager.append(self.employee_id.parent_id.user_id.id)
        if users:
            template = self.env.ref('penalty_enhancement.mail_penalty_request_template')
            email_users = self.env['res.users'].sudo().search([('id', 'in', users)]).mapped('email')
            if email_users:
                if False in email_users:
                    email_users.remove(False)
            template.write({'email_to': ', '.join(email_users)})
            template.send_mail(self.id, force_send=True, raise_exception=False)
        if users_manager:
            m_template = self.env.ref('penalty_enhancement.mail_penalty_request_manager_template')
            m_email_users = self.env['res.users'].sudo().search([('id', 'in', users_manager)]).mapped('email')
            if m_email_users:
                if False in m_email_users:
                    m_email_users.remove(False)
            m_template.write({'email_to': ', '.join(m_email_users)})
            m_template.send_mail(self.id, force_send=True, raise_exception=False)
        return res

    def hr_manager_confirm(self):
        for rec in self:
            rec.write({'state': 'approved'})

    def employee_manager_confirm(self):
        for item in self:
            if self.env.user.id == item.employee_id.parent_id.user_id.id:
                item.write({'state': 'emp_mang_submit'})
