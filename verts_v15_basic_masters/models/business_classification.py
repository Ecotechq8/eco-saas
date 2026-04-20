from odoo import fields, models, api


class IndustryVertical(models.Model):
    _name = "industry.vertical"
    _description = "Industry Vertical"

    name = fields.Char(string='Industry Vertical', required=True)


class Source(models.Model):
    _name = "source"
    _description = "Source"

    name = fields.Char(string='Source', required=True)

