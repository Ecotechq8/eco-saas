from odoo import fields, models, api, _
import logging
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class AccountTax(models.Model):
    _inherit = "account.tax"
    _description = "Account Tax"

    foodics_id = fields.Char("Foodics")

    def sync_single_taxes(self):
        """
        - Sync Product from foodics
        :return:
        """
        connector = self.env['foodic.connector'].search([('state', '=', 'authenticated')], limit=1)
        if not connector:
            raise ValidationError(_("Please check Foodics Configuration Detail."))
        if self.foodics_id:
            post_url = '/taxes/' + self.foodics_id
            response = connector.call_foodics_api('GET', post_url, {})
            data = self.prepare_data_foodics_to_odoo(response.get('data'))
            self.update(data)
        else:
            data = self.prepare_data_odoo_to_foodics()
            response = connector.call_foodics_api('POST', '/taxes', data)
            data = self.prepare_data_foodics_to_odoo(response.get('data'))
            self.update(data)

    def prepare_data_foodics_to_odoo(self, data):
        """
        Prepare The Data
        :param data:
        :return:
        """
        vals = {}
        connector = self.env['foodic.connector'].search([('state', '=', 'authenticated')], limit=1)
        taxes_data = connector.call_foodics_api(post_url='/taxes/%s' % data.get('id'))
        if taxes_data and taxes_data.get('data') and taxes_data.get('data').get('tax_groups'):
            tax_group_data = taxes_data.get('data').get('tax_groups')[0]
            if tax_group_data and tax_group_data.get('id'):
                tax_group = self.env['account.tax.group'].search([('foodics_id', '=', tax_group_data.get('id'))])
                if tax_group:
                    vals = {
                        'foodics_id': taxes_data.get('data').get('id'),
                        'name': taxes_data.get('data').get('name'),
                        'amount': taxes_data.get('data').get('rate'),
                        'tax_group_id': tax_group.id,
                    }
        return vals


    def prepare_data_odoo_to_foodics(self):
        """
        Prepare The Data for odoo to foodics
        :param data:
        :return:
        """
        response = {
            'name': self.name,
            'rate': self.amount,
            "tax_groups": [
                {
                    "id": self.tax_group_id.foodics_id
                }
            ]
        }
        return response

    # def sync_specific_taxes(self):
    #     """
    #     Sync Specific Taxes
    #     :return:
    #     """
    #     foodic_connector_id = self.env['foodic.connector'].search([('state', '=', 'authenticated')], limit=1)
    #     sync_specific_tax = foodic_connector_id.get_read_data(post_url="/taxes")
    #     for rec in sync_specific_tax.get('data'):
    #         sync_specific_tax = foodic_connector_id.get_read_data(post_url="/taxes/" + rec.get('id'))
    #         for each_rec in sync_specific_tax.get('data'):
    #             if self.foodics_id == each_rec.get('id'):
    #                 vals = {
    #                     'name': each_rec.get('name'),
    #                     'amount': each_rec.get('rate'),
    #                 }
    #                 self.write(vals)
    #
    # def sync_all_taxes(self):
    #     """
    #     Sync All Taxes
    #     :return:
    #     """
    #     foodic_connector_id = self.env['foodic.connector'].search([('state', '=', 'authenticated')], limit=1)
    #     sync_all_taxes = foodic_connector_id.get_read_data(post_url="/taxes")
    #     for rec in sync_all_taxes.get('data'):
    #         sync_all_taxes = foodic_connector_id.get_read_data(post_url="/taxes/" + rec.get('id'))
    #         for each_rec in sync_all_taxes.get('data'):
    #             if not self.search([('foodics_id', '=', each_rec.get('id'))]):
    #                 vals = {
    #                     'foodics_id': each_rec.get('id'),
    #                     'name': each_rec.get('name'),
    #                     'amount': each_rec.get('rate'),
    #                 }
    #                 self.create(vals)
    #
    #             for each in self:
    #                 if each.foodics_id and each.foodics_id == each_rec.get('id'):
    #                     vals = {
    #                         'name': each_rec.get('name'),
    #                         'amount': each_rec.get('rate'),
    #                     }
    #                     each.write(vals)
