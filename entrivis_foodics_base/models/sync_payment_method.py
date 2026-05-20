from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class PosPaymentMethod(models.Model):
    _inherit = "pos.payment.method"

    foodics_id = fields.Char("Foodics Id")

    def prepare_payment_method_data(self, data):
        journal_domain = []
        if data.get('type') == 1:
            journal_domain.append(('type', '=', 'cash'))
        if data.get('type') == 2:
            journal_domain.append(('type', '=', 'bank'))
        journal_id = self.env['account.journal'].search(journal_domain, limit=1)
        if not journal_id:
            raise ValidationError(_("Please Configure Account Journal."))
        return {
            'foodics_id': data.get('id'),
            'name': data.get('name'),
            'journal_id': journal_id.id
        }

    def sync_payment_method(self):
        """
        - Sync Specific Payment Method from foodics
        :return:
        """
        connector = self.env['foodic.connector'].search([('state', '=', 'authenticated')], limit=1)
        if not connector:
            raise ValidationError(_("Please check Foodics Configuration Detail."))
        if self.foodics_id:
            post_url = '/payment_methods/' + self.foodics_id
            response = connector.call_foodics_api('GET', post_url, {})
            data = self.prepare_data_foodics_to_odoo_pay(response.get('data'))
            self.update(data)
        else:
            data = self.prepare_data_odoo_to_foodics_pay()
            response = connector.call_foodics_api('POST', '/payment_methods', data)
            data = self.prepare_data_foodics_to_odoo_pay(response.get('data'))
            self.update(data)

    def prepare_data_foodics_to_odoo_pay(self, data):
        """
        Prepare The Data
        :param data:
        :return:
        """
        response = {
            'foodics_id': data.get('id'),
            'name': data.get('name'),
        }
        return response

    def prepare_data_odoo_to_foodics_pay(self):
        """
        Prepare The Data for odoo to foodics
        :param data:
        :return:
        """
        return {
            "name": self.name,
        }
