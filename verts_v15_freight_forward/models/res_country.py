# -*- coding: utf-8 -*-
# Copyright 2021 Verts Services India Pvt Ltd.
# http://www.verts.co.in

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, AccessError,ValidationError
from datetime import date,datetime,timedelta
import base64
import xlrd
from io import StringIO, BytesIO



class res_country(models.Model):
    _inherit = "res.country"

    def _ecgc_rating(self):
        for rec in self:
            if rec.ecgc_rating:
                rating_id = self.env['ecgc.rating'].search([('name','=',rec.ecgc_rating)])
                self.ecgc_rating_id = rating_id
        return self.ecgc_rating_id

    ecgc_rating_id = fields.Many2one('ecgc.rating', compute='_ecgc_rating',string='ECGC Rating/Classification ')
    country_export_expense_line = fields.One2many('export.expense', 'country_id', 'Export Expenses')
    country_export_document_line = fields.One2many('country.export.document', 'country_id', 'Export Documents')
    ecgc_rating= fields.Char('ECGC Rating/Classification')
    fumigation_lines = fields.One2many('fumigation.lines', 'country_id', 'Fumigation Lines')
    schedule_lines = fields.One2many('country.schedule.line', 'country_id', 'Schedule Lines')
 
    
    load_state_values = fields.Binary('Excelsheet(State Values)')
    load_export_expense_values = fields.Binary('Excelsheet(Expense Values)',help='Sheet Example\n Product Code --> 21745-1 \nCurrency --> INR')
    load_export_doc_values = fields.Binary('Excelsheet(Doc Values)')
    load_fumigation_values = fields.Binary('Excelsheet(Fumigation Values)')
    load_schedule_values = fields.Binary('ExcelsheetSchedule Values')
    
    
