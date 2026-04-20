# -*- coding: utf-8 -*-
# Copyright 2021 Verts Services India Pvt Ltd.
# http://www.verts.co.in
import json

from odoo import api, fields, models, _
from odoo.exceptions import UserError



class PurchaseOrder(models.Model):
    _inherit = "purchase.order"


    def action_view_invoice(self, invoices=False):
        """This function returns an action that display existing vendor bills of
        given purchase order ids. When only one found, show the vendor bill
        immediately.
        """
        if not invoices:
            # Invoice_ids may be filtered depending on the user. To ensure we get all
            # invoices related to the purchase order, we read them in sudo to fill the
            # cache.
            self.sudo()._read(['invoice_ids'])
            invoices = self.invoice_ids

        result = self.env['ir.actions.act_window']._for_xml_id('account.action_move_in_invoice_type')
        # choose the view_mode accordingly
        if len(invoices) > 1:
            result['domain'] = [('id', 'in', invoices.ids)]
        elif len(invoices) == 1:
            res = self.env.ref('verts_v15_freight_forward.custom_view_move_form_ff', False)
            form_view = [(res and res.id or False, 'form')]
            if 'views' in result:
                result['views'] = form_view + [(state, view) for state, view in result['views'] if view != 'form']
            else:
                result['views'] = form_view
            result['res_id'] = invoices.id
        else:
            result = {'type': 'ir.actions.act_window_close'}

        return result

        

    opportunity_id = fields.Many2one('crm.lead', string="Opportunity ID")
    is_agent_quote = fields.Boolean(string="Is Agent Quote", default=False)
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
        ('cross_trade', 'Cross Trade')], string='Import/Export')

    # import_export = fields.Selection([
    #     ('import', 'Import'),
    #     ('export', 'Export'),
    #     ('cross_trade', 'Cross Trade'),
    # ], string='Import/Export')

    customer_id = fields.Many2one('res.partner', string="Customer")
    goods_category_id = fields.Many2one('export.product.category', string='Goods Category')
    hs_code = fields.Char(string="HS Code")

    stuffing_point_id = fields.Many2one('ports', string="Stuffing Point")
    port_of_discharge_id = fields.Many2one('ports', string="Point of Discharge")
    port_of_loading_id = fields.Many2one('ports', string="Point of Loading")
    incoterm_id = fields.Many2one('account.incoterms', string="Shipment (Inco) Terms")
    service_type = fields.Many2one('service.type', string="Service Type")
    total_pieces = fields.Float(string='Total Pieces', compute='_compute_total_pieces', store=True)
    # total_gross_weight = fields.Float(string='Total Gross Weight')
    total_cbm = fields.Float(string='Total CBM')
    total_value = fields.Float(string='Total Value', compute='_compute_total_value', store=True)
    total_chargeable_weight = fields.Float(string='Total Chargeable Weight')
    total_volume_cbm = fields.Float(string='Total Volume (cbm)', compute='_compute_total_volume_cbm', store=True)
    total_volumetric_weight = fields.Float(string='Total Volumetric weight')
    account_analytic_id = fields.Many2one('account.analytic.account', string='Analytic Account')
    weight_uom_id = fields.Many2one('uom.uom', string='Weight UOM')
    dimension_uom_id = fields.Many2one('uom.uom', string='Dimension UOM')
    carrier_name = fields.Char(string="Carrier Name")
    transit_time = fields.Integer(string="Transit Time")
    validity_date = fields.Datetime(string="Validity of the Quote")
    freight_type = fields.Char(string='Freight Type')
    notes2 = fields.Text(string="Notes")
    freight_order_line = fields.One2many('freight.purchase.line', 'purchase_id', string="Freight Order Line")
    purchase_container_line_ids = fields.One2many('purchase.container.lines', "purchase_id", "Container Details")
    container_load = fields.Selection([("fcl", "Full Container Load (FCL)"), ("lcl", "Less than Container Load (LCL)")],
                                      string="Container Load")
    currency_conversion_rate = fields.Float(string='Currency Conversion Rate', digits='Currency Rate')
    company_currency_id = fields.Many2one('res.currency', related='company_id.currency_id')
    total_cur_conversion_amount = fields.Monetary(
        string='Total After Currency Conversion',
        currency_field='company_currency_id',
        compute='_compute_total_cur_conversion_amount',
        store=True
    )
    pivot_weight = fields.Float(string="Pivot Weight",)
    total_gross_weight = fields.Float(string="Total Gross Weight", compute="_compute_freight_weights", inverse='_inverse_total_gross_weight', store=True)
    sum_total_volumetric_weight = fields.Float(string="Total Volumetric Weight", compute="_compute_freight_weights",
                                               store=True)
    sum_of_total_chargeable_weight = fields.Float(
        string='Sum of Total Chargeable Weight',
        compute='_compute_sum_of_total_chargeable_weight',
        store=True
    )
    freight_forwarding = fields.Boolean(string="Freight Forwarding", default=False)
    pre_cargo_carriage = fields.Boolean(string="Pre Cargo Carriage", default=False)
    custom_clearance = fields.Boolean(string="Custom Clearance", default=False)
    reefer_dry = fields.Selection([
        ('reefer', 'Reefer'),
        ('dry', 'Dry')], string="Reefer/Dry")
    genset = fields.Boolean(string="Genset", default=False)
    gsa_sales = fields.Boolean(string="GSA Sales", default=False)
    sale_id = fields.Many2one('sale.order',string='Sale Id')


    def _prepare_invoice(self):
        invoice_vals = super()._prepare_invoice()
        bill_of_lading_no = False
        mawb = False
        hawb = False
        mawb_land = False
        shipping_line = False
        air_airline_code = False
        air_airline_no = False
        flight_date_1 = False
        agent_id = False
        if self.opportunity_id:
            sale_ids =  self.env['sale.order'].search([('opportunity_id', '=', self.opportunity_id.id)], limit=1)
            if sale_ids and sale_ids.cargo_id:
                bill_of_lading_no = sale_ids.cargo_id.bill_of_lading_no
                mawb = sale_ids.cargo_id.mawb.id if sale_ids.cargo_id.mawb else False
                hawb = sale_ids.cargo_id.hawb if sale_ids.cargo_id.hawb else False
                mawb_land = sale_ids.cargo_id.mawb_land if sale_ids.cargo_id.mawb_land else False
                shipping_line = sale_ids.cargo_id.shipping_line.id if sale_ids.cargo_id.shipping_line else False
                air_airline_code = sale_ids.cargo_id.air_airline_code if sale_ids.cargo_id.air_airline_code else False
                air_airline_no = sale_ids.cargo_id.air_airline_no if sale_ids.cargo_id.air_airline_no else False
                flight_date_1 = sale_ids.cargo_id.flight_date_1 if sale_ids.cargo_id.flight_date_1 else False
                agent_id = sale_ids.cargo_id.agent_id if sale_ids.cargo_id.agent_id else False
                flight_number_1 = sale_ids.cargo_id.flight_number_1 if sale_ids.cargo_id.flight_number_1 else False

        invoice_vals.update({
            'cur_rate': self.currency_conversion_rate,
                # 'consignee_id': self.consignee_id and self.consignee_id.id or False,
                # 'consignor_id': res.consignor_id and res.consignor_id.id or False,
                # 'notify_id': res.notify_id and res.notify_id.id or False,
                # 'cha_id': res.cha_id and res.cha_id.id osale_idr False,
                # 'reference_by_id': res.reference_by_id and res.reference_by_id.id or False,
                # 'cur_rate': res.sale_id and res.sale_id.cur_rate or res.cur_rate,
                'stuffing_point_id': self.stuffing_point_id and self.stuffing_point_id.id or False,
                'port_of_loading_id': self.port_of_loading_id and self.port_of_loading_id.id or False,
                'port_of_discharge_id': self.port_of_discharge_id and self.port_of_discharge_id.id or False,
                'order_type': self.order_type,
                'mode': self.mode,
                'import_export': self.import_export,
                'invoice_incoterm_id': self.incoterm_id and self.incoterm_id.id or False,
                # 'account_analytic_id': res.account_analytic_id and res.account_analytic_id.id or False,
                'customer_po_ref': self.partner_ref,
                ###
                'bill_of_lading_no': bill_of_lading_no,
                'mawb': mawb,
                'hawb': hawb,
                'mawb_land': mawb_land,
                'shipping_line': shipping_line,
                'air_airline_code': air_airline_code,
                'air_airline_no': air_airline_no,
                'flight_date_1' : flight_date_1,
                'flight_number_1' : flight_number_1,
                'agent_id' : agent_id,
                ###
                # 'estimated_time_departure': res.estimated_time_departure,
                # 'eta_port_of_destination': res.eta_port_of_destination,
                # 'total_pieces': self.total_pieces,
                'total_gross_weight': self.total_gross_weight,
                'total_chargeable_weight': self.sum_of_total_chargeable_weight,
                # 'total_cbm': res.total_cbm,
                # 'total_value': res.total_value,
                # 'total_volume_cbm': res.total_volume_cbm,
                # 'total_volumetric_weight': res.total_volumetric_weight,
                ###
                ####
                # 'narration':res.other_remarks,
                'currency_id':self.currency_id and self.currency_id.id or False,
                'freight_forwarding': self.freight_forwarding,
                'pre_cargo_carriage': self.pre_cargo_carriage,
                'custom_clearance': self.custom_clearance,
                'reefer_dry': self.reefer_dry,
                'genset': self.genset,
                'gsa_sales': self.gsa_sales,
                 'is_export': True,
        })
        return invoice_vals

    def button_confirm(self):
        for order in self:
            print(f"Currency ID: {order.currency_id.id}, Company Currency ID: {order.company_id.currency_id.id}")
            print(f"Currency Conversion Rate: {order.currency_conversion_rate}")

            if order.currency_id.id != order.company_id.currency_id.id:
                print("Currencies are different")
                if not order.currency_conversion_rate or order.currency_conversion_rate == 0:
                    print("Currency conversion rate is empty or zero")
                    raise UserError(_('Currency conversion rate has to be filled and cannot be zero'))
        return super(PurchaseOrder, self).button_confirm()

    def _inverse_total_gross_weight(self):
        pass

    @api.depends('freight_order_line.commercial_invoice_value')
    def _compute_total_value(self):
        for order in self:
            order.total_value = sum(line.commercial_invoice_value for line in order.freight_order_line)

    @api.depends('freight_order_line.total_volume_cbm')
    def _compute_total_volume_cbm(self):
        for order in self:
            order.total_volume_cbm = sum(line.total_volume_cbm for line in order.freight_order_line)

    @api.depends('freight_order_line.product_uom_quantity')
    def _compute_total_pieces(self):
        for order in self:
            total = sum(line.product_uom_quantity for line in order.freight_order_line)
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
        'freight_order_line',
        'freight_order_line.total_weight',
        'freight_order_line.total_volumetric_weight',
    )
    def _compute_freight_weights(self):
        for rec in self:
            # pivot = 0.0
            gross = 0.0
            volumetric = 0.0

            for line in rec.freight_order_line:
                # pivot += line.pivot_weight or 0.0
                gross += line.total_weight or 0.0
                volumetric += line.total_volumetric_weight or 0.0

            # rec.pivot_weight = pivot
            rec.total_gross_weight = gross
            rec.sum_total_volumetric_weight = volumetric

    @api.depends('amount_total', 'currency_conversion_rate')
    def _compute_total_cur_conversion_amount(self):
        for order in self:
            # base_total = sum( for line in order.order_line)
            order.total_cur_conversion_amount = order.amount_total*order.currency_conversion_rate if order.currency_conversion_rate > 0 else 0.0

    @api.onchange('goods_category_id')
    def _onchange_goods_category_id(self):
        if self.goods_category_id:
            self.hs_code = self.goods_category_id.hs_code
        else:
            self.hs_code = False

    # @api.model
    # def create(self, vals):
    #     '''Purchase Order Create Function'''
    #     print("create===")
    #     if vals.get('is_agent') == True:
    #         print("is_agent===", vals.get('is_agent'))
    #         if vals.get('name', _('New')) == _('New'):
    #             print("is_agent===", vals.get('name'))
    #             vals['name'] = self.env['ir.sequence'].next_by_code('agent.quote.seq')
    #     return super(PurchaseOrder, self).create(vals)



    def action_create_quotation(self):
        for res in self:
            if res.opportunity_id and res.opportunity_id.partner_id:
                partner = res.opportunity_id.partner_id.id
            else:
                partner = res.partner_id.id
            order_id = self.env['sale.order'].create({
                'opportunity_id': res.opportunity_id and res.opportunity_id.id or False,
                'partner_id': partner or False,
                'team_id': res.opportunity_id.team_id.id,
                'campaign_id': res.opportunity_id.campaign_id.id,
                'medium_id': res.opportunity_id.medium_id.id,
                'origin': res.name,
                'source_id': res.opportunity_id.source_id.id,
                'company_id': res.company_id.id or res.env.company.id,
                'tag_ids': [(6, 0, res.opportunity_id.tag_ids.ids)],
                'consignor_id': res.opportunity_id.consignor_id and res.opportunity_id.consignor_id.id or False,
                'consignee_id': res.opportunity_id.consignee_id and res.opportunity_id.consignee_id.id or False,
                'notify_id': res.opportunity_id.notify_id and res.opportunity_id.notify_id.id or False,
                'validity_date': res.opportunity_id.validity_date,
                'cha_id': res.opportunity_id.cha_id and res.opportunity_id.cha_id.id or False,
                'reference_by_id': res.opportunity_id.reference_by_id and res.opportunity_id.reference_by_id.id or False,
                # 'cur_rate': res.opportunity_id.cur_rate,
                'stuffing_point_id': res.opportunity_id.stuffing_point_id and res.opportunity_id.stuffing_point_id.id or False,
                'port_of_loading_id': res.opportunity_id.port_of_loading_id and res.opportunity_id.port_of_loading_id.id or False,
                'port_of_discharge_id': res.opportunity_id.port_of_discharge_id and res.opportunity_id.port_of_discharge_id.id or False,
                'incoterm_id': res.opportunity_id.incoterm_id and res.opportunity_id.incoterm_id.id or False,
                'analytic_account_id': res.account_analytic_id and res.account_analytic_id.id or False,
                'export': True,
                'order_type': res.order_type,
                'mode': res.mode,
                'import_export': res.import_export,
                'carrier_name': res.carrier_name,
                'transit_time': res.transit_time,
                'freight_type': res.freight_type,
                'notes2': res.notes2,
                'total_pieces': res.total_pieces,
                'total_gross_weight': res.total_gross_weight,
                'total_cbm': res.total_cbm,
                'total_value': res.total_value,
                'total_chargeable_weight': res.total_chargeable_weight,
                'total_volume_cbm': res.total_volume_cbm,
                'total_volumetric_weight': res.total_volumetric_weight,
                'hs_code': res.hs_code,
                'commodity': res.goods_category_id and res.goods_category_id.id or False,
                'pivot_weight': res.pivot_weight,
                'purchase_id': res.id,
                'cur_rate': res.currency_conversion_rate,
                'freight_forwarding': res.freight_forwarding,
                'pre_cargo_carriage': res.pre_cargo_carriage,
                'custom_clearance': res.custom_clearance,
                'reefer_dry': res.reefer_dry,
                'genset': res.genset,
                'gsa_sales': res.gsa_sales,
            })
            if order_id:
                res.sale_id = order_id.id
                # for each in res.order_line:
                #     order_line_id = self.env['sale.order.line'].create({
                #         'product_id': each.product_id and each.product_id.id or False,
                #         'order_id': order_id and order_id.id or False,
                #         'name': each.product_id.name,
                #         'product_uom_qty': each.product_qty,
                #         'product_uom': each.product_uom and each.product_uom.id or False,
                #         'price_unit': each.price_unit,
                #         # 'tax_id': [(6, False, each.tax_ids.ids)],
                #     })
                #     order_line_id.product_id_change()
                for lines in res.freight_order_line:
                    vals2 = {
                        'sale_id': order_id and order_id.id or False,
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
                        "pivot_weight": lines.pivot_weight,
                        "hs_code": lines.hs_code,
                        'commodity_type': lines.commodity_type and lines.commodity_type.id or False,
                        'volumetric_weight': lines.volumetric_weight,
                        'total_chargeable_weight': lines.total_chargeable_weight,
                        'chargeable_weight': lines.chargeable_weight,
                        'volume_cbcm': lines.volume_cbcm,
                        'volume': lines.volume,
                        'total_weight': lines.total_weight,
                        'total_volume_cbm': lines.total_volume_cbm,
                        'total_volumetric_weight': lines.total_volumetric_weight,
                    }
                    sale_freight_line = self.env['sale.freight.line'].create(vals2)
                    sale_freight_line.onchange_product_id()
                order_id.total_gross_weight = self.total_gross_weight
                view = self.env.ref('verts_v15_freight_forward.sale_order_export_form_view_inherit')
                return {
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'sale.order',
                    'views': [(view.id, 'form')],
                    'view_id': view.id,
                    'res_id': order_id.id,
                    'context': self.env.context,
                }

    def action_create_invoice(self):
        for order in self:
            sale_ids = self.env['sale.order'].search([('opportunity_id', '=', self.opportunity_id.id)], limit=1)
            if not sale_ids:
                raise UserError(_("Please create customer quote first."))
            if sale_ids and not sale_ids.is_cargo_done:
                raise UserError(_("Please create the cargo order from corresponding Customer Order."))

        # Call super to create the invoice/bill
        res = super().action_create_invoice()
        return res

