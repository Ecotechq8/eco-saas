# -*- coding: utf-8 -*-
# Copyright 2021 Verts Services India Pvt Ltd.
# http://www.verts.co.in

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError, AccessError

from datetime import datetime
from num2words import num2words


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def convert_amount_in_word(self):
        total = ''
        if self.amount_total:
            total = num2words(float(self.amount_total)).upper()
        return total

    # @api.multi
    # def _get_amount_in_words(self):
    #     self.ensure_one()
    #     wGenerator = convert_number_to_word.Number2Words()
    #     amt_en = wGenerator.convertNumberToWords(self.amount_total, self.currency_id)
    #     return convert_number_to_word.textwrap.fill(amt_en, 50)

    def calculate_total_quantity(self):
        total = 0
        for val in self.order_line:
            if val.product_uom_qty:
                total += val.product_uom_qty
        return total

    @api.model
    def _get_default_team(self):
        if self._context.get('default_export'):
            return False
        return self.env['crm.team']._get_default_team_id()

    @api.model
    def _get_default_user(self):
        if self._context.get('default_export'):
            return False
        return self.env.user

    @api.depends('amount_total', 'cur_rate', 'currency_id')
    def _so_total_amount_usd(self):
        for res in self:
            if res.currency_id.name == 'INR' and res.amount_total and self.cur_rate > 0.0:
                res.so_amount_total_usd = res.amount_total / res.cur_rate
            else:
                res.so_amount_total_usd = res.amount_total

    export = fields.Boolean('Exports')
    country_id = fields.Many2one('res.country', 'Country')
    port_of_loading_id = fields.Many2one('ports', 'Port of Loading')
    port_of_discharge_id = fields.Many2one('ports', 'Port of Discharge')
    cha_id = fields.Many2one('res.partner', 'Custom House Agent ')
    freight_forwarder_id = fields.Many2one('res.partner', 'Freight Forwarder')
    stuffing_point_id = fields.Many2one('ports', 'Stuffing Point')
    cur_rate = fields.Float('Currency Conversion Rate.', digits='Currency Rate')
    reference_by_id = fields.Many2one('res.partner', 'Reference By')
    # payment_term_ids = fields.Many2many('account.payment.term', 'payment_term_rel', 'order_id', 'payment_term_id',string='Payment Terms')
    container_detail_line = fields.One2many('container.detail', 'order_id', 'Container Details')
    sale_expense_line = fields.One2many('expense.line', 'order_id', 'Expenses')
    dry_port_id = fields.Many2one('ports', 'Dry/ICD Port')
    payment_term_line = fields.One2many('payment.term.line', 'order_id', 'Payment Details')
    sale_export_document_line = fields.One2many('sale.export.document', 'order_id', 'Export Documents')
    total_expense = fields.Float(String="Total Expenses", store='True', compute='get_total_expense')
    rate_per_kg_on_expense = fields.Float(String="Rate Per Kg On Expense", store='True', compute='get_total_expense')
    is_load_ecgc_insurance = fields.Boolean(string="Is Load ECGC Insurance")
    schedule_lines = fields.One2many('sale.schedule.line', 'sale_id', 'Schedule Lines')
    qc_pro_specification_line = fields.One2many('order.qc.specification.line', 'order_id',
                                                string='QC Product Specification Line')
    team_id = fields.Many2one('crm.team', 'Sales Team', change_default=True, default=_get_default_team,
                              oldname='section_id')
    user_id = fields.Many2one('res.users', string='Salesperson', index=True, tracking=True,
                               default=_get_default_user)
    export_tc_set_ids = fields.Many2many('term.and.condition.set', string="Terms & Condtions Set")
    export_so_tc_set_line = fields.One2many('export.so.tc.set.lines', 'export_so_tc_set_id',
                                            string='Terms And Condition Set Lines')
    ex_p_street = fields.Char('Street ', size=64)
    ex_p_street2 = fields.Char('Street2 ', size=64)
    ex_p_zip = fields.Char('Zip ', size=64)
    ex_p_city = fields.Char('City ', size=64)
    ex_p_state_id = fields.Many2one('res.country.state', string="State")
    ex_p_country_id = fields.Many2one('res.country', string="Country")
    ex_d_street = fields.Char('Street', size=64)
    ex_d_street2 = fields.Char('Street2', size=64)
    ex_d_zip = fields.Char('Zip', size=64)
    ex_d_city = fields.Char('City', size=64)
    ex_d_state_id = fields.Many2one('res.country.state', string="State.")
    ex_d_country_id = fields.Many2one('res.country', string="Country.")
    consignor_id = fields.Many2one('res.partner', string="Consignor")
    consignee_id = fields.Many2one('res.partner', string="Consignee")
    notify_id = fields.Many2one('res.partner', string="Notify Party")
    so_invoice_id = fields.Many2one('so.invoice.value', string="So Inv Val")
    so_amount_total_usd = fields.Float(compute='_so_total_amount_usd', string='SO Amount In USD')
    incoterm_id = fields.Many2one('account.incoterms', string="Shipment (Inco) Terms")
    # order_type = fields.Selection([
    #     ('sea_outbound', 'Sea Outbound'),
    #     ('sea_inbound', 'Sea Inbound'),
    #     ('air_outbound', 'Air Outbound'),
    #     ('air_inbound', 'Air Inbound'),
    #     ('custom_clearance', 'Custom Clearance')], string='Order Type')
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
    total_pieces = fields.Float(string='Total Pieces', compute='_compute_total_pieces', store=True)
    # total_gross_weight = fields.Float(string='Total Gross Weight')
    total_cbm = fields.Float(string='Total CBM')
    total_value = fields.Float(string='Total Value', compute='_compute_total_value', store=True)
    total_chargeable_weight = fields.Float(string='Total Chargeable')
    total_volume_cbm = fields.Float(string='Total Volume (cbm)', compute='_compute_total_volume_cbm', store=True)
    total_volumetric_weight = fields.Float(string='Total Volumetric weight')
    carrier_name = fields.Char(string="Carrier Name")
    transit_time = fields.Integer(string="Transit Time")
    # validity_date = fields.Datetime(string="Validity of the Quote")
    freight_type = fields.Char(string='Freight Type')
    notes2 = fields.Text(string="Notes")
    sale_freight_line = fields.One2many('sale.freight.line', 'sale_id', string='Sale Freight Lines')
    container_load = fields.Selection([("fcl", "Full Container Load (FCL)"), ("lcl", "Less than Container Load (LCL)")],
                                      string="Container Load")
    job_order_id = fields.Many2one("job.order", string="Job Order")

    # cargo_order = fields.Boolean(string='Cargo Order')
    # export_import = fields.Selection([('export', 'Export'), ('import', 'Import')], string='Export/Import')
    commodity = fields.Many2one('export.product.category', string="Commodity")
    hs_code = fields.Char(string="HS Code")
    agent_id = fields.Many2one('res.partner', string="Agent")
    payable_to = fields.Many2one('res.partner', string="Payable To")
    company_currency_id = fields.Many2one('res.currency', related='company_id.currency_id')
    total_cur_conversion_amount = fields.Monetary(
        string='Total After Currency Conversion',
        currency_field='company_currency_id',
        compute='_compute_total_cur_conversion_amount',
        store=True
    )
    pivot_weight = fields.Float(string="Pivot Weight")
    total_gross_weight = fields.Float(string="Total Gross Weight", compute="_compute_freight_weights", inverse='_inverse_total_gross_weight', store=True)
    sum_total_volumetric_weight = fields.Float(string="Total Volumetric Weight",
                                               compute="_compute_freight_weights",
                                               store=True)
    sum_of_total_chargeable_weight = fields.Float(
        string='Total Chargeable Weight',
        compute='_compute_sum_of_total_chargeable_weight',
        store=True
    )
    purchase_id = fields.Many2one('purchase.order', string='Related Purchase Order')

    freight_forwarding = fields.Boolean(string="Freight Forwarding", default=False)
    pre_cargo_carriage = fields.Boolean(string="Pre Cargo Carriage", default=False)
    custom_clearance = fields.Boolean(string="Custom Clearance", default=False)
    reefer_dry = fields.Selection([
        ('reefer', 'Reefer'),
        ('dry', 'Dry')], string="Reefer/Dry")
    genset = fields.Boolean(string="Genset", default=False)
    gsa_sales = fields.Boolean(string="GSA Sales", default=False)
    is_cargo_done = fields.Boolean(string="Is Cargo", default=False)
    cargo_id = fields.Many2one('cargo.order', 'Cargo Id')

    # def action_confirm(self):
    #     for order in self:
    #         zzzzz
    #         if order.currency_id.id != order.company_currency_id.id:
    #             if not order.cur_rate or order.cur_rate == 0.0:
    #                 raise UserError(_(
    #                     "Currency conversion rate has to be filled and cannot be zero"
    #                 ))
    #     return super(SaleOrder, self).action_confirm()


    def _inverse_total_gross_weight(self):
        pass

    @api.depends('sale_freight_line.commercial_invoice_value')
    def _compute_total_value(self):
        for order in self:
            order.total_value = sum(line.commercial_invoice_value for line in order.sale_freight_line)

    @api.depends('sale_freight_line.total_volume_cbm')
    def _compute_total_volume_cbm(self):
        for order in self:
            order.total_volume_cbm = sum(line.total_volume_cbm for line in order.sale_freight_line)

    @api.depends('sale_freight_line.product_uom_quantity')
    def _compute_total_pieces(self):
        for order in self:
            total = sum(line.product_uom_quantity for line in order.sale_freight_line)
            order.total_pieces = total

    @api.depends('total_gross_weight', 'sum_total_volumetric_weight', 'pivot_weight')
    def _compute_sum_of_total_chargeable_weight(self):
        for rec in self:
            rec.sum_of_total_chargeable_weight = max(
                rec.total_gross_weight or 0.0,
                rec.sum_total_volumetric_weight or 0.0,
                rec.pivot_weight or 0.0
            )

    @api.depends(
        'sale_freight_line',
        'sale_freight_line.total_weight',
        'sale_freight_line.total_volumetric_weight',
    )
    def _compute_freight_weights(self):
        for rec in self:
            # pivot = 0.0
            gross = 0.0
            volumetric = 0.0

            for line in rec.sale_freight_line:
                # pivot += line.pivot_weight or 0.0
                gross += line.total_weight or 0.0
                volumetric += line.total_volumetric_weight or 0.0

            # rec.pivot_weight = pivot
            rec.total_gross_weight = gross
            rec.sum_total_volumetric_weight = volumetric

    @api.depends('amount_total', 'cur_rate')
    def _compute_total_cur_conversion_amount(self):
        for rec in self:
            rec.total_cur_conversion_amount = rec.amount_total * rec.cur_rate if rec.cur_rate > 0 else 0.0

    @api.onchange('commodity')
    def _onchange_commodity(self):
        if self.commodity:
            self.hs_code = self.commodity.hs_code
        else:
            self.hs_code = False

    # shipment_by = fields.Selection([('sea', 'Sea'), ('air', 'Air')], string='Shipment By')
    # shipping_line = fields.Many2one('res.partner', string="Shipping Line")
    # vessel_id = fields.Many2one('ocean.vessel', string="Ocean Vessel")
    # voyage_id = fields.Many2one('ocean.voyage', string="Voyage")
    # shipping_order_no = fields.Char(string="Shipping Order No.")
    # carrier_booking_no = fields.Char(string="Carrier Booking No.")
    # eta_port_of_loading = fields.Date(string="ETA - Port of Loading")
    # cut_off_time = fields.Date(string="Cut off Time")
    # estimated_time_departure = fields.Date(string="Estimated Time of Departure")
    # actual_time_sailing = fields.Date(string="Actual Time of Sailing")
    # eta_port_of_destination = fields.Date(string="ETA - Port of Destination")
    # est_transit_days = fields.Date(string="Est. Transit Days ")
    # bill_of_lading_type = fields.Many2one('bill.lading.type', string="Bill of Lading Type")
    # freight_forwarding_reqd = fields.Boolean(string="Freight Forwarding")
    # pre_cargo_carriage_reqd = fields.Boolean(string="Pre Cargo Carriage")
    # custom_clearance_reqd = fields.Boolean(string="Custom Clearance")
    # reefer_dry = fields.Selection([('reefer', 'Reefer'), ('dry', 'Dry')], string='Reefer/Dry')
    # genset_reqd = fields.Boolean(string="Genset")
    # state = fields.Selection(selection_add=[
    #     ('requested_cro', 'Requested CRO'),
    #     ('cro_received', 'CRO Received'),
    #     ('stuffing_started', 'Stuffing Started'),
    #     ('stuffing_completed', 'Stuffing Completed'),
    #     ('sent_to_port_ICD', 'Sent to Port/ICD'),
    #     ('custom_clearance_done', 'Custom Clearance Done'),
    #     ('sealing_done', 'Sealing Done'),
    #     ('prealert_sent_to_sl', 'PreAlert sent to SL'),
    #     ('released_bill_of_lading', 'Released Bill of Lading'),
    #     ('completed', 'Completed')],
    #     string='State')

    def create_job_order(self):
        for res in self:
            # if res.order_type == 'freight' and res.mode == 'air' and res.import_export == 'import':
            #     internal_type = 'air_inbound'
            #     state = 'cargo_ready'
            # elif res.order_type == 'freight' and res.mode == 'air' and res.import_export == 'export':
            #     internal_type = 'air_outbound'
            #     state = 'cargo_ready'
            # elif res.order_type == 'freight' and res.mode == 'sea' and res.import_export == 'import':
            #     internal_type = 'sea_inbound'
            #     state = 'cargo_ready'
            # elif res.order_type == 'freight' and res.mode == 'sea' and res.import_export == 'export':
            #     internal_type = 'sea_outbound'
            #     state = 'cargo_ready'
            # elif res.order_type == 'custom':
            #     internal_type = 'custom_clearance'
            #     state = 'prealert_received'
            # elif res.order_type == 'packing_and_removal':
            #     internal_type = 'packing_and_removal'
            #     state = 'draft'
            # elif res.order_type == 'warehousing':
            #     internal_type = 'warehousing'
            #     state = 'draft'
            # else:
            #     internal_type = ''
            #     state = 'draft'
            if res.order_type == 'freight':
                state = 'job_ready'
            else:
                state = 'prealert_received'
            vals = {
                'partner_id': res.partner_id and res.partner_id.id or False,
                'consignee_id': res.consignee_id and res.consignee_id.id or False,
                'consignor_id': res.consignor_id and res.consignor_id.id or False,
                'notify_id': res.notify_id and res.notify_id.id or False,
                'date_order': res.date_order,
                'validity_date': res.validity_date,
                'cha_id': res.cha_id and res.cha_id.id or False,
                'reference_by_id': res.reference_by_id and res.reference_by_id.id or False,
                'cur_rate': res.cur_rate,
                'stuffing_point_id': res.stuffing_point_id and res.stuffing_point_id.id or False,
                'port_of_loading_id': res.port_of_loading_id and res.port_of_loading_id.id or False,
                'port_of_discharge_id': res.port_of_discharge_id and res.port_of_discharge_id.id or False,
                'client_order_ref': res.client_order_ref,
                'incoterm_id': res.incoterm_id and res.incoterm_id.id or False,
                # 'account_analytic_id': res.analytic_account_id and res.analytic_account_id.id or False,
                'state': state,
                'service_type': res.opportunity_id and res.opportunity_id.service_type and res.opportunity_id.service_type.id or False,
                'weight_uom_id': res.opportunity_id and res.opportunity_id.weight_uom_id and res.opportunity_id.weight_uom_id.id or False,
                'dimension_uom_id': res.opportunity_id and res.opportunity_id.dimension_uom_id and res.opportunity_id.dimension_uom_id.id or False,
                'opportunity_id': res.opportunity_id and res.opportunity_id.id or False,
                'order_type': res.order_type,
                'mode': res.mode,
                'import_export': res.import_export,
                'total_pieces': res.total_pieces,
                'total_gross_weight': res.total_gross_weight,
                'total_cbm': res.total_cbm,
                'total_value': res.total_value,
                'total_chargeable_weight': res.total_chargeable_weight,
                'total_volume_cbm': res.total_volume_cbm,
                'total_volumetric_weight': res.total_volumetric_weight,
            }
            job_id = self.env['job.order'].create(vals)
            if job_id:
                job_id.onchange_partner_id()
                for each in res.order_line:
                    vals2 = {
                        'product_id': each.product_id and each.product_id.id or False,
                        'order_id': job_id.id,
                        'name': each.name,
                        'container_type_id': each.container_type_id and each.container_type_id.id or False,
                        'capacity_in_mt': each.capacity_in_mt,
                        'product_uom_qty': each.product_uom_qty,
                        'product_uom': each.product_uom and each.product_uom.id or False,
                        'bag_box_qty': each.bag_box_qty,
                        'packing_type': each.packing_type and each.packing_type.id or False,
                        'price_unit': each.price_unit,
                        'tax_id': [(6, False, each.tax_id.ids)],
                    }
                    job_line_id = self.env['job.order.line'].create(vals2)
                    job_line_id.product_id_change()
                if res.sale_freight_line:
                    for lines in res.sale_freight_line:
                        vals2 = {
                            'job_id': job_id and job_id.id or False,
                            'product_id': lines.product_id and lines.product_id.id or False,
                            'container_type_id': lines.container_type_id and lines.container_type_id.id or False,
                            'capacity_in_mt': lines.capacity_in_mt,
                            'container_qty': lines.container_qty,
                            'commercial_invoice_value': lines.commercial_invoice_value,
                            'goods_desc': lines.goods_desc,
                            'packing_type': lines.packing_type and lines.packing_type.id or False,
                            'product_uom': lines.product_uom and lines.packing_type.id or False,
                            'type': lines.type,
                            'product_uom_quantity': lines.product_uom_quantity,
                            'weight_input': lines.weight_input,
                            'weight_per_package': lines.weight_per_package,
                            'loose_bool': lines.loose_bool,
                            'length_per_package': lines.length_per_package,
                            'width_per_package': lines.width_per_package,
                            'height_per_package': lines.height_per_package,
                            'weight_factor': lines.weight_factor,
                            'remarks': lines.remarks,
                        }
                        job_line_id = self.env['job.freight.line'].create(vals2)
                        job_line_id.onchange_product_id()
                view = self.env.ref('verts_v15_freight_forward.job_order_export_form_view_inherit')
                analytic_account = self.env["account.analytic.account"].create({
                    "name": job_id.name,
                    "partner_id": res.partner_id and res.partner_id.id or False

                })
                job_id.account_analytic_id = analytic_account.id
                res.job_order_id = job_id.id
                return {
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'job.order',
                    'views': [(view.id, 'form')],
                    'view_id': view.id,
                    'res_id': job_id.id,
                    'context': self.env.context,
                }

    @api.depends('sale_expense_line', 'order_line')
    def get_total_expense(self):
        expenses_total = 0.0
        for sline in self.sale_expense_line:
            expenses_total += sline.exp_amt
        line_total_qty = 0.0
        for line in self.order_line:
            line_total_qty += line.product_uom_qty
        if line_total_qty > 0 and expenses_total > 0:
            self.total_expense = expenses_total
            self.rate_per_kg_on_expense = expenses_total / line_total_qty

    # def so_inv_val_script(self):
    #     sale_ids = self.env['sale.order'].search([('so_invoice_id','=',False), ('export','=',True)])
    #     if sale_ids:
    #         for sale in sale_ids:
    #             if sale.invoice_ids and len(sale.invoice_ids)==1:
    #                 so_inv_id = self.env['so.invoice.value'].create({
    #                                                                 'sale_id': sale.id,
    #                                                                 'invoice_id':sale.invoice_ids.id
    #                                                                 })
    #                 sale.so_invoice_id = so_inv_id.id
    #                 sale.invoice_ids.so_invoice_id = so_inv_id.id
    #             elif sale.invoice_ids and len(sale.invoice_ids)>1:
    #                 so_inv_id = self.env['so.invoice.value'].create({
    #                                                                 'sale_id': sale.id,
    #                                                                 })
    #                 sale.so_invoice_id = so_inv_id.id
    #                 for invoice in sale.invoice_ids:
    #                     if sale.so_invoice_id and not sale.so_invoice_id.invoice_id:
    #                         sale.so_invoice_id.invoice_id = invoice.id
    #                         invoice.so_invoice_id = sale.so_invoice_id.id
    #                     else:
    #                         so_inv_id = sale.so_invoice_id.copy(
    #                                                             {
    #                                                             'invoice_id': invoice.id,
    #                                                             })
    #                         invoice.so_invoice_id = so_inv_id.id
    #             else:
    #                 so_inv_id = self.env['so.invoice.value'].create({
    #                                                                 'sale_id': sale.id,
    #                                                                 })
    #                 sale.so_invoice_id = so_inv_id.id   ##by kajal

    @api.onchange('partner_invoice_id')
    def onchange_ex_partner_invoice_id(self):
        if self.partner_invoice_id:
            self.ex_p_street = self.partner_invoice_id.street
            self.ex_p_street2 = self.partner_invoice_id.street2
            self.ex_p_zip = self.partner_invoice_id.zip
            self.ex_p_city = self.partner_invoice_id.city
            self.ex_p_state_id = self.partner_invoice_id.state_id.id
            self.ex_p_country_id = self.partner_invoice_id.country_id.id

    @api.onchange('partner_shipping_id')
    def onchange_ex_partner_shipping_id(self):
        if self.partner_shipping_id:
            self.ex_d_street = self.partner_shipping_id.street
            self.ex_d_street2 = self.partner_shipping_id.street2
            self.ex_d_zip = self.partner_shipping_id.zip
            self.ex_d_city = self.partner_shipping_id.city
            self.ex_d_state_id = self.partner_shipping_id.state_id.id
            self.ex_d_country_id = self.partner_shipping_id.country_id.id

    def cal_date_order(self):
        date = ''
        if self.date_order:
            order_date = datetime.strptime(str(self.date_order), '%Y-%m-%d %H:%M:%S')
            date = order_date.strftime("%d-%m-%y")
        return date

    def cal_port_of_discharge_id(self):
        country = ''
        if self.port_of_discharge_id:
            country = '(' + self.port_of_discharge_id.country_id.name + ')'
        return country

    def cal_cur_rate(self):
        x = 2.0
        currency = ''
        if self.cur_rate:
            cur = str(self.cur_rate) + '+' + str(x)
            currency = cur + '=' + str(self.cur_rate + float(x))
        return currency

    def cal_transit_time(self):
        days = ''
        if self.port_of_discharge_id:
            obj = self.env['transit.duration'].search([('dest_port_id', '=', self.port_of_discharge_id.id)])
            days = str(obj.transit_days) + '  ' + 'Days'
        return days

    @api.onchange('payment_term_line')
    def onchange_payment_term_line(self):
        for val in self:
            value = 0.0
            for payment in val.payment_term_line:
                value += payment.value
            if value > 100.0:
                raise UserError(_("Payment should not greater than 100%"))

    @api.onchange('partner_id')
    def on_get_country_id(self):
        if self.partner_id:
            self.country_id = self.partner_id.country_id.id

    @api.onchange('country_id')
    def onchange_country_id(self):
        values = []
        values2 = []
        if self.sale_export_document_line:
            for doc in self.sale_export_document_line:
                doc.unlink()
        if self.schedule_lines:
            for sch in self.schedule_lines:
                sch.unlink()
        if self.country_id and self.country_id.country_export_document_line:
            for document in self.country_id.country_export_document_line:
                values.append((0, 0, {
                    'export_document_id': document.export_document_id.id,
                }))
            self.update({'sale_export_document_line': values})
        if self.country_id and self.country_id.schedule_lines:
            for schedule in self.country_id.schedule_lines:
                values2.append((0, 0, {
                    'schedule_id': schedule.schedule_id.id,
                    'report_at_time': schedule.report_at_time,
                    'req_from': schedule.req_from,
                    'country_specific': schedule.country_specific,
                    'port_of_loading_specific': schedule.port_of_loading_specific,
                }))
            self.update({'schedule_lines': values2})

    # @api.onchange('export_tc_set_ids')
    # def _onchange_export_tc_set_ids(self):
    #     tc_set_id = {}
    #     new_lines = self.env['export.so.tc.set.lines']
    #     self.update({'export_so_tc_set_line': ''})
    #     for tset in self.export_tc_set_ids:
    #         tc_idss = self.env['tc.set.lines'].search([('tc_set_id', '=',tset.id)])
    #         for tset_line in tset.tc_set_line:
    #             tc_set_id={'term_and_condition_id': tset_line.term_and_condition_id.id, 'removable': tset_line.removable}
    #             new_line = new_lines.new(tc_set_id)
    #             new_lines += new_line
    #     if new_lines:
    #         self.update({'export_so_tc_set_line': new_lines})

    def get_expense_details(self):
        expense_line_obj = self.env['expense.line']
        for rec in self.sale_expense_line:
            rec.unlink()
        # if self.stuffing_point_id and self.port_of_loading_id and self.port_of_discharge_id and self.dry_port_id:
        if self.stuffing_point_id and self.port_of_loading_id and self.port_of_discharge_id:
            for rec in self.stuffing_point_id.export_expense_line:
                expense_line_obj.create({'expense_id': rec.expense_id.id,
                                         'exp_related_to': "Stuffing Point - " + self.stuffing_point_id.name,
                                         'order_id': self.id,
                                         'product_class': rec.expense_id.product_class.id,
                                         'rate': rec.price,
                                         })
            for rec in self.port_of_loading_id.export_expense_line:
                expense_line_obj.create({'expense_id': rec.expense_id.id,
                                         'exp_related_to': "Port of loading - " + self.port_of_loading_id.name,
                                         'order_id': self.id,
                                         'product_class': rec.expense_id.product_class.id,
                                         'rate': rec.price,
                                         })
            for rec in self.port_of_discharge_id.export_expense_line:
                expense_line_obj.create({'expense_id': rec.expense_id.id,
                                         'exp_related_to': "Port of Discharge - " + self.port_of_discharge_id.name,
                                         'order_id': self.id,
                                         'product_class': rec.expense_id.product_class.id,
                                         'rate': rec.price,
                                         })
            for rec in self.port_of_discharge_id.country_id.country_export_expense_line:
                expense_line_obj.create({'expense_id': rec.expense_id.id,
                                         'exp_related_to': "Port of Discharge (Country) - " + self.port_of_discharge_id.country_id.name,
                                         'order_id': self.id,
                                         'product_class': rec.expense_id.product_class.id,
                                         'rate': rec.price,
                                         })

            charge_id1 = self.env['empty.trailer.cost'].search(
                [('place_of_stuffing_id', '=', self.stuffing_point_id.id)],
                limit=1)
            for container_detail_id in self.container_detail_line:
                charges_expense_ids = charge_id1.empty_cost_line.filtered(
                    lambda cost_line: cost_line.container_type == container_detail_id.container_type_id and
                                      cost_line.qty < container_detail_id.capacity_in_mt and cost_line.to_qty >= container_detail_id.capacity_in_mt)
                for charges_expense_id in charges_expense_ids:
                    expense_amount = container_detail_id.container_qty * charges_expense_id.price
                    expense_line_obj.create({'expense_id': charge_id1.expense_id.id,
                                             'exp_related_to': "Empty Trailer Cost" + container_detail_id.container_type_id.name,
                                             'rate': expense_amount,
                                             'product_class': charge_id1.expense_id.product_class.id,
                                             'order_id': self.id,
                                             })

            thc_obj = self.env['terminal.handling.charges'].search(
                [('point_of_stuffing_id', '=', self.stuffing_point_id.id)],
                limit=1)
            for container_detail_id in self.container_detail_line:
                thc_ids = thc_obj.terminal_charges_line.filtered(
                    lambda charge_line: charge_line.container_type == container_detail_id.container_type_id)
                for thc in thc_ids:
                    expense_amount = container_detail_id.container_qty * thc.price
                    expense_line_obj.create({'expense_id': thc_obj.expense_id.id,
                                             'exp_related_to': "THC " + container_detail_id.container_type_id.name,
                                             'rate': expense_amount,
                                             'product_class': thc_obj.expense_id.product_class.id,
                                             'order_id': self.id,
                                             })

            fumigation_obj = self.env['res.country'].search(
                [('id', '=', self.partner_id.country_id.id)],
                limit=1)
            for container_detail_id in self.container_detail_line:
                fumigation_ids = fumigation_obj.fumigation_lines.filtered(
                    lambda fg_line: fg_line.container_type_id == container_detail_id.container_type_id)
                for fg in fumigation_ids:
                    expense_line_obj.create({'expense_id': fg.alp_charges_id.id,
                                             'exp_related_to': "Fumigation ALP",
                                             'rate': fg.alp_price,
                                             'product_class': fg.alp_charges_id.product_class.id,
                                             'order_id': self.id,
                                             })
                    expense_line_obj.create({'expense_id': fg.mbr_filled_id.id,
                                             'exp_related_to': "Fumigation MBR",
                                             'rate': fg.mbr_filled_price,
                                             'product_class': fg.mbr_filled_id.product_class.id,
                                             'order_id': self.id,
                                             })
                    expense_line_obj.create({'expense_id': fg.mbr_empty_charges_id.id,
                                             'exp_related_to': "Empty Fumigation MBR",
                                             'rate': fg.mbr_empty_price,
                                             'product_class': fg.mbr_empty_charges_id.product_class.id,
                                             'order_id': self.id,
                                             })

            # health_obj = self.env['health.certificate.charges'].search([('international_region_id','=',self.partner_id.international_gid.id)], limit=1)
            health_country_obj = self.env['health.certi.country.line'].search(
                [('country_id', '=', self.partner_id.country_id.id)], limit=1)
            health_obj = self.env['health.certificate.charges'].search(
                [('id', '=', health_country_obj.health_certi_id.id)], limit=1)
            health_ids = health_obj.health_certi_charges_line.filtered(
                lambda
                    health_line: health_line.amt_from <= self.amount_total and health_line.amt_to >= self.amount_total)
            for health in health_ids:
                expense_line_obj.create({'expense_id': health_obj.expense_id.id,
                                         'exp_related_to': "Health",
                                         'rate': health.price,
                                         'product_class': health_obj.expense_id.product_class.id,
                                         'order_id': self.id,
                                         })

            spice_obj = self.env['spice.board.rate.master'].search(
                [('country_id', '=', self.partner_id.country_id.id)], limit=1)
            # spice_ids = self.env['sale.order.line'].search_count([('order_id', '=', self.id)])
            spice_qty_ids = self.env['sale.order.line'].search([('order_id', '=', self.id)])
            for spice in spice_qty_ids:
                spice_board_ids = spice_obj.spice_board_line.filtered(
                    lambda spice_line: spice_line.product_id == spice.product_id and
                                       spice_line.from_qty < spice.product_uom_qty and spice_line.to_qty >= spice.product_uom_qty)
                for board_ids in spice_board_ids:
                    expense_line_obj.create({'expense_id': spice_obj.product_id.id,
                                             'exp_related_to': "Spice Board " + spice_obj.product_id.name,
                                             'rate': board_ids.price,
                                             'product_class': spice_obj.product_id.product_class.id,
                                             'remark': spice_obj.qc_id.name,
                                             'order_id': self.id,
                                             })

            self.is_load_ecgc_insurance = False
        else:
            return True

    def get_ecgc_insurance_details(self):
        expense_line_obj = self.env['expense.line']
        for res in self:
            if not res.sale_expense_line:
                raise UserError(_("First Click on Load Expense Button and generate Expense details."))

            ecgc_line_id = self.env["ecgc.rating.line"].search([('country_id', '=', res.partner_id.country_id.id)],
                                                               limit=1)
            ecgc_id = self.env["ecgc.rating"].search([('id', '=', ecgc_line_id.ecgc_rating_id.id)], limit=1)
            qty = 0.0
            for expense in res.sale_expense_line:
                for ecgc in ecgc_id.ecgc_calculation_groups:
                    if expense.product_class.name == ecgc.name:
                        qty += expense.exp_amt
            cif_value = qty + res.amount_total
            calculate_amount = cif_value
            term_amt = 0.0
            # ecgc_amt = 0.0
            total_ecgc = 0.0
            for payment in res.payment_term_line:
                term_amt = (calculate_amount * payment.value) / 100
                ecgc_amt = (term_amt * payment.ecgc_rate) / 100
                total_ecgc += ecgc_amt
                calculate_amount -= term_amt
            cif_ecgc_total = cif_value + total_ecgc

            expense_line_obj.create({'expense_id': ecgc_id.expense_id.id,
                                     'exp_related_to': "ECGC",
                                     'rate': total_ecgc,
                                     'product_class': ecgc_id.expense_id.product_class.id,
                                     'order_id': self.id,
                                     })

            ins_obj = self.env['insurance'].search([], limit=1)

            for ins in ins_obj:
                ins_amount = (cif_ecgc_total * ins.insurance) / 100
                expense_line_obj.create({'expense_id': ins_obj.expense_id.id,
                                         'exp_related_to': "Insurance",
                                         'rate': ins_amount,
                                         'product_class': ins_obj.expense_id.product_class.id,
                                         'order_id': self.id,
                                         })
            # expenses_total = qty + total_ecgc + ins_amount
            # res.total_expense = expenses_total
            # line_total_qty = 0.0
            # for line in res.order_line:
            #     line_total_qty += line.product_uom_qty
            # if line_total_qty > 0:
            #     res.rate_per_kg_on_expense = expenses_total / line_total_qty
            res.is_load_ecgc_insurance = True

    def create_cargo_order(self):
        for res in self:
            # if res.order_type == 'freight' and res.mode == 'air' and res.import_export == 'import':
            #     internal_type = 'air_inbound'
            #     state = 'cargo_ready'
            # elif res.order_type == 'freight' and res.mode == 'air' and res.import_export == 'export':
            #     internal_type = 'air_outbound'
            #     state = 'cargo_ready'
            # elif res.order_type == 'freight' and res.mode == 'sea' and res.import_export == 'import':
            #     internal_type = 'sea_inbound'
            #     state = 'cargo_ready'
            # elif res.order_type == 'freight' and res.mode == 'sea' and res.import_export == 'export':
            #     internal_type = 'sea_outbound'
            #     state = 'cargo_ready'
            # elif res.order_type == 'custom':
            #     internal_type = 'custom_clearance'
            #     state = 'prealert_received'
            # elif res.order_type == 'packing_and_removal':
            #     internal_type = 'packing_and_removal'
            #     state = 'draft'
            # elif res.order_type == 'warehousing':
            #     internal_type = 'warehousing'
            #     state = 'draft'
            # else:
            #     internal_type = ''
            #     state = 'draft'
            if res.order_type == 'freight':
                state = 'cargo_ready'
            else:
                state = 'prealert_received'
            vals = {
                'partner_id': res.partner_id and res.partner_id.id or False,
                'consignee_id': res.consignee_id and res.consignee_id.id or False,
                'consignor_id': res.consignor_id and res.consignor_id.id or False,
                'notify_id': res.notify_id and res.notify_id.id or False,
                'date_order': res.date_order,
                'validity_date': res.validity_date,
                'cha_id': res.cha_id and res.cha_id.id or False,
                'agent_id': res.agent_id and res.agent_id.id or False,
                'payable_to': res.payable_to and res.payable_to.id or False,
                'reference_by_id': res.reference_by_id and res.reference_by_id.id or False,
                'cur_rate': res.cur_rate,
                'stuffing_point_id': res.stuffing_point_id and res.stuffing_point_id.id or False,
                'port_of_loading_id': res.port_of_loading_id and res.port_of_loading_id.id or False,
                'port_of_discharge_id': res.port_of_discharge_id and res.port_of_discharge_id.id or False,
                'client_order_ref': res.client_order_ref,
                'incoterm_id': res.incoterm_id and res.incoterm_id.id or False,
                'account_analytic_id': res.analytic_account_id and res.analytic_account_id.id or False,
                'state': state,
                'service_type': res.opportunity_id and res.opportunity_id.service_type and res.opportunity_id.service_type.id or False,
                'weight_uom_id': res.opportunity_id and res.opportunity_id.weight_uom_id and res.opportunity_id.weight_uom_id.id or False,
                'dimension_uom_id': res.opportunity_id and res.opportunity_id.dimension_uom_id and res.opportunity_id.dimension_uom_id.id or False,
                'opportunity_id': res.opportunity_id and res.opportunity_id.id or False,
                'order_type': res.order_type,
                'mode': res.mode,
                'import_export': res.import_export,
                'total_pieces': res.total_pieces,
                'total_gross_weight': res.total_gross_weight,
                'total_cbm': res.total_cbm,
                'total_value': res.total_value,
                'total_chargeable_weight': res.total_chargeable_weight,
                'total_volume_cbm': res.total_volume_cbm,
                'total_volumetric_weight': res.total_volumetric_weight,
                'hs_code': res.hs_code,
                # 'gsa_sales': res.gsa_sales,
                'commodity': res.commodity and res.commodity.id or False,
                'sale_id': res.id,
                'purchase_id': res.purchase_id.id or False,
                'freight_forwarding': res.freight_forwarding,
                'pre_cargo_carriage': res.pre_cargo_carriage,
                'custom_clearance': res.custom_clearance,
                'reefer_dry': res.reefer_dry,
                'genset': res.genset,
                'gsa_sales': res.gsa_sales,
            }
            cargo_id = self.env['cargo.order'].create(vals)

            if cargo_id:
                res.is_cargo_done = True
                res.cargo_id = cargo_id.id
                cargo_id.onchange_partner_id()
                for each in res.order_line:
                    vals2 = {
                        'product_id': each.product_id and each.product_id.id or False,
                        'order_id': cargo_id.id,
                        'name': each.name,
                        'container_type_id': each.container_type_id and each.container_type_id.id or False,
                        'capacity_in_mt': each.capacity_in_mt,
                        'product_uom_qty': each.product_uom_qty,
                        'product_uom': each.product_uom and each.product_uom.id or False,
                        'bag_box_qty': each.bag_box_qty,
                        'packing_type': each.packing_type and each.packing_type.id or False,
                        'price_unit': each.price_unit,
                        'tax_id': [(6, False, each.tax_id.ids)],
                        'show_in_awb': each.show_in_awb,
                        'charge_type': each.charge_type,
                    }
                    cargo_line_id = self.env['cargo.order.line'].create(vals2)
                    cargo_line_id.product_id_change()

                if res.sale_freight_line:
                    for lines in res.sale_freight_line:
                        vals2 = {
                            'cargo_id': cargo_id and cargo_id.id or False,
                            'product_id': lines.product_id and lines.product_id.id or False,
                            'container_type_id': lines.container_type_id and lines.container_type_id.id or False,
                            'capacity_in_mt': lines.capacity_in_mt,
                            'container_qty': lines.container_qty,
                            'commercial_invoice_value': lines.commercial_invoice_value,
                            'goods_desc': lines.goods_desc,
                            'packing_type': lines.packing_type and lines.packing_type.id or False,
                            'product_uom': lines.product_uom and lines.packing_type.id or False,
                            'type': lines.type,
                            'product_uom_quantity': lines.product_uom_quantity,
                            'weight_input': lines.weight_input,
                            'weight_per_package': lines.weight_per_package,
                            'loose_bool': lines.loose_bool,
                            'length_per_package': lines.length_per_package,
                            'width_per_package': lines.width_per_package,
                            'height_per_package': lines.height_per_package,
                            'weight_factor': lines.weight_factor,
                            'remarks': lines.remarks,
                            'hs_code': lines.hs_code,
                            'commodity_type': lines.commodity_type and lines.commodity_type.id or False,
                        }
                        cargo_line_id = self.env['cargo.freight.line'].create(vals2)
                        cargo_line_id.onchange_product_id()

                if res.mode == 'air':
                    details_vals = {
                            'order_id': cargo_id and cargo_id.id or False,
                            'uom_id': res.opportunity_id and res.opportunity_id.weight_uom_id and res.opportunity_id.weight_uom_id.id or False,
                            'no_of_pieces': res.total_pieces,
                            'gross_weight': res.total_gross_weight,
                            'chargeable_weight': res.sum_of_total_chargeable_weight,
                        }
                    self.env['cargo.details.line'].create(details_vals)
                        
                    view = self.env.ref('verts_v15_freight_forward.air_freight_import_form_view_inherit')
                else:
                    view = self.env.ref('verts_v15_freight_forward.cargo_order_export_form_view_inherit')
                return {
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'cargo.order',
                    'views': [(view.id, 'form')],
                    'view_id': view.id,
                    'res_id': cargo_id.id,
                    'context': self.env.context,
                }

    # def create_cargo_order(self):
    #     cargo_id = self.copy(default={'cargo_order': True, 'export': False})
    #     if cargo_id:
    #         view = self.env.ref('verts_v15_freight_forward.cargo_order_export_form_view_inherit')
    #         return {
    #             'type': 'ir.actions.act_window',
    #             'view_type': 'form',
    #             'view_mode': 'form',
    #             'res_model': 'sale.order',
    #             'views': [(view.id, 'form')],
    #             'view_id': view.id,
    #             'res_id': cargo_id.id,
    #             'context': self.env.context,
    #         }

    def action_confirm(self):
        for order in self:
            if order.currency_id.id != order.company_currency_id.id:
                if not order.cur_rate or order.cur_rate == 0.0:
                    raise UserError(_(
                        "Currency conversion rate has to be filled and cannot be zero"
                    ))
        res = super(SaleOrder, self).action_confirm()
        for order in self:
            if order.export:
                picking_id = False
                for line in order.payment_term_line:
                    if line.value < 1:
                        raise UserError(_('Payment [%s] -  Value should be greater than 0!') % (line.payment_id.name))
                for line in order.order_line:
                    line.base_price = line.price_unit
                    line.overhead_expenses = order.rate_per_kg_on_expense
                    line.price_unit = line.base_price + order.rate_per_kg_on_expense
                    for pick in self.picking_ids:
                        for move in pick.move_ids_without_package:
                            if move.product_id == line.product_id:
                                move.write({'packing_type': line.packing_type and line.packing_type.id or False,
                                            'bag_box_qty': line.bag_box_qty})
                        pick.is_export = True
                        picking_id = pick.id
                for l in self.qc_pro_specification_line:
                    l.write({'picking_id': picking_id})
        return res

    @api.model
    def create(self, vals):
        '''Sale Order Create Function'''
        if vals.get('cargo_order') == True:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('cargo.order.seq')
        if vals.get('export') == True and vals.get('date_order'):
            if vals.get('name', _('New')) == _('New'):
                date_order = vals['date_order'].split(" ")
                date = datetime.strptime(date_order[0], '%Y-%m-%d')
                current_year = date.strftime("%y")
                current_month = date.month
                if len(str(current_month)) < 2:
                    current_month = '0' + str(current_month)
                seq_obj = self.env['ir.sequence'].search([('code', '=', 'seq.export.sale')], limit=1)
                seq = seq_obj.next_by_code('seq.export.sale') or '/'
                prefix = seq_obj.prefix
                lst = seq.split('/')
                name = prefix + str(current_month) + '/' + str(current_year) + '/' + lst[-1]
                vals['name'] = name
        res = super(SaleOrder, self).create(vals)
        if res:
            so_inv_id = self.env['so.invoice.value'].create({
                'sale_id': res.id,
            })
            res.so_invoice_id = so_inv_id.id
        return res


