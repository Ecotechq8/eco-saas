from odoo import api, models


class StockPickingType(models.Model):
    _inherit = "stock.picking.type"

    @api.model
    def _get_user_inventory_dashboard_warehouses(self):
        user = self.env.user.with_company(self.env.company)
        if "inventory_dashboard_warehouse_ids" in user._fields:
            warehouses = user.inventory_dashboard_warehouse_ids
            if warehouses:
                return warehouses
        for field_name in ("property_warehouse_id", "default_warehouse_id"):
            if field_name in user._fields:
                warehouse = user[field_name]
                if warehouse:
                    return warehouse
        return self.env["stock.warehouse"]

    @api.model
    def _restrict_dashboard_domain_to_user_warehouses(self, domain):
        if not self.env.context.get("restrict_inventory_dashboard_warehouses"):
            return domain

        warehouses = self._get_user_inventory_dashboard_warehouses()
        if not warehouses:
            return domain

        return [("warehouse_id", "in", warehouses.ids)] + list(domain or [])

    @api.model
    def _search(self, domain, *args, **kwargs):
        return super()._search(
            self._restrict_dashboard_domain_to_user_warehouses(domain),
            *args,
            **kwargs
        )

    @api.model
    def read_group(self, domain, fields, groupby, *args, **kwargs):
        return super().read_group(
            self._restrict_dashboard_domain_to_user_warehouses(domain),
            fields,
            groupby,
            *args,
            **kwargs
        )
