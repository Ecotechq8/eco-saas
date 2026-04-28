from odoo import models, fields, api, _


class Employee(models.Model):
    _inherit = 'hr.employee'

    has_social_insurance = fields.Boolean(compute='get_social_insurance')

    def get_social_insurance(self):
        for item in self:
            item.has_social_insurance = False
            if item.country_id.name == 'Saudi Arabia':
                item.has_social_insurance = True
