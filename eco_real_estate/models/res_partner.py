from odoo import fields, models, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_agent = fields.Boolean(string='Is_agent', required=False)
    id_type = fields.Selection(
        string=' Type',
        selection=[('id', 'ID'),('pass', 'Passport'), ])
    id_number = fields.Char(string='Number', required=False)
        