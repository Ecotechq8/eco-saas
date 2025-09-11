# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd. - ©
# Technaureus Info Solutions Pvt. Ltd 2020. All rights reserved.
from odoo import api, fields, models
from ast import literal_eval


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    squarefeet_pricing = fields.Float(string='Squarefeet Pricing')

    @api.model
    def set_values(self):
        res = super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].set_param('facility_management_erp.squarefeet_pricing', self.squarefeet_pricing)
        return res

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        squarefeet_pricing = ICPSudo.get_param('facility_management_erp.squarefeet_pricing')
        res.update(
            squarefeet_pricing=squarefeet_pricing,
        )
        return res


