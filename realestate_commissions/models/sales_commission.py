# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

import datetime
from dateutil.relativedelta import relativedelta

import pytz


class SalesCommission(models.Model):
    _name = "sales.commission"
    _description = "Sales Commission"
    _order = 'id desc'
    _rec_name = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']

    @api.depends('sales_commission_line')
    def _get_amount_total(self):
        for rec in self:
            total_amount = []
            for line in rec.sales_commission_line:
                total_amount.append(line.commission_amount)
            rec.amount = sum(total_amount)

    def unlink(self):
        for rec in self:
            if not rec.state != 'draft':
                raise UserError(_('You can not delete Sales Commission Except in Draft state.'))
        return super(SalesCommission, self).unlink()

    @api.depends('invoice_id', 'invoice_id.payment_state')
    def _is_paid_invoice(self):
        for rec in self:
            if rec.invoice_id.payment_state == 'paid':
                rec.is_paid = True
                rec.state = 'paid'

    name = fields.Char(
        string="Name", )
    state = fields.Selection([('draft', 'Draft'),
                              ('generate', 'Generated'),
                              ('confirm', 'Confirmed'),
                              ('invoice', 'Invoiced'),
                              ('payslip', 'Payslip'),
                              ('cancel', 'Cancelled')], default='draft', tracking=True, copy=False, string="Status")
    type = fields.Selection(
        string='Type',
        selection=[
            ("direct", "Direct"),
            ("indirect", "Indirect"),
        ],
        required=True, default='direct')
    direct_type = fields.Selection(
        string='Direct Type',
        selection=[
            ("sales_person", "Sales Person"),
            ("sales_manager", "Sales Manager"),
            ("sales_agent", "Sales Agent"),
        ], )

    start_date = fields.Date(string='Start Date', )
    end_date = fields.Date(string='End Date')
    commission_user_id = fields.Many2one('res.users', string='Sales Member', required=True, readonly=True, )
    sales_commission_line = fields.One2many('sales.commission.line', 'sales_commission_id', readonly=True)
    notes = fields.Text(string="Internal Notes")
    company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id, string='Company',
                                 readonly=True)
    product_id = fields.Many2one('product.product', domain=[('is_commission_product', '=', True)],
                                 string='Commission Product For Invoice', readonly=True, )
    amount = fields.Float(string='Total Commission', compute="_get_amount_total",
                          store=True, readonly=True, )
    invoice_id = fields.Many2one('account.move', string='Commission Invoice', readonly=True, )
    is_paid = fields.Boolean(string="Is Commission Paid", compute="_is_paid_invoice", store=True,
                             readonly=True, )
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string='Currency', readonly=True, )
    effective_date = fields.Date(string='Effective Date', required=True)

    def genrate_commission_lines(self):
        sale_order_ids = self.env['sale.order'].search(
            [
                ('user_id', '=', self.commission_user_id.id),
                ('state', '=', 'sale'),
                ('property_id', '!=', None),
            ]
        )
        print('sale_order_ids', sale_order_ids)
        if sale_order_ids:
            commission_rate = self.get_commission_range(len(sale_order_ids), self.direct_type)
            vals = []
            for rec in sale_order_ids:
                vals.append((0, 0, {
                    'sale_order_id': rec.id,
                    'commission_rate': commission_rate,

                }))
            self.sales_commission_line.unlink()
            self.write({'sales_commission_line': vals})
            self.write({'state': 'generate'})

    def get_commission_range(self, count, direct_type=None):
        commission_range = self.env['commission.range'].search([
            ('date_from', '<=', self.start_date),
            ('date_to', '>=', self.end_date),
            ('type', '=', self.type),
            ('state', '=', 'confirm'),
        ])
        if self.type == 'direct':
            range = commission_range.sales_team_commission_ids.filtered(
                lambda line: line.range_from <= count and line.range_to >= count)
            print(range)
            print(range.mapped('sales_person_percent'))
            if range and direct_type == 'sales_person':
                return range.mapped('sales_person_percent')[0]

    def _prepare_invoice_line(self):
        """
        Prepare the dict of values to create the new invoice line for a sales order line.
        :param qty: float quantity to invoice
        """

        product = self.env['product.product'].search([('is_commission_product', '=', True)], limit=1)
        print(product)
        if not product:
            raise UserError(
                _('Please define Commission Product'))
        res = {
            'product_id': product.id,
            'price_unit': self.amount,
            'quantity': 1,
        }
        return res

    def _prepare_invoice(self):
        """
        Prepare the dict of values to create the new invoice . This method may be
        overridden to implement custom invoice generation (making sure to call super() to establish
        a clean extension chain).
        """
        self.ensure_one()

        partner = self.commission_user_id.partner_id
        if not partner.property_account_payable_id:
            raise UserError(_('Please set Payable Account on Vendor Form For: %s!' % (partner.name)))

        domain = [('type', '=', 'purchase'), ('company_id', '=', self.company_id.id)]
        journal_id = self.env['account.journal'].search(domain, limit=1)
        if not journal_id:
            raise UserError(_('Please configure purchase journal for company: %s' % (self.company_id.name)))
        vals = self._prepare_invoice_line()

        invoice_vals = {
            'ref': self.name or '',
            'invoice_origin': self.name,
            'invoice_date': self.effective_date,
            'move_type': 'in_invoice',
            'partner_id': partner.id,
            'journal_id': journal_id.id,
            'narration': partner.name,
            'company_id': self.company_id.id,
            'invoice_line_ids': [(0, 0, vals)]
        }
        return invoice_vals

    def action_create_invoice(self):
        inv_obj = self.env['account.move']

        inv_data = self._prepare_invoice()
        invoice = inv_obj.create(inv_data)
        self.invoice_id = invoice.id
        self.state = 'invoice'
    def action_create_payslip(self):
        self.state = 'payslip'
    def action_cancel(self):
        self.state = 'cancel'

    def action_draft(self):
        self.state = 'draft'

    def action_confirm(self):
        self.state = 'confirm'


class SalesCommissionLine(models.Model):
    _name = "sales.commission.line"
    _order = 'id desc'
    _rec_name = 'sales_commission_id'

    sales_commission_id = fields.Many2one('sales.commission', string="Sales Commission")
    commission_amount = fields.Float(string='Commission Amount', compute='_compute_commission_amount')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id, string='Company',
                                 readonly=True)
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  default=lambda self: self.env.user.company_id.currency_id.id)
    sale_order_id = fields.Many2one('sale.order', string='Sale Order')
    property_id = fields.Many2one(related='sale_order_id.property_id')

    sale_amount_total = fields.Monetary(related='sale_order_id.amount_total', string='Sales Price')
    commission_rate = fields.Float(string='Commission Rate')

    @api.depends('sale_amount_total', 'commission_rate')
    def _compute_commission_amount(self):
        for rec in self:
            if rec.commission_amount < 0:
                rec.commission_amount = 0
            else:
                rec.commission_amount = rec.sale_amount_total * (rec.commission_rate / 100)
