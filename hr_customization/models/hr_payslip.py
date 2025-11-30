# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


class HrPayslip(models.Model):
    _inherit = ['hr.payslip', 'mail.thread']
    _name = 'hr.payslip'

    def compute_sheet(self):
        for rec in self:
            rec._compute_normal_work_days()
        return super().compute_sheet()

    normal_work_days = fields.Float(compute="_compute_normal_work_days", store=True)

    total_num_of_days = fields.Float(compute="_compute_normal_work_days", store=True)
    number_of_leave_days = fields.Float(compute="_compute_normal_work_days", store=True)
    number_of_sick_days = fields.Float(compute="_compute_normal_work_days", store=True, string="Number of sick leaves")

    @api.depends("employee_id")
    def _compute_normal_work_days(self):
        """
        - We made this function to calculate the total number of days without depending on work entries
        """
        for rec in self:
            if rec.contract_id:
                if rec.contract_id.number_of_month_days > 0:
                    # _logger.info("contract_id.number_of_month_days:{}".format(rec.contract_id.number_of_month_days))
                    # day_rate = 30 / rec.contract_id.number_of_month_days 
                    # _logger.info("day_rate:{}".format(day_rate))
                    # days_diff = rec.date_to - rec.date_from
                    # _logger.info("days_diff.days:{}".format(days_diff.days))

                    # rec.total_num_of_days =  (days_diff.days)/day_rate # add one to handle the lost day factor
                    # rec.total_num_of_days =  (days_diff.days+1)/day_rate # add one to handle the lost day factor

                    rec.total_num_of_days = rec.contract_id.number_of_month_days
                    _logger.info("total_num_of_days:{}".format(rec.total_num_of_days))

                all_leaves = self.env['hr.leave'].search([
                    ("employee_id", '=', rec.employee_id.id),
                    ('date_from', '>=', rec.date_from),
                    ('date_to', '<=', rec.date_to),
                    ("holiday_status_id.sick_leave", '!=', True),
                    ('state', '=', 'validate')
                ])
                _logger.info("all_leaves:{}".format(all_leaves))
                sum(all_leaves.mapped("number_of_days"))
                _logger.info("number_of_leave_days:{}".format(rec.number_of_leave_days))
                if rec.contract_id.number_of_month_days > 0:
                    rec.normal_work_days = rec.total_num_of_days - rec.number_of_leave_days
                    _logger.info("normal_work_days:{}".format(rec.normal_work_days))

                sick_leave_days = self.env['hr.leave'].search([
                    ("employee_id", '=', rec.employee_id.id),
                    ('date_from', '>=', rec.date_from),
                    ('date_to', '<=', rec.date_to),
                    ("holiday_status_id.sick_leave", '=', True),
                    ('state', '=', 'validate')
                ])
                _logger.info("sick_leave_days:{}".format(sick_leave_days))

                rec.number_of_sick_days = sum(sick_leave_days.mapped("number_of_days_display"))

    def action_payslip_send(self):
        '''
        This function opens a window to compose an email, with email template
        message loaded by default
        '''

        for rec in self:
            template = self.env.ref('hr_customization.email_template_payslip')
            compose_form = self.env.ref(
                'mail.email_compose_message_wizard_form')
            self = self.with_context(
                default_model='hr.payslip',
                default_res_id=rec.id,
                default_use_template=bool(template),
                default_template_id=template.id,
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
                'context': self.env.context,
            }

    def force_payslip_send(self):
        composer_obj = self.env['mail.compose.message']
        email_act = self.action_payslip_send()
        if email_act and email_act.get('context'):
            composer_values = {}
            email_ctx = email_act['context']
            composer_values.update(composer_obj.onchange_template_id(
                template_id=email_ctx.get('default_template_id'),
                composition_mode=email_ctx.get('default_composition_mode'),
                model=email_ctx.get('default_model'),
                res_id=email_ctx.get('default_res_id')
            ).get('value', {}))
            if not composer_values.get('email_from'):
                composer_values['email_from'] = self.company_id.email

            composer_obj = composer_obj.with_context(
                default_model=email_ctx.get('default_model'),
                default_res_id=email_ctx.get('default_res_id'),
                default_use_template=email_ctx.get('default_use_template'),
                default_template_id=email_ctx.get('default_template_id'),
                default_composition_mode=email_ctx.get(
                    'default_composition_mode'),
                mark_so_as_sent=email_ctx.get('mark_so_as_sent')
            )
            composer = composer_obj.create(composer_values)
            composer.send_mail()
        return True

    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
    total_allowance_wage = fields.Monetary(compute='_compute_basic_net', store=True, string='Total Allowance',
                                           currency_field='currency_id')
    total_deduction_wage = fields.Monetary(compute='_compute_basic_net', store=True, string='Total Deduction',
                                           currency_field='currency_id')

    @api.depends('line_ids.total')
    def _compute_basic_net(self):
        # line_values = (self._origin)._get_line_values(['BASIC', 'GROSS', 'NET'])
        for payslip in self:
            for line in payslip.line_ids:
                if line.category_id.code == 'BASIC':
                    payslip.basic_wage = line.total
                if line.category_id.code == 'GROSS':
                    payslip.gross_wage = line.total
                if line.category_id.code == 'NET':
                    payslip.net_wage = line.total
                if line.category_id.code == 'TALL':
                    payslip.total_allowance_wage = line.total
                if line.category_id.code == 'TDN':
                    payslip.total_deduction_wage = line.total
