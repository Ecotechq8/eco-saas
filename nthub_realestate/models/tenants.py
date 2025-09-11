# -*- coding: utf-8 -*-
from odoo import models, fields, api,_


class Tenants(models.Model):
    _inherit = 'res.partner'

    is_tenant = fields.Boolean(string=_("Tenant"))
    is_owner = fields.Boolean(string=_("Owner"))

