# -*- coding: utf-8 -*-
# Copyright 2021 Verts Services India Pvt Ltd.
# http://www.verts.co.in

from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError


class CrmLead(models.Model):
    _inherit = "crm.lead"
    _order = 'id desc'

    def _get_default_dimension_uom_id(self):
        return self.env.ref('uom.product_uom_cm')

    def _get_default_weight_uom_id(self):
        return self.env.ref('uom.product_uom_kgm')

    code = fields.Char(string='Code', required=True, copy=False, default=lambda self: _('New'))
    date_order = fields.Datetime(string='Order Date')
    validity_date = fields.Datetime(string='Expiration')
    consignor_id = fields.Many2one('res.partner', string="Shipper")
    consignor_name = fields.Char(string='Shipper Name')
    consignor_phone = fields.Char(string='Phone Number')
    consignor_email = fields.Char(string='Email Id')
    meeting_count = fields.Char(string='Meeting')  # added by kajal
    consignor_point_contact = fields.Char(string='Point of Contact')
    consignor_street = fields.Char(string='Consignor Street')
    consignor_street2 = fields.Char(string='Consignor Street2')
    consignor_city_id = fields.Many2one('cities.basic.masters', string='Consignor City')
    consignor_state_id = fields.Many2one('res.country.state', string="Consignor State")
    consignor_zip = fields.Char(string='Consignor Zip')
    consignor_country_id = fields.Many2one('res.country', string="Consignor Country")
    consignee_id = fields.Many2one('res.partner', string="Consignee")
    consignee_name = fields.Char(string='Consignee Name')
    consignee_phone = fields.Char(string='Consignee Phone')
    consignee_email = fields.Char(string='Consignee Mail')
    consignee_street = fields.Char(string='Consignee Street')
    consignee_street2 = fields.Char(string='Consignee Street2')
    consignee_city_id = fields.Many2one('cities.basic.masters', string='Consignee City')
    consignee_state_id = fields.Many2one('res.country.state', string="Consignee State")
    consignee_zip = fields.Char(string='Consignee Zip')
    consignee_country_id = fields.Many2one('res.country', string="Consignee Country")
    notify_id = fields.Many2one('res.partner', string="Notify Party")
    cha_id = fields.Many2one('res.partner', string="Custom House Agent")
    reference_by_id = fields.Many2one('res.partner', string="Reference By")
    pricelist_id = fields.Many2one('product.pricelist', string="Pricelist")
    cur_rate = fields.Float(string="Currency Rate")
    port_of_discharge_id = fields.Many2one('ports', string="Point of Discharge")
    port_of_loading_id = fields.Many2one('ports', string="Point of Loading")
    is_freight_lead = fields.Boolean(string="Is CRM Freight")
    order_line = fields.One2many('lead.order.line', 'lead_id', string='CRM Lead Line', copy=True)
    lead_container_line = fields.One2many('lead.container.lines', 'lead_id', string='Container Line')
    incoterm_id = fields.Many2one('account.incoterms', string="Shipment (Inco) Terms")
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
    goods_category_id = fields.Many2one('export.product.category', string='Goods Category')
    hs_code = fields.Char(string="HS Code")
    partner_contacts = fields.Many2one('res.partner', string="Partner Contacts")
    service_type = fields.Many2one('service.type', string="Service Type")
    total_pieces = fields.Float(string='Total Pieces', store=True, compute='_compute_sum_of_total')
    total_volume = fields.Float(string='Total Volume', store=True, compute='_compute_sum_of_total')
    total_gross_weight = fields.Float(string='Total Gross Weight', store=True, compute='_compute_sum_of_total', inverse='_inverse_gross_weight')
    total_cbm = fields.Float(string='Total CBM', store=True, compute='_compute_sum_of_total')
    total_value = fields.Float(string='Total Value', store=True, compute='_compute_sum_of_total')
    sum_of_total_chargeable_weight = fields.Float(string='Total Chargeable weight', store=True,
                                                  compute='_compute_sum_of_total_chargeable_weight', inverse='_inverse_chargeable_weight')
    sum_total_volume_cbm = fields.Float(string='Total Volume (cbm)', store=True, compute='_compute_sum_of_total')
    sum_total_volumetric_weight = fields.Float(string='Total Volumetric weight', store=True,
                                               compute='_compute_sum_of_total')
    pivot_weight = fields.Float(string='Pivot Weight', compute='_compute_sum_of_total', inverse='_inverse_pivot_weight', store=True)
    
    # agent_order_count = fields.Char(string='Count', compute='_compute_agent_order_count', store=True, help="Agent Order Count")
    # agent_order_lines = fields.One2many('purchase.order', 'opportunity_id', string='Agent Orders')
    weight_uom_id = fields.Many2one('uom.uom', string='Weight UOM', default=_get_default_weight_uom_id)
    dimension_uom_id = fields.Many2one('uom.uom', string='Dimension UOM', default=_get_default_dimension_uom_id)
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account')
    freight_forwarding = fields.Boolean(string="Freight Forwarding", default=False)
    pre_cargo_carriage = fields.Boolean(string="Pre Cargo Carriage", default=False)
    custom_clearance = fields.Boolean(string="Custom Clearance", default=False)
    reefer_dry = fields.Selection([
        ('reefer', 'Reefer'),
        ('dry', 'Dry')], string="Reefer/Dry")
    genset = fields.Boolean(string="Genset", default=False)
    gsa_sales = fields.Boolean(string="GSA Sales", default=False)
    stuffing_point_type = fields.Selection([
        ('port', 'Port'),
        ('other_location', 'Other Locations')], string="Stuffing Point Type")
    stuffing_point_id = fields.Many2one('res.partner', string="Point of Stuffing")
    stuffing_port_id = fields.Many2one('ports', string="Port of Stuffing")
    discharge_point_type = fields.Selection([
        ('port', 'Port'),
        ('other_location', 'Other Locations')], string="Discharge Point Type")
    point_of_delivery = fields.Many2one('res.partner', string="Point of Delivery")
    container_load = fields.Selection([("fcl", "Full Container Load (FCL)"), ("lcl", "Less than Container Load (LCL)")],
                                      string="Container Load")

    @api.depends('total_gross_weight', 'sum_total_volumetric_weight', 'pivot_weight')
    def _compute_sum_of_total_chargeable_weight(self):
        for rec in self:
            rec.sum_of_total_chargeable_weight = max(
                rec.total_gross_weight or 0,
                rec.sum_total_volumetric_weight or 0,
                rec.pivot_weight or 0
            )
            
    @api.onchange('goods_category_id')
    def _onchange_goods_category_id(self):
        if self.goods_category_id:
            self.hs_code = self.goods_category_id.hs_code
        else:
            self.hs_code = False

    def open_bulk_entry_wizard(self):
        # return {
        #     'name': 'Box Details Wizard',
        #     'type': 'ir.actions.act_window',
        #     'res_model': 'box.details.wizard',
        #     'view_mode': 'form',
        #     'target': 'new',
        #     'context': {
        #         'default_lead_id': self.id,
        #     },
        # }
        order_id = self.env['box.details.wizard'].create({
                'lead_id': self.id,
                'total_boxes': sum(line.product_uom_quantity for line in self.order_line)
            })
        for line in self.order_line:
            vals = {
                "wizard_id": order_id.id,
                "lead_line_id": line.id,
                "box_count": line.product_uom_quantity,
                "commodity_type": line.commodity_type and line.commodity_type.id or False,
                "hs_code": line.hs_code,
                "length": line.length_per_package,
                "width": line.width_per_package,
                "height": line.height_per_package,
                "weight": line.weight_input,
            }
            self.env['box.details.line'].create(vals)
        view = self.env.ref('verts_v15_freight_forward_crm.view_box_details_wizard_form')
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'box.details.wizard',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'res_id': order_id.id,
            'context': self.env.context,
            'target': 'new',
        }
        
    # @api.depends('agent_order_lines')
    # def _compute_agent_order_count(self):
    #     for res in self:
    #         agent_order_count = self.env['purchase.order'].sudo().search_count(
    #             [('opportunity_id', '=', res.id), ('is_agent_quote', '=', True)])
    #         res.agent_order_count = agent_order_count

    # def action_view_agent_order(self):
    #     action = self.env["ir.actions.act_window"]._for_xml_id("verts_v15_freight_forward_crm.action_ff_agent_quote_id")
    #     if self.id:
    #         action['domain'] = [('opportunity_id', '=', self.id)]
    #     else:
    #         action = {'type': 'ir.actions.act_window_close'}
    #     return action

    @api.depends('order_line', 'order_line.product_uom_quantity', 'order_line.volume',
                 'order_line.total_weight', 'order_line.commercial_invoice_value',
                 'order_line.total_chargeable_weight', 'order_line.total_volume_cbm',
                 'order_line.total_volumetric_weight', 'order_line.pivot_weight')
    def _compute_sum_of_total(self):
        for res in self:
            total_pieces = 0.0
            total_gross_weight = 0.0
            total_cbm = 0.0
            total_value = 0.0
            total_chargeable_weight = 0.0
            total_volume_cbm = 0.0
            total_volumetric_weight = 0.0
            total_pivot_weight = 0.0
            for line in res.order_line:
                total_pieces += line.product_uom_quantity
                total_gross_weight += line.total_weight
                total_cbm += line.volume
                total_value += line.commercial_invoice_value
                total_chargeable_weight += line.total_chargeable_weight
                total_volume_cbm += line.total_volume_cbm
                total_volumetric_weight += line.total_volumetric_weight
                total_pivot_weight += line.pivot_weight
            res.total_pieces = total_pieces
            res.total_gross_weight = total_gross_weight
            res.total_cbm = total_cbm
            res.total_value = total_value
            # res.sum_of_total_chargeable_weight = total_chargeable_weight
            res.sum_total_volume_cbm = total_volume_cbm
            res.sum_total_volumetric_weight = total_volumetric_weight
            res.pivot_weight = total_pivot_weight
            
    def _inverse_pivot_weight(self):
        # This method is required but can be left empty if user input doesn't affect anything else.
        # Just allows field to be editable manually.
        pass
    
    def _inverse_chargeable_weight(self):
        pass
    
    def _inverse_gross_weight(self):
        pass

    @api.model
    def create(self, vals):
        '''Partner Create Function'''
        if vals.get('code', _('New')) == _('New'):
            if vals.get('is_freight_lead'):
                vals['code'] = self.env['ir.sequence'].next_by_code('crm.opportunity.seq')
            else:
                vals['code'] = self.env['ir.sequence'].next_by_code('crm.lead.seq')
        res = super(CrmLead, self).create(vals)
        return res

    @api.onchange('consignee_id')
    def onchange_consignee_id(self):
        if self.consignee_id:
            self.consignee_name = self.consignee_id.name
            self.consignee_street = self.consignee_id.street
            self.consignee_street2 = self.consignee_id.street2
            self.consignee_city_id = self.consignee_id.city_id.id
            self.consignee_state_id = self.consignee_id.state_id.id
            self.consignee_zip = self.consignee_id.zip
            self.consignee_country_id = self.consignee_id.country_id.id
            self.consignee_phone = self.consignee_id.phone
            self.consignee_email = self.consignee_id.email
        else:
            self.consignee_name = ''
            self.consignee_street = ''
            self.consignee_street2 = ''
            self.consignee_city_id = False
            self.consignee_state_id = False
            self.consignee_zip = ''
            self.consignee_country_id = False
            self.consignee_phone = False
            self.consignee_email = False

    @api.onchange('consignor_id')
    def onchange_consignor_id(self):
        if self.consignor_id:
            self.consignor_name = self.consignor_id.name
            self.consignor_street = self.consignor_id.street
            self.consignor_street2 = self.consignor_id.street2
            self.consignor_city_id = self.consignor_id.city_id.id
            self.consignor_state_id = self.consignor_id.state_id.id
            self.consignor_zip = self.consignor_id.zip
            self.consignor_country_id = self.consignor_id.country_id.id
            self.consignor_phone = self.consignor_id.phone
            self.consignor_email = self.consignor_id.email
        else:
            self.consignor_name = ''
            self.consignor_street = ''
            self.consignor_street2 = ''
            self.consignor_city_id = False
            self.consignor_state_id = False
            self.consignor_zip = ''
            self.consignor_country_id = False
            self.consignor_phone = False
            self.consignor_email = False

    def redirect_lead_opportunity_view(self):
        self.ensure_one()
        if self.is_freight_lead:
            view_id = self.env.ref('verts_v15_freight_forward_crm.freight_forward_crm_crm_lead_view_form').id
            return {
                'name': _('Lead or Opportunity'),
                'view_mode': 'form',
                'res_model': 'crm.lead',
                'domain': [('type', '=', self.type)],
                'res_id': self.id,
                # 'view_id': view_id,
                'views': [[view_id, 'form']],
                'type': 'ir.actions.act_window',
                'context': {'default_type': self.type}
            }
        else:
            return {
                'name': _('Lead or Opportunity'),
                'view_mode': 'form',
                'res_model': 'crm.lead',
                'domain': [('type', '=', self.type)],
                'res_id': self.id,
                'view_id': False,
                'type': 'ir.actions.act_window',
                'context': {'default_type': self.type}
            }

    def action_request_price(self):
        channel_id = self.env.ref('verts_v15_freight_forward_crm.channel_ff_price_request_leads_id', raise_if_not_found=False)
        menu = self.env.ref('verts_v15_freight_forward_crm.menu_action_crm_opp_freight_forw_crm', raise_if_not_found=False)
        action = self.env['ir.model.data']._xmlid_to_res_id(
            'verts_v15_freight_forward_crm.freight_forward_crm_crm_lead_all_leads')
        if channel_id and menu and action:
            message = _(
                'Please provide price for the lead: <a href="/web#id=%s&action=%s&model=crm.lead&view_mode=form&menu_id=%s" target="_blank">[%s]%s</a>' % (
                    self.id, action, menu.id, self.code, self.name))
            channel_id.message_post(
                subject='Lead Generated',
                body=message,
                subtype_xmlid='mail.mt_comment')
        self.ensure_one()
        ir_mail_server = self.env['ir.mail_server']
        mail_server_ids = ir_mail_server.search([], order='sequence', limit=1)
        if mail_server_ids and mail_server_ids.smtp_user:
            template = self.env.ref('verts_v15_freight_forward_crm.email_template_for_ff_price_request',
                                    raise_if_not_found=False)
            if template:
                emails = []
                if self.service_type and self.service_type.email_partner_ids:
                    for partner in self.service_type.email_partner_ids:
                        if partner.email:
                            emails.append(partner.email)
                if not emails:
                    raise UserError(_('No recipient email addresses were found on the selected service type.'))
                email_to = str(','.join(emails))
                template.send_mail(
                    self.id,
                    force_send=True,
                    raise_exception=False,
                    email_values={'email_to': email_to})
            else:
                raise UserError(_('The freight price request email template is missing.'))
        else:
            raise UserError(_(
                'Outgoing Mail server not configured.'))
        self.message_post(body="E-mail sent Successfully")
        return ({
            'effect': {
                'fadeout': 'slow',
                'message': "Mail Sent Successfully.",
                'type': 'rainbow_man',
            }
        })

    def action_view_agent_quotes(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Vendor Quotes",
            "res_model": "purchase.order",
            "domain": [('opportunity_id', '=', self.id), ('state', '!=', 'purchase')],
            "context": {"create": False},
            "view_mode": "list,form",
            "views": [
                (self.env.ref('verts_v15_freight_forward.ff_agent_order_tree').id, 'list'),
                (self.env.ref('verts_v15_freight_forward.custom_purchase_order_form').id, 'form'),
            ],
        }

    def action_view_agent_orders(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Vendor Orders",
            "res_model": "purchase.order",
            "domain": [('opportunity_id', '=', self.id), ('state', '=', 'purchase')],
            "context": {"create": False},
            "view_mode": "list,form",
            "views": [
                (self.env.ref('verts_v15_freight_forward.ff_agent_order_tree').id, 'list'),
                (self.env.ref('verts_v15_freight_forward.custom_purchase_order_form').id, 'form'),
            ],
        }

    def action_view_customer_quotes(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Customer Quotes",
            "res_model": "sale.order",
            "domain": [('opportunity_id', '=', self.id), ('state', '!=', 'sale')],
            "context": {"create": False},
            "view_mode": "list,form",
            "views": [
                (self.env.ref('verts_v15_freight_forward.sale_export_order_tree_view_inherit').id, 'list'),
                (self.env.ref('verts_v15_freight_forward.sale_order_export_form_view_inherit').id, 'form'),
            ],
        }

    def action_view_customer_orders(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Customer Orders",
            "res_model": "sale.order",
            "domain": [('opportunity_id', '=', self.id), ('state', '=', 'sale')],
            "context": {"create": False},
            "view_mode": "list,form",
            "views": [
                (self.env.ref('verts_v15_freight_forward.sale_export_order_tree_view_inherit').id, 'list'),
                (self.env.ref('verts_v15_freight_forward.sale_order_export_form_view_inherit').id, 'form'),
            ],
        }

    def action_create_agent_quote(self):
        for res in self:
            agent_partner = self.env['res.partner'].search([('is_agent', '=', True)], limit=1)
            if not agent_partner:
                raise UserError(_(
                    'Please Define Default Agent Partner.'))
            order_id = self.env['purchase.order'].create({
                'opportunity_id': self.id,
                'weight_uom_id': self.weight_uom_id and self.weight_uom_id.id or False,
                'dimension_uom_id': self.dimension_uom_id and self.dimension_uom_id.id or False,
                'partner_id': agent_partner.id,
                'service_type': self.service_type and self.service_type.id or False,
                'customer_id': self.partner_id and self.partner_id.id or False,
                'goods_category_id': self.goods_category_id and self.goods_category_id.id or False,
                'stuffing_point_id': self.stuffing_port_id and self.stuffing_port_id.id or False,
                'port_of_loading_id': self.port_of_loading_id and self.port_of_loading_id.id or False,
                'port_of_discharge_id': self.port_of_discharge_id and self.port_of_discharge_id.id or False,
                'incoterm_id': self.incoterm_id and self.incoterm_id.id or False,
                'account_analytic_id': self.analytic_account_id and self.analytic_account_id.id or False,
                'order_type': self.order_type,
                'mode': self.mode,
                'hs_code': self.hs_code,
                'import_export': self.import_export,
                'is_agent_quote': True,
                'total_pieces': self.total_pieces,
                'total_gross_weight': self.total_gross_weight,
                'total_cbm': self.total_cbm,
                'total_value': self.total_value,
                'total_chargeable_weight': self.sum_of_total_chargeable_weight,
                'total_volume_cbm': self.sum_total_volume_cbm,
                'total_volumetric_weight': self.sum_total_volumetric_weight,
                "pivot_weight": self.pivot_weight,
                # "total_gross_weight": self.total_gross_weight,
                # "sum_total_volumetric_weight": self.sum_total_volumetric_weight,
                # "pivot_weight": self.pivot_weight,
                # "sum_of_total_chargeable_weight": self.sum_of_total_chargeable_weight,
            })
            for line in self.order_line:
                vals = {
                    'product_id': line.product_id.id,
                    "goods_desc": line.goods_desc,
                    "purchase_id": order_id.id,
                    "commodity_type": line.commodity_type and line.commodity_type.id or False,
                    "product_uom_quantity": line.product_uom_quantity,
                    "weight_factor": line.weight_factor,
                    "total_chargeable_weight": line.total_chargeable_weight,
                    "chargeable_weight": line.chargeable_weight,
                    "length_per_package": line.length_per_package,
                    "weight_per_package": line.weight_per_package,
                    "height_per_package": line.height_per_package,
                    "width_per_package": line.width_per_package,
                    "weight_input": line.weight_input,
                    "volume_cbcm": line.volume_cbcm,
                    "volume": line.volume,
                    "total_weight": line.total_weight,
                    "total_volume_cbm": line.total_volume_cbm,
                    "total_volumetric_weight": line.total_volumetric_weight,
                    "packing_type": line.packing_type and line.packing_type.id or False,
                    "commercial_invoice_value": line.commercial_invoice_value,
                    "volumetric_weight": line.volumetric_weight,
                    "loose_bool": line.loose_bool,
                    "pivot_weight": line.pivot_weight,
                    "hs_code": line.hs_code,
                    "type": line.type,
                }
                self.env['freight.purchase.line'].create(vals)
            order_id.total_gross_weight = self.total_gross_weight
            view = self.env.ref('verts_v15_freight_forward.custom_purchase_order_form')
            return {
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'purchase.order',
                'views': [(view.id, 'form')],
                'view_id': view.id,
                'res_id': order_id.id,
                'context': self.env.context,
            }

    def action_create_quotation(self):
        for res in self:
            order_id = self.env['sale.order'].create({
                'opportunity_id': self.id,
                'partner_id': self.partner_id and self.partner_id.id or False,
                'team_id': self.team_id.id,
                'campaign_id': self.campaign_id.id,
                'medium_id': self.medium_id.id,
                'origin': self.name,
                'source_id': self.source_id.id,
                'company_id': self.company_id.id or self.env.company.id,
                'tag_ids': [(6, 0, self.tag_ids.ids)],
                'consignor_id': self.consignor_id and self.consignor_id.id or False,
                'consignee_id': self.consignee_id and self.consignee_id.id or False,
                'notify_id': self.notify_id and self.notify_id.id or False,
                'validity_date': self.validity_date,
                'cha_id': self.cha_id and self.cha_id.id or False,
                'reference_by_id': self.reference_by_id and self.reference_by_id.id or False,
                'cur_rate': self.cur_rate,
                'stuffing_point_id': self.stuffing_port_id and self.stuffing_port_id.id or False,
                'port_of_loading_id': self.port_of_loading_id and self.port_of_loading_id.id or False,
                'port_of_discharge_id': self.port_of_discharge_id and self.port_of_discharge_id.id or False,
                'incoterm_id': self.incoterm_id and self.incoterm_id.id or False,
                'analytic_account_id': self.analytic_account_id and self.analytic_account_id.id or False,
                'order_type': self.order_type,
                'mode': self.mode,
                'hs_code': self.hs_code,
                'commodity': self.goods_category_id and self.goods_category_id.id or False,
                'import_export': self.import_export,
                'export': True,
                'total_pieces': self.total_pieces,
                'total_gross_weight': self.total_gross_weight,
                'total_cbm': self.total_cbm,
                'total_value': self.total_value,
                'total_chargeable_weight': self.sum_of_total_chargeable_weight,
                'total_volume_cbm': self.sum_total_volume_cbm,
                'total_volumetric_weight': self.sum_total_volumetric_weight,
                "pivot_weight": self.pivot_weight,
                'gsa_sales': res.gsa_sales,
                # "total_gross_weight": self.total_gross_weight,
                # "sum_total_volumetric_weight": self.sum_total_volumetric_weight,
                # "pivot_weight": self.pivot_weight,
                # "sum_of_total_chargeable_weight": self.sum_of_total_chargeable_weight,
            })
            if order_id:
                # for each in res.order_line:
                #     order_line_id = self.env['sale.order.line'].create({
                #         'product_id': each.product_id and each.product_id.id or False,
                #         'order_id': order_id and order_id.id or False,
                #         'name': each.product_id.name,
                #         'product_uom_qty': each.product_uom_quantity,
                #         'product_uom': each.product_uom and each.product_uom.id or False,
                #         'packing_type': each.packing_type and each.packing_type.id or False,
                #     })
                #     order_line_id.product_id_change()
                for line in self.order_line:
                    vals = {
                        'product_id': line.product_id.id,
                        "goods_desc": line.goods_desc,
                        "sale_id": order_id.id,
                        "commodity_type": line.commodity_type and line.commodity_type.id or False,
                        "product_uom_quantity": line.product_uom_quantity,
                        "weight_factor": line.weight_factor,
                        "volumetric_weight": line.volumetric_weight,
                        "total_chargeable_weight": line.total_chargeable_weight,
                        "chargeable_weight": line.chargeable_weight,
                        "length_per_package": line.length_per_package,
                        "weight_per_package": line.weight_per_package,
                        "height_per_package": line.height_per_package,
                        "width_per_package": line.width_per_package,
                        "weight_input": line.weight_input,
                        "volume_cbcm": line.volume_cbcm,
                        "volume": line.volume,
                        "total_weight": line.total_weight,
                        "total_volume_cbm": line.total_volume_cbm,
                        "total_volumetric_weight": line.total_volumetric_weight,
                        "packing_type": line.packing_type and line.packing_type.id or False,
                        "commercial_invoice_value": line.commercial_invoice_value,
                        "loose_bool": line.loose_bool,
                        "pivot_weight": line.pivot_weight,
                        "hs_code": line.hs_code,
                        "type": line.type,
                    }
                    self.env['sale.freight.line'].create(vals)
                order_id.total_gross_weight = self.total_gross_weight
                view = self.env.ref('verts_v15_freight_forward.sale_order_export_form_view_inherit')
                return {
                    'type': 'ir.actions.act_window',
                    'view_mode': 'form',
                    'res_model': 'sale.order',
                    'views': [(view.id, 'form')],
                    'view_id': view.id,
                    'res_id': order_id.id,
                    'context': self.env.context,
                }

    def update_lead_line_Calculation(self):
        for res in self:
            for line in res.order_line:
                line.onchange_get_weight_factor()
                line.onchange_get_uoms()
                line.onchange_weight_input()

                # _compute_total_weight
        # _compute_volume_cbcm
        # _compute_volume_cbm
        # _compute_total_chargeable_weight
        # _compute_volumetric_weight
        # _compute_chargeable_weight
        # _compute_total_volume_cbm
        # _compute_total_volumetric_weight


