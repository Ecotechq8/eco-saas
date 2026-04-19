# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime, timedelta
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.misc import formatLang, get_lang
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare
from num2words import num2words


class JobOrder(models.Model):
    _name = "job.order"
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _description = "job Order"
    _order = 'date_order desc, id desc'
    _check_company_auto = True

    def _default_validity_date(self):
        if self.env['ir.config_parameter'].get_param('sale.use_quotation_validity_days'):
            days = self.env.company.quotation_validity_days
            if days > 0:
                return fields.Date.to_string(datetime.now() + timedelta(days))
        return False

    @api.depends('order_line.price_total')
    def _amount_all(self):
        """
        Compute the total amounts of the SO.
        """
        for order in self:
            amount_untaxed = amount_tax = 0.0
            for line in order.order_line:
                amount_untaxed += line.price_subtotal
                amount_tax += line.price_tax
            order.update({
                'amount_untaxed': amount_untaxed,
                'amount_tax': amount_tax,
                'amount_total': amount_untaxed + amount_tax,
            })

    @api.model
    def _default_note(self):
        return self.env['ir.config_parameter'].get_param(
            'account.use_invoice_terms') and self.env.company.invoice_terms or ''

    @api.model
    def _get_default_team(self):
        return self.env['crm.team']._get_default_team_id()

    @api.onchange('fiscal_position_id')
    def _compute_tax_id(self):
        """
        Trigger the recompute of the taxes if the fiscal position is changed on the SO.
        """
        for order in self:
            order.order_line._compute_tax_id()

    def _get_default_dimension_uom_id(self):
        return self.env.ref('uom.product_uom_cm')

    def _get_default_weight_uom_id(self):
        return self.env.ref('uom.product_uom_kgm')

    name = fields.Char(string='Order Reference', required=True, copy=False, readonly=True,
                       index=True, default=lambda self: _('New'))
    origin = fields.Char(string='Source Document',
                         help="Reference of the document that generated this sales order request.")
    client_order_ref = fields.Char(string='Customer Reference', copy=False)
    # profitability = fields.Float(string='Profitability',compute='_compute_profatibility')##by kajal
    reference = fields.Char(string='Payment Ref.', copy=False,
                            help='The payment communication of this sale order.')
    invoice_amount = fields.Char(string="invoice Amount")
    profit_on_order = fields.Char(string="invoice Amount")
    state = fields.Selection([
        ('job_ready', 'job Ready'),
        ('cro_requested', 'CRO Requested'),
        ('cro_released', 'CRO Released'),
        ('stuff_started', 'Stuff Started'),
        ('stuffing_completed', 'Stuffing Completed'),
        ('sent_to_port', 'Sent to Port'),
        ('custom_clearance', 'Custom Clearance'),
        ('sealing_done', 'Sealing Done'),
        ('bill_of_lading_completed', 'Bill of Lading Completed'),
        ('vessel_set_to_sail', 'Vessel Set to Sail'),
        ('pre_alert', 'PreAlert'),
        ('destination_arrival', 'Destination Arrival'),
        ('destination_clearance', 'Destination Clearance'),
        ('delivery', 'Delivery'),
        ('completed', 'Completed'),
        ('book_with_the_flight', 'Book with the flight'),
        ('arrange_the_airway_bill', 'Arrange the Airway Bill'),
        ('pickup', 'Pickup'),
        ('booking_flight_schedule_confirmation', 'Booking/Flight Schedule Confirmation'),
        ('prealert_received', 'Prealert Received'),
        ('eta_shipment_arrival', 'ETA - Shipment Arrival'),
        ('document_readiness', 'Document Readiness'),
        ('job_arrival_notice', 'job Arrival Notice'),
        ('forward_for_clearance', 'Forward for Clearance'),
        ('under_clearance', 'Under Clearance'),
        ('awaiting_approval', 'Awaiting Approval'),
        ('custom_declaration_completed', 'Custom Declaration Completed'),
        ('under_custom_inspection', 'Under Custom Inspection'),
        ('out_for_delivery', 'Out for Delivery'),
        ('draft', 'Draft'),
        ('request_confirm', 'Request Confirm'),
        ('picking', 'Picking'),
        ('packing', 'Packing'),
        ('material_received', 'Material Received'),
        ('material_received_done', 'Material Received Done')],
        string='Status', readonly=True, copy=False, index=True, tracking=3)

    date_order = fields.Datetime(string='Order Date', required=True, index=True, copy=False,
                                 default=fields.Datetime.now,
                                 help="Creation date of draft/sent orders,\nConfirmation date of confirmed orders.")
    validity_date = fields.Date(string='Expiration', copy=False, default=_default_validity_date)
    is_expired = fields.Boolean(compute='_compute_is_expired', string="Is expired")

    create_date = fields.Datetime(string='Creation Date', readonly=True, index=True,
                                  help="Date on which sales order is created.")
    # order type selection
    # internal_type = fields.Selection([
    #     ('sea_outbound', 'Sea Outbound'),
    #     ('sea_inbound', 'Sea Inbound'),
    #     ('air_outbound', 'Air Outbound'),
    #     ('air_inbound', 'Air Inbound'),
    #     ('custom_clearance', 'Custom Clearance'),
    #     # ('packing_and_removal', 'Packing And Removal'),
    #     # ('warehousing', 'Warehousing')
    # ], string='Internal Type')
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
        # ('courier', 'Courier')
    ], string='Mode')
    import_export = fields.Selection([
        ('import', 'Import'),
        ('export', 'Export'),
        ('cross_trade', 'Cross Trade')
    ], string='Import/Export')
    user_id = fields.Many2one(
        'res.users', string='Salesperson', index=True, tracking=2, default=lambda self: self.env.user,
        domain=lambda self: [('groups_id', 'in', self.env.ref('sales_team.group_sale_salesman').id)])
    partner_id = fields.Many2one(
        'res.partner', string='Customer',
        required=True, change_default=True, index=True, tracking=1,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    partner_invoice_id = fields.Many2one(
        'res.partner', string='Invoice Address',
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]", )
    partner_shipping_id = fields.Many2one(
        'res.partner', string='Delivery Address',
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]", )

    pricelist_id = fields.Many2one(
        'product.pricelist', string='Pricelist', check_company=True,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]", tracking=1,
        help="If you change the pricelist, only newly added lines will be affected.")
    currency_id = fields.Many2one(related='pricelist_id.currency_id', depends=["pricelist_id"], store=True)
    order_line = fields.One2many('job.order.line', 'order_id', string='Order Lines',
                                 states={'cancel': [('readonly', True)], 'done': [('readonly', True)]}, copy=True,
                                 auto_join=True)

    note = fields.Text('Terms and conditions', default=_default_note)

    amount_untaxed = fields.Monetary(string='Untaxed Amount', store=True, readonly=True, compute='_amount_all',
                                     tracking=5)
    amount_by_group = fields.Binary(string="Tax amount by group", compute='_amount_by_group',
                                    help="type: [(name, amount, base, formated amount, formated base)]")
    amount_tax = fields.Monetary(string='Taxes', store=True, readonly=True, compute='_amount_all')
    amount_total = fields.Monetary(string='Total', store=True, readonly=True, compute='_amount_all', tracking=4)
    currency_rate = fields.Float("Currency Rate", compute='_compute_currency_rate', compute_sudo=True, store=True,
                                 digits=(12, 6), readonly=True,
                                 help='The rate of the currency to the currency of rate 1 applicable at the date of the order')

    payment_term_id = fields.Many2one(
        'account.payment.term', string='Payment Terms', check_company=True,  # Unrequired company
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]", )
    fiscal_position_id = fields.Many2one(
        'account.fiscal.position', string='Fiscal Position',
        domain="[('company_id', '=', company_id)]", check_company=True,
        help="Fiscal positions are used to adapt taxes and accounts for particular customers or sales orders/invoices."
             "The default value comes from the customer.")
    company_id = fields.Many2one('res.company', 'Company', required=True, index=True,
                                 default=lambda self: self.env.company)
    team_id = fields.Many2one(
        'crm.team', 'Sales Team',
        change_default=True, default=_get_default_team, check_company=True,  # Unrequired company
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")

    signature = fields.Image('Signature', help='Signature received through the portal.', copy=False, attachment=True,
                             max_width=1024, max_height=1024)
    signed_by = fields.Char('Signed By', help='Name of the person that signed the SO.', copy=False)
    signed_on = fields.Datetime('Signed On', help='Date of the signature.', copy=False)

    commitment_date = fields.Datetime('Delivery Date', copy=False,
                                      states={'done': [('readonly', True)], 'cancel': [('readonly', True)]},
                                      help="This is the delivery date promised to the customer. "
                                           "If set, the delivery order will be scheduled based on "
                                           "this date rather than product lead times.")
    amount_undiscounted = fields.Float('Amount Before Discount', compute='_compute_amount_undiscounted', digits=0)

    export = fields.Boolean('Exports')
    country_id = fields.Many2one('res.country', 'Country')
    port_of_loading_id = fields.Many2one('ports', 'Port of Loading')
    port_of_discharge_id = fields.Many2one('ports', 'Port of Discharge')
    cha_id = fields.Many2one('res.partner', 'Custom House Agent ')
    freight_forwarder_id = fields.Many2one('res.partner', 'Freight Forwarder')
    stuffing_point_id = fields.Many2one('ports', 'Stuffing Point')
    cur_rate = fields.Float('Currency Rate.')
    reference_by_id = fields.Many2one('res.partner', 'Reference By')
    # payment_term_ids = fields.Many2many('account.payment.term', 'payment_term_rel', 'order_id', 'payment_term_id',string='Payment Terms')
    sale_expense_line = fields.One2many('job.expense.line', 'order_id', 'Expenses')
    dry_port_id = fields.Many2one('ports', 'Dry/ICD Port')
    payment_term_line = fields.One2many('job.payment.term.line', 'order_id', 'Payment Details')
    sale_export_document_line = fields.One2many('job.export.document', 'order_id', 'Export Documents')
    total_expense = fields.Float(String="Total Expenses", store='True', compute='get_total_expense')
    rate_per_kg_on_expense = fields.Float(String="Rate Per Kg On Expense", store='True', compute='get_total_expense')
    is_load_ecgc_insurance = fields.Boolean(string="Is Load ECGC Insurance")
    schedule_lines = fields.One2many('job.schedule.line', 'sale_id', 'Schedule Lines')
    qc_pro_specification_line = fields.One2many('job.qc.specification.line', 'order_id',
                                                string='QC Product Specification Line')
    # team_id = fields.Many2one('crm.team', 'Sales Team', change_default=True, default=_get_default_team,
    #                           oldname='section_id')
    # user_id = fields.Many2one('res.users', string='Salesperson', index=True, track_visibility='onchange',
    #                           track_sequence=2, default=lambda self: self.env.user)
    export_tc_set_ids = fields.Many2many('term.and.condition.set', string="Terms & Condtions Set")
    export_so_tc_set_line = fields.One2many('job.so.tc.set.lines', 'export_so_tc_set_id',
                                            string='Terms And Condition Set Lines')
    ex_p_street = fields.Char('Street ', size=64)
    ex_p_street2 = fields.Char('Street2 ', size=64)
    ex_p_zip = fields.Char('Zip ', size=64)
    ex_p_city = fields.Char('City ', size=64)
    ex_p_state_id = fields.Many2one('res.country.state', string="State ")
    # origin1 = fields.Many2one('account.move', string="Origin")#by kajal
    ex_p_country_id = fields.Many2one('res.country', string="Country ")
    ex_d_street = fields.Char('Street', size=64)
    ex_d_street2 = fields.Char('Street2', size=64)
    ex_d_zip = fields.Char('Zip', size=64)
    ex_d_city = fields.Char('City', size=64)
    ex_d_state_id = fields.Many2one('res.country.state', string="State.")
    ex_d_country_id = fields.Many2one('res.country', string="Country.")
    consignee_id = fields.Many2one('res.partner', string="Consignee address ")
    consignor_id = fields.Many2one('res.partner', string="Consignor address ")
    notify_id = fields.Many2one('res.partner', string="Notify Party")
    so_invoice_id = fields.Many2one('so.invoice.value', string="So Inv Val")
    so_amount_total_usd = fields.Float(compute='_so_total_amount_usd', string='SO Amount In USD')

    # export_import = fields.Selection([('export', 'Export'), ('import', 'Import')], string='Export/Import')
    commodity = fields.Many2one('export.product.category', string="Commodity Type")
    shipment_by = fields.Selection([('sea', 'Sea'), ('air', 'Air')], string='Shipment By')
    shipping_line = fields.Many2one('res.partner', string="Shipping Line")
    vessel_id = fields.Many2one('ocean.vessel', string="Ocean Vessel")
    voyage_id = fields.Many2one('ocean.voyage', string="Voyage")
    shipping_order_no = fields.Char(string="Shipping Order No.")
    carrier_booking_no = fields.Char(string="Carrier Booking No.")
    eta_port_of_loading = fields.Date(string="ETA - Port of Loading")
    cut_off_time = fields.Date(string="Cut off Time")
    estimated_time_departure = fields.Date(string="Estimated Time of Departure")
    actual_time_sailing = fields.Date(string="Actual Time of Sailing")
    eta_port_of_destination = fields.Date(string="ETA - Port of Destination")
    est_transit_days = fields.Date(string="Est. Transit Days ")
    bill_of_lading_type = fields.Many2one('bill.lading.type', string="Bill of Lading Type")
    bill_of_lading_no = fields.Char(string="Bill of Lading No.")
    mawb = fields.Char(string="MAWB")
    hawb = fields.Char(string="HAWB")
    customer_po_ref = fields.Char(string="Customer’s PO Ref.")
    freight_forwarding_reqd = fields.Boolean(string="Freight Forwarding")
    pre_job_carriage_reqd = fields.Boolean(string="Pre job Carriage")
    custom_clearance_reqd = fields.Boolean(string="Custom Clearance")
    reefer_dry = fields.Selection([('reefer', 'Reefer'), ('dry', 'Dry')], string='Reefer/Dry')
    genset_reqd = fields.Boolean(string="Genset")
    incoterm_id = fields.Many2one('account.incoterms', string="Shipment (Inco) Terms")
    service_type = fields.Many2one('service.type', string="Service Type")
    weight_uom_id = fields.Many2one('uom.uom', string='Weight UOM', default=_get_default_weight_uom_id)
    dimension_uom_id = fields.Many2one('uom.uom', string='Dimension UOM', default=_get_default_dimension_uom_id)
    job_freight_line = fields.One2many('job.freight.line', 'job_id', string='job Freight Line', copy=True)
    total_pieces = fields.Float(string='Total Pieces', store=True, compute='_compute_sum_of_total')
    total_gross_weight = fields.Float(string='Total Gross Weight', store=True, compute='_compute_sum_of_total')
    total_cbm = fields.Float(string='Total CBM', store=True, compute='_compute_sum_of_total')
    total_value = fields.Float(string='Total Value', store=True, compute='_compute_sum_of_total')
    total_chargeable_weight = fields.Float(string='Total Chargeable weight', store=True,
                                           compute='_compute_sum_of_total')
    total_volume_cbm = fields.Float(string='Total Volume (cbm)', store=True, compute='_compute_sum_of_total')
    total_volumetric_weight = fields.Float(string='Total Volumetric weight', store=True,
                                           compute='_compute_sum_of_total')
    account_analytic_id = fields.Many2one('account.analytic.account', string='Analytic Account')
    opportunity_id = fields.Many2one('crm.lead', string='Opportunity ID')
    job_container_line = fields.One2many('job.container.lines', 'job_order_id', string='Container Line')

    def action_view_customer_quotes(self):
        self.ensure_one()
        result = {
            "type": "ir.actions.act_window",
            "res_model": "sale.order",
            "domain": [('job_order_id', '=', self.id)],
            "context": {"create": False},
            "name": "Customer Quotes",
            'view_mode': 'tree,form',
        }
        return result

    @api.depends('job_freight_line', 'job_freight_line.product_uom_quantity', 'job_freight_line.volume',
                 'job_freight_line.total_weight', 'job_freight_line.commercial_invoice_value',
                 'job_freight_line.total_chargeable_weight', 'job_freight_line.total_volume_cbm',
                 'job_freight_line.total_volumetric_weight')
    def _compute_sum_of_total(self):
        for res in self:
            total_pieces = 0.0
            total_gross_weight = 0.0
            total_cbm = 0.0
            total_value = 0.0
            total_chargeable_weight = 0.0
            total_volume_cbm = 0.0
            total_volumetric_weight = 0.0
            for line in res.job_freight_line:
                total_pieces += line.product_uom_quantity
                total_gross_weight += line.total_weight
                total_cbm += line.volume
                total_value += line.commercial_invoice_value
                total_chargeable_weight += line.total_chargeable_weight
                total_volume_cbm += line.total_volume_cbm
                total_volumetric_weight += line.total_volumetric_weight
            res.total_pieces = total_pieces
            res.total_gross_weight = total_gross_weight
            res.total_cbm = total_cbm
            res.total_value = total_value
            res.total_chargeable_weight = total_chargeable_weight
            res.total_volume_cbm = total_volume_cbm
            res.total_volumetric_weight = total_volumetric_weight

    @api.model
    def create(self, vals):
        """job Order Create Function"""
        # if vals.get('name', _('New')) == _('New') and vals.get('order_type') == 'freight' \
        #         and vals.get('mode') == 'sea' and vals.get('import_export') == 'import':
        #     vals['name'] = self.env['ir.sequence'].next_by_code('job.sea.import.seq')
        # elif vals.get('name', _('New')) == _('New') and vals.get('order_type') == 'freight' \
        #         and vals.get('mode') == 'sea' and vals.get('import_export') == 'export':
        #     vals['name'] = self.env['ir.sequence'].next_by_code('job.sea.export.seq')
        # elif vals.get('name', _('New')) == _('New') and vals.get('order_type') == 'freight' \
        #         and vals.get('mode') == 'air' and vals.get('import_export') == 'import':
        #     vals['name'] = self.env['ir.sequence'].next_by_code('job.air.import.seq')
        # elif vals.get('name', _('New')) == _('New') and vals.get('order_type') == 'freight' \
        #         and vals.get('mode') == 'air' and vals.get('import_export') == 'export':
        #     vals['name'] = self.env['ir.sequence'].next_by_code('job.air.export.seq')
        # elif vals.get('name', _('New')) == _('New') and vals.get('order_type') == 'custom' \
        #         and vals.get('import_export') == 'import':
        #     vals['name'] = self.env['ir.sequence'].next_by_code('job.clearance.import.seq')
        # elif vals.get('name', _('New')) == _('New') and vals.get('order_type') == 'custom' \
        #         and vals.get('import_export') == 'export':
        #     vals['name'] = self.env['ir.sequence'].next_by_code('job.clearance.export.seq')
        # elif vals.get('name', _('New')) == _('New') and vals.get('order_type') == 'freight' \
        #         and vals.get('mode') == 'land' and vals.get('import_export') == 'import':
        #     vals['name'] = self.env['ir.sequence'].next_by_code('job.land.import.seq')
        # elif vals.get('name', _('New')) == _('New') and vals.get('order_type') == 'freight' \
        #         and vals.get('mode') == 'land' and vals.get('import_export') == 'export':
        #     vals['name'] = self.env['ir.sequence'].next_by_code('job.land.export.seq')
        # # elif vals.get('name', _('New')) == _('New') and vals.get('order_type') == 'packing_and_removal':
        # #     vals['name'] = self.env['ir.sequence'].next_by_code('packing.removal.job.seq')
        # # elif vals.get('name', _('New')) == _('New') and vals.get('order_type') == 'warehousing':
        # #     vals['name'] = self.env['ir.sequence'].next_by_code('warehousing.job.seq')
        # else:
        vals['name'] = self.env['ir.sequence'].next_by_code('job.order.seq')

        if vals.get('order_type') == 'freight':
            vals['state'] = 'job_ready'
        if vals.get('order_type') == 'custom':
            vals['state'] = 'prealert_received'
        res = super(JobOrder, self).create(vals)
        return res

    # def _compute_origin_value(self):
    #     if self.partner_id:
    #         self.name = self.origin1.co_id.id
    #
    #     else:
    #         self.name = self.origin1.co_id.id

    # def _compute_profatibility(self):
    #     bill = self.origin1.search([('co_id','=',self.id),('move_type','=','in_invoice')])
    #     invoice = self.origin1.search([('co_id','=',self.id),('move_type','=','out_invoice')])
    #     if bill and invoice:
    #         final_amt=bill.amount_untaxed-invoice.amount_untaxed
    #         self.profitability = final_amt
    #     else:
    #         self.profitability =0.00 ##by kajal

    # def action_get_bill(self):
    #     itemIds = self.env['account.move'].search([])
    #     itemIds = itemIds.ids
    #     return {
    #         'name': _('Vendor Bill'),
    #         'type': 'ir.actions.act_window',
    #         'view_type': 'form',
    #         'view_mode': 'tree,form',
    #         'res_model': 'account.move',
    #         'view_id': False,
    #         'context': {'default_move_type': 'in_invoice','default_co_id':self.id},
    #         'domain': [('id', 'in', itemIds),('move_type','=','in_invoice')],
    #     }  ##by kajal

    # def action_get_invoice(self):
    #     itemIds = self.env['account.move'].search([])
    #     itemIds = itemIds.ids
    #     return {
    #         'name': ('Customer Invoice'),
    #         'type': 'ir.actions.act_window',
    #         'view_type': 'form',
    #         'view_mode': 'tree,form',
    #         'res_model': 'account.move',
    #         'view_id': False,
    #         'context':{'default_move_type': 'out_invoice','default_co_id':self.id},
    #         'domain': [('id', 'in', itemIds),('move_type','=','out_invoice')],
    #     }##by kajal

    # @api.model
    # def create(self, vals):
    #     '''job Order Create Function'''
    #     if vals.get('name', _('New')) == _('New'):
    #         vals['name'] = self.env['ir.sequence'].next_by_code('job.order.seq')
    #     if vals.get('internal_type') in ('sea_outbound', 'sea_inbound', 'air_outbound', 'air_inbound'):
    #         vals['state'] = 'job_ready'
    #     if vals.get('internal_type') == 'custom_clearance':
    #         vals['state'] = 'prealert_received'
    #     res = super(jobOrder, self).create(vals)
    #     return res

    def write(self, vals):
        '''job Order Write Function'''
        if vals.get('internal_type') in ('sea_outbound', 'sea_inbound', 'air_outbound', 'air_inbound'):
            vals['state'] = 'job_ready'
        if vals.get('internal_type') == 'custom_clearance':
            vals['state'] = 'prealert_received'
        res = super(JobOrder, self).write(vals)
        return res

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if self.partner_id:
            self.pricelist_id = self.partner_id.property_product_pricelist.id

    def action_cro_requested(self):
        self.state = 'cro_requested'

    def action_cro_released(self):
        self.state = 'cro_released'

    def action_stuff_started(self):
        self.state = 'stuff_started'

    def action_stuffing_completed(self):
        self.state = 'stuffing_completed'

    def action_sent_to_port(self):
        self.state = 'sent_to_port'

    def action_custom_clearance(self):
        self.state = 'custom_clearance'

    def action_sealing_done(self):
        self.state = 'sealing_done'

    def action_bill_of_lading_completed(self):
        self.state = 'bill_of_lading_completed'

    def action_vessel_set_to_sail(self):
        self.state = 'vessel_set_to_sail'

    def action_pre_alert(self):
        self.state = 'pre_alert'

    def action_destination_arrival(self):
        self.state = 'destination_arrival'

    def action_destination_clearance(self):
        self.state = 'destination_clearance'

    def action_delivery(self):
        self.state = 'delivery'

    def action_completed(self):
        self.state = 'completed'

    def action_book_with_flight(self):
        self.state = 'book_with_the_flight'

    def action_arrange_the_airway_bill(self):
        self.state = 'arrange_the_airway_bill'

    def action_pickup(self):
        self.state = 'pickup'

    def action_sent_to_port(self):
        self.state = 'sent_to_port'

    def action_booking_flight_schedule_confirmation(self):
        self.state = 'booking_flight_schedule_confirmation'

    def action_eta_shipment_arrival(self):
        self.state = 'eta_shipment_arrival'

    def action_document_readiness(self):
        self.state = 'document_readiness'

    def action_job_arrival_notice(self):
        self.state = 'job_arrival_notice'

    def action_forward_for_clearance(self):
        self.state = 'forward_for_clearance'

    def action_under_clearance(self):
        self.state = 'under_clearance'

    def action_awaiting_approval(self):
        self.state = 'awaiting_approval'

    def action_custom_declaration_completed(self):
        self.state = 'custom_declaration_completed'

    def action_under_custom_inspection(self):
        self.state = 'under_custom_inspection'

    def action_out_for_delivery(self):
        self.state = 'out_for_delivery'

    def action_send_to_finance(self):
        name_list = []
        for res in self:
            if not res.order_line:
                raise ValidationError(_('No Lines To Send Finance!'))
            if not res.partner_id:
                raise ValidationError(_(
                    'You can not make invoice without partner. Please select customer in case there is no customer.'))
            if res.order_type:
                journal_id = self.env['account.journal'].sudo().search(
                    [('type', '=', 'sale'), ('order_type', '=', res.order_type),
                     ('mode', '=', res.mode), ('import_export', '=', res.import_export)], limit=1)
            else:
                journal_id = self.env['account.journal'].sudo().search(
                    [('type', '=', 'sale')], limit=1)
                print('-------id',journal_id)
            invoice_vals = {
                'partner_id': res.partner_id and res.partner_id.id or False,
                # 'pricelist_id': res.pricelist_id and res.pricelist_id.id or False,  #commented by kajal
                'move_type': 'out_invoice',
                'state': 'draft',
                'invoice_date': datetime.today(),
                'journal_id': journal_id and journal_id.id or False, #commented by kajal
                'invoice_line_ids': [],
                'is_export': True,
                'consignee_id': res.consignee_id and res.consignee_id.id or False,
                'consignor_id': res.consignor_id and res.consignor_id.id or False,
                'notify_id': res.notify_id and res.notify_id.id or False,
                'cha_id': res.cha_id and res.cha_id.id or False,
                'reference_by_id': res.reference_by_id and res.reference_by_id.id or False,
                'cur_rate': res.cur_rate,
                'stuffing_point_id': res.stuffing_point_id and res.stuffing_point_id.id or False,
                'port_of_loading_id': res.port_of_loading_id and res.port_of_loading_id.id or False,
                'port_of_discharge_id': res.port_of_discharge_id and res.port_of_discharge_id.id or False,
                'order_type': res.order_type,
                'mode': res.mode,
                'import_export': res.import_export,
                'invoice_incoterm_id': res.incoterm_id and res.incoterm_id.id or False,
                'account_analytic_id': res.account_analytic_id and res.account_analytic_id.id or False,
                'customer_po_ref': res.customer_po_ref,
                'bill_of_lading_no': res.bill_of_lading_no,
                'mawb': res.mawb,
                'hawb': res.hawb,
                'estimated_time_departure': res.estimated_time_departure,
                'eta_port_of_destination':res.eta_port_of_destination,
                'total_pieces': res.total_pieces,
                'total_gross_weight': res.total_gross_weight,
                'total_cbm': res.total_cbm,
                'total_value': res.total_value,
                'total_chargeable_weight': res.total_chargeable_weight,
                'total_volume_cbm': res.total_volume_cbm,
                'total_volumetric_weight': res.total_volumetric_weight,
            }
            print('=========',invoice_vals)
            for lines in res.order_line:
                dict1 = {}
                dict1.update({
                    'name': lines.product_id.name,
                    'product_uom_id': lines.product_id.uom_id.id,
                    'product_id': lines.product_id.id,
                    'price_unit': lines.price_unit,
                    'quantity': lines.product_uom_qty,
                    'tax_ids': [(6, False, lines.tax_id.ids)],
                })
                invoice_vals['invoice_line_ids'].append((0, 0, dict1))
            for exp_line in res.sale_expense_line:
                dict2 = {}
                dict2.update({
                    'name': exp_line.exp_related_to,
                    'product_id': exp_line.expense_id.id,
                    'product_uom_id': exp_line.expense_id.uom_id.id,
                    'price_unit': exp_line.rate,
                    'quantity': exp_line.qty,
                })
                invoice_vals['invoice_line_ids'].append((0, 0, dict2))
            inv_id = self.env['account.move'].create(invoice_vals)
            if inv_id:
                for lines in res.job_container_line:
                    vals = {
                        'move_id': inv_id and inv_id.id or False,
                        'container_type_id': lines.container_type_id and lines.container_type_id.id or False,
                        'count': lines.count,
                        'container_qty': lines.container_qty,
                    }
                    container_lines = self.env['move.container.lines'].create(vals)
                return {
                    'type': 'ir.actions.act_window',
                    'view_mode': 'form',
                    'res_model': 'account.move',
                    'target': 'current',
                    'res_id': inv_id.id
                } ##by kajal


class JobOrderLine(models.Model):
    _name = 'job.order.line'
    _description = 'job Order Line'
    _order = 'order_id, sequence, id'
    _check_company_auto = True

    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id')
    def _compute_amount(self):
        """
        Compute the amounts of the SO line.
        """
        for line in self:
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty,
                                            product=line.product_id, partner=line.order_id.partner_shipping_id)
            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })
            if self.env.context.get('import_file', False) and not self.env.user.user_has_groups(
                    'account.group_account_manager'):
                line.tax_id.invalidate_cache(['invoice_repartition_line_ids'], [line.tax_id.id])

    order_id = fields.Many2one('job.order', string='Order Reference', required=True, ondelete='cascade', index=True,
                               copy=False)
    name = fields.Text(string='Description', required=True)
    remark = fields.Text(string='Remark')
    sequence = fields.Integer(string='Sequence', default=10)
    price_unit = fields.Float('Unit Price', required=True, digits='Product Price', default=0.0)
    price_subtotal = fields.Monetary(compute='_compute_amount', string='Subtotal', readonly=True, store=True)
    price_tax = fields.Float(compute='_compute_amount', string='Total Tax', readonly=True, store=True)
    price_total = fields.Monetary(compute='_compute_amount', string='Total', readonly=True, store=True)
    tax_id = fields.Many2many('account.tax', string='Taxes',
                              domain=['|', ('active', '=', False), ('active', '=', True)])
    discount = fields.Float(string='Discount (%)', digits='Discount', default=0.0)
    product_id = fields.Many2one(
        'product.product', string='Product',
        domain="[('sale_ok', '=', True), '|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        change_default=True, ondelete='restrict', check_company=True)  # Unrequired company
    product_template_id = fields.Many2one(
        'product.template', string='Product Template',
        related="product_id.product_tmpl_id", domain=[('sale_ok', '=', True)])
    product_uom_qty = fields.Float(string='Quantity', digits='Product Unit of Measure', required=True, default=1.0)
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure',
                                  domain="[('category_id', '=', product_uom_category_id)]")
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id', readonly=True)
    product_uom_readonly = fields.Boolean(compute='_compute_product_uom_readonly')

    untaxed_amount_invoiced = fields.Monetary("Untaxed Invoiced Amount", compute='_compute_untaxed_amount_invoiced',
                                              compute_sudo=True, store=True)
    untaxed_amount_to_invoice = fields.Monetary("Untaxed Amount To Invoice",
                                                compute='_compute_untaxed_amount_to_invoice', compute_sudo=True,
                                                store=True)

    salesman_id = fields.Many2one(related='order_id.user_id', store=True, string='Salesperson', readonly=True)
    currency_id = fields.Many2one(related='order_id.currency_id', depends=['order_id.currency_id'], store=True,
                                  string='Currency', readonly=True)
    company_id = fields.Many2one(related='order_id.company_id', string='Company', store=True, readonly=True, index=True)
    order_partner_id = fields.Many2one(related='order_id.partner_id', store=True, string='Customer', readonly=False)
    is_expense = fields.Boolean('Is expense',
                                help="Is true if the sales order line comes from an expense or a vendor bills")
    state = fields.Selection(
        related='order_id.state', string='Order Status', readonly=True, copy=False, store=True)

    display_type = fields.Selection([
        ('line_section', "Section"),
        ('line_note', "Note")], default=False, help="Technical field for UX purpose.")

    base_price = fields.Float(string="Base Price", digits=('16', 2))
    overhead_expenses = fields.Float(string="Overhead/Expenses")
    packing_type = fields.Many2one('export.packing.type', string="Packing Type")
    bag_box_qty = fields.Float(string="Bag/Box Qty.")
    container_type_id = fields.Many2one('container.type', 'Container Type')
    capacity_in_mt = fields.Float('Capacity(MT)')

    def _compute_tax_id(self):
        for line in self:
            line = line.with_company(line.company_id)
            fpos = line.order_id.fiscal_position_id or line.order_id.fiscal_position_id.get_fiscal_position(
                line.order_partner_id.id)
            # If company_id is set, always filter taxes by the company
            taxes = line.product_id.taxes_id.filtered(lambda t: t.company_id == line.env.company)
            line.tax_id = fpos.map_tax(taxes, line.product_id, line.order_id.partner_shipping_id)

    @api.onchange('container_type_id')
    def onchange_container_type_id(self):
        if self.container_type_id:
            self.capacity_in_mt = self.container_type_id.capacity

    @api.onchange('product_id')
    def product_id_change(self):
        if not self.product_id:
            return
        if self.product_id:
            self.product_uom = self.product_id.uom_id
            self.product_uom_qty = self.product_uom_qty or 1.0
            self.name = self.product_id.display_name
            self.tax_id = [(6, False, self.product_id.taxes_id.ids)]

    @api.onchange('product_id', 'price_unit', 'product_uom', 'product_uom_qty', 'tax_id')
    def _onchange_discount(self):
        if not (self.product_id and self.product_uom and
                self.order_id.partner_id and self.order_id.pricelist_id and
                self.order_id.pricelist_id.discount_policy == 'without_discount' and
                self.env.user.has_group('product.group_discount_per_so_line')):
            return

        self.discount = 0.0
        product = self.product_id.with_context(
            lang=self.order_id.partner_id.lang,
            partner=self.order_id.partner_id,
            quantity=self.product_uom_qty,
            date=self.order_id.date_order,
            pricelist=self.order_id.pricelist_id.id,
            uom=self.product_uom.id,
            fiscal_position=self.env.context.get('fiscal_position')
        )

        product_context = dict(self.env.context, partner_id=self.order_id.partner_id.id, date=self.order_id.date_order,
                               uom=self.product_uom.id)

        price, rule_id = self.order_id.pricelist_id.with_context(product_context).get_product_price_rule(
            self.product_id, self.product_uom_qty or 1.0, self.order_id.partner_id)
        new_list_price, currency = self.with_context(product_context)._get_real_price_currency(product, rule_id,
                                                                                               self.product_uom_qty,
                                                                                               self.product_uom,
                                                                                               self.order_id.pricelist_id.id)

        if new_list_price != 0:
            if self.order_id.pricelist_id.currency_id != currency:
                # we need new_list_price in the same currency as price, which is in the SO's pricelist's currency
                new_list_price = currency._convert(
                    new_list_price, self.order_id.pricelist_id.currency_id,
                    self.order_id.company_id or self.env.company, self.order_id.date_order or fields.Date.today())
            discount = (new_list_price - price) / new_list_price * 100
            if (discount > 0 and new_list_price > 0) or (discount < 0 and new_list_price < 0):
                self.discount = discount


