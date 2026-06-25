# -*- coding: utf-8 -*-

from odoo import api, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    @api.model
    def default_get(self, fields_list):
        self.env['res.company']._ensure_missing_internal_projects()
        return super().default_get(fields_list)
