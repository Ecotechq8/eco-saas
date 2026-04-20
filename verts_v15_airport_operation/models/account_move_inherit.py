# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class AccountMove(models.Model):
    _inherit = 'account.move'

    # Airport Operation Custom Fields
    cur_rate = fields.Float(string='Currency Rate', digits=(12, 6), default=1.0)
    airline_id = fields.Many2one('air.line', string='Airline')
    bill_of_lading_no = fields.Char(string='Bill of Lading No')
    customer_po_ref = fields.Char(string='Customer PO Reference')
    doc_number = fields.Char(string='Document Number')
    is_export = fields.Boolean(string='Is Export', default=False)
    mode = fields.Selection([('air', 'Air'), ('sea', 'Sea'), ('road', 'Road')], string='Mode')
    order_type = fields.Selection([('freight', 'Freight'), ('custom', 'Custom')], string='Order Type')
    import_export = fields.Selection([('import', 'Import'), ('export', 'Export')], string='Import/Export')
    remarks = fields.Text(string='Remarks')
    year_ref = fields.Char(string='Year Reference')
    flt_from = fields.Char(string='Flight From')
    flt_to = fields.Char(string='Flight To')
    route = fields.Char(string='Route')
    other_info = fields.Text(string='Other Info')
    estimated_time_departure = fields.Datetime(string='Estimated Time of Departure')
    eta_port_of_destination = fields.Datetime(string='ETA Port of Destination')
    consignment_id = fields.Char(string='Consignment ID')
    mawb = fields.Char(string='MAWB')
    hawb = fields.Char(string='HAWB')

    # Container Fields
    container_type_id = fields.Many2one('container.type', string='Container Type')
    container_qty = fields.Integer(string='Container Quantity', default=1)
    container_details = fields.Text(string='Container Details')
    total_pieces = fields.Integer(string='Total Pieces')
    total_cbm = fields.Float(string='Total CBM')
    total_gross_weight = fields.Float(string='Total Gross Weight')
    total_chargeable_weight = fields.Float(string='Total Chargeable Weight')
    total_volumetric_weight = fields.Float(string='Total Volumetric Weight')
    total_value = fields.Float(string='Total Value')

    # Weight Fields
    gross_wt = fields.Float(string='Gross Weight')
    chg_wt = fields.Float(string='Chargeable Weight')
    total_chg_wt = fields.Float(string='Total Chargeable Weight')

    # Flight Details
    flt_date = fields.Date(string='Flight Date')
    flt_number = fields.Char(string='Flight Number')
    flt_details = fields.Text(string='Flight Details')
    flt_details_ids = fields.One2many('inbound.flight.details', 'invoice_flight_id', string='Flight Details Lines')
    shipment_details = fields.Text(string='Shipment Details')
    weight_details = fields.Text(string='Weight Details')

    # GSA Fields
    gsa_invoice = fields.Boolean(string='GSA Invoice', default=False)
    bank = fields.Char(string='Bank')

    # Move Container Line
    move_container_line = fields.One2many('move.container.line', 'move_id', string='Container Lines')

    # Fetch Flight
    def fetch_flt(self):
        pass


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    # Custom fields for invoice lines
    discount = fields.Float(string='Discount (%)')
    analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Analytic Tags')


class MoveContainerLine(models.Model):
    _name = 'move.container.line'
    _description = 'Move Container Line'

    move_id = fields.Many2one('account.move', string='Invoice', required=True, ondelete='cascade')
    container_type_id = fields.Many2one('container.type', string='Container Type')
    quantity = fields.Integer(string='Quantity', default=1)
    description = fields.Char(string='Description')