class container_detail(models.Model):
    _name = "container.detail"
    _description = 'container Detail'

    order_id = fields.Many2one('sale.order', 'Order Id')
    container_type_id = fields.Many2one('container.type', 'Container Type')
    container_qty = fields.Char('Container Quantity', default=1)
    capacity_in_mt = fields.Float('Capacity(MT)')

    # invoice_id = fields.Many2one('account.invoice', string="Invoice")##by kajal

    @api.onchange('container_type_id')
    def onchange_container_type_id(self):
        if self.container_type_id:
            self.capacity_in_mt = self.container_type_id.capacity


class SaleFreightline(models.Model):
    _name = "sale.freight.line"
    _description = "Sale Freight Line"

    def _get_default_dimension_uom_id(self):
        return self.env.ref('uom.product_uom_cm')

    def _get_default_weight_uom_id(self):
        return self.env.ref('uom.product_uom_kgm')

    sale_id = fields.Many2one('sale.order', string="Sale Id")
    product_id = fields.Many2one('product.product', string="Product")
    container_type_id = fields.Many2one('container.type', string="Container Type")
    capacity_in_mt = fields.Float(string="Capacity (MT)")
    container_qty = fields.Integer(string="Container Qty.")
    commercial_invoice_value = fields.Float(string="Commercial Invoice Value")
    goods_desc = fields.Text(string='Goods Description')
    packing_type = fields.Many2one('export.packing.type', string="Packing Type")
    product_uom = fields.Many2one('uom.uom', string="Unit of Measurement")
    hs_code = fields.Char('HS code')
    commodity_type = fields.Many2one('export.product.category', string="Commodity Type")
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
    pivot_weight = fields.Float(string="Pivot Weight")


    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.product_id:
            self.product_uom = self.product_id.uom_id.id

    @api.onchange('container_type_id')
    def onchange_container_type_id(self):
        if self.container_type_id:
            self.capacity_in_mt = self.container_type_id.capacity

    # @api.onchange('product_id', 'sale_id.service_type')
    # def onchange_get_weight_factor(self):
    #     if self.sale_id.service_type:
    #         self.weight_factor = self.sale_id.service_type.weight_factor
    #         self.full_container_service = self.sale_id.service_type.full_container_service

    # @api.onchange('product_id', 'sale_id.weight_uom_id', 'sale_id.dimension_uom_id')
    # def onchange_get_uoms(self):
    #     if self.sale_id.weight_uom_id:
    #         self.weight_uom_id = self.sale_id.weight_uom_id.id
    #     if self.sale_id.dimension_uom_id:
    #         self.dimension_uom_id = self.sale_id.dimension_uom_id.id

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

    # @api.depends('chargeable_weight', 'product_uom_quantity')
    # def _compute_total_chargeable_weight(self):
    #     for res in self:
    #         res.total_chargeable_weight = res.chargeable_weight * res.product_uom_quantity
    
    @api.depends('total_volumetric_weight', 'total_weight', 'pivot_weight')
    def _compute_total_chargeable_weight(self):
        for rec in self:
            # res.total_chargeable_weight = res.chargeable_weight * res.product_uom_quantity
            rec.total_chargeable_weight = max(
                rec.total_volumetric_weight or 0,
                rec.total_weight or 0,
                rec.pivot_weight or 0
            )

    # @api.depends('volume_cbcm', 'weight_factor', 'sale_id.service_type')
    @api.depends('volume_cbcm', 'weight_factor', 'sale_id', 'sale_id.opportunity_id')
    def _compute_volumetric_weight(self):
        for res in self:
            if res.weight_factor > 0:
                if res.sale_id.opportunity_id.service_type.weight_factor_type == 'on_cbcm':
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


