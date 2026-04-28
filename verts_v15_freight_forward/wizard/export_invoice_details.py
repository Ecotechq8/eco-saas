# -*- coding: utf-8 -*-
# Copyright 2021 Verts Services India Pvt Ltd.
# http://www.verts.co.in

from odoo import models, fields, api
from datetime import datetime, timedelta
import xlwt
from odoo import api, fields, models, _
import base64
from io import StringIO, BytesIO
from odoo.exceptions import UserError, RedirectWarning, ValidationError


class export_invoice_details(models.TransientModel):
    _name = 'export.invoice.details'
    _description = 'export Invoice Details'

    from_date = fields.Date('From Date')
    to_date = fields.Date('To Date')

    # account.invoice not found in base module in version  14
    # invoice_no = fields.Many2one('account.invoice', string='Invoice Number')

    def report_print(self):
        if self.from_date > self.to_date:
            raise ValidationError(_('From Date should be less then To date'))

        string = 'status.xls'
        wb = xlwt.Workbook(encoding='utf-8')
        worksheet = wb.add_sheet(string)
        style_value = xlwt.easyxf('font: bold on ,colour_index black;')
        style_header = xlwt.easyxf('pattern: pattern solid;')
        filename = 'Export Invoice Details.xls'
        worksheet.write_merge(0, 1, 0, 14, "Export Invoice Details", xlwt.easyxf(
            'font: height 300, name Arial, colour_index black, bold on, italic off; align: wrap on, vert centre, horiz center;'))

        if self.invoice_no:
            worksheet.write(2, 0, 'INVOICE NO.', style_value)
            worksheet.write(2, 1, 'NOTIFY PARTY ', style_value)
            worksheet.write(2, 2, 'CONSIGNEE ADDRESS  ', style_value)
            worksheet.write(2, 3, 'DESC OF GOOD', style_value)
            worksheet.write(2, 4, 'Amount in Rs', style_value)
            worksheet.write(2, 5, 'INV.USD', style_value)
            worksheet.write(2, 6, 'PORT OF LOADING', style_value)
            worksheet.write(2, 7, 'ETD', style_value)
            worksheet.write(2, 8, 'ETA', style_value)
            worksheet.write(2, 9, 'BALANCE', style_value)
            worksheet.write(2, 10, 'CTNR NO.', style_value)
            worksheet.write(2, 11, 'LINE', style_value)
            worksheet.write(2, 12, 'REMARK', style_value)
            worksheet.write(2, 13, 'PR. Date', style_value)
            invoice = self.invoice_no
            a = 4

            worksheet.write(a, 6, invoice.port_of_loading_id.name or '')
            for val in invoice.invoice_line_ids:
                worksheet.write(a, 0, invoice.number or '')
                worksheet.write(a, 1, invoice.notify_id.name or '')
                worksheet.write(a, 2, invoice.consignee_id.name or '')
                worksheet.write(a, 3, val.product_id.complete_product_name or '')
                worksheet.write(a, 4, val.price_subtotal or '')
                worksheet.write(a, 5, val.price_subtotal/invoice.cur_rate or '')
                a += 1
            a += 1

            b = a + 1
            worksheet.write(b, 4, 'Total Amount(Rs.)', style_header)
            worksheet.write(b+1, 4, invoice.amount_total or '')

            # invoice_obj = self.env['account.invoice'].search(
            #     [('date_invoice', '>=', self.from_date), ('date_invoice', '<=', self.to_date),
            #      ('is_export', '=', True)])
            # for rec in invoice_obj:
            #     if invoice == rec.id:
            #         worksheet.write(a, 1, invoice.notify_id.name or '')
            #         worksheet.write(a, 4, invoice.port_of_loading_id.name or '')
            #         for val in invoice.invoice_line_ids:
            #             worksheet.write(a, 0, invoice.sequence_number_next_prefix or '')
            #             worksheet.write(a, 3, val.price_subtotal or '')
            #             worksheet.write(a, 2, val.product_id.complete_product_name or '')
            #             a += 1
            #         a += 1
            #         b=a+1
            #         worksheet.write(b, 2, 'Total',style_value)
        else:
            worksheet.write(2, 0, 'INVOICE NO.', style_value)
            worksheet.write(2, 1, 'NOTIFY PARTY ', style_value)
            worksheet.write(2, 2, 'CONSIGNEE ADDRESS ', style_value)
            worksheet.write(2, 3, 'DESC OF GOOD', style_value)
            worksheet.write(2, 4, 'Amount in Rs.', style_value)
            worksheet.write(2, 5, 'INV. USD', style_value)
            worksheet.write(2, 6, 'PORT OF LOADING', style_value)
            worksheet.write(2, 7, 'ETD', style_value)
            worksheet.write(2, 8, 'ETA', style_value)
            worksheet.write(2, 9, 'BALANCE', style_value)
            worksheet.write(2, 10, 'CTNR NO.', style_value)
            worksheet.write(2, 11, 'LINE', style_value)
            worksheet.write(2, 12, 'REMARK', style_value)
            worksheet.write(2, 13, 'PR. Date', style_value)
            worksheet.write(2, 14, 'Total Amount(Rs.)', style_value)
            a = 4
            invoice_obj = self.env['account.invoice'].search(
                [('date_invoice', '>=', self.from_date), ('date_invoice', '<=', self.to_date),
                 ('is_export', '=', True)])
            for rec in invoice_obj:

                worksheet.write(a, 6, rec.port_of_loading_id.name or '')
                worksheet.write(a, 14, rec.amount_total or '')
                for val in rec.invoice_line_ids:
                    worksheet.write(a, 0, rec.number or '')
                    worksheet.write(a, 1, rec.notify_id.name or '')
                    worksheet.write(a, 2, rec.consignee_id.name or '')
                    worksheet.write(a, 3, val.product_id.complete_product_name or '')
                    worksheet.write(a, 4, val.price_subtotal or '')
                    worksheet.write(a, 5, val.price_subtotal / rec.cur_rate or '')
                    a += 1
                a += 2

        fp = BytesIO()
        wb.save(fp)
        out = base64.encodestring(fp.getvalue())
        view_report_status_id = self.env['export.invoice.details.view'].create(
            {'excel_file': out, 'file_name': filename})
        return {
            'res_id': view_report_status_id.id,
            'name': 'Report',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'export.invoice.details.view',
            'view_id': False,
            'type': 'ir.actions.act_window',
        }


class export_invoice_details_report_view(models.TransientModel):
    _name = 'export.invoice.details.view'
    _description = 'export Invoice Details View'
    _rec_name = 'excel_file'

    excel_file = fields.Binary('Download report Excel')
    file_name = fields.Char('Excel File', size=64)
