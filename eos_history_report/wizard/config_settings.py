import xlsxwriter
from io import BytesIO
from odoo import models, fields, api

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    eos_calculation_type = fields.Selection([
        ('monthly','Monthly'),
        ('daily','daily'),
    ])

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        res.update(eos_calculation_type=params.get_param('eos_calculation_type', default=False))
        return res
        
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param("eos_calculation_type", self.eos_calculation_type)
