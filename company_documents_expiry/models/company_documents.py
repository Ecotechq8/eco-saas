# -*- coding: utf-8 -*-
from datetime import datetime, date, timedelta
from odoo import models, fields, api, _


class HrEmployeeDocument(models.Model):
    _name = 'hr.company.document'
    _description = 'Company Documents'

    def mail_reminder(self):
        """Sending document expiry notification to employees."""

        now = datetime.now() + timedelta(days=1)
        # date_now = now.date()
        date_now = fields.Date.today()
        match = self.search([])
        for i in match:
            if i.expiry_date:
                if i.notification_type == 'single':
                    if date_now == i.expiry_date:
                        mail_content = "  Hello  " + i.company_ref.name + ",<br>Your Document " + i.name + " is going to expire on " + \
                                       str(i.expiry_date) + ". Please renew it before expiry date"
                        email_notify_group = self.env.ref(
                            'company_documents_expiry.group_company_expiry_mail_send').id
                        users = self.env['res.users'].sudo().search([('groups_id', 'in', [email_notify_group])])
                        for user in users:
                            main_content = {
                                'subject': _('Document-%s Expired On %s') % (i.name, i.expiry_date),
                                'author_id': self.env.user.partner_id.id,
                                'body_html': mail_content,
                                'email_to': user.partner_id.email,
                            }
                            self.env['mail.mail'].create(main_content).send()

                elif i.notification_type == 'multi':
                    exp_date = fields.Date.from_string(i.expiry_date) - timedelta(days=i.before_days)
                    if date_now == exp_date or date_now == i.expiry_date:  # on Expire date and few days(As it set) before expire date
                        mail_content = "  Hello  " + i.company_ref.name + ",<br>Your Document " + i.name + \
                                       " is going to expire on " + str(i.expiry_date) + \
                                       ". Please renew it before expiry date"
                        email_notify_group = self.env.ref(
                            'company_documents_expiry.group_company_expiry_mail_send').id
                        users = self.env['res.users'].sudo().search([('groups_id', 'in', [email_notify_group])])
                        for user in users:
                            main_content = {
                                'subject': _('Document-%s Expired On %s') % (i.name, i.expiry_date),
                                'author_id': self.env.user.partner_id.id,
                                'body_html': mail_content,
                                'email_to': user.partner_id.email,
                            }
                            self.env['mail.mail'].create(main_content).send()

                elif i.notification_type == 'everyday':
                    exp_date = fields.Date.from_string(i.expiry_date) - timedelta(days=i.before_days)
                    if date_now >= exp_date or date_now == i.expiry_date:
                        mail_content = "  Hello  " + i.company_ref.name + ",<br>Your Document " + i.name + \
                                       " is going to expire on " + str(i.expiry_date) + \
                                       ". Please renew it before expiry date"
                        email_notify_group = self.env.ref(
                            'company_documents_expiry.group_company_expiry_mail_send').id
                        users = self.env['res.users'].sudo().search([('groups_id', 'in', [email_notify_group])])
                        for user in users:
                            main_content = {
                                'subject': _('Document-%s Expired On %s') % (i.name, i.expiry_date),
                                'author_id': self.env.user.partner_id.id,
                                'body_html': mail_content,
                                'email_to': user.partner_id.email,
                            }
                            self.env['mail.mail'].create(main_content).send()

                elif i.notification_type == 'everyday_after':
                    exp_date = fields.Date.from_string(i.expiry_date) + timedelta(days=i.before_days)
                    if date_now <= exp_date or date_now == i.expiry_date:
                        mail_content = "  Hello  " + i.company_ref.name + ",<br>Your Document " + i.name + \
                                       " is expired on " + str(i.expiry_date) + ". Please renew it "
                        email_notify_group = self.env.ref(
                            'company_documents_expiry.group_company_expiry_mail_send').id
                        users = self.env['res.users'].sudo().search([('groups_id', 'in', [email_notify_group])])
                        for user in users:
                            main_content = {
                                'subject': _('Document-%s Expired On %s') % (i.name, i.expiry_date),
                                'author_id': self.env.user.partner_id.id,
                                'body_html': mail_content,
                                'email_to': user.partner_id.email,
                            }
                            self.env['mail.mail'].create(main_content).send()
                else:
                    exp_date = fields.Date.from_string(i.expiry_date) - timedelta(days=7)
                    if date_now == exp_date:
                        mail_content = "  Hello  " + i.company_ref.name + ",<br>Your Document " + i.name + \
                                       " is going to expire on " + str(
                            i.expiry_date) + ". Please renew it before expiry date"
                        email_notify_group = self.env.ref(
                            'company_documents_expiry.group_company_expiry_mail_send').id
                        users = self.env['res.users'].sudo().search([('groups_id', 'in', [email_notify_group])])
                        for user in users:
                            main_content = {
                                'subject': _('Document-%s Expired On %s') % (i.name, i.expiry_date),
                                'author_id': self.env.user.partner_id.id,
                                'body_html': mail_content,
                                'email_to': user.partner_id.email,
                            }
                            self.env['mail.mail'].create(main_content).send()

    @api.constrains('expiry_date')
    def check_expr_date(self):
        for each in self:
            if each.expiry_date:
                exp_date = fields.Date.from_string(each.expiry_date)
                if exp_date < date.today():
                    raise Warning('Your Document Is Expired.')

    name = fields.Char(string='Document Number', required=True, copy=False, help='You can give your'
                                                                                 'Document number.')
    description = fields.Text(string='Description', copy=False, help="Description")
    expiry_date = fields.Date(string='Expiry Date', copy=False, help="Date of expiry")
    company_ref = fields.Many2one('res.company', invisible=1, copy=False, default=lambda self: self.env.company)
    document_responsible = fields.Many2one('res.users', invisible=1, copy=False)
    company_doc_attachment_id = fields.Many2many('ir.attachment', 'company_doc_attach_rel', 'doc_id', 'attach_id3',
                                                 string="Attachment",
                                                 help='You can attach the copy of your document', copy=False)
    issue_date = fields.Date(string='Issue Date', default=fields.datetime.now(), help="Date of issue", copy=False)
    document_type = fields.Many2one('company.document.type', string="Document Type", help="Document type")
    before_days = fields.Integer(string="Days", help="How many number of days before to get the notification email")
    notification_type = fields.Selection([
        ('single', 'Notification on expiry date'),
        ('multi', 'Notification before few days'),
        ('everyday', 'Everyday till expiry date'),
        ('everyday_after', 'Notification on and after expiry')
    ], string='Notification Type',
        help="""
        Notification on expiry date: You will get notification only on expiry date.
        Notification before few days: You will get notification in 2 days.On expiry date and number of days before date.
        Everyday till expiry date: You will get notification from number of days till the expiry date of the document.
        Notification on and after expiry: You will get notification on the expiry date and continues upto Days.
        If you did't select any then you will get notification before 7 days of document expiry.""")

    @api.onchange('document_type')
    def _onchange_document_type(self):
        for item in self:
            print(item.document_type)
            if item.document_type:
                item.notification_type = item.document_type.notification_type
                item.before_days = item.document_type.before_days


class HrEmployee(models.Model):
    _inherit = 'res.partner'

    def _document_count(self):
        for each in self:
            document_ids = self.env['hr.company.document'].sudo().search([])  # ('company_ref', '=', each.id)
            each.document_count = len(document_ids)

    def document_view(self):
        self.ensure_one()
        domain = [
            ('company_ref', '=', self.id)]
        return {
            'name': _('Documents'),
            'domain': domain,
            'res_model': 'hr.company.document',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'list,form',
            'help': _('''<p class="oe_view_nocontent_create">
                           Click to Create for New Documents
                        </p>'''),
            'limit': 80,
            # 'context': "{'default_company_ref': %s}" % self.id
        }

    document_count = fields.Integer(compute='_document_count', string='# Documents')


class HrEmployeeAttachment(models.Model):
    _inherit = 'ir.attachment'

    company_doc_attach_rel = fields.Many2many('hr.company.document', 'company_doc_attachment_id', 'attach_id3',
                                              'doc_id',
                                              string="Attachment", invisible=1)
    attach_rel = fields.Many2many('hr.document', 'attach_id', 'attachment_id3', 'document_id',
                                  string="Attachment", invisible=1)
