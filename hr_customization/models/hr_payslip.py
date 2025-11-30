# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)

class HrPayslip(models.Model):
    _inherit = ['hr.payslip', 'mail.thread']

    # Wage fields
    basic_wage = fields.Monetary(string='Basic Wage', compute='_compute_basic_net', store=True,
                                 currency_field='currency_id')
    gross_wage = fields.Monetary(string='Gross Wage', compute='_compute_basic_net', store=True,
                                 currency_field='currency_id')
    net_wage = fields.Monetary(string='Net Wage', compute='_compute_basic_net', store=True,
                               currency_field='currency_id')
    total_allowance_wage = fields.Monetary(compute='_compute_basic_net', store=True, string='Total Allowance',
                                           currency_field='currency_id')
    total_deduction_wage = fields.Monetary(compute='_compute_basic_net', store=True, string='Total Deduction',
                                           currency_field='currency_id')

    # Attendance-related fields
    normal_work_days = fields.Float(compute="_compute_normal_work_days", store=True)
    total_num_of_days = fields.Float(compute="_compute_normal_work_days", store=True)
    number_of_leave_days = fields.Float(compute="_compute_normal_work_days", store=True)
    number_of_sick_days = fields.Float(compute="_compute_normal_work_days", store=True, string="Number of sick leaves")

    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)

    def compute_sheet(self):
        # Compute normal work days before generating the payslip
        self._compute_normal_work_days()
        return super(HrPayslip, self).compute_sheet()

    @api.depends("employee_id", "contract_id", "date_from", "date_to")
    def _compute_normal_work_days(self):
        for rec in self:
            # Total number of days from contract
            rec.total_num_of_days = rec.contract_id.number_of_month_days if rec.contract_id else 0.0

            # Non-sick leaves
            leaves = self.env['hr.leave'].search([
                ('employee_id', '=', rec.employee_id.id),
                ('date_from', '>=', rec.date_from),
                ('date_to', '<=', rec.date_to),
                ('holiday_status_id.sick_leave', '!=', True),
                ('state', '=', 'validate')
            ])
            rec.number_of_leave_days = sum(leaves.mapped('number_of_days')) if leaves else 0.0

            # Sick leaves
            sick_leaves = self.env['hr.leave'].search([
                ('employee_id', '=', rec.employee_id.id),
                ('date_from', '>=', rec.date_from),
                ('date_to', '<=', rec.date_to),
                ('holiday_status_id.sick_leave', '=', True),
                ('state', '=', 'validate')
            ])
            rec.number_of_sick_days = sum(sick_leaves.mapped('number_of_days')) if sick_leaves else 0.0

            # Normal work days
            rec.normal_work_days = rec.total_num_of_days - rec.number_of_leave_days

    @api.depends('line_ids.total', 'line_ids.category_id')
    def _compute_basic_net(self):
        for payslip in self:
            payslip.basic_wage = payslip.gross_wage = payslip.net_wage = 0.0
            payslip.total_allowance_wage = payslip.total_deduction_wage = 0.0
            for line in payslip.line_ids:
                if line.category_id.code == 'BASIC':
                    payslip.basic_wage = line.total
                elif line.category_id.code == 'GROSS':
                    payslip.gross_wage = line.total
                elif line.category_id.code == 'NET':
                    payslip.net_wage = line.total
                elif line.category_id.code == 'TALL':
                    payslip.total_allowance_wage = line.total
                elif line.category_id.code == 'TDN':
                    payslip.total_deduction_wage = line.total

    def action_payslip_send(self):
        """Open email compose wizard for payslip"""
        for rec in self:
            template = self.env.ref('hr_customization.email_template_payslip', raise_if_not_found=False)
            compose_form = self.env.ref('mail.email_compose_message_wizard_form', raise_if_not_found=False)
            ctx = dict(
                self.env.context,
                default_model='hr.payslip',
                default_res_id=rec.id,
                default_use_template=bool(template),
                default_template_id=template.id if template else False,
                default_composition_mode='comment',
                mark_so_as_sent=True
            )
            return {
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'mail.compose.message',
                'views': [(compose_form.id, 'form')],
                'view_id': compose_form.id,
                'target': 'new',
                'context': ctx,
            }

    def force_payslip_send(self):
        composer_obj = self.env['mail.compose.message']
        email_act = self.action_payslip_send()
        if email_act and email_act.get('context'):
            composer_values = composer_obj.onchange_template_id(
                template_id=email_act['context'].get('default_template_id'),
                composition_mode=email_act['context'].get('default_composition_mode'),
                model=email_act['context'].get('default_model'),
                res_id=email_act['context'].get('default_res_id')
            ).get('value', {})
            if not composer_values.get('email_from'):
                composer_values['email_from'] = self.company_id.email

            composer_obj = composer_obj.with_context(email_act['context'])
            composer = composer_obj.create(composer_values)
            composer.send_mail()
        return True
