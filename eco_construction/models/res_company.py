from odoo import models, api

class ResCompany(models.Model):
    _inherit = 'res.company'

    @api.model
    def _update_tax_rounding_globally(self):
        companies = self.search([])
        companies.write({'tax_calculation_rounding_method': 'round_globally'})
