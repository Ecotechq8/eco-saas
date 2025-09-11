# -*- coding: utf-8 -*-


from odoo import api, fields, models, _
from odoo.exceptions import UserError


class LoanRejectReason(models.TransientModel):
    _name = "wizard.so.payment"

    order_id = fields.Many2one('sale.order', string='Sale Order', readonly=True)
    partner_id = fields.Many2one('res.partner', string='Customer', related='order_id.partner_id',store=True)
    company_id = fields.Many2one("res.company", string="Company", default=lambda self: self.env.company)
    adv_customer = fields.Many2one('account.account', string='Advanced Customer', compute='_compute_adv_customer',store=True)
    # customer_retention = fields.Many2one('account.account', string='Customer Retention', compute='_compute_customer_retention',store=True)
    currency_id = fields.Many2one(related='order_id.currency_id')
    journal_id = fields.Many2one('account.journal', string='Payment Method')

    amount_total = fields.Monetary(string='Total Amount' ,compute='_compute_amount_total')
    amount_type = fields.Selection(
        string='Amount Type',
        selection=[('percent', 'Percentage'), ('fixed', 'Fixed Amount')
                   ], default='percent')

    adv_amount = fields.Float(string='Advanced Amount', required=False)
    retention_amount = fields.Float(string='Retention Amount', required=False)
    adv_percent = fields.Float(string='Advanced Percent %',related='order_id.adv_percent' )
    retention_percent = fields.Float(string='Retention Percent %')


    @api.depends('partner_id','company_id')
    def _compute_adv_customer(self):
        self.adv_customer = None
        if self.partner_id.adv_customer :
           self.adv_customer = self.partner_id.adv_customer
        else:
            self.adv_customer = self.company_id.adv_customer

    @api.depends('order_id.amount_untaxed', 'adv_percent')
    def _compute_amount_total(self):
        self.amount_total = 0.0
        if self.adv_percent > 0 :
            self.amount_total = self.order_id.amount_untaxed * (self.adv_percent/100)
    # @api.depends('partner_id','company_id')
    # def _compute_customer_retention(self):
    #     self.customer_retention = None
    #     if self.partner_id.customer_retention:
    #         self.customer_retention = self.partner_id.customer_retention
    #     else:
    #         self.customer_retention = self.company_id.customer_retention
    #     print('self.customer_retention',self.customer_retention)
    # @api.constrains('adv_percent','retention_percent','adv_amount','retention_amount','amount_total')
    # def check_total(self):
    #     if self.amount_total <= 0 :
    #         raise UserError(_("The Total Amount  must be > 0  '%s'.", self.amount_total))
    #     if self.amount_type == 'percent':
    #         total_percent = self.adv_percent + self.retention_percent
    #         print('total_percent',total_percent)
    #         if total_percent != 100:
    #             raise UserError(_("The sum of the Advanced Percent and Retention Percent must be = 100%."))
    #     else:
    #         total_amount = self.adv_amount + self.retention_amount
    #         if total_amount != self.amount_total :
    #             raise UserError(_("The sum of the Advanced Amount and Retention Amount must be = '%s'.",self.amount_total))

    @api.constrains('partner_id','adv_customer')
    def check_accounts(self):
        if self.partner_id:
            if not self.adv_customer :
                raise UserError(_("you must Set Advanced Customer Account First"))
            # if not self.customer_retention :
            #     raise UserError(_("you must Set Customer Retention Account First"))

    def action_create_payment(self):
        payment_dict = {
            'partner_id': self.partner_id.id,
            'account_id': self.partner_id.adv_customer.id,
            # 'amount': self.amount_total,
            'amount1': self.amount_total,
            'is_construction': True,
            'send_rec_money': 'rece',
            'payment_method': self.journal_id.id,
        }
        # if self.amount_type == 'fixed' :
        #     payment_dict.update({
        #         'adv_percent': (self.adv_amount / self.amount_total) *100,
        #         'retention_percent': (self.retention_amount/ self.amount_total) *100 ,
        #     })
        # else:
        #     payment_dict.update({
        #         'adv_percent': self.adv_percent ,
        #         'retention_percent': self.retention_percent,
        #     })
        # print('payment_dict',payment_dict)
        # print(1/0)
        payment = self.env['normal.payments'].create(payment_dict)

        result = self.env.ref("check_management.check_action_norm_payment_receive_action")
        action_ref = result or False
        result = action_ref.sudo().read()[0]
        result['domain'] = str([('id', 'in', [payment.id])])
        return result
