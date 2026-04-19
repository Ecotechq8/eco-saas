from odoo import api, fields, models, _


class IndustryVertical(models.Model):
    _name = "industry.vertical"
    _description = "Industry Vertical"

    name = fields.Char(string='Name', required=True)


class Source(models.Model):
    _name = "source"
    _description = "Source"

    name = fields.Char(string='Name', required=True)
