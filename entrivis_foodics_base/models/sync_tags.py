from odoo import fields, models, api, _


class ProductTag(models.Model):
    _inherit = "product.tag"

    foodics_id = fields.Char("Foodics Tag Id")

    def prepare_tag_data(self, data):
        return {
            'foodics_id': data.get('id'),
            'name': data.get('name'),
        }


class ResPartnerCategory(models.Model):
    _inherit = "res.partner.category"

    foodics_id = fields.Char("Foodics Tag Id")

    def prepare_cus_tag_data(self, data):
        return {
            'foodics_id': data.get('id'),
            'name': data.get('name'),
        }

