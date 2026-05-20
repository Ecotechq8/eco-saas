from odoo import fields, models, api, _
from odoo.exceptions import ValidationError

class ResUsers(models.Model):
    _inherit = "res.users"

    foodics_id = fields.Char("Foodics User Id")

    def prepare_user_data(self, data):
        return {
            'login': data.get('email'),
            'foodics_id': data.get('id'),
            'name': data.get('name'),
            'phone': data.get('phone'),
            'email': data.get('email'),
        }

    def sync_user(self):
        """
        - Sync Specific User from foodics
        :return:
        """
        connector = self.env['foodic.connector'].search([('state', '=', 'authenticated')], limit=1)
        # foodics_id = self.foodics_id
        foodics_id = '8cd1956b'
        if not connector:
            raise ValidationError(_("Please check Foodics Configuration Detail."))
        """Read User Data from Foodics"""
        # read_specific_user = connector.call_foodics_api(post_url='/users/%s'%foodics_id)
        """Dummy User Data For Testing"""
        read_specific_user = {
            "data": [{
                "id": "8cd1956b",
                "pin": "12345",
                "name": "Ben Conroys Demo",
                "number": "4179",
                "email": "bconroy@example.net",
                "phone": "12345678",
                "lang": "en",
                "email_verified": False,
                "is_owner": False,
                "must_use_fingerprint": True,
                "last_cashier_login_at": '',
                "display_localized_names": True,
                "last_login_at": '',
                "created_at": "2019-02-11 07:28:29",
                "updated_at": "2019-02-11 07:28:29",
                "deleted_at": '',
                "notifications": [
                    "cost_adjustment_transaction_closed",
                    "count_transaction_closed"
                ],
                "branches": [
                    {
                        "id": "8f7ab00a"
                    }
                ],
                "roles": [
                    {
                        "id": "8f7ab2e2",
                        "pivot": {
                            "user_id": "8f7ab326",
                            "role_id": "8f7ab2e2"
                        }
                    }
                ],
                "tags": [
                    {
                        "id": "8f7b9538",
                        "pivot": {
                            "user_id": "8f7ab326",
                            "tag_id": "8f7b9538"
                        }
                    }
                ]
            }
            ]
        }
        for user_data in read_specific_user.get('data'):
            """Read User Data from Foodics"""
            # foodics_id = user_data.get('id') or ''
            """Dummy User Data For Testing"""
            foodics_id = '8cd1956b'
            user_rec = self.env['res.users'].search([('foodics_id', '=', foodics_id)])
            user_vals = user_rec.prepare_user_data(user_data)
            if user_rec:
                user_rec.update(user_vals)


