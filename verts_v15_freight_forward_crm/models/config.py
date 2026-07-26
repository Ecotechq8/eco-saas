# -*- coding: utf-8 -*-

import time
import datetime
from dateutil.relativedelta import relativedelta
from lxml import etree
import odoo
from odoo import SUPERUSER_ID
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class FfCrmConfig(models.Model):
    _name = 'ff.crm.config'

    air_price_request_email = fields.Many2many('res.partner', 'air_price_request_email_ids', 'config_id', 'partner_id', string='Air Price Request Email Ids')
    sea_price_request_email = fields.Many2many('res.partner', 'sea_price_request_email_ids', 'config_id', 'partner_id', string='Sea Price Request Email Ids')
    land_price_request_email = fields.Many2many('res.partner', 'land_price_request_email_ids', 'config_id', 'partner_id', string='Land Price Request Email Ids')

    @api.model
    def default_get(self, fields):
        res = super(FfCrmConfig, self).default_get(fields)
        air_emails = []
        sea_emails = []
        land_emails = []
        last_id = self.search([])
        if last_id:
            for partner_id in last_id[-1].air_price_request_email:
                air_emails.append(partner_id.id)
            for partner_id in last_id[-1].sea_price_request_email:
                sea_emails.append(partner_id.id)
            for partner_id in last_id[-1].land_price_request_email:
                land_emails.append(partner_id.id)
            res['air_price_request_email'] = air_emails
            res['sea_price_request_email'] = sea_emails
            res['land_price_request_email'] = land_emails
        return res
    
    def execute(self):
        config = self.env['res.config'].next() or {}
        if config.get('type') not in ('ir.actions.act_window_close',):
            return config
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
