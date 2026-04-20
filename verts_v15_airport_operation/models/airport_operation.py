# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class AirLine(models.Model):
    _name = "air.line"
    _description = "Air Line"

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code')
    active = fields.Boolean(string='Active', default=True)


class InboundFlight(models.Model):
    _name = "inbound.flight"
    _description = "Inbound Flight"
    _inherit = ['mail.thread']

    name = fields.Char(string='Name', required=True, copy=False, default='New', readonly=True)
    date = fields.Date(string='Date', default=fields.Date.context_today)
    loaded = fields.Boolean(string='Loaded', default=False)
    type = fields.Selection([('inbound', 'Inbound'), ('outbound', 'Outbound')], string='Type', default='inbound')
    airline_id = fields.Many2one('air.line', string='Airline')
    trx_type = fields.Char(string='Transaction Type')
    manifest = fields.Char(string='Manifest')
    gross_wt = fields.Float(string='Gross Weight')
    chrg_wt = fields.Float(string='Chargeable Weight')
    route = fields.Char(string='Route')
    route2 = fields.Char(string='Route 2')
    location = fields.Char(string='Location')
    flt_date = fields.Date(string='Flight Date')
    arr_date = fields.Date(string='Arrival Date')
    flt = fields.Char(string='Flight Number')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    flt_details_ids = fields.One2many('inbound.flight.details', 'flight_id', string='Flight Details')

    def action_create_invoice(self):
        pass


class InboundFlightDetails(models.Model):
    _name = "inbound.flight.details"
    _description = "Inbound Flight Details"

    flight_id = fields.Many2one('inbound.flight', string='Flight', required=True, ondelete='cascade')
    invoice_flight_id = fields.Many2one('gsa.invoice', string='Invoice Flight')
    flt_date = fields.Date(string='Flight Date')
    flt_number = fields.Char(string='Flight Number')
    route = fields.Char(string='Route')
    gross_wt = fields.Float(string='Gross Weight')
    chg_wt = fields.Float(string='Chargeable Weight')


class GsaInvoice(models.Model):
    _name = "gsa.invoice"
    _description = "GSA Invoice"
    _inherit = ['mail.thread']

    name = fields.Char(string='Name', required=True, copy=False, default='New', readonly=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    doc_number = fields.Char(string='Document Number')
    year_ref = fields.Char(string='Year Reference')
    flt_from = fields.Char(string='Flight From')
    flt_to = fields.Char(string='Flight To')
    customer_id = fields.Many2one('res.partner', string='Customer')
    remarks = fields.Text(string='Remarks')
    date = fields.Date(string='Date', default=fields.Date.context_today)
    airline_id = fields.Many2one('air.line', string='Airline')
    bank = fields.Char(string='Bank')
    gsa_invoice = fields.Boolean(string='GSA Invoice', default=False)
    invoice_line_ids = fields.One2many('gsa.invoice.line', 'invoice_id', string='Invoice Lines')
    flt_details_ids = fields.One2many('inbound.flight.details', 'invoice_flight_id', string='Flight Details')


class GsaInvoiceLine(models.Model):
    _name = "gsa.invoice.line"
    _description = "GSA Invoice Line"

    invoice_id = fields.Many2one('gsa.invoice', string='Invoice', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Product')
    name = fields.Char(string='Description')
    quantity = fields.Float(string='Quantity', default=1.0)
    price_unit = fields.Float(string='Unit Price')
    amount = fields.Float(string='Amount', compute='_compute_amount', store=True)
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
    exchange_rate = fields.Float(string='Exchange Rate', default=1.0)
    subtotal = fields.Float(string='Subtotal', compute='_compute_subtotal', store=True)

    @api.depends('quantity', 'price_unit')
    def _compute_amount(self):
        for line in self:
            line.amount = line.quantity * line.price_unit

    @api.depends('amount', 'exchange_rate')
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = line.amount * line.exchange_rate
