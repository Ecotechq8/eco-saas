from odoo import fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    allow_location_ids = fields.Many2many('stock.location')
    inventory_dashboard_warehouse_ids = fields.Many2many(
        'stock.warehouse',
        'res_users_inventory_dashboard_warehouse_rel',
        'user_id',
        'warehouse_id',
        string='Inventory Dashboard Warehouses',
        check_company=True,
        help='Warehouses visible on the Inventory Dashboard. If empty, the Default Warehouse is used.',
    )

    @property
    def SELF_READABLE_FIELDS(self):
        return super().SELF_READABLE_FIELDS + ['inventory_dashboard_warehouse_ids']

    @property
    def SELF_WRITEABLE_FIELDS(self):
        return super().SELF_WRITEABLE_FIELDS + ['inventory_dashboard_warehouse_ids']
