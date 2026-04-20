# -*- coding: utf-8 -*-
# Copyright 2021 Verts Services India Pvt Ltd.
# http://www.verts.co.in

from odoo import api,fields,models, _
from odoo.exceptions import UserError


class ecgc_rating(models.Model):
    _name = "ecgc.rating"
    _description = 'ecgc_rating'

    name = fields.Char('ECGC Rating/Classification', size=128, required=True)
    risk_perception = fields.Char('Risk Perception', size=128)
    expense_id = fields.Many2one('product.product', string='Expense Name')
    ecgc_calculation_groups = fields.Many2many('product.classification', 'ecgc_product_class_rel', 'ecgc_rating_id','prdouct_class_id', string='Product Class')
    # payment_term_id = fields.Many2many('account.payment.term', 'ecgc_payment_rel', 'ecgc_id', 'payment_id', string='Payment Terms')
    ecgc_rating_line = fields.One2many('ecgc.rating.line', 'ecgc_rating_id', 'ECGC Rating Line')
    payment_lines = fields.One2many('ecgc.premium.rate', 'ecgc_rating_id', 'Payment Details')

    @api.model
    def create(self, vals):
        if 'ecgc_rating_line' in vals and vals['ecgc_rating_line']:
            for rec in vals['ecgc_rating_line']:
                if rec[2] != False:
                    country_id = self.env['res.country'].browse(rec[2]['country_id'])
                    if country_id.ecgc_rating != False and country_id.ecgc_rating != vals['name']:
                        raise UserError(_("There is already ECGC rating for this %s") % (country_id.name))
                    country_id.write({"ecgc_rating":vals['name']})
        return super(ecgc_rating, self).create(vals)

    def write(self, vals):
        if 'ecgc_rating_line' in vals and vals['ecgc_rating_line']:
            for rec in vals['ecgc_rating_line']:
                if rec[2] != False:
                    country_id = self.env['res.country'].browse(rec[2]['country_id'])
                    if type(rec[1]) != str:
                        line_id = self.env['ecgc.rating.line'].browse(rec[1])
                        line_id.country_id.ecgc_rating = False
                    if country_id.ecgc_rating != False and country_id.ecgc_rating != self.name:
                        raise UserError(_("There is already ECGC rating for this %s") % (country_id.name))
                    country_id.write({"ecgc_rating": self.name})
        return super(ecgc_rating, self).write(vals)

class EcgcRatingLine(models.Model):
    _name = "ecgc.rating.line"
    _description = 'ecgc_rating_line'

    ecgc_rating_id = fields.Many2one('ecgc.rating', 'ECGC Rating')
    country_id = fields.Many2one('res.country', 'Country ')

class ecgc_premium_rate(models.Model):
    _name = "ecgc.premium.rate"
    _description = 'ecgc_premium_rate'
    
    ecgc_rating_id = fields.Many2one('ecgc.rating', ' ECGC Rating/Class',help=" ECGC Rating/Classification such as A1, A2, B1, B2 etc.")
    payment_term_id = fields.Many2one('account.payment.term', 'Payment Term')
    rate = fields.Float('Rate (%)', digits=(16, 3), help="ECGC Premium rate the percentage of the invoice value including, Freight, Terminal Handling charges and all other expenses")
    
class terminal_handling_charges(models.Model):
    _name = "terminal.handling.charges"
    _description = 'terminal_handling_charges'
    
    name = fields.Char('Name',required=True)
    port_of_loading_id = fields.Many2one('ports', 'Port of Loading')
    point_of_stuffing_id = fields.Many2one('ports', 'Point of Stuffing')
    expense_id = fields.Many2one('product.product', 'Expense Name')
    terminal_charges_line = fields.One2many('terminal.charges', 'terminal_id', 'Terminal Charges')
    
class terminal_charges(models.Model):
    _name = "terminal.charges"
    _description = 'terminal_charges'
    
    terminal_id = fields.Many2one('terminal.handling.charges', 'Terminal Charges')
    container_type = fields.Many2one('container.type','Container Type ')
    price = fields.Float('Price ')

class empty_trailer_cost(models.Model):
    _name = "empty.trailer.cost"
    _description = 'empty_trailer_cost'
    
    name = fields.Char('Name',required=True)
    port_of_loading_id = fields.Many2one('ports', 'Dry/ICD Port')
    place_of_stuffing_id = fields.Many2one('ports', 'Stuffing Point')
    expense_id = fields.Many2one('product.product', 'Expense Name')
    empty_cost_line = fields.One2many('empty.cost', 'empty_cost_id', 'Empty Cost')
    
class empty_cost(models.Model):
    _name = "empty.cost"
    _description = 'empty_cost'
    
    empty_cost_id = fields.Many2one('empty.trailer.cost', 'Cost')
    container_type = fields.Many2one('container.type','Container Type ')
    qty = fields.Float('From Capacity (Ton) ')
    to_qty = fields.Float('To Capacity (Ton) ')
    price = fields.Float('Price ')
    
    
class health_certificate_charges(models.Model):
    _name = "health.certificate.charges"
    _description = 'health_certificate_charges'
    
    name = fields.Char('Name',required=True)
    international_region_id = fields.Many2many('internation.zone', 'health_region_rel','health_id','region_id', string='International Zone ')
    # international_region_id = fields.Many2one('internation.zone', 'International Region ')
    expense_id = fields.Many2one('product.product', 'Expense Name')
    health_certi_charges_line = fields.One2many('health.charges', 'health_charges_id', 'Health Charges')
    health_certi_country_line = fields.One2many('health.certi.country.line', 'health_certi_id', 'Health Country Line')

