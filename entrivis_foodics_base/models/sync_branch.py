from odoo import fields, models, api, _
import logging
_logger = logging.getLogger(__name__)


class PosConfig(models.Model):
    _inherit = "pos.config"
    _description = "Pos Config"

    foodics_id = fields.Char("Foodics")

    def sync_specific_branch(self):
        """
        Sync Specific POS Branch
        :return:
        """
        foodic_connector_id = self.env['foodic.connector'].search([('state', '=', 'authenticated')], limit=1)
        sync_specific_branch = foodic_connector_id.call_foodics_api('GET', '/branches', {})
        for rec in sync_specific_branch.get('data'):
            if self.foodics_id == rec.get('id'):
                vals = {
                    'name': rec.get('name'),
                }
                self.write(vals)

    def sync_all_branch(self):
        """
        Sync All POS Branch
        :return:
        """
        foodic_connector_id = self.env['foodic.connector'].search([('state', '=', 'authenticated')], limit=1)
        sync_all_branch = foodic_connector_id.call_foodics_api('GET', '/branches', {})
        for rec in sync_all_branch.get('data'):
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

    def prepare_branch_data(self, data):
        return {
            'foodics_id': data.get('id'),
            'name': data.get('name'),
        }

    def open_session_cb_backend(self, user_id):
        """ new session button

        create one if none exist
        access cash control interface if enabled or start a session
        """
        self.ensure_one()
        if not self.current_session_id:
            self._check_company_journal()
            self._check_company_invoice_journal()
            self._check_company_payment()
            self._check_currencies()
            self._check_profit_loss_cash_journal()
            self._check_payment_method_ids()
            # self._check_payment_method_receivable_accounts()
            session = self.env['pos.session'].create({
                'user_id': user_id.id,
                'config_id': self.id
            })
            session.update_closing_control_state_session('Foodics')
        else:
            session = self.current_session_id
        return session
