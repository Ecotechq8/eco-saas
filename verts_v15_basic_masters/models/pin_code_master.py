from odoo import api, fields, models, _


class PinCodeMaster(models.Model):
    _name = "pin.code.master"
    _description = "Pin Code Master"

    name = fields.Char(string='Pin Code', required=True)
    area_id = fields.Many2one('areas.basic.masters', string='Area')
    district_id = fields.Many2one('res.zone.district', string='District')
    city_id = fields.Many2one('cities.basic.masters', string='City')
    state_id = fields.Many2one('res.country.state', string='State')
    country_id = fields.Many2one('res.country', string='Country')
    
    @api.onchange('state_id')
    def _onchange_state_id(self):
        if self.state_id and self.state_id.country_id:
            self.country_id = self.state_id.country_id
    
    @api.onchange('city_id')
    def _onchange_city_id(self):
        if self.city_id:
            if self.city_id.state_id:
                self.state_id = self.city_id.state_id
            if self.city_id.country_id:
                self.country_id = self.city_id.country_id