class jobFreightline(models.Model):
    _name = "job.freight.line"
    _description = "job Freight Line"

    def _get_default_dimension_uom_id(self):
        return self.env.ref('uom.product_uom_cm')

    def _get_default_weight_uom_id(self):
        return self.env.ref('uom.product_uom_kgm')

    job_id = fields.Many2one('job.order', string="job Id")
    product_id = fields.Many2one('product.product', string="Product")
    container_type_id = fields.Many2one('container.type', string="Container Type")
    capacity_in_mt = fields.Float(string="Capacity (MT)")
    container_qty = fields.Integer(string="Container Qty.")
    commercial_invoice_value = fields.Float(string="Commercial Invoice Value")
    goods_desc = fields.Text(string='Goods Description')
    packing_type = fields.Many2one('export.packing.type', string="Packing Type")
    product_uom = fields.Many2one('uom.uom', string="Unit of Measurement")
    # no_of_package = fields.Integer(string='No. Of Package')
    type = fields.Selection([
        ('stackable', 'Stackable'),
        ('non_stackable', 'Non-Stackable')], string='Type', help="Are packages stackable?")
    product_uom_quantity = fields.Float(string="No. of Bag/Box/Pack")
    weight_input = fields.Float(string='Weight')
    weight_per_package = fields.Float(string='Weight Per Package')
    total_weight = fields.Float(string='Total Weight', store=True, compute='_compute_total_weight')
    loose_bool = fields.Boolean(string="Loose Quantity", default=False)
    length_per_package = fields.Float(string='length Per Package(cm)')
    width_per_package = fields.Float(string='Width Per Package(cm)')
    height_per_package = fields.Float(string='Height Per Package(cm)')
    weight_factor = fields.Float(string='Weight Factor')
    chargeable_weight = fields.Float(string='Chargeable weight Per pack', store=True,
                                     compute='_compute_chargeable_weight')
    total_chargeable_weight = fields.Float(string='Total Chargeable weight', store=True,
                                           compute='_compute_total_chargeable_weight')
    volume_cbcm = fields.Float(string='Volume (Cubic cm)', store=True, compute='_compute_volume_cbcm')
    volume = fields.Float(string='Volume Per Package(cbm)', store=True, compute='_compute_volume_cbm')
    volumetric_weight = fields.Float(string='Volumetric Weight', store=True, compute='_compute_volumetric_weight',
                                     help="If weight factor type in service type is by Cubic CM then volumetric weight = volume/weight factor else volume*weight factor.")
    weight_uom_id = fields.Many2one('uom.uom', string='Weight UOM', default=_get_default_weight_uom_id)
    dimension_uom_id = fields.Many2one('uom.uom', string='Dimension UOM', default=_get_default_dimension_uom_id)
    uom_name = fields.Char(string="UoM Name", related='dimension_uom_id.name')
    remarks = fields.Text(string="Remarks")
    full_container_service = fields.Boolean(string="Full Container Service", default=False)
    # subtotal = fields.Float(string='Subtotal', compute='_compute_subtotal')
    total_volume_cbm = fields.Float(string='Total Volume (cbm)', store=True, compute='_compute_total_volume_cbm')
    total_volumetric_weight = fields.Float(string='Total Volumetric weight', store=True,
                                           compute='_compute_total_volumetric_weight')

    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.product_id:
            self.product_uom = self.product_id.uom_id.id

    @api.onchange('container_type_id')
    def onchange_container_type_id(self):
        if self.container_type_id:
            self.capacity_in_mt = self.container_type_id.capacity

    @api.onchange('product_id', 'job_id.service_type')
    def onchange_get_weight_factor(self):
        if self.job_id.service_type:
            self.weight_factor = self.job_id.service_type.weight_factor
            self.full_container_service = self.job_id.service_type.full_container_service

    @api.onchange('product_id', 'job_id.weight_uom_id', 'job_id.dimension_uom_id')
    def onchange_get_uoms(self):
        if self.job_id.weight_uom_id:
            self.weight_uom_id = self.job_id.weight_uom_id.id
        if self.job_id.dimension_uom_id:
            self.dimension_uom_id = self.job_id.dimension_uom_id.id

    @api.depends('weight_per_package', 'product_uom_quantity')
    def _compute_total_weight(self):
        for res in self:
            res.total_weight = res.weight_per_package * res.product_uom_quantity

    # @api.depends('total_weight', 'volume')
    # def _compute_subtotal(self):
    #     for res in self:
    #         res.subtotal = res.price_unit * (res.total_weight if res.total_weight > res.volume else res.volume)

    @api.depends('length_per_package', 'width_per_package', 'height_per_package')
    def _compute_volume_cbcm(self):
        for res in self:
            res.volume_cbcm = res.length_per_package * res.width_per_package * res.height_per_package

    # @api.depends('length_per_package', 'width_per_package', 'height_per_package')
    # def _compute_volume_cbm(self):
    #     for res in self:
    #         res.volume = (res.length_per_package * res.width_per_package * res.height_per_package) / 1000000

    @api.depends('volume_cbcm', 'dimension_uom_id', 'length_per_package', 'width_per_package', 'height_per_package')
    def _compute_volume_cbm(self):
        for res in self:
            if res.dimension_uom_id.name == 'm':
                res.volume = (res.length_per_package * res.width_per_package * res.height_per_package)
            elif res.dimension_uom_id.name == 'cm':
                res.volume = res.volume_cbcm / 1000000
            elif res.dimension_uom_id.name == 'in':
                res.volume = res.volume_cbcm / 61024
            else:
                res.volume = 0

    @api.depends('chargeable_weight', 'product_uom_quantity')
    def _compute_total_chargeable_weight(self):
        for res in self:
            res.total_chargeable_weight = res.chargeable_weight * res.product_uom_quantity

    @api.depends('volume_cbcm', 'weight_factor', 'job_id.service_type')
    def _compute_volumetric_weight(self):
        for res in self:
            if res.weight_factor > 0:
                if res.job_id.service_type.weight_factor_type == 'on_cbcm':
                    res.volumetric_weight = res.volume_cbcm / res.weight_factor
                else:
                    res.volumetric_weight = res.volume * res.weight_factor

    @api.onchange('weight_input', 'weight_per_package')
    def onchange_weight_input(self):
        # for res in self:
        if self.weight_uom_id.name == 'kg':
            self.weight_per_package = self.weight_input
        elif self.weight_uom_id.name == 'lb':
            self.weight_per_package = self.weight_input / 2.205
        else:
            self.weight_per_package = 0

    @api.depends('weight_per_package', 'volumetric_weight')
    def _compute_chargeable_weight(self):
        for res in self:
            if res.weight_per_package > res.volumetric_weight:
                res.chargeable_weight = res.weight_per_package
            else:
                res.chargeable_weight = res.volumetric_weight

    @api.depends('volume', 'product_uom_quantity')
    def _compute_total_volume_cbm(self):
        for res in self:
            res.total_volume_cbm = res.product_uom_quantity * res.volume

    @api.depends('volumetric_weight', 'product_uom_quantity')
    def _compute_total_volumetric_weight(self):
        for res in self:
            res.total_volumetric_weight = res.product_uom_quantity * res.volumetric_weight


