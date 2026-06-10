from odoo import api, models


class StockPickingType(models.Model):
    _inherit = "stock.picking.type"

    @api.model
    def _get_user_inventory_dashboard_warehouses(self):
        return self.env.user._get_allowed_stock_warehouses()

    @api.model
    def _restrict_dashboard_domain_to_user_warehouses(self, domain):
        if not self.env.context.get("restrict_inventory_dashboard_warehouses"):
            return domain

        return self._restrict_domain_to_user_warehouses(domain)

    @api.model
    def _restrict_domain_to_user_warehouses(self, domain):
        warehouses = self._get_user_inventory_dashboard_warehouses()
        if not warehouses:
            return domain

        return [("warehouse_id", "in", warehouses.ids)] + list(domain or [])

    @api.model
    def name_search(self, name="", args=None, operator="ilike", limit=100):
        return super().name_search(
            name=name,
            args=self._restrict_domain_to_user_warehouses(args),
            operator=operator,
            limit=limit,
        )

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
