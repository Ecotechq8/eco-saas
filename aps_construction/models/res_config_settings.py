# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    move_boq_to_sale_order = fields.Boolean(string="Move BOQ line to Sale Order")
    adv_customer = fields.Many2one('account.account', string='Advanced Customer', related='company_id.adv_customer',
                                   readonly=False)
    customer_retention = fields.Many2one('account.account', string='Customer Retention',
                                         related='company_id.customer_retention', readonly=False)

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        move_boq_to_sale_order = params.get_param('move_boq_to_sale_order', default=False)
        res.update(move_boq_to_sale_order=move_boq_to_sale_order)
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param("move_boq_to_sale_order", self.move_boq_to_sale_order)