class FreightCrmleadline(models.Model):
    _name = "lead.order.line"
    _description = "Lead Order Line"

    def _get_default_dimension_uom_id(self):
        return self.env.ref('uom.product_uom_cm')

    def _get_default_weight_uom_id(self):
        return self.env.ref('uom.product_uom_kgm')

    lead_id = fields.Many2one('crm.lead', string="Lead Id")
    product_id = fields.Many2one('product.product', string="Product")
    container_type_id = fields.Many2one('container.type', string="Container Type")
    capacity_in_mt = fields.Float(string="Capacity (MT)")
    no_of_container = fields.Float(string="No. of Container")
    container_qty = fields.Integer(string="Container Qty.")
    commercial_invoice_value = fields.Float(string="Commercial Invoice Value")
    goods_desc = fields.Text(string='Goods Description')
    packing_type = fields.Many2one('export.packing.type', string="Packing Type")
    commodity_type = fields.Many2one('export.product.category', string="Commodity Type")
    hs_code = fields.Char('HS code')

    service_type = fields.Many2one('service.type', string="Service Type")
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
    consignor_phone = fields.Char(string='Phone Number')
    consignor_email = fields.Char(string='Email Id')
    consignor_point_contact = fields.Char(string='Point of Contact')
    pivot_weight = fields.Float(string='Pivot Weight')



    @api.onchange('product_id', 'lead_id.consignor_id', 'lead_id.consignor_name', 'lead_id.consignor_street',
                  'lead_id.consignor_street2', 'lead_id.consignor_city_id', 'lead_id.consignor_state_id',
                  'lead_id.consignor_country_id')
    def onchange_get_shipper_details(self):
        if self.lead_id.consignor_id:
            self.consignor_id = self.lead_id.consignor_id.id
        if self.lead_id.consignor_name:
            self.consignor_name = self.lead_id.consignor_name
        if self.lead_id.consignor_street:
            self.consignor_street = self.lead_id.consignor_street
        if self.lead_id.consignor_street2:
            self.consignor_street2 = self.lead_id.consignor_street2
        if self.lead_id.consignor_city_id:
            self.consignor_city_id = self.lead_id.consignor_city_id.id
        if self.lead_id.consignor_state_id:
            self.consignor_state_id = self.lead_id.consignor_state_id.id
        if self.lead_id.consignor_country_id:
            self.consignor_country_id = self.lead_id.consignor_country_id.id



    def abc(self):
        if self.lead_id.service_type:
            self.weight_factor = self.lead_id.service_type.weight_factor
            self.full_container_service = self.lead_id.service_type.full_container_service

    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.product_id:
            self.product_uom = self.product_id.uom_id.id

    @api.onchange('product_id', 'lead_id.service_type')
    def onchange_get_weight_factor(self):
        if self.lead_id and self.lead_id.service_type:
            self.service_type = self.lead_id.service_type and self.lead_id.service_type.id or False
            self.weight_factor = self.lead_id.service_type.weight_factor
            self.full_container_service = self.lead_id.service_type.full_container_service

    @api.onchange('service_type')
    def onchange_service_type(self):
        if self.service_type:
            self.weight_factor = self.service_type.weight_factor

    @api.onchange('product_id', 'lead_id.weight_uom_id', 'lead_id.dimension_uom_id')
    def onchange_get_uoms(self):
        if self.lead_id.weight_uom_id:
            self.weight_uom_id = self.lead_id.weight_uom_id.id
        if self.lead_id.dimension_uom_id:
            self.dimension_uom_id = self.lead_id.dimension_uom_id.id

    @api.depends('weight_per_package', 'product_uom_quantity')
    def _compute_total_weight(self):
        for res in self:
            res.total_weight = res.weight_per_package * res.product_uom_quantity

    @api.onchange('commodity_type')
    def _onchange_commodity_type(self):
        if self.commodity_type:
            self.hs_code = self.commodity_type.hs_code
        else:
            self.hs_code = False

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
                if res.lead_id.service_type.weight_factor_type == 'on_cbcm':
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


class Leadcontainerlines(models.Model):
    _name = "lead.container.lines"
    _description = "Lead Container Line"

    lead_id = fields.Many2one('crm.lead', string="Lead ID")
    container_type_id = fields.Many2one('container.type', string="Container Type")
    capacity_in_mt = fields.Float(string="Capacity (MT)")
    container_qty = fields.Char(string="No. of Containers")

    @api.onchange('container_type_id')
    def onchange_container_type_id(self):
        if self.container_type_id:
            self.capacity_in_mt = self.container_type_id.capacity