class jobExpenseLine(models.Model):
    _name = "job.expense.line"
    _description = 'job Expense Line'

    @api.depends('qty', 'rate')
    def _get_exp_amt(self):
        for val in self:
            val.exp_amt = val.qty * val.rate

    order_id = fields.Many2one('job.order', 'Order Id')
    exp_related_to = fields.Char('Expense Related to')
    # product_class = fields.Many2one('product.classification', string='Product Class')
    expense_id = fields.Many2one('product.product', 'Expense Name')
    qty = fields.Integer(string='Quantity', default=1)
    usd_value = fields.Float(string='USD')
    rate = fields.Float('Rate')
    exp_amt_fc = fields.Float('Expense Amt (FC)')
    exp_amt = fields.Float('Expense Amt', compute='_get_exp_amt')
    remark = fields.Char('Remarks')

    # invoice_id = fields.Many2one('account.invoice', string="Invoice")

    # @api.onchange('expense_id')
    # def onchange_expense_id(self):
    #     if self.expense_id:
    #         self.product_class = self.expense_id.product_class.id

    @api.onchange('usd_value')
    def onchange_usd_value(self):
        for res in self:
            if res.usd_value > 0:
                res.rate = res.usd_value * res.order_id.cur_rate

    @api.onchange('rate')
    def onchange_rate(self):
        for res in self:
            if res.rate > 0 and res.order_id.cur_rate > 0:
                res.usd_value = res.rate / res.order_id.cur_rate


