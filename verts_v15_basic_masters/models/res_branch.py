from odoo import api, fields, models, _


class ResBranch(models.Model):
    _name = "res.branch"
    _description = "Branch"

    name = fields.Char(string='Branch Name', required=True)
    code = fields.Char(string='Branch Code')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    active = fields.Boolean(string='Active', default=True)
    street = fields.Char(string='Street')
    street2 = fields.Char(string='Street2')
    city = fields.Char(string='City')
    state_id = fields.Many2one('res.country.state', string='State')
    country_id = fields.Many2one('res.country', string='Country')
    zip = fields.Char(string='Zip')
    phone = fields.Char(string='Phone')
    email = fields.Char(string='Email')
    website = fields.Char(string='Website')
    logo_branch = fields.Binary(string="Branch Logo", attachment=True)
    
    @api.onchange('state_id')
    def _onchange_state_id(self):
        if self.state_id and self.state_id.country_id:
            self.country_id = self.state_id.country_id