# @api.onchange('international_region_id')
    # def onchange_international_region_id(self):
    #     values = []
    #     for rec in self.health_certi_country_line:
    #         rec.unlink()
    #     if self.international_region_id:
    #         values = []
    #         for region in self.international_region_id:
    #             if region.international_country_ids:
    #                 for country in region.international_country_ids:
    #                     values.append((0,0,{
    #                                     'country_id' : country.country_name.id,
    #                                     }))
    #         self.update({'health_certi_country_line':values})
    
    
    @api.onchange('international_region_id')
    def onchange_international_region_id(self):
        values = []
        # self.update({'health_certi_country_line': ''}) #commented by kajal
        if self.international_region_id:
            values = []
            for region in self.international_region_id:
                if region.international_country_ids:
                    for country in region.international_country_ids:
                        values.append((0,0,{
                                        'country_id' : country.country_name.id,
                                        }))

            self.update({'health_certi_country_line':values})

    def load_country(self):
        health_certi_country_obj = self.env['health.certi.country.line']
        for rec in self.health_certi_country_line:
            rec.unlink()
        if self.international_region_id:
            for region in self.international_region_id:
                if region.international_country_ids:
                    for country in region.international_country_ids:
                        health_certi_country_obj.create({'health_certi_id':self.id,
                                               'country_id':country.country_name.id,
                                               })

class health_charges(models.Model):
    _name = "health.charges"
    _description = 'health_charges'
    
    health_charges_id = fields.Many2one('health.certificate.charges', 'Health Charges')
    amt_from = fields.Float('From Amount ')
    amt_to = fields.Float('To Amount ')
    price = fields.Float('Price ')
    
    
class HealthCertiCountryLine(models.Model):
    _name = "health.certi.country.line"
    _description = 'HealthCertiCountryLine'
    
    health_certi_id = fields.Many2one('health.certificate.charges', 'Health certificate Charges')
    country_id = fields.Many2one('res.country', 'Country ')
    
    
    
class insurance(models.Model):
    _name = "insurance"
    _description = 'Insurance'
    
    name = fields.Char('Name',required=True)
    insurance = fields.Float('Insurance (%)',required=True,digits=('16', 5),help="Insurance rate the percentage of the invoice value including, Freight, Terminal Handling charges and all other expenses")
    expense_id = fields.Many2one('product.product', 'Expense Name')

class ports(models.Model):
    _inherit = 'ports'
    _description = 'Ports'

    export_expense_line = fields.One2many('export.expense', 'export_expense_id', 'Export Expenses')
    is_stuffing_point = fields.Boolean('Is Stuffing Point ')
    is_dry_port = fields.Boolean('Is Dry/ICD Port ')
    code = fields.Char('Code')
    
    
    @api.onchange('country_id')
    def onchange_country_id(self):
        values = []
        if self.export_expense_line:
            for ex in self.export_expense_line:
                ex.unlink()
        if self.country_id:
            for expense in self.country_id.country_export_expense_line:
                values.append((0,0,{
                                'expense_id' : expense.expense_id.id,
                                'price' : expense.price,
                                }))

            self.update({'export_expense_line':values})


class export_expense(models.Model):
    _name = "export.expense"
    _description = 'Export Expense'
    
    export_expense_id = fields.Many2one('ports', 'Export Expenses')
    country_id = fields.Many2one('res.country', 'Country Id')
    expense_id = fields.Many2one('product.product','Expense')
    price = fields.Float('Price')
    currency=fields.Many2one('res.currency',"Currency")
    # point_of_stuffing_id = fields.Many2one('ports', 'Point of Stuffing')
    
    @api.onchange("expense_id")
    def onchange_price(self):
        if self.expense_id:
            self.price = self.expense_id.standard_price
    
    
class export_document(models.Model):
    _name = "export.document"
    _description = 'Export Document'
    
    name = fields.Char('Name',required=True)
    
    
    
class country_export_document(models.Model):
    _name = "country.export.document"
    _description = 'Country Export Document'

    export_document_id = fields.Many2one('export.document', 'Document Name')
    country_id = fields.Many2one('res.country', 'Country Id')
    copies = fields.Integer('Copies',default=1)


class TransitDuration(models.Model):
    _name = "transit.duration"
    _description = 'Transit Duration'

    origin_port_id = fields.Many2one('ports', 'Origin Port')
    dest_port_id = fields.Many2one('ports', 'Destination Port')
    transit_days = fields.Float('Transit Days')

class AccountIncoterms(models.Model):
    _inherit = 'account.incoterms'

    code = fields.Char(
        'Code', size=16, required=True,
        help="Incoterm Standard Code")

class AccountPaymentTerm(models.Model):
    _inherit = 'account.payment.term'

    export_payment_term = fields.Boolean('Exports Payment Term', readonly=True, help="This payment term will be applicable only in exports.")

class ServiceType(models.Model):
    _name = "service.type"
    _description = 'Service Type'

    service = fields.Many2one('product.product', string='Service')
    name = fields.Char(string='Service Type')
    weight_factor_type = fields.Selection([('on_cbcm', 'On Cubic Centimeter'), ('on_cbm', 'On Cubic Meter')], string='Weight Factor Type', default='on_cbcm', help="Choose which kind of weight factor you wants to implement. If you Choose on Cubic centimeter then weight factor can be like 5000, if on Cubic Meter then weight factor be like 167")
    weight_factor = fields.Float(string='Weight Factor')
    full_container_service = fields.Boolean(string="Is full Container Service")
    email_partner_ids = fields.Many2many('res.partner', 'service_type_email_ids', 'service_type_id', 'partner_id', string='Price Request Email Ids')