class jobExportDocument(models.Model):
    _name = "job.export.document"
    _description = 'job Export Document'

    export_document_id = fields.Many2one('export.document', 'Document Name')
    order_id = fields.Many2one('job.order', 'job Order Id')
    # invoice_id = fields.Many2one('account.invoice', string="Invoice") ##by kajal


class jobPaymenTermLine(models.Model):
    _name = "job.payment.term.line"
    _description = 'job Payment term Line'

    order_id = fields.Many2one('job.order', 'Order Id')
    country_id = fields.Many2one('res.country', 'Country')
    payment_id = fields.Many2one('account.payment.term', 'Payment Term')
    value = fields.Float(string='Value (%)')
    ecgc_rate = fields.Float(string='ECGC Rate (%)')

    # invoice_id = fields.Many2one('account.invoice', string="Invoice") ##by kajal

    @api.onchange('payment_id')
    def get_ecgc_rate(self):
        for res in self:
            if self._context.get('country_id'):
                country_id = self.env["res.country"].browse(self._context.get('country_id'))
                if country_id:
                    ecgc_id = self.env["ecgc.rating.line"].search([('country_id', '=', country_id.id)], limit=1)
                    payment_id = self.env["ecgc.premium.rate"].search(
                        [('ecgc_rating_id', '=', ecgc_id.ecgc_rating_id.id)])
                    for payment in payment_id:
                        if payment.payment_term_id == res.payment_id:
                            res.ecgc_rate = payment.rate

    @api.onchange('payment_id')
    def onchange_payment_id(self):
        payment_ids_list = []
        if self._context.get('country_id'):
            country_id = self.env["res.country"].browse(self._context.get('country_id'))
            if country_id:
                ecgc_id = self.env["ecgc.rating.line"].search([('country_id', '=', country_id.id)], limit=1)
                payment_id = self.env["ecgc.premium.rate"].search([('ecgc_rating_id', '=', ecgc_id.ecgc_rating_id.id)])
                for payment in payment_id:
                    payment_ids_list.append(payment.payment_term_id.id)
        domain = {'payment_id': [('id', 'in', payment_ids_list)]}
        return {'domain': domain}


