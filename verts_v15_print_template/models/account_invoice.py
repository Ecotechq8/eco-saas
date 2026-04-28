# -*- coding: utf-8 -*-
import odoo
import sys
import datetime
from odoo import fields, models, api, tools,_


from odoo import tools
from odoo.tools.misc import formatLang
from odoo.tools import float_is_zero, float_compare

import time
from odoo.tools import amount_to_text_en
from odoo.report import report_sxw

import inflect
import textwrap

class Number2Words(object):

        def __init__(self):
            '''Initialise the class with useful data'''

            self.wordsDict = {1: 'one', 2: 'two', 3: 'three', 4: 'four', 5: 'five', 6: 'six', 7: 'seven',
                              8: 'eight', 9: 'nine', 10: 'ten', 11: 'eleven', 12: 'twelve', 13: 'thirteen',
                              14: 'fourteen', 15: 'fifteen', 16: 'sixteen', 17: 'seventeen',
                              18: 'eighteen', 19: 'nineteen', 20: 'twenty', 30: 'thirty', 40: 'forty',
                              50: 'fifty', 60: 'sixty', 70: 'seventy', 80: 'eighty', 90: 'ninty' }

            self.powerNameList = ['thousand', 'lakh', 'crore']


        def convertNumberToWords(self, number,currency_id):
            # Check if there is decimal in the number. If Yes process them as paisa part.
            formString = '%.2f' %(number)
            if formString.find('.') != -1:
                withoutDecimal, decimalPart = formString.split('.')
                #paisaPart =  str(round(float(formString), 2)).split('.')[1]
                p = inflect.engine()
                inPaisa=p.number_to_words(decimalPart)
                #inPaisa = self._formulateDoubleDigitWords(paisaPart)

                formString, formNumber = str(withoutDecimal), int(withoutDecimal)
            else:
                # Process the number part without decimal separately
                formNumber = int(number)
                inPaisa = None

            if not formNumber:
                return 'zero'

            self._validateNumber(formString, formNumber)

            inRupees = self._convertNumberToWords(formString)
            if currency_id.name == 'INR':
                if inPaisa and inPaisa != 'zero':
                    return '%s and %s Paise Only' % (inRupees.title(), inPaisa.title())
                else:
                    return '%s Only' % inRupees.title()
            elif currency_id.name == 'USD':
                if inPaisa and inPaisa != 'zero':
                    return 'Dollars %s and %s Cents Only' % (inRupees.title(), inPaisa.title())
                else:
                    return 'Dollars %s Only' % inRupees.title()
            elif currency_id.name == 'EUR':
                if inPaisa and inPaisa != 'zero':
                    return 'EURO %s and %s Cents Only' % (inRupees.title(), inPaisa.title())
                else:
                    return 'EURO %s Only' % inRupees.title()
            


        def _validateNumber(self, formString, formNumber):

            assert formString.isdigit()

            # Developed to provide words upto 999999999
            if formNumber > 999999999 or formNumber < 0:
                raise AssertionError('Out Of range')


        def _convertNumberToWords(self, formString):

            MSBs, hundredthPlace, teens = self._getGroupOfNumbers(formString)

            wordsList = self._convertGroupsToWords(MSBs, hundredthPlace, teens)

            return ' '.join(wordsList)


        def _getGroupOfNumbers(self, formString):

            hundredthPlace, teens = formString[-3:-2], formString[-2:]

            msbUnformattedList = list(formString[:-3])

            #---------------------------------------------------------------------#

            MSBs = []
            tempstr = ''
            for num in msbUnformattedList[::-1]:
                tempstr = '%s%s' % (num, tempstr)
                if len(tempstr) == 2:
                    MSBs.insert(0, tempstr)
                    tempstr = ''
            if tempstr:
                MSBs.insert(0, tempstr)

            #---------------------------------------------------------------------#

            return MSBs, hundredthPlace, teens


        def _convertGroupsToWords(self, MSBs, hundredthPlace, teens):

            wordList = []

            #---------------------------------------------------------------------#
            if teens:
                teens = int(teens)
                tensUnitsInWords = self._formulateDoubleDigitWords(teens)
                if tensUnitsInWords:
                    wordList.insert(0, tensUnitsInWords)
    
            #---------------------------------------------------------------------#
            if hundredthPlace:
                hundredthPlace = int(hundredthPlace)
                if not hundredthPlace:
                    # Might be zero. Ignore.
                    pass
                else:
                    hundredsInWords = '%s hundred' % self.wordsDict[hundredthPlace]
                    wordList.insert(0, hundredsInWords)
    
            #---------------------------------------------------------------------#
            if MSBs:
                MSBs.reverse()
    
                for idx, item in enumerate(MSBs):
                    inWords = self._formulateDoubleDigitWords(item)
                    if inWords:
                        inWordsWithDenomination = '%s %s' % (inWords, self.powerNameList[idx])
                        wordList.insert(0, inWordsWithDenomination)
    
            #---------------------------------------------------------------------#
            return wordList


        def _formulateDoubleDigitWords(self, doubleDigit):

            if not int(doubleDigit):
                # Might be zero. Ignore.
                return None
            elif self.wordsDict.has_key(int(doubleDigit)):
                # Global dict has the key for this number
                tensInWords = self.wordsDict[int(doubleDigit)]
                return tensInWords
            else:
                doubleDigitStr = str(doubleDigit)
                tens, units = int(doubleDigitStr[0])*10, int(doubleDigitStr[1])
                tensUnitsInWords = '%s %s' % (self.wordsDict[tens], self.wordsDict[units])
                return tensUnitsInWords
            
            

