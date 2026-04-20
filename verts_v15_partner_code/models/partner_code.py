# -*- coding: utf-8 -*-
# Copyright 2020 Verts Services India Pvt Ltd.
# http://www.verts.co.in

from odoo import api, fields, models, tools, _


class PartnerCode(models.Model):
    _name = 'partner.code'
    _description = 'Partner Code'

    name = fields.Char(string='Partner Code')  # Removed deprecated size parameter (Odoo 18)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    partner_code_id = fields.Many2one('partner.code', string='Partner Code')

class ProjectProject(models.Model):
    _inherit = 'project.project'

    partner_code_id = fields.Many2one('partner.code', string='Account/Partner Code')

    @api.onchange('partner_id')
    def onchange_partner_id2(self):
        if self.partner_id:
           self.partner_code_id = self.partner_id.partner_code_id.id


    @api.onchange('partner_code_id')
    def on_change_partner_code_id(self):
        # Odoo 18: Direct assignment instead of {'value': ...} return
        self.partner_id = False
        if self.partner_code_id:
            partner_ids = self.env['res.partner'].search([('partner_code_id', '=', self.partner_code_id.id)], limit=1)
            if partner_ids:
                self.partner_id = partner_ids