class jobScheduleLine(models.Model):
    _name = "job.schedule.line"
    _description = "job Schedule Line"
    _rec_name = "schedule_id"

    sale_id = fields.Many2one('job.order', string="Order Id")
    schedule_id = fields.Many2one('common.schedule', string="Schedule Name")
    report_at_time = fields.Selection([('pre_shipment', 'Pre Shipment'), ('post_shipment', 'Post Shipment')],
                                      string='Report at Time')
    req_from = fields.Selection([('other', 'Other'), ('self', 'Self')], string='Requirement From')
    country_specific = fields.Boolean(string="Country Specific")
    port_of_loading_specific = fields.Boolean(string="Port of Loading Specific")
    completion_date = fields.Date(string="Completion Date")
    fname = fields.Char()
    attachment = fields.Binary(string="Attachment")
    remarks = fields.Text(string="Remarks")
    # invoice_id = fields.Many2one('account.invoice', string="Invoice")##by kajal
    #     export_do_id = fields.Many2one('stock.picking', string="DO")
    sale_export_attachment_lines = fields.One2many('job.schedule.attachment.line', 'sale_export_attachment_id',
                                                   string='Attachment Lines')

    @api.onchange('schedule_id')
    def onchange_schedule_id(self):
        if self.schedule_id:
            self.report_at_time = self.schedule_id.report_at_time
            self.req_from = self.schedule_id.req_from
            self.country_specific = self.schedule_id.country_specific
            self.port_of_loading_specific = self.schedule_id.port_of_loading_specific


