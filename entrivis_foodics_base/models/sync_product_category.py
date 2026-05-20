from odoo import fields, models, api, _
import logging
_logger = logging.getLogger(__name__)


class ProductCategory(models.Model):
    _inherit = "product.category"
    _description = "Product Category"

    foodics_id = fields.Char("Foodics")

    def sync_specific_category(self):
        """
        Sync Specific Product Category
        :return:
        """
        foodic_connector_id = self.env['foodic.connector'].search([('state', '=', 'authenticated')], limit=1)
        sync_specific_category = foodic_connector_id.call_foodics_api('GET', "/categories", {})
        for rec in sync_specific_category.get('data'):
            if self.foodics_id == rec.get('id'):
                vals = {
                    'name': rec.get('name'),
                }
                self.write(vals)

    def sync_all_category(self):
        """
        Sync All Product Category
        :return:
        """
        foodic_connector_id = self.env['foodic.connector'].search([('state', '=', 'authenticated')], limit=1)
        sync_specific_category = foodic_connector_id.call_foodics_api('GET', "/categories", {})
        for rec in sync_specific_category.get('data'):
            if not self.search([('foodics_id', '=', rec.get('id'))]):
                vals = {
                    'foodics_id': rec.get('id'),
                    'name': rec.get('name'),
                }
                self.create(vals)

            for each in self:
                if each.foodics_id and each.foodics_id == rec.get('id'):
                    vals = {
                        'name': rec.get('name'),
                    }
                    each.write(vals)

    def prepare_category_data(self, data):
        return {
            'foodics_id': data.get('id'),
            'name': data.get('name'),
        }
