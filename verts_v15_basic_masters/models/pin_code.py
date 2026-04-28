from odoo import tools, api, fields, models, _


class PinCodeMaster(models.Model):
    _name = "pin.code.master"
    _description = "Pincode Master"

    name = fields.Char(string='Pin Code', required=True)
    area_id = fields.Many2one('areas.basic.masters', string='Area')
    district_id = fields.Many2one('res.zone.district', string="District")
    city_id = fields.Many2one('cities.basic.masters', string='City')
    state_id = fields.Many2one('res.country.state', string="State")
    country_id = fields.Many2one('res.country', string="Country")

