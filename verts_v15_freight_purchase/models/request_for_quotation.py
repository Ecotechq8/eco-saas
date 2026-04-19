# -*- coding: utf-8 -*-
# Copyright 2020 Verts Services India Pvt. Ltd.
# http://www.verts.co.in

from datetime import datetime, time

from odoo import api, fields, models, _
from odoo.exceptions import UserError

# dic_state = [ ('draft', 'Draft PO'),
#           ('sent', 'RFQ Sent'),
#           ('pending_approval', 'Pending Level1'),
#           ('to approve', 'Pending Level2'),
#           ('second_level_approved', 'Pending Level3'),
#           ('third_level_approved', 'Pending Level4'),
#           ('fourth_level_approved', 'Pending Level5'),
#           ('purchase', 'Order Approved'),
#           ('fully_adv_done', 'Fully Advance Done'),
#           ('partial_adv_done', 'Partial Advance Done'),
#           ('po_amended', 'PO Amended'),
#           ('done', 'Done'),
#           ('close', 'Closed'),
#           ('cancel', 'Cancelled')]
# dic_state = dict(dic_state)
# config_object = 'purchase.config'

PURCHASE_REQUISITION_STATES = [
    ('draft', 'Draft'),
    ('ongoing', 'Ongoing'),
    ('in_progress', 'Confirmed'),
    ('open', 'Bid Selection'),
    ('done', 'Closed'),
    ('cancel', 'Cancelled')
]


# Please do not use this file in future. It's use only for RFQ
# class PurchaseRequisition(models.Model):
#     _inherit = "purchase.requisition"
#
#     req_quot_id = fields.Many2one('request.for.quotation', string='RFQ', copy=False)
#
#     def create_rfq_through_pr(self):
#         rfq_pool = self.env['request.for.quotation']
#         rfq_line_pool = self.env['request.for.quotation.line']
#         view = self.env.ref('verts_v15_freight_purchase.view_new_rfq_request_for_quotation_form')
#         rfq_id = rfq_pool.create({'user_id': self.user_id.id, 'internal_product_type': self.internal_product_type, 'used_for_readonly': True})
#         for val in self:
#             if val.state != 'approved':
#                 raise UserError(_("Please approved PR first [%s].") % val.name)
#             if val.partner_id:
#                 rfq_id.write({'partner_ids': [(6, 0, [val.partner_id.id])]})
#             val.req_quot_id = rfq_id.id
#             self._cr.execute(""" INSERT INTO purchase_requisition_rfq_rel (req_quot_id, requisition_id)
#                         VALUES (%s, %s) """, (rfq_id.id, val.id))
#             for line in val.line_ids:
#                 rfq_line_id = rfq_line_pool.create({'purchase_requisition_line_id': line.id, 'req_quot_id': rfq_id.id,
#                                                     'product_id': line.product_id.id, 'product_qty': line.product_qty,
#                                                     'product_uom_id': line.product_uom_id.id})
#
#         return {
#             'name': _('RFQ'),
#             'type': 'ir.actions.act_window',
#             'view_type': 'form',
#             'view_mode': 'form',
#             'res_model': 'request.for.quotation',
#             'views': [[view.id, 'form']],
#             'view_id': view.id,
#             'res_id': rfq_id.id,
#             'context': {},
#         }
#