class expense_line(models.Model):
    _name = "expense.line"
    _description = 'expense Line'

    @api.depends('qty', 'rate')
    def _get_exp_amt(self):
        for val in self:
            val.exp_amt = val.qty * val.rate

    order_id = fields.Many2one('sale.order', 'Order Id')
    exp_related_to = fields.Char('Expense Related to')
    # product_class = fields.Many2one('product.classification', string='Product Class')
    expense_id = fields.Many2one('product.product', 'Expense Name')
    qty = fields.Integer(string='Quantity', default=1)
    usd_value = fields.Float(string='USD')
    rate = fields.Float('Rate')
    exp_amt_fc = fields.Float('Expense Amt (FC)')
    exp_amt = fields.Float('Expense Amt', compute='_get_exp_amt')
    remark = fields.Char('Remarks')

    # invoice_id = fields.Many2one('account.invoice', string="Invoice")##by kajal

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


class sale_export_document(models.Model):
    _name = "sale.export.document"
    _description = 'sale_export_document'

    export_document_id = fields.Many2one('export.document', 'Document Name')
    order_id = fields.Many2one('sale.order', 'Sale Order Id')
    # invoice_id = fields.Many2one('account.invoice', string="Invoice")##by kajal


class PaymenTermLine(models.Model):
    _name = "payment.term.line"
    _description = 'PaymenT erm Line'

    order_id = fields.Many2one('sale.order', 'Order Id')
    country_id = fields.Many2one('res.country', 'Country')
    payment_id = fields.Many2one('account.payment.term', 'Payment Term')
    value = fields.Float(string='Value (%)')
    ecgc_rate = fields.Float(string='ECGC Rate (%)')

    # invoice_id = fields.Many2one('account.invoice', string="Invoice")##by kajal

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


