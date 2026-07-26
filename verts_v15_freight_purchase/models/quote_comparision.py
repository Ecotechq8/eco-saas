from odoo import api, fields, models, _
from odoo.exceptions import UserError
from itertools import groupby
from collections import defaultdict


class QuoteComparision(models.Model):
    _name = 'quote.comparision'
    _inherit = "mail.thread"
    _description = 'Quote Comparision'
    _order = 'id desc'

    name = fields.Char('Compression No', reqired=True, copy=False, readonly=True, index=True,
                       default=lambda self: _('New'))
    rfq_no = fields.Many2one('request.for.quotation', string='RFQ No')
    rfq_no_line = fields.One2many('quote.comparision.line', 'rfq_id', 'RFQ No')
    remarks = fields.Text("Remarks")
    state = fields.Selection(string="Status", selection=[
        ('draft', 'Draft'), ('pending_approval', 'Pending Approval1'),
        ('to_approve', 'Pending Level2'),
        ('second_level_approved', 'Pending Level3'),
        ('third_level_approved', 'Pending Level4'),
        ('fourth_level_approved', 'Pending Level5'),
        ('approved', 'Approved')], default='draft')

    internal_product_type = fields.Selection([('fg', 'FG'), ('rm', 'RM'), ('consu', 'Consumables'),
                                              ('service', 'Service'), ('semi_fg_wip', 'Semi FG/WIP'),
                                              ('gi', 'General Items'), ('fa', 'Fixed Assets'), ('mix', 'Mix')],
                                             'Internal Product Type')
    is_show_create_po = fields.Boolean(string="Is Show Create PO", default=False)
    po_order_count = fields.Integer(string='Po Order', compute='_compute_picking_ids')
    advance_type = fields.Selection([('percentage', 'Percentage'), ('fix_amount', 'Fix Amount ')],
                                    string='Advance Type')
    advance_value = fields.Char(string='Advance Value')
    advance_remark = fields.Char(string='Advance Remark')


    def confirm_purchase_ids(self):
        action = self.env.ref('purchase.purchase_form_action').read()[0]
        pickings = self.env['purchase.order'].search([('quote_comp_id', '=', self.id)])
        if len(pickings) > 1:
            action['domain'] = "[('id','in',%s)]" % (pickings.ids)
        elif pickings:
            action['views'] = [
                (self.env.ref('purchase.purchase_order_form').id, 'form')]
            action['res_id'] = pickings.id
        return action

    def button_1st_approval(self):
        lst = []
        context = dict(self._context or {})
        ir_mail_server = self.env['ir.mail_server']
        mail_server_ids = ir_mail_server.search([], order='sequence', limit=1)
        po_config = self.env.user.company_id.po_config
        aproval_line_ids = self.env['users.approval.qc'].search(
            [('qc_id', '=', po_config.id), ('sequence', '=', '1st_lavels')], limit=1)
        if aproval_line_ids:
            if not self._uid == aproval_line_ids.user_id.id:
                raise UserError(_('You are not Authorized Person to Approve'))
        if po_config.quote_validation and int(po_config.quote_validation) > 1:
            self.write({'state': 'to_approve'})
            if mail_server_ids and po_config:
                text2 = "<html><body><p>Hello, </p><p></p><p>You have sent <b>%s</b> for the approval to the next approving authority.<b></b></p><p>Thank You</p><p>Odoo Team</p></body></html>" % (
                    self.name)
                mail = mail_server_ids
                if mail.smtp_user:
                    approval_line_ids = self.env['users.approval.qc'].search(
                        [('qc_id', '=', po_config.id), ('sequence', '=', '2st_lavels')])
                    for approval_line in approval_line_ids:
                        lst.append(approval_line.user_id.partner_id.id)
                        template_id = approval_line.qc_mail_template
                        # if template_id and approval_line.user_id and not context.get('roger'):
                        #     print('reeeee')
                        #     template_id.send_mail(self.id, force_send=True,
                        #                           email_values={'email_to': approval_line.user_id.partner_id.email,
                        #                                         'email_from': mail.smtp_user or ''})
                        if approval_line.user_id.partner_id.email:
                            vals2 = {
                                'email_from': mail.smtp_user,
                                'email_to': approval_line.user_id.partner_id.email,
                                'subject': _('Service Order Approval'),
                                'body': text2,
                                'body_html': text2,
                                'parent_id': None,
                                'auto_delete': True,
                            }
                            mail2 = self.env['mail.mail'].create(vals2)
                            if not context.get('roger'):
                                mail2.send()
        else:
            self.write({'state': 'approved'})


    def button_2nd_approval(self):
        lst = []
        context = dict(self._context or {})
        ir_mail_server = self.env['ir.mail_server']
        mail_server_ids = ir_mail_server.search([], order='sequence', limit=1)
        po_config = self.env.user.company_id.po_config
        aproval_line_ids = self.env['users.approval.qc'].search(
            [('qc_id', '=', po_config.id), ('sequence', '=', '2st_lavels')], limit=1)
        if aproval_line_ids:
            if not self._uid == aproval_line_ids.user_id.id:
                raise UserError(_('You are not Authorized Person to Approve'))
        if po_config.quote_validation and int(po_config.quote_validation) > 2:
            self.write({'state': 'second_level_approved'})
            if mail_server_ids and po_config:
                text2 = "<html><body><p>Hello, </p><p></p><p>You have sent <b>%s</b> for the approval to the next approving authority.<b></b></p><p>Thank You</p><p>Odoo Team</p></body></html>" % (
                    self.name)
                mail = mail_server_ids
                if mail.smtp_user:
                    approval_line_ids = self.env['users.approval.qc'].search(
                        [('qc_id', '=', po_config.id), ('sequence', '=', '3st_lavels')])
                    for approval_line in approval_line_ids:
                        lst.append(approval_line.user_id.partner_id.id)
                        template_id = approval_line.qc_mail_template
                        # if template_id and approval_line.user_id and not context.get('roger'):
                        #     print('reeeee')
                        #     template_id.send_mail(self.id, force_send=True,
                        #                           email_values={'email_to': approval_line.user_id.partner_id.email,
                        #                                         'email_from': mail.smtp_user or ''})
                        if approval_line.user_id.partner_id.email:
                            vals2 = {
                                'email_from': mail.smtp_user,
                                'email_to': approval_line.user_id.partner_id.email,
                                'subject': _('Service Order Approval'),
                                'body': text2,
                                'body_html': text2,
                                'parent_id': None,
                                'auto_delete': True,
                            }
                            mail2 = self.env['mail.mail'].create(vals2)
                            if not context.get('roger'):
                                mail2.send()
        else:
            self.write({'state': 'approved'})

    def button_3rd_approval(self):
        lst = []
        context = dict(self._context or {})
        ir_mail_server = self.env['ir.mail_server']
        mail_server_ids = ir_mail_server.search([], order='sequence', limit=1)
        po_config = self.env.user.company_id.po_config
        aproval_line_ids = self.env['users.approval.qc'].search(
            [('qc_id', '=', po_config.id), ('sequence', '=', '3st_lavels')], limit=1)
        if aproval_line_ids:
            if not self._uid == aproval_line_ids.user_id.id:
                raise UserError(_('You are not Authorized Person to Approve'))
        if po_config.quote_validation and int(po_config.quote_validation) > 3:
            self.write({'state': 'third_level_approved'})
            if mail_server_ids and po_config:
                text2 = "<html><body><p>Hello, </p><p></p><p>You have sent <b>%s</b> for the approval to the next approving authority.<b></b></p><p>Thank You</p><p>Odoo Team</p></body></html>" % (
                    self.name)
                mail = mail_server_ids
                if mail.smtp_user:
                    approval_line_ids = self.env['users.approval.qc'].search(
                        [('qc_id', '=', po_config.id), ('sequence', '=', '4st_lavels')])
                    for approval_line in approval_line_ids:
                        lst.append(approval_line.user_id.partner_id.id)
                        template_id = approval_line.qc_mail_template
                        # if template_id and approval_line.user_id and not context.get('roger'):
                        #     print('reeeee')
                        #     template_id.send_mail(self.id, force_send=True,
                        #                           email_values={'email_to': approval_line.user_id.partner_id.email,
                        #                                         'email_from': mail.smtp_user or ''})
                        if approval_line.user_id.partner_id.email:
                            vals2 = {
                                'email_from': mail.smtp_user,
                                'email_to': approval_line.user_id.partner_id.email,
                                'subject': _('Service Order Approval'),
                                'body': text2,
                                'body_html': text2,
                                'parent_id': None,
                                'auto_delete': True,
                            }
                            mail2 = self.env['mail.mail'].create(vals2)
                            if not context.get('roger'):
                                mail2.send()
        else:
            self.write({'state': 'approved'})



    def button_4th_approval(self):
        lst = []
        context = dict(self._context or {})
        ir_mail_server = self.env['ir.mail_server']
        mail_server_ids = ir_mail_server.search([], order='sequence', limit=1)
        po_config = self.env.user.company_id.po_config
        aproval_line_ids = self.env['users.approval.qc'].search(
            [('qc_id', '=', po_config.id), ('sequence', '=', '4st_lavels')], limit=1)
        if aproval_line_ids:
            if not self._uid == aproval_line_ids.user_id.id:
                raise UserError(_('You are not Authorized Person to Approve'))
        if po_config.quote_validation and int(po_config.quote_validation) > 4:
            self.write({'state': 'fourth_level_approved'})
            if mail_server_ids and po_config:
                text2 = "<html><body><p>Hello, </p><p></p><p>You have sent <b>%s</b> for the approval to the next approving authority.<b></b></p><p>Thank You</p><p>Odoo Team</p></body></html>" % (
                    self.name)
                mail = mail_server_ids
                if mail.smtp_user:
                    approval_line_ids = self.env['users.approval.qc'].search(
                        [('qc_id', '=', po_config.id), ('sequence', '=', '5st_lavels')])
                    for approval_line in approval_line_ids:
                        lst.append(approval_line.user_id.partner_id.id)
                        template_id = approval_line.qc_mail_template
                        # if template_id and approval_line.user_id and not context.get('roger'):
                        #     print('reeeee')
                        #     template_id.send_mail(self.id, force_send=True,
                        #                           email_values={'email_to': approval_line.user_id.partner_id.email,
                        #                                         'email_from': mail.smtp_user or ''})
                        if approval_line.user_id.partner_id.email:
                            vals2 = {
                                'email_from': mail.smtp_user,
                                'email_to': approval_line.user_id.partner_id.email,
                                'subject': _('Service Order Approval'),
                                'body': text2,
                                'body_html': text2,
                                'parent_id': None,
                                'auto_delete': True,
                            }
                            mail2 = self.env['mail.mail'].create(vals2)
                            if not context.get('roger'):
                                mail2.send()
        else:
            self.write({'state': 'approved'})

    def button_5th_approval(self):
        po_config = self.env.user.company_id.po_config
        aproval_line_ids = self.env['users.approval.qc'].search(
            [('qc_id', '=', po_config.id), ('sequence', '=', '5st_lavels')], limit=1)
        if aproval_line_ids:
            if not self._uid == aproval_line_ids.user_id.id:
                raise UserError(_('You are not Authorized Person to Approve'))
        self.write({'state': 'approved'})

    # @api.depends('order_id')
    def _compute_picking_ids(self):
        print("xyz=====", )
        for order in self:
            order.po_order_count = 0
            print("order=====", order)
            pickings = self.env['purchase.order'].search([('quote_comp_id', '=', order.id)])
            print('pickings=============', pickings)
            if pickings:
                order.po_order_count = len(pickings)
            #     if any(pickings.filtered(lambda picking: picking.state not in ('done', 'cancel'))):
            #         order.dispatch_validated = True
            #     else:
            #         order.dispatch_validated = False
            # else:
            #     order.dispatch_validated = False

    @api.model
    def create(self, vals):
        list = []
        if vals.get('rfq_no_line'):
            for rec in vals.get('rfq_no_line'):
                list.append(rec[2].get('price_unit'))
            list.sort()
            list_no = list[0]
            for rec in vals.get('rfq_no_line'):
                if rec[2].get('price_unit') == list_no:
                    rec[2]['color_change'] = True
                else:
                    rec[2]['color_change'] = False
        seq = self.env['ir.sequence'].next_by_code('quote.comparision') or _('New')
        vals.update({'name': seq})
        res = super(QuoteComparision, self).create(vals)
        return res

    # def write(self, vals):
    #     res = super(QuoteComparision, self).write(vals)
    #     list = []
    #     if self.rfq_no_line:
    #         for rec in self.rfq_no_line:
    #             list.append(rec.price_unit)
    #         list.sort()
    #         list_no = list[0]
    #         for rec in self.rfq_no_line:
    #             if rec.price_unit == list_no:
    #                 rec.color_change = True
    #             else:
    #                 rec.color_change = False
    #     return res

    def write(self, vals):
        list2 = []
        list3 = []
        lp = []
        lo = []
        res = super(QuoteComparision, self).write(vals)
        if self.rfq_no_line:
            for rec in self.rfq_no_line:
                rec.color_change = False
                list2.append(rec.product_id.id)
            for x in list2:
                if x not in list3:
                    list3.append(x)
            for l in list3:
                p=self.rfq_no_line.filtered(lambda o: o.product_id.id == l)
                for y in p:
                    lo.append(y.price_unit)
                lo.sort()
                q = self.rfq_no_line.filtered(lambda o: o.price_unit == lo[0] and o.product_id.id == l)
                for line_id in q:
                    if line_id:
                        line_id.color_change = True
                lo=[]
        return res

    def action_in_progress(self):
        po_config = self.env.user.company_id.po_config
        # aproval_line_ids = self.env['users.approval.qc'].search(
        #     [('qc_id', '=', po_config.id), ('sequence', '=', '1st_lavels')], limit=1)
        # if aproval_line_ids:
        #     if not self._uid == aproval_line_ids.user_id.id:
        #         raise UserError(_('You are not Authorized Person to Approve'))
        if po_config.quote_validation and int(po_config.quote_validation) > 0:
            self.write({'state': 'pending_approval'})
        else:
            self.write({'state': 'approved'})
        # print("hello.............")
        # lst = []
        # self.ensure_one()
        # po_config = self.env.user.company_id.po_config
        # context = dict(self._context or {})
        # ir_mail_server = self.env['ir.mail_server']
        # mail_server_ids = ir_mail_server.search([], order='sequence', limit=1)
        # # start_date = datetime.now()
        # # self.count_no_of_days(start_date, False)
        # ir_model_data = self.env['ir.model.data']
        # ir_model_fields_obj = self.env['ir.model.fields']
        # ir_model_fields_id = ir_model_fields_obj.search([('name', '=', 'reporting_manager_id')])
        # try:
        #     compose_form_id = \
        #         ir_model_data._xmlid_lookup('verts_v15_freight_purchase.simpa_email_compose_message_wizard_form')[1]
        # except ValueError:
        #     compose_form_id = False
        #
        # for indent in self:
        #     print('for')
        #     new_date = []
        #     aprrovers = []
        #     print(po_config.quote_validation,'po_config.po_validation')
        #     if po_config and int(
        #             po_config.quote_validation) > 0:
        #         ########Next Approver###
        #         # print("if")
        #         approval_line_ids = self.env['users.approval.qc'].search(
        #             [('qc_id', '=', po_config.id), ('sequence', '=', '1st_lavels')], limit=1)
        #         print('approval_line_ids', approval_line_ids)
        #         for line in approval_line_ids:
        #             print('line', line.user_id.id)
        #             aprrovers.append(line.user_id.id)
        #             # week_after = datetime.strptime(str(DT.date.today()), "%Y-%m-%d") + DT.timedelta(days=line.sla_days)
        #             # new_date.append(datetime.strftime(week_after, "%Y-%m-%d"))
        #             # week_after = datetime.strptime(str(DT.date.today()), "%Y-%m-%d") + DT.timedelta(days=line.sla_days)
        #             # new_date.append(datetime.strftime(week_after, "%Y-%m-%d"))
        #         # print('new_date',new_date)
        #         # print("+++++++++++++++", new_date[0])
        #         ##########
        #         self.env['purchase.order.history'].create({
        #             'purchase_id': indent.id,
        #             'user': self._uid,
        #             'desc': "Send for Approval",
        #             'po_name': indent.name,
        #             # 'logging_date': datetime.now(),
        #             # 'status': dic_state[indent.state],
        #             'mark_green': True,
        #             ###Next Approver###
        #             'next_approver': [(6, 0, aprrovers)],
        #             # 'next_approval_deadline': new_date[0] if new_date else False
        #         })
        #         self.write({'state': 'pending_approval'})
        #         if mail_server_ids:
        #             mail = mail_server_ids
        #             if mail.smtp_user:
        #                 approval_line_ids = self.env['users.approval.qc'].search(
        #                     [('qc_id', '=', po_config.id), ('sequence', '=', '1st_lavels')])
        #                 for approval_line in approval_line_ids:
        #                     lst.append(approval_line.user_id.partner_id.id)
        #                     indent.send_for_approve_msg(approval_line.user_id.partner_id)
        #                     template_id = approval_line.po_mail_template
        #                     indent.write({'approver_user_id': approval_line.user_id.id})
        #                     if template_id and approval_line.user_id and not context.get('roger'):
        #                         template_id.send_mail(self.id, force_send=True,
        #                                               email_values={'email_to': approval_line.user_id.partner_id.email,
        #                                                             'email_from': mail.smtp_user or ''})
        #                 if indent.department_id.manager_id.user_id.partner_id:
        #                     lst.append(indent.department_id.manager_id.user_id.partner_id.id)
        #                     indent.send_for_approve_msg(indent.department_id.manager_id.user_id.partner_id)
        #                 if self.department_id and self.department_id.manager_id and self.department_id.manager_id.work_email:
        #                     text3 = "<html><body><p>Hello <b>%s</b>,</p><p></p><p>Please approve PO no. <b>%s</b> in Odoo.</p>This is an automatically generated email, please do not reply.<p> <b></b> .</p><p>Thank You</p><p>Odoo Team</p></body></html>" % (
        #                         self.department_id.manager_id.name, self.name)
        #                     indent.write({'approver_user_id': self.department_id.manager_id.user_id.id})
        #                     vals2 = {
        #                         'email_from': mail.smtp_user,
        #                         'email_to': self.department_id.manager_id.work_email,
        #                         'subject': _("PO Approval"),
        #                         'body': text3,
        #                         'body_html': text3,
        #                         'parent_id': None,
        #                         'auto_delete': True,
        #                     }
        #                     mail2 = self.env['mail.mail'].create(vals2)
        #                     if not context.get('roger'):
        #                         mail2.send()
        #                 text2 = "<html><body><p>Hello, </p><p></p><p>You have sent <b>%s</b> for the approval to the next approving authority.<b></b></p><p>Thank You</p><p>Odoo Team</p></body></html>" % (
        #                     self.name)
        #                 if self.env.user.partner_id.email:
        #                     vals2 = {
        #                         'email_from': mail.smtp_user,
        #                         'email_to': self.env.user.partner_id.email,
        #                         'subject': _("PO Approval"),
        #                         'body': text2,
        #                         'body_html': text2,
        #                         'parent_id': None,
        #                         'auto_delete': True,
        #                     }
        #                     mail2 = self.env['mail.mail'].create(vals2)
        #                     if not context.get('roger'):
        #                         mail2.send()
        #             if lst:
        #                 indent.message_subscribe(lst)
        #     else:
        #         self.write({'state': 'approved'})
        #     #     self.write({'state': 'purchase'})
            #     self.env['purchase.order.history'].create({
            #         'purchase_id': indent.id,
            #         'user': self._uid,
            #         "new_value": "Approved",
            #         'desc': "Final Approved",
            #         "old_value": "",
            #         "po_name": indent.name,
            #         'logging_date': datetime.now(),
            #         'status': dic_state[self.state],
            #         'mark_green': True
            #     })
            #     indent.final_approve()
            # for pi in indent.indents_ids:
            #     attach_ids = self.env['ir.attachment'].search(
            #         [('res_model', '=', 'purchase.requisition'), ('res_id', '=', pi.id)])
            #     for attach in attach_ids:
            #         attach_id = attach.copy()
            #         if attach_id:
            #             attach_id.write({'res_id': indent.id,
            #                              'res_model': 'purchase.order',
            #                              'res_name': indent.name,
            #                              'res_model_name': 'Purchase Order',
            #                              'res_name': indent.name,
            #                              })
            # if self.forecast_id:
            #     for line in self.order_line.filtered(lambda r: r.account_analytic_id):
            #         amount = line.price_total
            #         self.forecast_id.update_expenses(line.account_analytic_id, self.name, ptype='po', amount=amount)
            #
            # if indent.new_reject_seq > 0:
            #     if indent.new_reject_seq == 1:
            #         indent.name = str(indent.name) + '-' + str(indent.new_reject_seq)
            #     else:
            #         indent.name = str(indent.name.split('-')[0]) + '-' + str(indent.new_reject_seq)
            # if indent.company_id.po_submission == 'yes':
            #     template_id = indent.company_id.po_submission_template_id.id
            #     if ir_model_fields_id and indent.user_id.reporting_manager_id:
            #         if template_id:
            #             ctx = dict()
            #             ctx.update({
            #                 'default_model': 'purchase.order',
            #                 'default_res_id': self.id,
            #                 'default_use_template': bool(template_id),
            #                 'default_template_id': template_id,
            #                 'default_composition_mode': 'comment',
            #                 'default_partner_ids': [(6, 0, [indent.user_id.reporting_manager_id.partner_id.id])],
            #             })
            #             return {
            #                 'type': 'ir.actions.act_window',
            #                 'view_type': 'form',
            #                 'view_mode': 'form',
            #                 'res_model': 'mail.compose.message',
            #                 'views': [(compose_form_id, 'form')],
            #                 'view_id': compose_form_id,
            #                 'target': 'new',
            #                 'context': ctx,
            #             }

        # self.state = 'pending_approval'

    def action_in_approve(self):
        lst = []
        context = dict(self._context or {})
        ir_mail_server = self.env['ir.mail_server']
        po_config = self.env.user.company_id.po_config
        mail_server_ids = ir_mail_server.search([], order='sequence', limit=1)
        # end_date = datetime.now()
        # self.count_no_of_days(False, end_date)
        ir_model_data = self.env['ir.model.data']
        ir_model_fields_obj = self.env['ir.model.fields']
        ir_model_fields_id = ir_model_fields_obj.search([('name', '=', 'reporting_manager_id')])
        try:
            compose_form_id = \
                ir_model_data._xmlid_lookup('verts_v15_freight_purchase.simpa_email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        ##############Next Approver##############
        user_seq = self.env['users.approval.qc'].search(
            [('qc_id', '=', po_config.id), ('sequence', '=', '1st_lavels')], limit=1)
        # for usr in user_seq:
        #     for hist in self.purchase_history_lines:
        #         if usr.user_id.id == hist.next_approver.id:
        #             hist.next_approver = False
        # hist.next_approval_date = False
        ####################################
        for order in self:
            #######New Appproval########
            aprrovers2 = []
            new_date1 = []
            approval_line_ids = self.env['users.approval.qc'].search(
                [('qc_id', '=', po_config.id), ('sequence', '=', '2nd_lavels')], limit=1)
            for line in approval_line_ids:
                aprrovers2.append(line.user_id.id)
                # week_after = datetime.strptime(str(DT.date.today()), "%Y-%m-%d") + DT.timedelta(days=line.sla_days)
                # new_date1.append(datetime.strftime(week_after, "%Y-%m-%d"))
            ########################
            # order._add_supplier_to_product()
            # order.action_approve()
            # order.first_level_approval_date = datetime.now()
            if po_config and int(
                    po_config.po_validation) > 1:
                self.env['purchase.order.history'].create({
                    'purchase_id': order.id,
                    'user': self._uid,
                    'desc': "1st Level Approved",
                    'po_name': order.name,
                    # 'logging_date': datetime.now(),
                    # 'status': dic_state[order.state],
                    'mark_green': True,
                    #############
                    'next_approver': [(6, 0, aprrovers2)],
                    # 'next_approval_deadline': new_date1[0] if new_date1 else False
                })
                self.write({'state': 'approved'})
            #     if mail_server_ids:
            #         text2 = "<html><body><p>Hello, </p><p></p><p>You have sent <b>%s</b> for the approval to the next approving authority.<b></b></p><p>Thank You</p><p>Odoo Team</p></body></html>" % (
            #             self.name)
            #         mail = mail_server_ids
            #         if mail.smtp_user:
            #             approval_line_ids = self.env['users.approval.po'].search(
            #                 [('po_id', '=', po_config.id), ('sequence', '=', '2nd_lavels')])
            #             for approval_line in approval_line_ids:
            #                 lst.append(approval_line.user_id.partner_id.id)
            #                 order.send_for_approve_msg(approval_line.user_id.partner_id)
            #                 template_id = approval_line.po_mail_template
            #                 order.write({'approver_user_id': approval_line.user_id.id})
            #                 if template_id and approval_line.user_id and not context.get('roger'):
            #                     template_id.send_mail(self.id, force_send=True,
            #                                           email_values={'email_to': approval_line.user_id.partner_id.email,
            #                                                         'email_from': mail.smtp_user or ''})
            #
            #             if self.env.user.partner_id.email:
            #                 vals2 = {
            #                     'email_from': mail.smtp_user,
            #                     'email_to': self.env.user.partner_id.email,
            #                     'subject': _("PO Approval"),
            #                     'body': text2,
            #                     'body_html': text2,
            #                     'parent_id': None,
            #                     'auto_delete': True,
            #                 }
            #                 mail2 = self.env['mail.mail'].create(vals2)
            #                 if not context.get('roger'):
            #                     mail2.send()
            #             if self.user_id.partner_id.email:
            #                 vals2 = {
            #                     'email_from': mail.smtp_user,
            #                     'email_to': self.user_id.partner_id.email,
            #                     'subject': _("PO Approval"),
            #                     'body': text2,
            #                     'body_html': text2,
            #                     'parent_id': None,
            #                     'auto_delete': True,
            #                 }
            #                 mail2 = self.env['mail.mail'].create(vals2)
            #                 if not context.get('roger'):
            #                     mail2.send()
            #         if lst:
            #             order.message_subscribe(lst)
            # else:
            #     self.write({'state': 'purchase'})
            #     self.env['purchase.order.history'].create({
            #         'purchase_id': order.id,
            #         'user': self._uid,
            #         "new_value": "Approved",
            #         'desc': "Final Approved",
            #         "old_value": "",
            #         "po_name": order.name,
            #         'logging_date': datetime.now(),
            #         'status': dic_state[order.state],
            #         'mark_green': True
            #     })
            #     order.final_approve()
            # # Start - Use this code for purchase agreement standard functionality
            # if not order.requisition_id:
            #     continue
            # if order.requisition_id.type_id.exclusive == 'exclusive':
            #     others_po = order.requisition_id.mapped('purchase_ids').filtered(lambda r: r.id != order.id)
            #     others_po.button_cancel()
            #     if order.state not in ['draft', 'sent', 'to approve']:
            #         order.requisition_id.action_done()
            # # Stop - Use this code for purchase agreement standard functionality
            # if order.company_id.po_approve == 'yes':
            #     template_id = order.company_id.po_approve_template_id.id
            #     if ir_model_fields_id and order.user_id.reporting_manager_id.reporting_manager_id.reporting_manager_id:
            #         if template_id:
            #             ctx = dict()
            #             ctx.update({
            #                 'default_model': 'purchase.order',
            #                 'default_res_id': self.id,
            #                 'default_use_template': bool(template_id),
            #                 'default_template_id': template_id,
            #                 'default_composition_mode': 'comment',
            #                 'default_partner_ids': [(6, 0, [
            #                     order.user_id.reporting_manager_id.reporting_manager_id.reporting_manager_id.partner_id.id])],
            #             })
            #             return {
            #                 'type': 'ir.actions.act_window',
            #                 'view_type': 'form',
            #                 'view_mode': 'form',
            #                 'res_model': 'mail.compose.message',
            #                 'views': [(compose_form_id, 'form')],
            #                 'view_id': compose_form_id,
            #                 'target': 'new',
            #                 'context': ctx,
            #             }
        # self.state = 'approved'

    def create_po(self):
        dct = {}
        for rec in self.rfq_no_line:
            if rec.initiate_po:
                if rec.partner_id.id not in dct:
                    po_id = self.env['purchase.order'].create({
                        'partner_id': rec.partner_id.id,
                        'internal_product_type': self.internal_product_type,
                        'quote_comp_id': self.id,
                        'origin_type': 'rfq',
                        'advance_type': rec.order_id.advance_type,
                        'advance_value': rec.order_id.advance_value,
                        'advance_remark': rec.order_id.advance_remark,
                        'readonly_qty': True,
                        'readonly_price': True,
                    })
                    if po_id:
                        self.env['purchase.order.line'].create({
                            'order_id': po_id.id,
                            'product_id': rec.product_id.id,
                            'product_qty': rec.po_qty,
                            'price_unit': rec.price_unit,
                        })
                        dct.update({rec.order_id.id: po_id.id})
                else:
                    self.env['purchase.order.line'].create({
                        'order_id': dct[rec.order_id.id],
                        'product_id': rec.product_id.id,
                        'price_unit': rec.price_unit,
                        'product_qty': rec.po_qty,
                    })
                rec.write({
                    'done_rfq_qty': rec.done_rfq_qty + rec.po_qty,
                    'pending_rfq_qty': rec.rfq_qty - (rec.done_rfq_qty + rec.po_qty),
                })
            po_config = self.env.user.company_id.po_config
            if not po_config.create_multiple_rfq:
                self.is_show_create_po= True
        return {
            'effect': {
                'fadeout': 'slow',
                'message': 'Purchase Order have been created successfully for the Initiated Products',
                'type': 'rainbow_man',
            }
        }

class QuoteComparisionLine(models.Model):
    _name = "quote.comparision.line"
    _description = 'Quote Comparision Line'

    rfq_id = fields.Many2one('quote.comparision', string='RFQ No')
    order_id = fields.Many2one('purchase.order', string='Oder Reference')
    partner_id = fields.Many2one('res.partner', string='Vendor')
    product_id = fields.Many2one('product.product', string='Product')
    price_unit = fields.Float(string='Unit Price')
    rfq_qty = fields.Float(string='RFQ Qty')
    pending_rfq_qty = fields.Float(string='Pending RFQ Qty')
    done_rfq_qty = fields.Float(string='Done RFQ Qty')
    po_qty = fields.Float(string='Proposed Po Qty')
    uom_id = fields.Many2one('uom.uom', string='UoM')
    date_planned = fields.Datetime(string='Scheduled Date')
    remarks = fields.Char(string="Remarks")
    color_change = fields.Boolean(string="Color Change")
    initiate_po = fields.Boolean(string="Initiate PO")
    display_type = fields.Selection([
        ('line_section', "Section"),
        ('line_note', "Note")], default=False, help="Technical field for UX purpose.")
    name = fields.Char(string='.', required=False)

    @api.onchange('order_id')
    def _onchange_product_id(self):
        if self.order_id:
            self.partner_id = self.order_id.partner_id

    @api.onchange('po_qty')
    def _onchange_po_qty(self):
        if self.po_qty:
            if self.po_qty > self.pending_rfq_qty:
                raise UserError(_('Please Select appropriate Qty from Pending RFQ Qty'))
            else:
                pass