#-----------Coded by Daud-------#
    def upload_state(self):
        '''method used for import states via sheet'''
    #------files uploded-------#
        data_decode = self.load_state_values
    #------files uploded-------#
    
    #------If files not uploded-----#
        if not data_decode:
            raise UserError(_('Please Choose The File!'))
    #------If files not uploded-----#
    
    #------Sheet Compiling Process----#
        val = base64.decodestring(data_decode)
        fp = BytesIO()
        fp.write(val)
        wb = xlrd.open_workbook(file_contents=fp.getvalue())
        wb.sheet_names()
        sheet_name = wb.sheet_names()
        sh = wb.sheet_by_name(sheet_name[0])
        n_rows = sh.nrows
    #------Sheet Compiling Process----#
    
    #------Loop for data Importing----#
        for row in range(1, n_rows):
            name = ''
            code = ''
        #-----Create data----#
            if sh.row_values(row)[0] and sh.row_values(row)[1]:
                name = str(sh.row_values(row)[0])
                code = str(sh.row_values(row)[1])
                if name and code:
                    self.env['res.country.state'].create({
                                                       'country_id':self.id,
                                                       'name':name,
                                                       'code':code,
                                                        })
        #-----Create data----#
        
    #------Loop for data Importing----#
    
    #------------Return Success Alert-------#
        return({
               'effect': {
               'fadeout': 'slow',
               'message': "Successfully State Import",
               'type': 'rainbow_man',
               }
               })
    #------------Return Success Alert-----#
    
    
    
    def upload_export_expense(self):
        lst_product =[]
        l='verts'
        data_decode = self.load_export_expense_values
        currency_pool = self.env['res.currency']
        product_pool = self.env['product.product']
        if not data_decode:
            raise UserError(_('Please Choose The File!'))
        val = base64.decodestring(data_decode)
        fp = BytesIO()
        fp.write(val)
        wb = xlrd.open_workbook(file_contents=fp.getvalue())
        wb.sheet_names()
        sheet_name = wb.sheet_names()
        sh = wb.sheet_by_name(sheet_name[0])
        n_rows = sh.nrows
        for row in range(1, n_rows):
            expense_id = False
            price = 0.0
            currency = False
            product_id = False
            
            if sh.row_values(row)[0]:
                default_code = str(sh.row_values(row)[0])
                product_id = product_pool.search([('default_code', '=', default_code)],limit=1)
                if product_id:
                    product_id = product_id.id
                else:
                    lst_product.append(str(sh.row_values(row)[0]))
             
            if sh.row_values(row)[1]:
                price = str(sh.row_values(row)[1])
                
            if sh.row_values(row)[2]:
                default_currency = sh.row_values(row)[2]
                currency = currency_pool.search([('name', '=', default_currency)],limit=1) 
                currency = currency.id
                    
            l=self.env['export.expense'].create({
                                               'country_id':self.id,
                                               'expense_id':product_id or False,
                                               'price': price or 0.0,
                                               'currency':currency or False,
                                                })
        if lst_product:   
            raise UserError(_('Product code %s not found') % (lst_product))
        
        if l != 'verts':              
            return({
                   'effect': {
                   'fadeout': 'slow',
                   'message': "Successfully Export Expense Import",
                   'type': 'rainbow_man',
                   }
                   })
        
        

    def upload_export_doc(self):
        data_decode = self.load_export_doc_values
        doc_pool = self.env['export.document']
        if not data_decode:
            raise UserError(_('Please Choose The File!'))
        val = base64.decodestring(data_decode)
        fp = BytesIO()
        fp.write(val)
        wb = xlrd.open_workbook(file_contents=fp.getvalue())
        wb.sheet_names()
        sheet_name = wb.sheet_names()
        sh = wb.sheet_by_name(sheet_name[0])
        n_rows = sh.nrows
        for row in range(1, n_rows):
            export_document_id = False
            copies = 0
            if sh.row_values(row)[0] and sh.row_values(row)[1]:
                doc_ids = doc_pool.search([('name', '=', str(sh.row_values(row)[0]))])
                for doc_id in doc_ids:
                    copies = int(sh.row_values(row)[1])
                    self.env['country.export.document'].create({
                                                       'country_id':self.id,
                                                       'export_document_id':doc_id.id or False,
                                                       'copies':copies or 0,
                                                        })
        return({
               'effect': {
               'fadeout': 'slow',
               'message': "Successfully Export Document Import",
               'type': 'rainbow_man',
               }
               })
        
    def upload_fumigation(self):
        l='verts'
        data_decode = self.load_fumigation_values
        container_pool = self.env['container.type']
        product_pool = self.env['product.product']
        if not data_decode:
            raise UserError(_('Please Choose The File!'))
        val = base64.decodestring(data_decode)
        fp = BytesIO()
        fp.write(val)
        wb = xlrd.open_workbook(file_contents=fp.getvalue())
        wb.sheet_names()
        sheet_name = wb.sheet_names()
        sh = wb.sheet_by_name(sheet_name[0])
        n_rows = sh.nrows
        
        for row in range(1, n_rows):
            container_type_id = False
            alp_dosage = ''
            alp_hours = ''
            alp_price = ''
            alp_charges_id = False               
            mbr_filled_dosage = ''                   
            mbr_filled_hours = ''
            mbr_filled_price = ''
            mbr_filled_id = False
            mbr_empty_dosage = ''
            mbr_empty_hours = ''
            mbr_empty_price = ''
            mbr_empty_charges_id = False
            
            if sh.row_values(row)[0]:   
                container_type_id = container_pool.search([('name', '=', str(sh.row_values(row)[0]))],limit=1)
                container_type_id=container_type_id.id
            if sh.row_values(row)[1]:   
                alp_dosage = str(sh.row_values(row)[1])
            if sh.row_values(row)[2]:
                alp_hours = str(sh.row_values(row)[2])
            if sh.row_values(row)[3]:
                alp_price = str(sh.row_values(row)[3])
            if sh.row_values(row)[4]:
                alp_charges_id = product_pool.search([('default_code', '=', str(sh.row_values(row)[4]))],limit=1)
                alp_charges_id=alp_charges_id.id
            if sh.row_values(row)[5]:
                mbr_filled_dosage = str(sh.row_values(row)[5])
            if sh.row_values(row)[6]:
                mbr_filled_hours = str(sh.row_values(row)[6])
            if sh.row_values(row)[7]:
                mbr_filled_price = str(sh.row_values(row)[7])
            if sh.row_values(row)[8]:
                mbr_filled_id = product_pool.search([('default_code', '=', str(sh.row_values(row)[8]))],limit=1)
                mbr_filled_id=mbr_filled_id.id
            if sh.row_values(row)[9]:
                mbr_empty_dosage = str(sh.row_values(row)[9])
            if sh.row_values(row)[10]:
                mbr_empty_hours = str(sh.row_values(row)[10])
            if sh.row_values(row)[11]:
                mbr_empty_price = str(sh.row_values(row)[11])
            if sh.row_values(row)[12]:
                mbr_empty_charges_id = product_pool.search([('default_code', '=', str(sh.row_values(row)[12]))],limit=1)
                mbr_empty_charges_id =mbr_empty_charges_id.id
            if sh.row_values(row)[0] or sh.row_values(row)[1] or sh.row_values(row)[2] or sh.row_values(row)[3] or sh.row_values(row)[4] or sh.row_values(row)[5] or sh.row_values(row)[6] or sh.row_values(row)[7] or sh.row_values(row)[8] or sh.row_values(row)[9] or sh.row_values(row)[10] or sh.row_values(row)[11] or sh.row_values(row)[12]:
                
                l=self.env['fumigation.lines'].create({
                                                   'country_id':self.id,
                                                   'container_type_id':container_type_id or False,
                                                   'alp_dosage':alp_dosage or False,
                                                    'alp_hours':alp_hours or False,
                                                    'alp_price':alp_price or False,
                                                    'alp_charges_id':alp_charges_id or False,
                                                     'mbr_filled_dosage':mbr_filled_dosage or False,
                                                      'mbr_filled_hours':mbr_filled_hours or False,
                                                       'mbr_filled_price':mbr_filled_price or False,
                                                        'mbr_filled_id':mbr_filled_id or False,
                                                         'mbr_empty_dosage':mbr_empty_dosage or False,
                                                          'mbr_empty_hours':mbr_empty_hours or False,
                                                          'mbr_empty_price':mbr_empty_price or False,
                                                           'mbr_empty_charges_id':mbr_empty_charges_id or False,
                                                    })
             
         
        if l != 'verts':       
            return({
                   'effect': {
                   'fadeout': 'slow',
                   'message': "Successfully Fumigation Import",
                   'type': 'rainbow_man',
                   }
                   })    
        
    def upload_schedule(self):
        data_decode = self.load_schedule_values
        schedule_pool = self.env['common.schedule']
        if not data_decode:
            raise UserError(_('Please Choose The File!'))
        val = base64.decodestring(data_decode)
        fp = BytesIO()
        fp.write(val)
        wb = xlrd.open_workbook(file_contents=fp.getvalue())
        wb.sheet_names()
        sheet_name = wb.sheet_names()
        sh = wb.sheet_by_name(sheet_name[0])
        n_rows = sh.nrows
        for row in range(1, n_rows):
            schedule_id = False
            if sh.row_values(row)[0]:
                schedule_ids = schedule_pool.search([('name', '=', str(sh.row_values(row)[0]))])
                for schedule_id in schedule_ids:
                    self.env['country.schedule.line'].create({
                                                       'country_id':self.id,
                                                       'schedule_id':schedule_id.id or False,
                                                       'report_at_time':schedule_id.report_at_time or False,
                                                        'req_form':schedule_id.req_from or False,
                                                        'country_specific':schedule_id.country_specific or False,
                                                        'port_of_loading_specific':schedule_id.port_of_loading_specific or False,
                                                        })
        return({
               'effect': {
               'fadeout': 'slow',
               'message': "Successfully Schedule Import",
               'type': 'rainbow_man',
               }
               })
                        
        
        

