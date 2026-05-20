from odoo import fields, models, api


class ModelName(models.Model):
    _name = 'foodics.history'
    _description = "It's show a history of foodics data sync"
    _rec_name = 'user_id'

    date_time = fields.Datetime('Date', readonly=1)
    user_id = fields.Many2one('res.users', 'User', readonly=1)
    req_url = fields.Char("Request Url", readonly=1)
    req_data = fields.Text("Request Data", readonly=1)
    response = fields.Text("Response", readonly=1)