class AccountInvoice(models.Model):
    _inherit = 'account.move'
    
    @api.onchange('partner_id', 'company_id')
    def _onchange_partner_id(self):
        result = super(AccountInvoice, self)._onchange_partner_id()
        if self.partner_id:
            self.report_template_id = self.partner_id.report_template_id.id or False
        return result

    @api.model
    def _default_report_template(self):
        report_obj = self.env['ir.actions.report']
        report_id = report_obj.search([('model', '=', 'account.move'), ('report_name' ,'=', 'verts_v15_print_template.report_invoice_template_custom')])
        if report_id:
            report_id = report_id[0]
        else:
            report_id = report_obj.search([('model', '=', 'account.move')])[0]
        return report_id


    @api.depends('partner_id')
    def _default_report_template1(self):
        report_obj = self.env['ir.actions.report']
        report_id = report_obj.search([('model', '=', 'account.move'), ('report_name' ,'=', 'verts_v15_print_template.report_invoice_template_custom')])
        if report_id:
            report_id = report_id[0]
        else:
            report_id = report_obj.search([('model', '=', 'account.move')])[0]
        if self.report_template_id and self.report_template_id.id < report_id.id:
            self.write({'report_template_id': report_id and report_id.id or False})
            #self.report_template_id = report_id and report_id.id or False
        self.report_template_id = self.partner_id.report_template_id or False
        self.report_template_id1 = report_id and report_id.id or False


    def invoice_print(self):
        """ Print the invoice and mark it as sent, so that we can see more
            easily the next step of the workflow
        """
        self.ensure_one()
        self.sent = True
        res = super(AccountInvoice, self).invoice_print()
        if self.report_template_id or self.partner_id and self.partner_id.report_template_id or self.company_id and self.company_id.report_template_id:
            report_name = self.report_template_id and self.report_template_id.report_name or self.partner_id and self.partner_id.report_template_id.report_name or self.company_id and self.company_id.report_template_id.report_name
            report = self.env['report'].get_action(self, self.report_template_id and self.report_template_id.report_name or self.partner_id and self.partner_id.report_template_id.report_name or self.company_id and self.company_id.report_template_id.report_name)
            report.update({'report_name': 'account.report_invoice'})
            return report
        return res


    def _get_street(self, partner):
        self.ensure_one()
        res = {}
        address = ''
        if partner.street:
            address = "%s" % (partner.street)
        if partner.street2:
            address += ", %s" % (partner.street2)
        reload(sys)
        sys.setdefaultencoding("utf-8")
        html_text= str(tools.plaintext2html(address,container_tag=True))
        data = html_text.split('p>')
        if data:
            return data[1][:-2]
        return False
    

    def _get_address_details(self, partner):
        self.ensure_one()
        res = {}
        address = ''
        if partner.city:
            address = "%s" % (partner.city)
        if partner.state_id.name:
            address += ", %s" % (partner.state_id.name)
        if partner.zip:
            address += ", %s" % (partner.zip)
        if partner.country_id.name:
            address += ", %s" % (partner.country_id.name)
        reload(sys)
        sys.setdefaultencoding("utf-8")
        html_text= str(tools.plaintext2html(address,container_tag=True))
        data = html_text.split('p>')
        if data:
            return data[1][:-2]
        return False


    def _get_origin_date(self, origin):
        self.ensure_one()
        res = {}
        if self.type in ('in_invoice','in_refund'):
            sale_obj = self.env['purchase.order']
        else:
            sale_obj = self.env['sale.order']
        lang = self._context.get("lang")
        lang_obj = self.env['res.lang']
        ids = lang_obj.search([("code", "=", lang or 'en_US')])
        sale = sale_obj.search([('name', '=', origin)])
        if sale:
            timestamp = datetime.datetime.strptime(sale.date_order, tools.DEFAULT_SERVER_DATETIME_FORMAT)
            ts = odoo.fields.Datetime.context_timestamp(self, timestamp)
            n_date = ts.strftime(ids.date_format).decode('utf-8')
            if sale:
                return n_date
        return False


    def _get_invoice_date(self):
        self.ensure_one()
        res = {}
        sale_obj = self.env['sale.order']
        lang = self._context.get("lang")
        lang_obj = self.env['res.lang']
        ids = lang_obj.search([("code", "=", lang or 'en_US')])
        if self.date_invoice:
            timestamp = datetime.datetime.strptime(self.date_invoice, tools.DEFAULT_SERVER_DATE_FORMAT)
            ts = odoo.fields.Datetime.context_timestamp(self, timestamp)
            n_date = ts.strftime(ids.date_format).decode('utf-8')
            if self:
                return n_date
        return False


    def _get_invoice_due_date(self):
        self.ensure_one()
        res = {}
        sale_obj = self.env['sale.order']
        lang = self._context.get("lang")
        lang_obj = self.env['res.lang']
        ids = lang_obj.search([("code", "=", lang or 'en_US')])
        if self.date_due:
            timestamp = datetime.datetime.strptime(self.date_due, tools.DEFAULT_SERVER_DATE_FORMAT)
            ts = odoo.fields.Datetime.context_timestamp(self, timestamp)
            n_date = ts.strftime(ids.date_format).decode('utf-8')
            if self:
                return n_date
        return False


    def _get_tax_amount(self, amount,payment=None):
        self.ensure_one()
        res = {}
        currency = self.currency_id or self.company_id.currency_id
        res = formatLang(self.env, amount, currency_obj=currency)
        #for payment in self.payment_move_line_ids:
        if payment != None:
            if self.type in ('out_invoice', 'in_refund'):
                amount = sum([p.amount for p in payment.matched_debit_ids if p.debit_move_id in self.move_id.line_ids])
                amount_currency = sum([p.amount_currency for p in payment.matched_debit_ids if p.debit_move_id in self.move_id.line_ids])
            elif self.type in ('in_invoice', 'out_refund'):
                amount = sum([p.amount for p in payment.matched_credit_ids if p.credit_move_id in self.move_id.line_ids])
                amount_currency = sum([p.amount_currency for p in payment.matched_credit_ids if p.credit_move_id in self.move_id.line_ids])
            # get the payment value in invoice currency
            if payment.currency_id and payment.currency_id == self.currency_id:
                amount_to_show = amount_currency
            else:
                amount_to_show = payment.company_id.currency_id.with_context(date=payment.date).compute(amount, self.currency_id)
            if float_is_zero(amount_to_show, precision_rounding=self.currency_id.rounding):
                return res
            res = formatLang(self.env, amount_to_show, currency_obj=currency)
        return res

    report_template_id1 = fields.Many2one('ir.actions.report' , string="Invoice Template", compute='_default_report_template1', help="Please select Template report for Invoice", domain=[('model', '=', 'account.move')])
    report_template_id = fields.Many2one('ir.actions.report' , string="Invoice Template", help="Please select Template report for Invoice", domain=[('model', '=', 'account.move')])