class SaleScheduleLine(models.Model):
    _name = "sale.schedule.line"
    _description = "Sale Schedule Line"
    _rec_name = "schedule_id"

    sale_id = fields.Many2one('sale.order', string="Order Id")
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
    sale_export_attachment_lines = fields.One2many('sale.schedule.attachment.line', 'sale_export_attachment_id',
                                                   string='Attachment Lines')

    @api.onchange('schedule_id')
    def onchange_schedule_id(self):
        if self.schedule_id:
            self.report_at_time = self.schedule_id.report_at_time
            self.req_from = self.schedule_id.req_from
            self.country_specific = self.schedule_id.country_specific
            self.port_of_loading_specific = self.schedule_id.port_of_loading_specific


class SaleScheduleAttachmentLine(models.Model):
    """ Attachment Details """
    _name = "sale.schedule.attachment.line"
    _description = 'Sale Schedule Attachment Line'

    sale_export_attachment_id = fields.Many2one('sale.schedule.line')
    sale_remark = fields.Char(string='Remark')
    fname = fields.Char()
    sale_attachment_value = fields.Binary(string='Attachment')


class order_qc_specification_line(models.Model):
    _name = "order.qc.specification.line"
    _description = "Order Qc Specification Line"
    _rec_name = 'qc_parameter_id'

    order_id = fields.Many2one('sale.order', string="Order ID")
    product_id = fields.Many2one('product.product', string="Product")
    qc_parameter_id = fields.Many2one('product.mix.variants', string="Parameter")
    value = fields.Char(string="Value")
    picking_id = fields.Many2one('stock.picking', string="Picking")

    # invoice_id = fields.Many2one('account.invoice', string="Invoice")##by kajal

    @api.onchange('qc_parameter_id')
    def onchange_qc_parameter_id(self):
        if self.qc_parameter_id:
            self.value = self.qc_parameter_id.value


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    base_price = fields.Float(string="Base Price", digits=('16', 2))
    overhead_expenses = fields.Float(string="Overhead/Expenses")
    packing_type = fields.Many2one('export.packing.type', string="Packing Type")
    bag_box_qty = fields.Float(string="Bag/Box Qty.")
    container_type_id = fields.Many2one('container.type', 'Container Type')
    capacity_in_mt = fields.Float('Capacity(MT)')
    show_in_awb = fields.Boolean('Show in AWB', defalt=False)
    charge_type = fields.Selection([
                                    ('due_agent', "Due Agent"),
                                    ('due_carrier', "Due Carrier")], string="Charge Type")
    as_per_actual = fields.Boolean('As per Actual', defalt=False)
    # delete_selected = fields.Boolean(string='Select for Deletion', defalt=False)


    @api.onchange('container_type_id')
    def onchange_container_type_id(self):
        if self.container_type_id:
            self.capacity_in_mt = self.container_type_id.capacity


class ExportSoTcSetLines(models.Model):
    _name = "export.so.tc.set.lines"
    _description = "Export So Tc Set Lines"

    s_no = fields.Integer(string="S No", compute="_sequence_ref")
    export_so_tc_set_id = fields.Many2one('sale.order', string='Terms And Condition Set Id')
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
