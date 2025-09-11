# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions, _
from datetime import date, datetime, time, timedelta
import odoo.addons.decimal_precision as dp
import ast


class NormalPayments(models.Model):
    _name = 'normal.payments'
    _rec_name = 'name'
    _description = 'Payments'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    def get_user(self):
        return self._uid

    def get_currency(self):
        return self.env['res.users'].search([('id', '=', self.env.user.id)]).company_id.currency_id.id

    payment_No = fields.Char()
    name = fields.Char(string="", required=False, compute="get_title", readonly=True)
    partner_id = fields.Many2one(comodel_name="res.partner", string="Partner Name", required=False)
    payment_date = fields.Datetime(string="Payment Date", required=True, default=datetime.today())
    amount = fields.Float(string="Amount", compute="change_checks_ids", store=True, track_visibility='onchange')
    amount1 = fields.Float(string="Amount", track_visibility='onchange')
    payment_method = fields.Many2one(comodel_name="account.journal", string="Payment Journal", required=True)
    #  domain=[('type', 'in', ('bank', 'cash'))])

    payment_subtype = fields.Selection(related='payment_method.payment_subtype')
    user_id = fields.Many2one(comodel_name="res.users", default=get_user)
    currency_id = fields.Many2one(comodel_name="res.currency", default=get_currency)
    state = fields.Selection(selection=[
        ('draft', 'Draft'),
        ('send', 'Sent'),
        ('posted', 'Posted'),
        ('cancel', 'Cancel'),
    ], default='draft', track_visibility='onchange')

    def set_to_draft(self):
        for rec in self:
            rec.state = "draft"

    pay_check_ids = fields.One2many('native.payments.check.create', 'nom_pay_id', string=_('Checks'))
    send_rec_money = fields.Selection(
        string="Payment Type",
        selection=[
            ('send', 'Send Money'),
            ('rece', 'Receive Money'),
            ('internal', 'Internal'),
        ], default='rece')

    payment_for = fields.Selection(
        string="Payment for (vendor/expense)",
        selection=[
            ("vendor", "vendor"),
            ("expense", "expense")
        ]
    )
    description = fields.Char()
    receipt_number = fields.Char(string="Receipt Number")
    account_id = fields.Many2one('account.account', string="Account", required=True)
    analyitc_id = fields.Many2one('account.analytic.account', string="Analytic Account")

    is_bank_issued = fields.Boolean()
    is_bank_recieved = fields.Boolean()

    custom_partner_domain = fields.Char(compute="_compute_partner_domain")
    custom_payment_domain = fields.Char(compute="_compute_payment_domain")

    def action_open_manual_reconciliation_widget(self):
        ''' Open the manual reconciliation widget for the current payment.
        :return: A dictionary representing an action.
        '''
        self.ensure_one()
        action_values = self.env['ir.actions.act_window']._for_xml_id(
            'account_accountant.action_move_line_posted_unreconciled')
        if self.partner_id:
            context = ast.literal_eval(action_values['context'])
            context.update({'search_default_partner_id': self.partner_id.id})
            if self.send_rec_money == 'rece':
                context.update({'search_default_trade_receivable': 1})
            elif self.send_rec_money == 'send':
                context.update({'search_default_trade_payable': 1})
            action_values['context'] = context
        return action_values

    def action_create_pay_check(self):
        result = {
            "name": "Pay Check",
            "type": "ir.actions.act_window",
            "res_model": "normal.payments",
            'view_mode': 'form',
            'context': {'default_is_bank_issued': True, 'default_send_rec_money': 'send'}
        }
        return result

    def action_create_receive_check(self):
        result = {
            "name": "Receive Check",
            "type": "ir.actions.act_window",
            "res_model": "normal.payments",
            'view_mode': 'list,form',
            'domain': [("is_bank_recieved", '=', True), ("send_rec_money", '=', 'rece')],
            'context': {'default_is_bank_recieved': True, 'default_send_rec_money': 'rece'}
        }
        return result

    @api.model
    def create(self, vals):
        if vals['send_rec_money'] == "send":
            vals['receipt_number'] = self.env['ir.sequence'].next_by_code('pay.send') or 'New'
        elif vals['send_rec_money'] == "rece":
            vals['receipt_number'] = self.env['ir.sequence'].next_by_code('receive.pay') or 'New'
        elif vals['send_rec_money'] == "internal":
            vals['receipt_number'] = self.env['ir.sequence'].next_by_code('internal.pay') or 'New'
        result = super(NormalPayments, self).create(vals)
        return result

    # @api.multi
    @api.constrains('amount')
    def _total_amount(self):
        if self.send_rec_money != 'internal':
            if self.payment_subtype:
                if self.amount == 0.0:
                    raise exceptions.ValidationError('amount for checks must be more than zerO!')
            else:
                if self.amount1 == 0.0:
                    raise exceptions.ValidationError('amount for payment must be more than zerO!')

    @api.onchange('partner_id', 'send_rec_money')
    def get_partner_acc(self):
        if self.send_rec_money == 'send':
            self.account_id = self.partner_id.property_account_payable_id.id
        elif self.send_rec_money == 'rece':
            self.account_id = self.partner_id.property_account_receivable_id.id

    # @api.multi
    @api.depends('pay_check_ids', 'payment_method', 'amount1')
    def change_checks_ids(self):
        for rec in self:
            tot_amnt = 0.0
            if rec.sudo().payment_subtype:
                if rec.sudo().pay_check_ids:
                    for x in rec.sudo().pay_check_ids:
                        tot_amnt += x.amount
            else:
                tot_amnt = rec.amount1
            rec.amount = tot_amnt
            if rec.amount and not rec.amount1:
                rec.amount1 = rec.amount

    # @api.multi
    def button_journal_entries(self):
        return {
            'name': 'Journal Items',
            'view_type': 'form',
            'view_mode': 'list,form',
            'res_model': 'account.move.line',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('jebal_con_pay_id', 'in', self.ids)],
        }

    @api.onchange('send_rec_money')
    def _compute_partner_domain(self):
        if self.send_rec_money == "send":
            self.custom_partner_domain = str([('supplier_rank', '>', 0)])
        else:
            self.custom_partner_domain = str([('customer_rank', '>', 0)])

    @api.onchange('send_rec_money')
    def _compute_payment_domain(self):
        if self.send_rec_money in ['rece', 'send']:
            if self.is_bank_issued:
                self.custom_payment_domain = [('payment_subtype', '=', 'issue_check'), ('type', '=', 'bank')]
            elif self.is_bank_recieved:
                self.custom_payment_domain = [('payment_subtype', '=', 'rece_check'), ('type', '=', 'bank')]
            else:
                self.custom_payment_domain = str([('type', '=', 'cash')])
        else:
            self.custom_payment_domain = str([])

    @api.depends('partner_id', 'send_rec_money', 'payment_for')
    def get_title(self):
        for rec in self:
            if rec.send_rec_money == "send":
                if rec.payment_for == "vendor" and rec.partner_id:
                    rec.name = "Payment for Vendor " + str(rec.partner_id.name)
                else:
                    if rec.payment_for == "expense":
                        rec.name = "Payment for Expense"
                    else:
                        rec.name = '*'
            elif rec.send_rec_money == "rece":
                rec.name = "Payment for Customer " + str(rec.partner_id.name)
            elif rec.send_rec_money == "internal":
                rec.name = "Internal Payment"
            else:
                rec.name = '*'

    def action_send(self):
        self.state = "send"

    def action_cancel(self):
        self.state = "cancel"

    def action_confirm(self):
        pay_amt = 0
        if self.payment_subtype and self.send_rec_money != 'internal':
            pay_amt = self.amount
        else:
            pay_amt = self.amount1
        move = {
            'name': '/',
            'journal_id': self.payment_method.id,
            'ref': self.receipt_number + "-" + self.description if self.description else self.receipt_number,
            'company_id': self.user_id.company_id.id,
            'normal_payment_id': self.id,
        }

        move_line_name = 'Partner Payment ' + 'Receipt:' + self.receipt_number if self.partner_id else 'Receipt:' + self.receipt_number
        move_line = {
            'name': move_line_name + "-" + self.description if self.description else move_line_name,
            'partner_id': self.partner_id.id,
            'ref': self.receipt_number + "-" + self.description if self.description else self.receipt_number,
            'jebal_con_pay_id': self.id,
            'normal_payment_id': self.id,
        }

        if self.send_rec_money in ['send', 'internal']:
            debit_account = [{'account': self.account_id.id, 'percentage': 100, 'analyitc_id': self.analyitc_id.id, }]
            credit_account = [{'account': self.payment_method.default_account_id.id, 'percentage': 100}]
        else:
            credit_account = [{'account': self.account_id.id, 'percentage': 100, }]
            # debit_account = [{'account': self.payment_method.default_account_id.id, 'percentage': 100}]
            debit_account = [{'account': self.payment_method.default_account_id.id, 'percentage': 100,
                              'analyitc_id': self.analyitc_id.id, }]

        self.env['create.moves'].create_move_lines(move=move, move_line=move_line,
                                                   debit_account=debit_account,
                                                   credit_account=credit_account,
                                                   src_currency=self.currency_id,
                                                   amount=pay_amt)
        self.state = 'posted'
        if self.payment_subtype:
            for check in self.pay_check_ids:
                check_line_val = {}
                check_line_val['check_book_id'] = check.check_book_id.id
                check_line_val['check_number'] = check.check_number
                check_line_val['pay_check_id'] = check.id
                check_line_val['check_date'] = check.check_date
                check_line_val['check_bank'] = check.bank.id
                check_line_val['dep_bank'] = check.dep_bank.id
                check_line_val['currency_id'] = self.currency_id.id
                if self.send_rec_money == 'rece':
                    check_line_val['state'] = 'holding'
                    check_line_val['check_type'] = 'rece'
                else:
                    check_line_val['state'] = 'handed'
                    check_line_val['check_type'] = 'pay'
                check_line_val['amount'] = check.amount
                check_line_val['open_amount'] = check.amount
                check_line_val['type'] = 'regular'
                check_line_val['notespayable_id'] = self.payment_method.default_account_id.id
                check_line_val['notes_rece_id'] = self.payment_method.default_account_id.id
                check_line_val['investor_id'] = self.partner_id.id
                check_line_val['journal_id'] = self.payment_method.id
                check.check_management_id = self.env['check.management'].create(check_line_val)
        return True


