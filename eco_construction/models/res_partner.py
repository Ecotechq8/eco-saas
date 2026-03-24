# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_construction = fields.Boolean(string='Allow Construction', compute='_compute_is_construction')

    @api.depends_context('company')
    def _compute_is_construction(self):
        for record in self:
            record.is_construction = self.env.company.is_construction

    adv_customer = fields.Many2one('account.account', string='Advanced Customer', required=False,
                                   company_dependent=True,
                                   domain="[('account_type', '=', 'asset_receivable'), ('deprecated', '=', False)]")
    customer_retention = fields.Many2one('account.account', string='Customer Retention', required=False,
                                         company_dependent=True,
                                         domain="[('account_type', '=', 'asset_receivable'), ('deprecated', '=', False)]")


class ResCompany(models.Model):
    _inherit = 'res.company'

    is_construction = fields.Boolean(string='Allow Construction')
    adv_customer = fields.Many2one('account.account', string='Advanced Customer', required=False)
    customer_retention = fields.Many2one('account.account', string='Customer Retention', required=False)
