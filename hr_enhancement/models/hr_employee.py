from odoo import fields, models, api, _
from datetime import date


class Employee(models.Model):
    _inherit = 'hr.employee'

    registration_number = fields.Char('Employee code', groups="hr.group_hr_user", copy=False)

    delegation_required = fields.Boolean()
    passport_location = fields.Selection(selection=[('with_emp', 'مع الموظف'),
                                                    ('with_comp', 'مع الشركة')], tracking=True,
                                         string='Passport Location')
    probation_date_end = fields.Date('Probation Period End')

    identification_expiry_date = fields.Date()
    passport_expiry_date = fields.Date(string='Passport Expiry Date')
    medical_card_number = fields.Char()
    medical_card_expiry_date = fields.Date()
    bank_card_expiry_date = fields.Date()

    arabic_name = fields.Char(string='Arabic Name')
    iqama_profession = fields.Char(string='Iqama Profession')
    expiry_date = fields.Date(string='Iqama Expiry Date')
    sponsor_name = fields.Many2one(comodel_name='employee.sponsor', string='Sponsor Name')
    sponsor_address = fields.Char(string='عنوان المنشاءة', related="sponsor_name.sponsor_address")
    sponsor_delivery_postal_address = fields.Char(string='العنوان البريدى',
                                                  related="sponsor_name.sponsor_delivery_postal_address")
    sponsor_registration_number = fields.Char(string='رقم التسجيل', related="sponsor_name.sponsor_registration_number")
    sponsor_civil_id = fields.Char(string='الرقم المدنى', related="sponsor_name.sponsor_civil_id")
    sponsor_phone = fields.Char(string='تليفون', related="sponsor_name.sponsor_phone")
    sponsor_fax = fields.Char(string='فاكس', related="sponsor_name.sponsor_fax")

    nationality_number = fields.Char()
    article = fields.Char()
    nationality_date = fields.Date()
    bank_number = fields.Char()
    bank_iban_number = fields.Char()
    bank_id = fields.Many2one(comodel_name='res.bank')

    def _notify_hr_manager(self):
        for record in self.search([]):
            email_notify_group = self.env.ref('hr.group_hr_manager').id
            users = self.env['res.users'].sudo().search([('groups_id', 'in', [email_notify_group])])

            if users:
                for user in users:
                    # Construct the notification message
                    if record.identification_expiry_date == date.today():
                        message = f"Identification of employee {record.name} is expired Today.Please update it."

                        todos = {
                            'res_id': record.id,
                            'res_model_id': self.env['ir.model'].search([('model', '=', 'hr.employee')]).id,
                            'user_id': user.id,
                            'summary': 'Identification Expiry Notification',
                            'note': message,
                            'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                            'date_deadline': fields.Date.today(),
                        }
                        self.env['mail.activity'].create(todos)

                    if record.passport_expiry_date == date.today():
                        message = f"Passport of employee {record.name} is expired Today.Please update it."

                        todos = {
                            'res_id': record.id,
                            'res_model_id': self.env['ir.model'].search([('model', '=', 'hr.employee')]).id,
                            'user_id': user.id,
                            'summary': 'Passport Expiry Notification',
                            'note': message,
                            'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                            'date_deadline': fields.Date.today(),
                        }
                        self.env['mail.activity'].create(todos)

                    if record.expiry_date == date.today():
                        message = f"Iqama of employee {record.name} is expired Today.Please update it."

                        todos = {
                            'res_id': record.id,
                            'res_model_id': self.env['ir.model'].search([('model', '=', 'hr.employee')]).id,
                            'user_id': user.id,
                            'summary': 'Iqama Expiry Notification',
                            'note': message,
                            'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                            'date_deadline': fields.Date.today(),
                        }
                        self.env['mail.activity'].create(todos)

                    if record.visa_expire == date.today():
                        message = f"Visa of employee {record.name} is expired Today.Please update it."

                        todos = {
                            'res_id': record.id,
                            'res_model_id': self.env['ir.model'].search([('model', '=', 'hr.employee')]).id,
                            'user_id': user.id,
                            'summary': 'Visa Expiry Notification',
                            'note': message,
                            'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                            'date_deadline': fields.Date.today(),
                        }
                        self.env['mail.activity'].create(todos)


class HrEmployeesPublic(models.Model):
    _inherit = 'hr.employee.public'

    delegation_required = fields.Boolean()
    passport_location = fields.Selection(selection=[('with_emp', 'مع الموظف'),
                                                    ('with_comp', 'مع الشركة')], tracking=True, string='مكان الجواز')
    probation_date_end = fields.Date('Probation Period End')

    identification_expiry_date = fields.Date()
    passport_expiry_date = fields.Date()
    medical_card_number = fields.Char()
    medical_card_expiry_date = fields.Date()
    bank_card_expiry_date = fields.Date()

    arabic_name = fields.Char(string='Arabic Name')
    iqama_profession = fields.Char(string='Iqama Profession')
    expiry_date = fields.Date(string='Expiry Date')
    sponsor_name = fields.Many2one(comodel_name='employee.sponsor', string='Sponsor Name')

    nationality_number = fields.Char()
    article = fields.Char()
    nationality_date = fields.Date()
    bank_number = fields.Char()