# Please do not use this file in future. It's use only for RFQ
class RequestForQuotation(models.Model):
    _name = "request.for.quotation"
    _description = "Request For Quotation"
    _inherit = ['mail.thread']
    _order = "id desc"

    def _get_picking_in(self):
        pick_in = self.env.ref('stock.picking_type_in', raise_if_not_found=False)
        company = self.env['res.company']._company_default_get('request.for.quotation')
        if not pick_in or pick_in.sudo().warehouse_id.company_id.id != company.id:
            pick_in = self.env['stock.picking.type'].search(
                [('warehouse_id.company_id', '=', company.id), ('code', '=', 'incoming')],
                limit=1,
            )
        return pick_in

    def _get_warehouse_id(self):
        warehouse_ids = self.env['stock.warehouse'].search([])
        for rec in warehouse_ids:
            if rec.name == 'Noida':
                return rec.id

    name = fields.Char(string='Agreement Reference', required=True, copy=False, default='New', readonly=True)
    origin = fields.Char(string='Source Document Origin')
    order_count = fields.Integer(compute='_compute_orders_number', string='Number of Orders')
    vendor_id = fields.Many2one('res.partner', string="Vendor")
    partner_ids = fields.Many2many('res.partner', 'rfq_partner_rel', 'rfq_id', 'partner_id',
                                   'Vendor(s)')
    #     type_id = fields.Many2one('request.for.quotation.type', string="Agreement Type", required=True, default=_get_type_id)
    ordering_date = fields.Date(string="Ordering Date", tracking=True)
    date_end = fields.Datetime(string='Agreement Deadline', tracking=True)
    schedule_date = fields.Date(string='Delivery Date', index=True,
                                help="The expected and scheduled delivery date where all the products are received",
                                tracking=True)
    user_id = fields.Many2one('res.users', string='Purchase Representative', default=lambda self: self.env.user)
    description = fields.Text()
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env['res.company']._company_default_get(
                                     'request.for.quotation'))
    purchase_ids = fields.One2many('purchase.order', 'req_quot_id', string='Purchase Orders')
    line_ids = fields.One2many('request.for.quotation.line', 'req_quot_id', string='Products to Purchase',
                               copy=True)
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse', default=_get_warehouse_id)
    state = fields.Selection(PURCHASE_REQUISITION_STATES,
                             'Status', tracking=True, required=True,
                             copy=False, default='draft')
    state_blanket_order = fields.Selection(PURCHASE_REQUISITION_STATES, compute='_set_state')
    picking_type_id = fields.Many2one('stock.picking.type', 'Operation Type', required=True, default=_get_picking_in)
    #     is_quantity_copy = fields.Selection(related='type_id.quantity_copy', readonly=True)
    currency_id = fields.Many2one('res.currency', 'Currency', required=True,
                                  default=lambda self: self.env.user.company_id.currency_id.id)
    internal_product_type = fields.Selection([('fg', 'FG'), ('rm', 'RM'), ('consu', 'Consumables'),
                                              ('service', 'Service'), ('semi_fg_wip', 'Semi FG/WIP'),
                                              ('gi', 'General Items'), ('fa', 'Fixed Assets'), ('mix', 'Mix')],
                                             'Internal Product Type')
    remarks = fields.Char('Remark')
    advance_type = fields.Selection([('percentage', 'Percentage'), ('fix_amount', 'Fix Amount ')],
                                    string='Advance Type', default='fix_amount')
    advance_value = fields.Char(string='Advance Value')
    advance_remark = fields.Char(string='Advance Remark')
    used_for_readonly = fields.Boolean(string='Used for readonly')

    @api.depends('state')
    def _set_state(self):
        self.state_blanket_order = self.state

    @api.depends('purchase_ids')
    def _compute_orders_number(self):
        for req_quot_id in self:
            req_quot_id.order_count = len(req_quot_id.purchase_ids)

    def action_in_progress(self):
        self.ensure_one()
        if not all(obj.line_ids for obj in self):
            raise UserError(_("You cannot confirm agreement '%s' because there is no product line.") % self.name)

        self.write({'state': 'in_progress'})
        # Set the sequence number regarding the requisition type
        if self.name == 'New':
            #             if self.is_quantity_copy != 'none':
            self.name = self.env['ir.sequence'].next_by_code('request.for.quotation.tender')

    #             else:
    #                 self.name = self.env['ir.sequence'].next_by_code('purchase.requisition.blanket.order')

    def action_open(self):
        self.write({'state': 'open'})

    def action_cancel(self):
        # try to set all associated quotations to cancel state
        for requisition in self:
            #             for requisition_line in requisition.line_ids:
            #                 requisition_line.supplier_info_ids.unlink()
            requisition.purchase_ids.button_cancel()
            for po in requisition.purchase_ids:
                po.message_post(body=_('Cancelled by the agreement associated to this quotation.'))
        self.write({'state': 'cancel'})

    def action_draft(self):
        self.ensure_one()
        self.name = 'New'
        self.write({'state': 'draft'})

    def action_done(self):
        """
        Generate all purchase order based on selected lines, should only be called on one agreement at a time
        """
        if any(purchase_order.state in ['draft', 'sent', 'to approve'] for purchase_order in
               self.mapped('purchase_ids')):
            raise UserError(_('You have to cancel or validate every RfQ before closing the purchase requisition.'))
        #         for requisition in self:
        #             for requisition_line in requisition.line_ids:
        #                 requisition_line.supplier_info_ids.unlink()
        self.write({'state': 'done'})

    def action_compare_quotation(self):
        lst = []
        self.ensure_one()
        po_config = self.env.user.company_id.po_config
        context = dict(self._context or {})
        ir_mail_server = self.env['ir.mail_server']
        mail_server_ids = ir_mail_server.search([], order='sequence', limit=1)
        start_date = datetime.now()
        # self.count_no_of_days(start_date, False)
        ir_model_data = self.env['ir.model.data']
        ir_model_fields_obj = self.env['ir.model.fields']
        ir_model_fields_id = ir_model_fields_obj.search([('name', '=', 'reporting_manager_id')])

        for indent in self:
            print('for')
            new_date = []
            aprrovers = []
            # if not indent.order_line:
            #     raise UserError(_('You cannot raise request without a line'))
            # if po_config and int(po_config.po_validation) > 0 and indent.amount_total >= po_config.po_double_validation_amt:
            if po_config and int(po_config.po_validation) > 0:
                ########Next Approver###
                # print("if")
                approval_line_ids = self.env['users.approval.qc'].search(
                    [('qc_id', '=', po_config.id), ('sequence', '=', '1st_lavels')], limit=1)
                print('approval_line_ids', approval_line_ids)
                for line in approval_line_ids:
                    print('line', line.user_id.id)
                    aprrovers.append(line.user_id.id)
                    # week_after = datetime.strptime(str(DT.date.today()), "%Y-%m-%d") + DT.timedelta(days=line.sla_days)
                    # new_date.append(datetime.strftime(week_after, "%Y-%m-%d"))
                    # week_after = datetime.strptime(str(DT.date.today()), "%Y-%m-%d") + DT.timedelta(days=line.sla_days)
                    # new_date.append(datetime.strftime(week_after, "%Y-%m-%d"))
                # print('new_date',new_date)
                # print("+++++++++++++++", new_date[0])
                ##########
                # self.env['purchase.order.history'].create({
                #                                                'purchase_id':indent.id,
                #                                                'user':self._uid,
                #                                                'desc':"Send for Approval",
                #                                                'po_name':indent.name,
                #                                                'logging_date':datetime.now(),
                #                                                # 'status':dic_state[indent.state],
                #                                                'mark_green':True,
                #                                                ###Next Approver###
                #                                                 'next_approver': [(6, 0, aprrovers)],
                #                                                 # 'next_approval_deadline':  new_date[0] if new_date else False
                #                                                       })
                # self.write({'state':'pending_approval'})

        quote_ids = self.env['quote.comparision'].search([('rfq_no', '=', self.id)], limit=1)
        if quote_ids:
            view_id = self.env.ref('verts_v15_freight_purchase.view_quote_comparision_form')
            # print("if =======", view_id)
            return {
                'name': _('Quote Comparision'),
                'view_mode': 'form',
                'res_model': 'quote.comparision',
                'view_id': view_id.id if view_id else False,
                'res_id': quote_ids.id if quote_ids else False,
                'type': 'ir.actions.act_window',
            }
        else:
            quote_obj = self.env['quote.comparision']
            quote_line_obj = self.env['quote.comparision.line']
            quote_id = quote_obj.create({'rfq_no': self.id, 'internal_product_type': self.internal_product_type,
                                         'advance_type': self.advance_type,
                                         'advance_value': self.advance_value or False,
                                         'advance_remark': self.advance_remark or False})
            if quote_id:
                po_line_ids = self.purchase_ids.mapped('order_line')
                for val in po_line_ids:
                    quote_line_obj.create(
                        {
                            'rfq_id': quote_id.id,
                            'order_id': val.order_id and val.order_id.id or False,
                            'partner_id': val.partner_id and val.partner_id.id or False,
                            'product_id': val.product_id and val.product_id.id or False,
                            'price_unit': val.price_unit or 0.0,
                            'rfq_qty': val.product_qty or 0.0,
                            'pending_rfq_qty': val.product_qty or 0.0,
                            'uom_id': val.product_uom and val.product_uom.id or False,
                            # 'full_qty': 0.0,
                            'date_planned': val.date_planned,
                        }
                    )
                view_id = self.env.ref('verts_v15_freight_purchase.view_quote_comparision_form')
                return {
                    'name': _('Quote Comparision'),
                    'view_mode': 'form',
                    'res_model': 'quote.comparision',
                    'view_id': view_id.id if view_id else False,
                    'res_id': quote_id.id if quote_id else False,
                    'type': 'ir.actions.act_window',
                }

    # def action_compare_quotation2(self):
    #     # pol_pool = self.env['purchase.order.line']
    #     po_line_ids = self.purchase_ids.mapped('order_line')
    #     # action = self.env.ref('verts_v15_freight_purchase.purchase_line_form_action').read()[0]
    #     # action['domain'] = [('id', 'in', po_line_ids.ids),('type_of_po','=','VQ')]
    #     # action['context'] = {'group_by' : 'product_id'}
    #     # return action
    #     view_id = self.env.ref('verts_v15_freight_purchase.purchase_order_line_tree_inherit')
    #     return {
    #         'name': _('Purchase Order Line'),
    #         'view_mode': 'tree',
    #         'res_model': 'purchase.order.line',
    #         'domain': [('id', 'in', po_line_ids.ids), ('type_of_po', '=', 'VQ')],
    #         'view_id': view_id.id if view_id else False,
    #         'type': 'ir.actions.act_window',
    #         'context': {'group_by': 'product_id'}
    #     }

    def _get_po_report_base_filename(self):
        # ----------------INFO------------------------#
        """This Method is used for generating Custom file name for Qweb PO Reports.
        """
        # ----------------INFO------------------------#
        self.ensure_one()
        return _('%s') % (self.name)

    def action_rfq_send(self):
        '''
        This function opens a window to compose an email, with the edi quotation template message loaded by default
        '''
        self.ensure_one()
        quotation_template_id = self.env.ref('verts_v15_freight_purchase.email_template_edi_request_quotation').id
        compose_form_id = self.env.ref('mail.email_compose_message_wizard_form').id
        ctx = dict(
            default_composition_mode='comment',
            default_res_id=self.id,
            default_model='request.for.quotation',
            default_partner_ids=self.partner_ids.ids,
            default_use_template=bool(quotation_template_id),
            default_template_id=quotation_template_id,
            custom_layout='mail.mail_notification_light'
        )
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }

    # comment by akash the function give error
    # @api.onchange('requsition_ids')
    # def _onchange_requsition_ids(self):
    #     product_dict = {}
    #     req_line_id = {}
    #     new_lines = self.env['request.for.quotation.line']
    #     product_pool = self.env['product.product']
    #     self.update({'line_ids': ''})
    #     for req_id in self.requsition_ids:
    #         for line in req_id.line_ids:
    #             if line.product_id.id in product_dict:
    #                     product_dict[line.product_id.id] += line.product_qty
    #             else:
    #                 product_dict[line.product_id.id] = line.product_qty
    #     for key,value in product_dict.items():
    #         if key:
    #             product_id = product_pool.browse(key)
    #         req_line_id = {'req_quot_id':self._origin.id,'product_id':key,'product_qty':value,'product_uom_id':product_id.uom_po_id.id}
    #         new_line = new_lines.new(req_line_id)
    #         new_lines += new_line
    #     if new_lines:
    #         self.update({'line_ids': new_lines})

    def rais_new_quote(self):
        if self.partner_ids:
            if len(self.partner_ids.ids) == 1:
                # for partner in self.partner_ids:
                #     po_id= self.action_new_quote(partners=partner)
                return {
                    'name': _('Purchase Order'),
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'purchase.order',
                    'context': {'default_req_quot_id': self.id, 'default_partner_id': self.partner_ids.id},
                    'domain': [('req_quot_id', '=', self.id)],
                }
            else:
                return {
                    'name': _('Create Po Wizard'),
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'create.po.wiz',
                    'context': {'default_req_quot_id': self.id},
                    'target': 'new', }
        else:
            return {
                'name': _('Purchase Order'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'purchase.order',
                'context': {"default_req_quot_id": self.id},
                'domain': [('req_quot_id', '=', self.id)],
            }

    def action_new_quote(self, partners=False):
        FiscalPosition = self.env['account.fiscal.position']
        if partners:
            for partner in partners:
                product_list = []
                fpos = FiscalPosition.get_fiscal_position(partner.id)
                fpos = FiscalPosition.browse(fpos)
                payment_term = partner.property_supplier_payment_term_id
                for line in self.line_ids:
                    product_lang = line.product_id.with_context({
                        'lang': partner.lang,
                        'partner_id': partner.id,
                    })
                    name = product_lang.display_name
                    if product_lang.description_purchase:
                        name += '\n' + product_lang.description_purchase

                    # Compute taxes
                    if fpos:
                        taxes_ids = fpos.map_tax(line.product_id.supplier_taxes_id.filtered(
                            lambda tax: tax.company_id == self.company_id)).ids
                    else:
                        taxes_ids = line.product_id.supplier_taxes_id.filtered(
                            lambda tax: tax.company_id == self.company_id).ids

                    # Compute quantity and price_unit
                    if line.product_uom_id != line.product_id.uom_po_id:
                        product_qty = line.product_uom_id._compute_quantity(line.product_qty, line.product_id.uom_po_id)
                        #                 price_unit = line.product_uom_id._compute_price(line.price_unit, line.product_id.uom_po_id)
                        price_unit = line.price_unit
                    else:
                        product_qty = line.product_qty
                        price_unit = line.price_unit

                    #             if requisition.type_id.quantity_copy != 'copy':
                    #                 product_qty = 0

                    # Create PO line
                    order_line_values = line._prepare_purchase_order_line(
                        name=name, product_qty=product_qty, price_unit=price_unit,
                        taxes_ids=taxes_ids)
                    product_list.append((0, 0, order_line_values))

                po_id = self.env['purchase.order'].create(
                    {
                        'partner_id': partner.id,
                        'warehouse_id': self.warehouse_id.id,
                        'req_quot_id': self.id,
                        'internal_product_type': self.internal_product_type,
                        'payment_term_id': payment_term.id,
                        'fiscal_position_id': fpos.id,
                        'company_id': self.company_id.id,
                        'currency_id': self.currency_id.id,
                        'type_of_po': 'VQ',
                        'origin': self.name,
                        'origin_type': 'rfq',
                        'notes': self.description,
                        'date_order': fields.Datetime.now(),
                        'picking_type_id': self.picking_type_id.id,
                        'order_line': product_list,
                        'readonly_qty': True,

                    }
                )
                # po_id.onchange_warehouse_id()
                po_id.onchange_add_partner_id()
                po_id.onchange_dest_address_id()
                po_id.onchange_bill_to_id()
        return po_id


# class SupplierInfo(models.Model):
#     _inherit = "product.supplierinfo"
#     _order = 'sequence, purchase_requisition_id desc, min_qty desc, price'
#
#     purchase_requisition_id = fields.Many2one('purchase.requisition', related='purchase_requisition_line_id.requisition_id', string='Blanket order', readonly=False)
#     purchase_requisition_line_id = fields.Many2one('purchase.requisition.line')


class RequestForQuotationLine(models.Model):
    _name = "request.for.quotation.line"
    _description = "Request For Quotation Line"
    _rec_name = 'product_id'

    product_id = fields.Many2one('product.product', string='Product', domain=[('purchase_ok', '=', True)],
                                 required=True)
    product_uom_id = fields.Many2one('uom.uom', string='Product Unit of Measure')
    product_qty = fields.Float(string='Quantity', digits='Product Unit of Measure')
    price_unit = fields.Float(string='Unit Price', digits='Product Price',
                              related='product_id.standard_price')
    #     qty_ordered = fields.Float(compute='_compute_ordered_qty', string='Ordered Quantities')
    req_quot_id = fields.Many2one('request.for.quotation', string='Purchase Agreement')
    # purchase_requisition_line_id = fields.Many2one('purchase.requisition.line', string='Purchase Agreement Line')
    company_id = fields.Many2one('res.company', related='req_quot_id.company_id', string='Company', store=True,
                                 readonly=True, default=lambda self: self.env['res.company']._company_default_get(
            'request.for.quotation.line'))
    account_analytic_id = fields.Many2one('account.analytic.account', string='Analytic Account')
    analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Analytic Tags')
    schedule_date = fields.Date(string='Scheduled Date')
    move_dest_id = fields.Many2one('stock.move', 'Downstream Move')
    name = fields.Char('Name')
    display_type = fields.Selection([
        ('line_section', "Section"),
        ('line_note', "Note")], default=False, help="Technical field for UX purpose.")

    #     supplier_info_ids = fields.One2many('product.supplierinfo', 'purchase_requisition_line_id')

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.product_uom_id = self.product_id.uom_po_id.id

    def _prepare_purchase_order_line(self, name, product_qty=0.0, price_unit=0.0, taxes_ids=False):
        self.ensure_one()
        req_quot_id = self.req_quot_id
        if req_quot_id.schedule_date:
            date_planned = datetime.combine(req_quot_id.schedule_date, time.min)
        else:
            date_planned = datetime.now()
        return {
            'name': name,
            'product_id': self.product_id.id,
            'product_uom': self.product_id.uom_po_id.id,
            'product_qty': product_qty,
            'price_unit': price_unit,
            'taxes_id': [(6, 0, taxes_ids)],
            'date_planned': date_planned,
            'account_analytic_id': self.account_analytic_id.id,
            'analytic_tag_ids': self.analytic_tag_ids.ids,
            'move_dest_ids': self.move_dest_id and [(4, self.move_dest_id.id)] or [],
            'req_quot_line_id': self.id
        }