class FreightPurchaseline(models.Model):
    _name = "freight.purchase.line"
    _description = "Freight Purchase Line"

    def _get_default_dimension_uom_id(self):
        return self.env.ref('uom.product_uom_cm')

    def _get_default_weight_uom_id(self):
        return self.env.ref('uom.product_uom_kgm')

    purchase_id = fields.Many2one('purchase.order', string="Purchase Id")
    product_id = fields.Many2one('product.product', string="Product")
    container_type_id = fields.Many2one('container.type', string="Container Type")
    capacity_in_mt = fields.Float(string="Capacity (MT)")
    container_qty = fields.Integer(string="Container Qty.")
    commodity_type = fields.Many2one('export.product.category', string="Commodity Type")
    hs_code = fields.Char('HS code')
    commercial_invoice_value = fields.Float(string="Commercial Invoice Value")
    goods_desc = fields.Text(string='Goods Description')
    packing_type = fields.Many2one('export.packing.type', string="Packing Type")
    product_uom = fields.Many2one('uom.uom', string="Unit of Measurement")
    # no_of_package = fields.Integer(string='No. Of Package')
    type = fields.Selection([
        ('stackable', 'Stackable'),
        ('non_stackable', 'Non-Stackable')], string='Type', help="Are packages stackable?")
    product_uom_quantity = fields.Float(string="No. of Bag/Box/Pack", default=1.0)
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
    consignor_id = fields.Many2one('res.partner', string="Shipper")
    consignor_name = fields.Char(string='Shipper Name')
    consignor_street = fields.Char(string='Consignor Street')
    consignor_street2 = fields.Char(string='Consignor Street2')
    consignor_city_id = fields.Many2one('cities.basic.masters', string='Consignor City')
    consignor_state_id = fields.Many2one('res.country.state', sting="Consignor State")
    consignor_zip = fields.Char(string='Consignor Zip')
    consignor_country_id = fields.Many2one('res.country', string="Consignor Country")
    pivot_weight = fields.Float(string="Pivot Weight")



    @api.onchange('commodity_type')
    def _onchange_commodity_type(self):
        if self.commodity_type:
            self.hs_code = self.commodity_type.hs_code
        else:
            self.hs_code = False  # अगर commodity_type हटे तो HS Code भी हट जाए


    # @api.onchange('product_id', 'purchase_id.consignor_id', 'purchase_id.consignor_name', 'purchase_id.consignor_street',
    #               'purchase_id.consignor_street2', 'purchase_id.consignor_city_id', 'purchase_id.consignor_state_id',
    #               'purchase_id.consignor_country_id')
    # def onchange_get_shipper_details(self):
    #     if self.purchase_id.consignor_id:
    #         self.consignor_id = self.purchase_id.consignor_id.id
    #     if self.purchase_id.consignor_name:
    #         self.consignor_name = self.purchase_id.consignor_name
    #     if self.purchase_id.consignor_street:
    #         self.consignor_street = self.purchase_id.consignor_street
    #     if self.purchase_id.consignor_street2:
    #         self.consignor_street2 = self.purchase_id.consignor_street2
    #     if self.purchase_id.consignor_city_id:
    #         self.consignor_city_id = self.purchase_id.consignor_city_id.id
    #     if self.purchase_id.consignor_state_id:
    #         self.consignor_state_id = self.purchase_id.consignor_state_id.id
    #     if self.purchase_id.consignor_country_id:
    #         self.consignor_country_id = self.purchase_id.consignor_country_id.id

    def abc(self):
        if self.purchase_id.service_type:
            self.weight_factor = self.purchase_id.service_type.weight_factor
            self.full_container_service = self.purchase_id.service_type.full_container_service

    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.product_id:
            self.product_uom = self.product_id.uom_id.id

    @api.onchange('product_id', 'purchase_id.service_type')
    def onchange_get_weight_factor(self):
        if self.purchase_id.service_type:
            self.weight_factor = self.purchase_id.service_type.weight_factor
            self.full_container_service = self.purchase_id.service_type.full_container_service

    @api.onchange('product_id', 'purchase_id.weight_uom_id', 'purchase_id.dimension_uom_id')
    def onchange_get_uoms(self):
        if self.purchase_id.weight_uom_id:
            self.weight_uom_id = self.purchase_id.weight_uom_id.id
        if self.purchase_id.dimension_uom_id:
            self.dimension_uom_id = self.purchase_id.dimension_uom_id.id

    @api.depends('weight_per_package', 'product_uom_quantity')
    def _compute_total_weight(self):
        for res in self:
            res.total_weight = res.weight_per_package * res.product_uom_quantity

    @api.depends('length_per_package', 'width_per_package', 'height_per_package')
    def _compute_volume_cbcm(self):
        for res in self:
            res.volume_cbcm = res.length_per_package * res.width_per_package * res.height_per_package

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

    @api.depends('volume_cbcm', 'weight_factor')
    def _compute_volumetric_weight(self):
        for res in self:
            if res.weight_factor > 0:
                if res.purchase_id.service_type.weight_factor_type == 'on_cbcm':
                    res.volumetric_weight = res.volume_cbcm / res.weight_factor
                else:
                    res.volumetric_weight = res.volume * res.weight_factor

    @api.onchange('weight_input', 'weight_per_package')
    def onchange_weight_input(self):
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


class Purchasecontainerlines(models.Model):
    _name = "purchase.container.lines"
    _description = "Purchase Container Line"

    purchase_id = fields.Many2one('purchase.order', string="Purchase ID")
    container_type_id = fields.Many2one('container.type', string="Container Type")
    capacity_in_mt = fields.Float(string="Capacity (MT)")
    container_qty = fields.Char(string="No. of Containers")

    @api.onchange('container_type_id')
    def onchange_container_type_id(self):
        if self.container_type_id:
            self.capacity_in_mt = self.container_type_id.capacity
            
class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    as_per_actual = fields.Boolean('As per Actual', defalt=False)
    # commission_loaded = fields.Boolean(string="Commission Loaded", default=False)

