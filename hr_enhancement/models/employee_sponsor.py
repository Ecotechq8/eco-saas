from odoo import fields, models, api, _


class EmployeeSponsor(models.Model):
    _name = 'employee.sponsor'

    name = fields.Char()
    sponsor_address = fields.Char(string='عنوان المنشاءة')
    sponsor_delivery_postal_address = fields.Char(string='العنوان البريدى')
    sponsor_registration_number = fields.Char(string='رقم التسجيل')
    sponsor_civil_id = fields.Char(string='الرقم المدنى')
    sponsor_phone = fields.Char(string='تليفون')
    sponsor_fax = fields.Char(string='فاكس')
