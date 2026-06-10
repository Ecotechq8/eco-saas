from odoo import fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    allow_location_ids = fields.Many2many('stock.location')
    inventory_dashboard_warehouse_ids = fields.Many2many(
        'stock.warehouse',
        'res_users_inventory_dashboard_warehouse_rel',
        'user_id',
        'warehouse_id',
        string='Allowed Warehouses',
        check_company=True,
        help=(
            'Warehouses this user can access in Inventory. '
            'Leave empty to allow access to all warehouses.'
        ),
    )

    def _get_allowed_stock_warehouses(self):
        self.ensure_one()
        return self.with_company(self.env.company).inventory_dashboard_warehouse_ids

    @property
    def SELF_READABLE_FIELDS(self):
        return super().SELF_READABLE_FIELDS + ['inventory_dashboard_warehouse_ids']
