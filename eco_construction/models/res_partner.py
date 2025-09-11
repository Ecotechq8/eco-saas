# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    adv_customer = fields.Many2one('account.account',string='Advanced Customer',required=False,company_dependent=True,domain="[('account_type', '=', 'asset_receivable'), ('deprecated', '=', False)]")
    customer_retention = fields.Many2one('account.account',string='Customer Retention',required=False,company_dependent=True,domain="[('account_type', '=', 'asset_receivable'), ('deprecated', '=', False)]")

class ResCompany(models.Model):
    _inherit = 'res.company'

    adv_customer = fields.Many2one('account.account', string='Advanced Customer', required=False)
    customer_retention = fields.Many2one('account.account', string='Customer Retention', required=False)
