# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions, _
import odoo.addons.decimal_precision as dp
from datetime import datetime
from datetime import timedelta

from odoo.exceptions import ValidationError
from odoo.fields import Date as fDate
from lxml import etree


class CheckManagement(models.Model):
    _name = 'check.management'
    _description = 'Check'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'state'
    name = fields.Char(compute='_compute_check_name', store=True)
    pay_check_id = fields.Many2one("native.payments.check.create")
    # pay_check_id = fields.Many2one("native.payments.check.create")
    check_number = fields.Char(string=_("Check Number"), required=True, default="0")
    check_date = fields.Date(string=_("Check Date"), required=True)
    check_bank = fields.Many2one('res.bank', string=_('Check Bank'))
    dep_bank = fields.Many2one('res.bank', string=_('Deposit Bank'))
    amount = fields.Float(string=_('Check Amount'),
                          digits=dp.get_precision('Product Price'))

    check_book_id = fields.Many2one("check.book", domain=[('state', '=', 'active')])
    amount_reg = fields.Float(string="Check Regular Amount",
                              digits=dp.get_precision('Product Price'))

    open_amount_reg = fields.Float(
        string="Check Regular Open Amount", digits=dp.get_precision('Product Price'))

    open_amount = fields.Float(string=_('Open Amount'), digits=dp.get_precision('Product Price'),
                               track_visibility='onchange')
    investor_id = fields.Many2one('res.partner', string=_("Partner"))

    type = fields.Selection(string="Type", selection=[
        ('reservation', 'Reservation Installment'),
        ('contracting', 'Contracting Installment'),
        ('regular', 'Regular Installment'),
        ('ser', 'Services Installment'),
        ('garage', 'Garage Installment'),
        ('mod', 'Modification Installment'),
    ], required=True, default="regular")
    state = fields.Selection(selection=[
        ('holding', 'Holding'), ('depoisted', 'Depoisted'),
        ('approved', 'Approved'), ('rejected', 'Rejected'),
        # ('transfer_to_collect', 'Transfer To Collect'),
        ('returned', 'Responsed'), ('handed', 'Handed'),
        ('debited', 'Debited'), ('canceled', 'Canceled'),
        ('cs_return', 'Customer Returned'),
        ('vendor_return', 'Vendor Returned'),
    ], track_visibility='onchange')

    currency_id = fields.Many2one(comodel_name="res.currency")

    notes_rece_id = fields.Many2one('account.account')
    under_collect_id = fields.Many2one('account.account')
    notespayable_id = fields.Many2one('account.account')
    under_collect_jour = fields.Many2one('account.journal')
    check_type = fields.Selection(
        selection=[('rece', 'Notes Receivable'), ('pay', 'Notes Payable')])
    check_state = fields.Selection(
        selection=[('active', 'Active'), ('suspended', 'Suspended')], default='active')
    check_from_check_man = fields.Boolean(string="Check Managment", default=False)
    # will_collection = fields.Date(string="Maturity Date" , compute = "_compute_days")
    will_collection_user = fields.Date(
        string="Bank Maturity Date", track_visibility='onchange')
    journal_id = fields.Many2one('account.journal', string='Journal')

    payment_date = fields.Date()
    transaction_date = fields.Date()
    reject_reason = fields.Text()
    is_police_report = fields.Boolean()
    police_number = fields.Char()
    police_date = fields.Date()
    automatic_policy_date = fields.Date(default=fields.Date.context_today, readonly=True)
    is_transfer_to_collect = fields.Boolean(string='Transfer To Collect')
    date_to_transfer = fields.Date(string='Transfer Date')
    automatic_transfer_date = fields.Date(default=fields.Date.context_today, readonly=True,
                                          string='Automatic Transfer Date')

    def button_journal_entries(self):
        return {
            'name': 'Journal Enties',
            'view_type': 'form',
            'view_mode': 'list,form',
            'res_model': 'account.move.line',
            'type': 'ir.actions.act_window',
            'domain': [('check_id', 'in', self.ids)],
        }


    @api.depends('check_date', 'investor_id', 'check_number')
    def _compute_check_name(self):
        for check in self:
            name = '{} - {} - {}'.format(check.check_date,
                                         check.investor_id.name, check.check_number)
            check.name = name

    @api.model
    def create(self, vals):
        if 'amount' in vals:
            vals['open_amount'] = vals['amount']
        return super(CheckManagement, self).create(vals)

    def write(self, vals):
        for rec in self:
            if 'amount' in vals:
                rec.open_amount = vals['amount']
        return super(CheckManagement, self).write(vals)

    def button_deposit_checks(self):
        return self.env['ir.actions.act_window']._for_xml_id('check_management.check_cycle_wizard_action')

    def button_approve_checks(self):
        return self.env['ir.actions.act_window']._for_xml_id('check_management.check_cycle_wizard_action3')

    def button_customer_return(self):
        return self.env['ir.actions.act_window']._for_xml_id('check_management.check_cycle_wizard_action7')

    def button_vendor_return(self):
        return self.env['ir.actions.act_window']._for_xml_id('check_management.check_cycle_wizard_action8')

    def button_reject_checks(self):
        return self.env['ir.actions.act_window']._for_xml_id('check_management.check_cycle_wizard_action2')

    def button_company_return(self):
        if self.is_police_report:
            return self.env['ir.actions.act_window']._for_xml_id('check_management.check_cycle_wizard_action5')
        else:
            raise ValidationError(_('Please select Policy report to continue.'))

    def button_debited_check(self):
        return self.env['ir.actions.act_window']._for_xml_id('check_management.check_cycle_wizard_action6')

    @api.model
    def create(self, values):
        if values.get('check_book_id'):
            # Get the start and last check numbers
            check_book = self.env['check.book'].browse(values.get('check_book_id'))
            start_check_no = check_book.start_check_no
            last_check_no = check_book.last_check_no
            # Find the next available check number within the range
            next_check_no = check_book.next_check_no
            if not values.get('check_number'):
                while next_check_no <= last_check_no:
                    if not self.search([('check_number', '=', next_check_no)]):
                        values['check_number'] = next_check_no
                        break
                    next_check_no += 1
                if next_check_no > last_check_no:
                    raise exceptions.ValidationError(
                        "All check numbers in the chack book's range are used, try create a new check book")
                check_book.next_check_no = next_check_no
            if next_check_no == last_check_no:
                check_book.close_check_book()
        return super(CheckManagement, self).create(values)

    @api.model
    def get_views(self, views, options=None):
        res = super().get_views(views, options)

        # form view toolbar
        if res['views']['form']['toolbar'] and res['views']['form']['toolbar'].get("action"):
            form_actions = res['views']['form']['toolbar'].get("action")
            # Define conditions for action removal based on action IDs
            form_conditions = {
                self.env.ref("check_management.native_check_holding_action").id: ["Deposit Checks", "Customer Return",
                                                                                  "Collect checks", "Split-Merge"],
                self.env.ref("check_management.native_check_depoisted_action").id: ["Customer Return", "Collect checks",
                                                                                    "Reject Checks", "Split-Merge"],
                self.env.ref("check_management.native_check_rejected_action").id: ["Company Responsed",
                                                                                   "Collect checks", "Split-Merge"],
                self.env.ref("check_management.native_check_returned_action").id: ["Deposit Checks", "Customer Return",
                                                                                   "Collect checks", "Split-Merge"],
                self.env.ref("check_management.native_check_handed_action").id: ["Vendor Return", "Debit Check"]
            }
            # Remove actions based on conditions
            form_actions = [action for action in form_actions if
                            action['name'] in form_conditions.get(options['action_id'], [])]
            res['views']['form']['toolbar']['action'] = form_actions

        # List view toolbar
        if res['views']['list']['toolbar'] and res['views']['list']['toolbar'].get("action"):
            actions_list = res['views']['list']['toolbar'].get("action")
            # Define conditions for action removal based on action IDs
            conditions = {
                self.env.ref("check_management.native_check_holding_action").id: ["Deposit Checks", "Customer Return",
                                                                                  "Collect checks", "Split-Merge"],
                self.env.ref("check_management.native_check_depoisted_action").id: ["Collect checks", "Reject Checks",
                                                                                    "Split-Merge"],
                self.env.ref("check_management.native_check_rejected_action").id: ["Company Responsed",
                                                                                   "Collect checks", "Split-Merge"],
                self.env.ref("check_management.native_check_returned_action").id: ["Deposit Checks", "Customer Return",
                                                                                   "Collect checks", "Split-Merge"],
                self.env.ref("check_management.native_check_handed_action").id: ["Vendor Return", "Debit Check"]
            }
            # Remove actions based on conditions
            actions_list = [action for action in actions_list if
                            action['name'] in conditions.get(options['action_id'], [])]
            res['views']['list']['toolbar']['action'] = actions_list

        return res
