# -*- coding: utf-8 -*-
# Copyright 2021 Verts Services India Pvt Ltd.
# http://www.verts.co.in

from datetime import datetime
from odoo import api, fields, models, tools
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from odoo import _
from odoo.exceptions import UserError, ValidationError


class SoInvoice(models.Model):
    _name = "so.invoice.value"
    _description = "So Invoice"

    name = fields.Char(string='Name',copy=False)
    sale_id = fields.Many2one('sale.order', "Sale Order",readonly=True)
    sale_state = fields.Selection(related='sale_id.state', string='Sale Status', readonly=True, store=True)
    currency_id = fields.Many2one("res.currency", default=lambda self: self.env.user.company_id.currency_id, string="Currency", readonly=True, required=True)
    total_amount = fields.Monetary(related='sale_id.amount_total', string='Total Amount', readonly=True)
    # invoice_id = fields.Many2one('account.invoice', "Invoice", readonly=True) ##by kajal
    notify_id =  fields.Many2one('res.partner', related='sale_id.notify_id', string="Notify Party",readonly=True)
    consignee_id =  fields.Many2one('res.partner', related='sale_id.consignee_id', string="Consignee Party ",readonly=True)
    # Not available in module
    # total_product = fields.Text(string='Desc Of Good',related='invoice_id.total_product')
    # amount_total_usd= fields.Float(string='Invoice Amount In USD',related='invoice_id.amount_total_usd')
    # stuffing_point_id = fields.Many2one('ports', related='invoice_id.stuffing_point_id',string='Stuffing Point')
    # port_of_loading_id = fields.Many2one('ports', related='invoice_id.port_of_loading_id', string='Port of Loading')
    production_date = fields.Date(string='Production Date',copy=False)
    stuffing_date = fields.Date(string='Stuffing Date',copy=False)
    etd_date = fields.Date(string='ETD',copy=False)
    eta_date = fields.Date(string='ETA',copy=False)
    # Not available in module
    # total_paid_amount = fields.Float(related='invoice_id.total_paid_amount',string='Received Amount In USD')
    counter= fields.Char(string='Counter Number',copy=False)
    line= fields.Char(string='Line',copy=False)
    remarks= fields.Char(string='Remarks',copy=False)
    # Not available in module
    # residual_usd= fields.Float(related='invoice_id.residual_usd',string='Total Balance Amount In USD')
    # invoice_amount = fields.Monetary(related='invoice_id.amount_total', string='Invoice Amount', readonly=True)
    # invoice_state = fields.Selection(related='invoice_id.state', string='Invoice Status', readonly=True)
    so_total_amount_usd = fields.Float(related='sale_id.so_amount_total_usd', string='SO Amount In USD', readonly=True)
    
    def unlink(self):
        for res in self:
            if res.sale_id:
                raise UserError(_('You cannot delete record.'))
        return super(SoInvoice, self).unlink()
    

    
    

