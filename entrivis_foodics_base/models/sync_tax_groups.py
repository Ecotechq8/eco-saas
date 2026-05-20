from odoo import fields, models, api, _
import logging

_logger = logging.getLogger(__name__)


class AccountTaxGroup(models.Model):
    _inherit = "account.tax.group"
    _description = "Account Tax Group"

    foodics_id = fields.Char("Foodics")

    def sync_specific_tax_group(self):
        """
        Sync Specific Tax Group
        :return:
        """
        foodic_connector_id = self.env['foodic.connector'].search([('state', '=', 'authenticated')], limit=1)
        post_url = '/tax_groups'
        sync_specific_tax_group = foodic_connector_id.call_foodics_api('GET', post_url, {})
        for rec in sync_specific_tax_group.get('data'):
            if self.foodics_id == rec.get('id'):
                vals = {
                    'name': rec.get('name'),
                }
                self.write(vals)

    def sync_all_tax_group(self):
        """
        Sync All Tax Group
        :return:
        """
        foodic_connector_id = self.env['foodic.connector'].search([('state', '=', 'authenticated')], limit=1)
        post_url = '/tax_groups'
        sync_all_tax_group = foodic_connector_id.call_foodics_api('GET', post_url, {})
        for rec in sync_all_tax_group.get('data'):
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

    def prepare_tax_group_data(self, data):
        return {
                'foodics_id': data.get('id'),
                'name': data.get('name'),
            }