# -*- coding: utf-8 -*-
# Copyright 2021 Verts Services India Pvt Ltd.
# http://www.verts.co.in

from odoo import api, fields, models, _

class ResPartner(models.Model):
    _inherit = "res.partner"

    code = fields.Char(string='Code', required=True, copy=False, default=lambda self: _('New'))
    party_full_name = fields.Char(string='Partner Full Name')
    is_export_partner = fields.Boolean(string='Is Export Partner')
    is_shipping_line = fields.Boolean(string='Is Shipping Line')
    is_cha = fields.Boolean(string='Is Custom House Agent')
    is_airline = fields.Boolean(string='Is Airline')
    is_agent = fields.Boolean(string="Is Agent", default=False, help="Enable for Agent Partner for Agent Order")
    airline_code = fields.Char(string='Airline Code')
    airline_no = fields.Char(string='Airline No.')

    @api.model
    def create(self, vals):
        '''Partner Create Function'''
        if vals.get('code', _('New')) == _('New'):
            if self._context.get('default_customer_rank') == 1 or 'customer_rank' in vals and vals['customer_rank'] == True:
                vals['code'] = self.env['ir.sequence'].next_by_code('res.partner.customer.seq')
                # vals['name'] = str([vals['code']]) + str(vals['name'])
            else:
                vals['code'] = self.env['ir.sequence'].next_by_code('res.partner.vendor.seq')
        res = super(ResPartner, self).create(vals)
        return res

    def name_get(self):
        res = []
        for rec in self:
            name = rec.name
            if rec.code:
                name = '[%s]%s' % (rec.code, name)
            res.append((rec.id, name))
        return res


class ResCompany(models.Model):
    _inherit = "res.company"

    export_import_license_no = fields.Char(string="Export Import License No.")



