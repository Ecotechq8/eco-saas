from odoo import fields, models, api, _
from odoo.exceptions import UserError


class Picking(models.Model):
    _inherit = "stock.picking"

    def _is_internal_transfer_context(self):
        return (
            self.env.context.get('restricted_picking_type_code') == 'internal'
            or self.env.context.get('default_picking_type_code') == 'internal'
        )

    def _get_user_default_internal_picking_type(self):
        user = self.env.user.with_company(self.env.company)
        allowed_warehouses = user._get_allowed_stock_warehouses()
        warehouse = user._get_default_warehouse_id()
        if allowed_warehouses and warehouse not in allowed_warehouses:
            warehouse = allowed_warehouses[:1]
        if warehouse and warehouse.int_type_id:
            return warehouse.int_type_id
        return self.env['stock.picking.type']

    def _default_picking_type_id(self):
        if self._is_internal_transfer_context():
            picking_type = self._get_user_default_internal_picking_type()
            if picking_type:
                return picking_type.id
        return super()._default_picking_type_id()

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        picking_type = self.env['stock.picking.type'].browse(res.get('picking_type_id'))

        if (
            self._is_internal_transfer_context()
            or picking_type.code == 'internal'
        ):
            user_internal_type = self._get_user_default_internal_picking_type()
            if user_internal_type:
                res['picking_type_id'] = user_internal_type.id
                if (
                    'location_id' in fields_list
                    and not res.get('location_id')
                    and user_internal_type.default_location_src_id
                ):
                    res['location_id'] = user_internal_type.default_location_src_id.id
                if (
                    'location_dest_id' in fields_list
                    and not res.get('location_dest_id')
                    and user_internal_type.default_location_dest_id
                ):
                    res['location_dest_id'] = user_internal_type.default_location_dest_id.id

        return res

    def _get_location_domain(self):
        """Return allowed locations only for internal transfers."""
        if self.picking_type_id.code == 'internal':
            return [('id', 'in', self.env.user.allow_location_ids.ids)]
        else:
            return []

    def button_validate(self):
        for picking in self:
            if picking.picking_type_id.code == 'internal':

                user_locations = self.env.user.allow_location_ids.ids
                dest_location = picking.location_dest_id.id

                if dest_location not in user_locations:
                    raise UserError(
                        _("You are not authorized to validate this transfer. Destination approval required.")
                    )
        return super(Picking, self).button_validate()