class PaymentsCheckCreate(models.Model):
    _name = 'native.payments.check.create'
    _order = 'check_number asc'
    _rec_name = "nom_pay_id"

    check_number = fields.Char(string=_("Check number"), required=False)
    check_date = fields.Date(string=_('Check Date'), required=True)
    amount = fields.Float(string=_('Amount'), required=True)
    bank = fields.Many2one('res.bank', string=_("Check Bank Name"))
    check_book_id = fields.Many2one('check.book', string=_("Check Book"))
    dep_bank = fields.Many2one('res.bank', string=_("Depoist Bank"))
    nom_pay_id = fields.Many2one('normal.payments')
    check_management_id = fields.Many2one('check.management', string='Check management', copy=False)

    @api.onchange('bank')
    def _onchange_bank_reset_book(self):
        self.check_book_id = False

    @api.model
    def create(self, values):
        if values.get('check_book_id'):
            # Get the start and last check numbers
            check_book = self.env['check.book'].browse(values.get('check_book_id'))
            start_check_no = check_book.next_check_no
            last_check_no = check_book.last_check_no
            # Find the next available check number within the range
            next_check_no = start_check_no
            while next_check_no <= last_check_no:
                if not self.search([('check_number', '=', next_check_no)]):
                    values['check_number'] = next_check_no
                    break
                next_check_no += 1
            if next_check_no > last_check_no:
                raise exceptions.ValidationError("All check numbers in the range are used")
            check_book.next_check_no = next_check_no

        return super(PaymentsCheckCreate, self).create(values)
