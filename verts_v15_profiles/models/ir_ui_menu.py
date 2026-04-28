# -*- encoding: utf-8 -*-

from odoo import api, models, SUPERUSER_ID


class IrUiMenu(models.Model):
    _inherit = 'ir.ui.menu'

    @api.model
    def _search(self, args, offset=0, limit=None, order=None, **kwargs):
        if self.env.uid != SUPERUSER_ID:
            menu_id = self.env['ir.model.data']._xmlid_to_res_id('verts_v15_profiles.menu_action_superadmin')
            args = [('id', '!=', menu_id)] + (args or [])
        return super()._search(args, offset=offset, limit=limit, order=order, **kwargs)
