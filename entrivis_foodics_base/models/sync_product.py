from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
import logging
import base64
import requests

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = "product.template"

    foodics_id = fields.Char("Foodics Id")
    is_sync_with_foodics = fields.Boolean("Is Sync With Foodics?")
    is_modifiers = fields.Boolean("Is Modifiers?")


class Product(models.Model):
    _inherit = "product.product"

    foodics_id = fields.Char("Foodics Id")
    is_sync_with_foodics = fields.Boolean("Is Sync With Foodics?")
    is_modifiers = fields.Boolean("Is Modifiers?")
    pricing_method = fields.Selection([('1', 'Pre Set'), ('2', 'Open price')], 'Pricing Method', default='1')
    selling_method = fields.Selection([('1', 'Unit'), ('2', 'Weight')], 'Selling Method', default='1')
    costing_method = fields.Selection([('1', 'Fixed'), ('2', 'From Ingredients')], 'Cost Method', default='1')

    def sync_single_products(self):
        """
        - Sync Product from foodics
        :return:
        """
        connector = self.env['foodic.connector'].search([('state', '=', 'authenticated')], limit=1)
        if not connector:
            raise ValidationError(_("Please check Foodics Configuration Detail."))
        if self.foodics_id:
            post_url = '/products/' + self.foodics_id
            response = connector.call_foodics_api('GET', post_url, {})
            data = self.prepare_data_foodics_to_odoo(response.get('data'))
            self.update(data)
        else:
            data = self.prepare_data_odoo_to_foodics()
            response = connector.call_foodics_api('POST', '/products', data)
            data = self.prepare_data_foodics_to_odoo(response.get('data'))
            self.update(data)

    def prepare_data_foodics_to_odoo(self, data, is_order=False):
        """
        Prepare The Data
        :param data:
        :return:
        """
        # commented due to taking time for each product sync
        # connector = self.env['foodic.connector'].search([('state', '=', 'authenticated')], limit=1)
        # foodics_category_id = False
        # category_data = False
        # if is_order:
        #     foodics_category_id = data.get('category', {}).get('id', False)
        #     category_data = data.get('category', {})
        #     category = self.env['product.category'].search([('foodics_id', '=', foodics_category_id)], limit=1)
        #
        # else:
        #     read_product = connector.call_foodics_api('GET', '/products/' + str(data.get('id')), {})
        #     if 'error' and 'error_message' in read_product:
        #         return {'error': read_product['error'],
        #                 'error_message': read_product['error_message'] + ' In Foodics Please try again'}
        #     category = self.env['product.category'].search([('foodics_id', '=', read_product.get('data').get(
        #         'category').get('id', False))], limit=1)
        #     if not category:
        #         foodics_category_id = read_product.get('data').get('category') and read_product.get('data').get(
        #             'category').get('id', False)
        #         category_data = connector.call_foodics_api('GET', '/categories/' + str(foodics_category_id), {}).get(
        #             'data')
        #         if 'error' and 'error_message' in category_data:
        #             return {'error': category_data['error'],
        #                     'error_message': category_data['error_message'] + ' In Foodics Please try again'}
        #
        # if not category:
        #     config_vals = self.env['product.category'].prepare_category_data(category_data)
        #     self.env['product.category'].create(config_vals)
        #     category = self.env['product.category'].search([('foodics_id', '=', foodics_category_id)], limit=1)

        response = {
            'foodics_id': data.get('id'),
            'default_code': data.get('sku') or '',
            'barcode': data.get('barcode') or '',
            'name': data.get('name'),
            'description': data.get('description'),
            'active': data.get('is_active'),
            # 'detailed_type': detailed_type,
            'available_in_pos': data.get('is_ready'),
            'lst_price': data.get('price'),
            'standard_price': data.get('cost'),
            # 'categ_id': category and category.id or self.env.ref('product.product_category_all').id,
            # 'image_1920': base64.b64encode(requests.get(data.get('image')).content) if data.get('image') else '',
            'pricing_method': str(data.get('pricing_method')),
            'selling_method': str(data.get('selling_method')),
            'costing_method': str(data.get('costing_method')),
            'is_sync_with_foodics': True,
        }
        return response

    def prepare_modifier_data_foodics_to_odoo(self, data, is_order=False, is_modifiers=False):
        """
        Prepare The Data
        :param data:
        :return:
        """
        connector = self.env['foodic.connector'].search([('state', '=', 'authenticated')], limit=1)
        foodics_category_id = False
        category_data = False
        if is_order:
            foodics_category_id = data.get('category', {}).get('id', False)
            category_data = data.get('category', {})
            category = self.env['product.category'].search([('foodics_id', '=', foodics_category_id)], limit=1)

        else:
            read_product = connector.call_foodics_api('GET', '/modifier_options/' + str(data.get('id')), {})
            if 'error' and 'error_message' in read_product:
                return {'error': read_product['error'],
                        'error_message': read_product['error_message'] + ' In Foodics Please try again'}
            category = self.env['product.category'].search([('foodics_id', '=', read_product.get('data').get('category') and read_product.get('data').get(
                'category').get('id', False))], limit=1)
            if not category:
                foodics_category_id = read_product.get('data').get('category') and read_product.get('data').get(
                    'category').get('id', False)
                category_data = connector.call_foodics_api('GET', '/categories/' + str(foodics_category_id), {}).get(
                    'data')
                if 'error' and 'error_message' in category_data:
                    return {'error': category_data['error'],
                            'error_message': category_data['error_message'] + ' In Foodics Please try again'}

        if not category:
            config_vals = self.env['product.category'].prepare_category_data(category_data)
            self.env['product.category'].create(config_vals)
            category = self.env['product.category'].search([('foodics_id', '=', foodics_category_id)], limit=1)

        response = {
            'foodics_id': data.get('id'),
            'default_code': data.get('sku') or '',
            'barcode': data.get('barcode') or '',
            'name': data.get('name'),
            'description': data.get('description'),
            'active': data.get('is_active'),
            'available_in_pos': data.get('is_ready'),
            'lst_price': data.get('price'),
            'standard_price': data.get('cost'),
            'categ_id': category and category.id or self.env.ref('product.product_category_all').id,
            # 'image_1920': base64.b64encode(requests.get(data.get('image')).content) if data.get('image') else '',
            # 'pricing_method': str(data.get('pricing_method')),
            # 'selling_method': str(data.get('selling_method')),
            # 'costing_method': str(data.get('costing_method')),
            'is_sync_with_foodics': True,
            'is_modifiers': is_modifiers
        }
        return response

    def prepare_data_odoo_to_foodics(self):
        """
        Prepare The Data for odoo to foodics
        :param data:
        :return:
        """
        # detailed_type = 'consu'
        # if data.get('is_stock_product'):
        #     detailed_type = 'product'
        # foodics_category_id = data.get('category') and data.get('category').get(id, False)
        # category = False
        # if foodics_category_id:
        #     category = self.env['product.category'].search([('foodics_id', '=', foodics_category_id)], limit=1)
        if self.is_sync_with_foodics:
            tax_group_id = self.taxes_id and self.taxes_id.tax_group_id and self.taxes_id.tax_group_id.foodics_id or ''
            category_id = self.categ_id and self.categ_id.foodics_id or ''
            is_stock_product = True if self.detailed_type == 'product' else False
            tags = []
            for tag in self.product_tag_ids:
                tags.append({
                    'id': tag.foodics_id.id,
                })
            return {
                "sku": self.default_code,
                "barcode": self.barcode,
                "name": self.name,
                "name_localized": "",
                "description": self.description,
                "description_localized": "",
                "image": "",
                "is_active": self.active,
                "is_stock_product": is_stock_product,
                "pricing_method": int(self.pricing_method),
                "selling_method": int(self.selling_method),
                "costing_method": int(self.costing_method),
                "preparation_time": 90,
                "price": self.lst_price,
                "cost": self.standard_price,
                "calories": 0,
                "tax_group_id": tax_group_id,
                "category_id": category_id,
                "tags": tags,
            }

    # Need to check for these parameters
    # "discounts": [
    #     {
    #         "id": "8d207fc3"
    #     }
    # ],
    # "timed_events": [
    #     {
    #         "id": "8d207fc3"
    #     }
    # ]
