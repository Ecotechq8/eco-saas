# -*- coding: utf-8 -*-
# Copyright 2022 Verts Services India Pvt Ltd.
# http://www.verts.co.in

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class Currency(models.Model):
    _inherit = "res.currency"

    def _convert(self, from_amount, to_currency, company, date, round=True):

        self, to_currency = self or to_currency, to_currency or self
        assert self, "convert amount from unknown currency"
        assert to_currency, "convert amount to unknown currency"
        assert company, "convert amount from unknown company"
        assert date, "convert amount from unknown date"
        # apply conversion rate
        manual_currency_rate = self.env.context.get('manual_currency_rate')
        if manual_currency_rate:
            if self == to_currency:
                amount = from_amount
            else:
                amount = from_amount * manual_currency_rate
            return to_currency.round(amount) if round else amount

            # Default fallback
        return super()._convert(from_amount, to_currency, company, date, round=round)

class AccountMove(models.Model):
    _inherit = "account.move"

    is_export = fields.Boolean(string="Is Export", default=False)
    # consignment_id = fields.Many2one(comodel_name='consignment.note', string='Consignment Id') #commented by kajal
    co_id = fields.Char(string="Is CO")
    cargo_id = fields.Many2one('cargo.order', string="Cargo ID", help='This will help to connect with cargo order ')
    stuffing_point_id = fields.Many2one('ports', string='Stuffing Point')
    port_of_loading_id = fields.Many2one('ports', string='Port of Loading')
    port_of_discharge_id = fields.Many2one('ports', string='Port of Discharge')
    dry_port_id = fields.Many2one('ports', string='Dry/ICD Port')
    cha_id = fields.Many2one('res.partner', string='Custom House Agent')
    consignor_id = fields.Many2one('res.partner', string="Consignor")
    consignee_id = fields.Many2one('res.partner', string="Consignee")
    notify_id = fields.Many2one('res.partner', string="Notify Party")
    cur_rate = fields.Float('Currency Rate.', digits='Currency Rate')
    reference_by_id = fields.Many2one('res.partner', 'Reference By')
    shipping_line = fields.Many2one('res.partner', string="Carrier")
    air_airline_no = fields.Char(string='Airline No(Prefix)')
    air_airline_code = fields.Char(string='Airline Code')
    agent_id = fields.Many2one('res.partner', string='Agent')

    order_type = fields.Selection([
        ('freight', 'Freight'),
        ('custom', 'Custom'),
        ('packing_and_removal', 'Packing And Removal'),
        ('warehousing', 'Warehousing')], string='Order Type')
    mode = fields.Selection([
        ('air', 'Air'),
        ('sea', 'Sea'),
        ('land', 'Land'),
        ('courier', 'Courier')
    ], string='Mode')
    import_export = fields.Selection([
        ('import', 'Import'),
        ('export', 'Export'),
        ('cross_trade', 'Cross Trade')
    ], string='Import/Export')

    freight_forwarding = fields.Boolean(string="Freight Forwarding", default=False)
    pre_cargo_carriage = fields.Boolean(string="Pre Cargo Carriage", default=False)
    custom_clearance = fields.Boolean(string="Custom Clearance", default=False)
    reefer_dry = fields.Selection([
        ('reefer', 'Reefer'),
        ('dry', 'Dry')], string="Reefer/Dry")
    genset = fields.Boolean(string="Genset", default=False)
    gsa_sales = fields.Boolean(string="GSA Sales", default=False)

    total_pieces = fields.Float(string='Total Pieces')
    total_gross_weight = fields.Float(string='Total Gross Weight')
    total_cbm = fields.Float(string='Total CBM')
    total_value = fields.Float(string='Total Value')
    total_chargeable_weight = fields.Float(string='Total Chargeable')
    total_volume_cbm = fields.Float(string='Total Volume (cbm)')
    total_volumetric_weight = fields.Float(string='Total Volumetric weight')
    account_analytic_id = fields.Many2one('account.analytic.account', string='Analytic Account')
    estimated_time_departure = fields.Date(string="Estimated Time of Departure")
    eta_port_of_destination = fields.Date(string="ETA - Port of Destination")
    date_order = fields.Date(string="Order date")
    flight_date_1 = fields.Date(string="Flight Date 1")
    flight_number_1 = fields.Char(string="Flight Number 1")
    bill_of_lading_no = fields.Char(string="Bill of Lading No.")
    # mawb = fields.Char(string="MAWB")
    mawb_land = fields.Char(string="MAWB")
    mawb = fields.Many2one('awb.master.line', string="MAWB")
    hawb = fields.Char(string="HAWB")
    customer_po_ref = fields.Char(string="Customer’s PO Ref.")
    ref_num = fields.Char(string='Shipper Ref. Number')
    move_container_line = fields.One2many('move.container.lines', 'move_id', string='Container Line')  ##by kajal

    # def action_post(self):
    #     res = super(AccountMove, self).action_post()
    #     payment_method_check = self.env.ref('account_check_printing.account_payment_method_check')
    #     for payment in self.filtered(lambda p: p.payment_method_id == payment_method_check and p.check_manual_sequencing):
    #         sequence = payment.journal_id.check_sequence_id
    #         payment.check_number = sequence.next_by_id()
    #     return res

    # for journal voucher print
    def cal_credit(self):
        credit = 0
        for rec in self.line_ids:
            credit = credit + rec.credit
        return credit

    # for journal voucher print
    def cal_debit(self):
        debit = 0
        for rec in self.line_ids:
            debit = debit + rec.debit
        return debit

    @api.onchange('shipping_line')
    def on_shipping_line(self):
        if self.shipping_line:
            self.air_airline_no = self.shipping_line.airline_no
            self.air_airline_code = self.shipping_line.airline_code
        else:
            self.air_airline_no = False
            self.air_airline_code = False


    @api.onchange('cur_rate')
    def _onchange_cur_rate(self):
        for val in self:
            if val.currency_id.id != val.company_currency_id.id:
                val.with_context(manual_currency_rate=val.cur_rate)._onchange_currency()

    @api.onchange('date', 'currency_id')
    def _onchange_currency(self):
        for val in self.with_context(manual_currency_rate=self.cur_rate):
            currency = val.currency_id or val.company_id.currency_id
            for line in val.line_ids:
                line.currency_id = currency