class jobScheduleAttachmentLine(models.Model):
    """ Attachment Details """
    _name = "job.schedule.attachment.line"
    _description = 'job Schedule Attachment Line'

    sale_export_attachment_id = fields.Many2one('job.schedule.line')
    sale_remark = fields.Char(string='Remark')
    fname = fields.Char()
    sale_attachment_value = fields.Binary(string='Attachment')


class jobQcSpecificationLine(models.Model):
    _name = "job.qc.specification.line"
    _description = "job Qc Specification Line"
    _rec_name = 'qc_parameter_id'

    order_id = fields.Many2one('job.order', string="Order ID")
    product_id = fields.Many2one('product.product', string="Product")
    qc_parameter_id = fields.Many2one('product.mix.variants', string="Parameter")
    value = fields.Char(string="Value")
    picking_id = fields.Many2one('stock.picking', string="Picking")

    # invoice_id = fields.Many2one('account.invoice', string="Invoice")##by kajal

    @api.onchange('qc_parameter_id')
    def onchange_qc_parameter_id(self):
        if self.qc_parameter_id:
            self.value = self.qc_parameter_id.value


class jobSoTcSetLines(models.Model):
    _name = "job.so.tc.set.lines"
    _description = "job So Tc Set Lines"

    s_no = fields.Integer(string="S No", compute="_sequence_ref")
    export_so_tc_set_id = fields.Many2one('job.order', string='Terms And Condition Set Id')
    term_and_condition_id = fields.Many2one('term.and.condition', string='Condition')
    removable = fields.Selection([('yes', 'Yes'), ('no', 'No')],
                                 help='If user is allowed to remove this condition in the form such as SO/PO etc then choose it as Yes.',
                                 string='Removable')
    term_and_condition_option_id = fields.Many2one('term.and.condition.option', string='Terms And Condition Option')

    @api.depends('export_so_tc_set_id.export_so_tc_set_line')
    def _sequence_ref(self):
        for line in self:
            no = 0
            for l in line.export_so_tc_set_id.export_so_tc_set_line:
                no += 1
                l.s_no = no


class jobcontainerlines(models.Model):
    _name = "job.container.lines"
    _description = "job Container Line"

    job_order_id = fields.Many2one('job.order', string="job Order ID")
    container_type_id = fields.Many2one('container.type', string="Container Type")
    count = fields.Integer(string="Count")
    container_qty = fields.Integer(string="Container Numbers")
