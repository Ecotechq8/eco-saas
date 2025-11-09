# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class CompanyDocumentType(models.Model):
    _name = 'company.document.type'

    name = fields.Char(string="Name", required=True, help="Name")
    before_days = fields.Integer(string="Days", help="How many number of days before to get the notification email")
    notification_type = fields.Selection([
        ('single', 'Notification on expiry date'),
        ('multi', 'Notification before few days'),
        ('everyday', 'Everyday till expiry date'),
        ('everyday_after', 'Notification on and after expiry')], string='Notification Type')
