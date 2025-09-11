# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    eos_with_wage = fields.Boolean(string='EOS Wage')
    eos_with_allow1 = fields.Boolean(string='EOS Housing Allowance')
    eos_with_allow2 = fields.Boolean(string='EOS Transportation Allowance')
    eos_with_allow3 = fields.Boolean(string='EOS Other Allowances')
    eos_with_allow4 = fields.Boolean(string='EOS Food Allowance')
    eos_with_allow5 = fields.Boolean(string='EOS Fuel Allowance')

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        res.update(eos_with_wage=params.get_param('eos_with_wage', default=False),
                   eos_with_allow1=params.get_param('eos_with_allow1', default=False),
                   eos_with_allow2=params.get_param('eos_with_allow2', default=False),
                   eos_with_allow3=params.get_param('eos_with_allow3', default=False),
                   eos_with_allow4=params.get_param('eos_with_allow4', default=False),
                   eos_with_allow5=params.get_param('eos_with_allow5', default=False))
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param("eos_with_wage", self.eos_with_wage)
        self.env['ir.config_parameter'].sudo().set_param("eos_with_allow1", self.eos_with_allow1)
        self.env['ir.config_parameter'].sudo().set_param("eos_with_allow2", self.eos_with_allow2)
        self.env['ir.config_parameter'].sudo().set_param("eos_with_allow3", self.eos_with_allow3)
        self.env['ir.config_parameter'].sudo().set_param("eos_with_allow4", self.eos_with_allow4)
        self.env['ir.config_parameter'].sudo().set_param("eos_with_allow5", self.eos_with_allow5)
