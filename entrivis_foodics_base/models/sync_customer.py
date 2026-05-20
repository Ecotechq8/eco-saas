from odoo import fields, models, api, _
import logging
_logger = logging.getLogger(__name__)
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = "res.partner"
    _description = "Res Partner"

    foodics_id = fields.Char("Foodics")


    def sync_address(self, address):
        """
        Sync Address
        :return:
        """
        foodic_connector_id = self.env['foodic.connector'].search([('state', '=', 'authenticated')], limit=1)
        address_data = foodic_connector_id.call_foodics_api('GET', "/customers/" + address.get('id'), {})
        address_foodics_id = self.search([('foodics_id', '=', address_data.get('id'))])
        address_id = False
        if not address_foodics_id:
            address_id = self.env['res.partner'].create({
                'street': address_data.get('description'),
                'name': address_data.get('name'),
                'type': 'other',
                'foodics_id': address_data.get('id'),
            })

        if address_foodics_id:
            address_foodics_id.write({
                'street': address_data.get('description'),
                'name': address_data.get('name'),
                'type': 'other',
            })

        return address_id.id if address_id else False

    def sync_single_customers(self):
        """
        - Sync customers from foodics
        :return:
        """
        connector = self.env['foodic.connector'].search([('state', '=', 'authenticated')], limit=1)
        if not connector:
            raise ValidationError(_("Please check Foodics Configuration Detail."))
        if self.foodics_id:
            post_url = '/customers/' + self.foodics_id
            response = connector.call_foodics_api('GET', post_url, {})
            data = self.prepare_data_foodics_to_odoo(response.get('data'))
            self.update(data)
        else:
            data = self.prepare_data_odoo_to_foodics()
            response = connector.call_foodics_api('POST', '/customers', data)
            data = self.prepare_data_foodics_to_odoo(response.get('data'))
            self.update(data)

    def prepare_data_foodics_to_odoo(self, data):
        """
        Prepare The Data
        :param data:
        :return:
        """
        """ dummy data"""
        vals = False
        child_lst = []
        for address in data.get('addresses', {}):
            address_id = self.sync_address(address)
            if address_id:
                child_lst.append((4, address_id))
        vals = {
            'name': data.get('name'),
            'phone': data.get('phone'),
            'email': data.get('email'),
            'active': True,
            'foodics_id': data.get('id'),
            'child_ids': child_lst,
        }
        return vals

    def prepare_data_odoo_to_foodics(self):
        """
        Prepare The Data for odoo to foodics
        :param data:
        :return:
        """
        child_lst = []
        for address in self.child_ids:
            address_id = self.sync_address(address)
            if address_id:
                child_lst.append((4, address_id))
        response = {
            'name': self.name,
            'phone': self.phone,
            'email': self.email,
            'is_blacklisted': self.active,
            'child_ids': child_lst,
        }
        return response


    # def sync_specific_customer(self):
    #     """
    #     Sync Specific Customer
    #     :return:
    #     """
    #     foodic_connector_id = self.env['foodic.connector'].search([('state', '=', 'authenticated')], limit=1)
    #     sync_specific_customer = foodic_connector_id.call_foodics_api('GET', "/customers", {})
    #     for rec in sync_specific_customer.get('data'):
    #         if self.foodics_id == rec.get('id'):
    #             child_lst = []
    #             for address in rec.get('addresses'):
    #                 address_id = self.sync_address(foodic_connector_id, address)
    #                 if address_id:
    #                     child_lst.append((4, address_id))
    #             vals = {
    #                 'name': rec.get('name'),
    #                 'phone': rec.get('phone'),
    #                 'email': rec.get('email'),
    #                 'active': rec.get('is_blacklisted'),
    #                 'child_ids': child_lst,
    #             }
    #             self.write(vals)
    #
    # def sync_all_customer(self):
    #     """
    #     Sync All Customer
    #     :return:
    #     """
    #     foodic_connector_id = self.env['foodic.connector'].search([('state', '=', 'authenticated')], limit=1)
    #     sync_specific_customer = foodic_connector_id.call_foodics_api('GET', "/customers", {})
    #     for rec in sync_specific_customer.get('data'):
    #         if not self.search([('foodics_id', '=', rec.get('id'))]):
    #             vals = {
    #                 'foodics_id': rec.get('id'),
    #                 'name': rec.get('name'),
    #                 'phone': rec.get('phone'),
    #                 'email': rec.get('email'),
    #                 'active': rec.get('is_blacklisted'),
    #                 'child_ids': self.sync_address(foodic_connector_id, rec.get('addresses')),
    #             }
    #             self.create(vals)
    #
    #         for each in self:
    #             if each.foodics_id and each.foodics_id == rec.get('id'):
    #                 vals = {
    #                     'name': rec.get('name'),
    #                     'phone': rec.get('phone'),
    #                     'email': rec.get('email'),
    #                     'active': rec.get('is_blacklisted'),
    #                     'child_ids': self.sync_address(foodic_connector_id, rec.get('addresses')),
    #                 }
    #                 each.write(vals)
