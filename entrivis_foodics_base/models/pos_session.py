from odoo import models, fields, api


class PosSession(models.Model):
    _inherit = 'pos.session'

    def sync_pos_session(self):
        foodic_connector = self.env['foodic.connector'].search([('state', '=', 'authenticated')], limit=1)
        session_date = self.start_at.strftime("%Y-%m-%d")
        filter_order_data = foodic_connector.call_foodics_api('GET', f'/orders?filter[business_date]={session_date}',
                                                              {})
        if not filter_order_data or not filter_order_data.get('data'):
            error_message = "No orders data found"
            return foodic_connector.show_notification(error_message, 'danger')
        for order_info in filter_order_data.get('data'):
            foodics_id = order_info.get('id')
            order = self.env['pos.order'].search([('foodics_id', '=', foodics_id)])
            if not order:
                order_data = foodic_connector.call_foodics_api('GET', f"/orders/{foodics_id}", {})
                if 'error' in order_data and 'error_message' in order_data:
                    error_message = order_data['error_message']
                    return foodic_connector.show_notification(error_message, 'danger')
                foodic_connector.sync_pos_orders(order_data)
        success_message = "Orders synchronized successfully"
        return foodic_connector.show_notification(success_message, 'success')