class FumigationLines(models.Model):
    _name = "fumigation.lines"
    _description = 'Fumigation Lines'

    container_type_id = fields.Many2one('container.type',string='Container Type')
    alp_dosage = fields.Char(string="ALP Dosage ")
    alp_hours = fields.Char(string="ALP Hours ")
    alp_price = fields.Char(string="ALP Price ")

    mbr_empty_dosage = fields.Char(string="MBR Empty Dosage ")
    mbr_empty_hours = fields.Char(string="MBR Empty Dosage Hours")
    mbr_empty_price = fields.Char(string="MBR Empty Dosage Price")
    mbr_filled_dosage = fields.Char(string="MBR Filled Dosage")
    mbr_filled_hours = fields.Char(string="MBR Filled Dosage Hours")
    mbr_filled_price = fields.Char(string="MBR Filled Dosage Price")

    alp_charges_id = fields.Many2one('product.product',string='ALP Charges On')
    mbr_empty_charges_id = fields.Many2one('product.product',string='MBR Empty Charges On')
    mbr_filled_id = fields.Many2one('product.product',string='MBR Filled Charges On')
    country_id = fields.Many2one('res.country',string='Country ID')

class CountryScheduleLine(models.Model):
    _name = "country.schedule.line"
    _description = 'Country Schedule Line'

    country_id =  fields.Many2one('res.country', string="Schedule Name(Country)")
    schedule_id =  fields.Many2one('common.schedule', string="Schedule Name")
    report_at_time = fields.Selection([('pre_shipment', 'Pre Shipment'), ('post_shipment', 'Post Shipment')], string='Report at Time')
    req_from = fields.Selection([('other', 'Other'), ('self', 'Self')], string='Requirement From')
    country_specific = fields.Boolean(string="Country Specific")
    port_of_loading_specific = fields.Boolean(string="Port of Loading Specific")

    @api.onchange('schedule_id')
    def onchange_schedule_id(self):
        if self.schedule_id:
            self.report_at_time = self.schedule_id.report_at_time
            self.req_from = self.schedule_id.req_from
            self.country_specific = self.schedule_id.country_specific
            self.port_of_loading_specific = self.schedule_id.port_of_loading_specific


class employee_internation_region(models.Model):
    _inherit = "internation.zone"

    def write(self, vals):
        res = super(employee_internation_region, self).write(vals)
        if res:
            health_ids = "SELECT health_id FROM health_region_rel WHERE region_id='%s'" \
                              % (self.id)
            self._cr.execute(health_ids)
            health = self._cr.fetchall()
            for hlth in health:
                health_obj = self.env['health.certificate.charges'].search([('id','=',hlth[0])])
                health_obj.load_country()