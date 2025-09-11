# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions,_
# from datetime import date, datetime, time, timedelta

class CheckBook(models.Model):
    _name = 'check.book'

    def get_currency(self):
        return self.env['res.users'].search([('id', '=', self.env.user.id)]).company_id.currency_id.id

    # partner_id = fields.Many2one("res.partner")
    name = fields.Char("name",required=True)
    payment_journal = fields.Many2one("account.journal",required=True,domain=[('type','=','bank')])
    amount = fields.Monetary(track_visibility='onchange')
    currency_id = fields.Many2one(comodel_name="res.currency", default=get_currency)
    #bank
    bank_id = fields.Many2one('res.bank', string=_("Bank"),required=True)

    number_of_digits = fields.Integer("No of Digits")
    start_check_no = fields.Integer()
    last_check_no = fields.Integer()

    next_check_no = fields.Integer(readonly=True)
    check_ids = fields.One2many("check.management",'check_book_id')

    state = fields.Selection([
        ('draft','Draft'),
        ('active','Active'),
        ('closed','Closed'),
    ],default="draft")

    def activate_check_book(self):
        for rec in self:
            rec.next_check_no = rec.start_check_no
            rec.state = 'active'

    def close_check_book(self):
        for rec in self:
            rec.state = 'closed'

    def cancel_current_check(self):
        for rec in self:
            self.env['check.management'].create({
                'state':'canceled',
                'check_book_id':rec.id,
                'check_type':'pay',
                'check_date':fields.Datetime.now(),
                'check_bank':rec.bank_id.id
            })
            rec.next_check_no+=1

            

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        default = dict(default or {})
        default['state'] = 'draft'
        return super(CheckBook, self).copy(default)
