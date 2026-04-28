import io
import base64
from odoo import models
import xlsxwriter

class CargoSalesReport(models.TransientModel):
    _name = 'cargo.sales.report'
    _description = 'Cargo Sales Report'

    def generate_excel_report(self):
        # Create an in-memory output file for the new workbook.
        output = io.BytesIO()

        # Create a workbook and add a worksheet.
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('CSR - SEA')

        # Define formats
        header_format = workbook.add_format({'bold': True, 'align': 'left', 'font_size': 11})
        sub_header_format = workbook.add_format({'bold': True, 'align': 'left', 'font_size': 9})
        table_header_format = workbook.add_format({'bold': True, 'bg_color': '#DDEBF7', 'border': 1, 'align': 'center'})
        normal_format = workbook.add_format({'align': 'left', 'font_size': 9})
        note_format = workbook.add_format({'italic': True, 'font_size': 9})

        # Header lines
        worksheet.write('C4', 'Cargo Sales Report for period :', header_format)
        worksheet.write('C5', 'Currency', header_format)
        worksheet.write('E5', ':', header_format)

        # Sub notes
        worksheet.write('I4', '* the from and to dates we select to generate this report should appear eg 1 Jan 2025 to 15 Jan 2025', sub_header_format)
        worksheet.write('I5', '* should be able to select to generate report in FC or DC currency', sub_header_format)

        # Table headers
        headers = ['Customer', 'Vendor', 'Freight Type', 'Doc Ref#', 'FROM', 'TO', 'No of Pcs', 'Gross Weight Kgs', 'Vol CBM', 'Total Receivable', 'Total Payable', 'Profit']
        for col_num, header in enumerate(headers):
            worksheet.write(6, col_num + 1, header, table_header_format)

        # Freight Type rows
        freight_types = [('LCL', 'B/L#', 'origin', 'destination'),
                         ('FCL', 'WB#', 'origin', 'destination'),
                         ('LTL', '', '', ''),
                         ('FTL', '', '', ''),
                         ('COU', '', '', ''),
                         ('B.Bulk', '', '', '')]

        for row_num, (freight, doc_ref, origin, destination) in enumerate(freight_types, start=7):
            worksheet.write(row_num, 3, freight, normal_format)
            worksheet.write(row_num, 4, doc_ref, normal_format)
            worksheet.write(row_num, 5, origin, normal_format)
            worksheet.write(row_num, 6, destination, normal_format)

        # Total Row
        worksheet.write(13, 10, 0, normal_format)
        worksheet.write(13, 11, 0, normal_format)
        worksheet.write(13, 12, 0, normal_format)

        # Notes
        worksheet.write('C16', '* Doc Ref # here is B/L #, Waybill# for land or Courier Waybill# for couriers shipment', note_format)
        worksheet.write('C17', 'Customer - receivable account name', note_format)
        worksheet.write('C18', 'Vendor - Payable account name', note_format)
        worksheet.write('C20', 'one customer receivable can have multiple vendor like - overseas agent, Shipping line or destination customs broker - please suggest how to manage this.', note_format)

        workbook.close()
        output.seek(0)
        excel_data = output.read()

        attachment = self.env['ir.attachment'].create({
            'name': 'Cargo_Sales_Report.xlsx',
            'type': 'binary',
            'datas': base64.b64encode(excel_data),
            'res_model': 'cargo.sales.report',
            'res_id': self.id,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'new',
        }