class MoveContainerlines(models.Model):
    _name = "move.container.lines"
    _description = "Move Container Line"

    move_id = fields.Many2one('account.move', string="Move ID") ##by kajal
    container_type_id = fields.Many2one('container.type', string="Container Type")
    count = fields.Integer(string="Count")
    container_qty = fields.Integer(string="Container Numbers")


class AccountJournal(models.Model):
    _inherit = "account.journal"

    order_type = fields.Selection([
        ('freight', 'Freight'),
        ('custom', 'Custom'),
        # ('packing_and_removal', 'Packing And Removal'),
        # ('warehousing', 'Warehousing')
    ], string='Order Type')
    mode = fields.Selection([
        ('air', 'Air'),
        ('sea', 'Sea'),
        ('land', 'Land'),
        ('courier', 'Courier')
    ], string='Mode')
    import_export = fields.Selection([
        ('import', 'Import'),
        ('export', 'Export'),
        ('cross_trade', 'Cross Trade')
    ], string='Import/Export')

    # internal_type = fields.Selection([
    #     ('sea_outbound', 'Sea Outbound'),
    #     ('sea_inbound', 'Sea Inbound'),
    #     ('air_outbound', 'Air Outbound'),
    #     ('air_inbound', 'Air Inbound'),
    #     ('custom_clearance', 'Custom Clearance'),
    #     ('packing_and_removal', 'Packing And Removal'),
    #     ('warehousing', 'Warehousing')
    # ], string='Internal Type')


class ExportAccountTcSetLines(models.Model):
    _name = "export.account.tc.set.lines"
    _description = 'Export Account Tc Set Lines'


class export_transporeter_lines(models.Model):
    _name = "export.transporeter.lines"
    _description = 'Export Transporeter Lines'
