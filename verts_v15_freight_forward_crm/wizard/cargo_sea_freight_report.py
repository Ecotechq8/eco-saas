import io
import base64
from odoo import models, fields
from odoo.tools.misc import xlsxwriter

class CargoSeaFreightReport(models.TransientModel):
    _name = 'cargo.sea.freight.report'
    _description = 'Cargo Sea Freight Report Wizard'

    date_from = fields.Date(string='From Date', required=True)
    date_to = fields.Date(string='To Date', required=True)
    currency_type = fields.Selection([
        ('fc', 'Foreign Currency'),
        ('dc', 'Domestic Currency')
    ], string='Currency Type', default='fc')

    def generate_excel_report(self):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('CSR - SEA')

        # Formats
        bold = workbook.add_format({'bold': True, 'align': 'center'})
        header_format = workbook.add_format({'bold': True, 'align': 'center', 'bg_color': '#D9E1F2', 'border': 1})
        red_bold = workbook.add_format({'bold': True, 'font_color': 'red'})

        # Title
        sheet.merge_range('B1:P1', 'Sea Freight Export or Import / Land Freight import or export / courier import or export - all have same format', bold)

        # Report Period
        sheet.write('C3', 'Cargo Sales Report for period :', bold)

        # Currency
        sheet.write('C5', 'Currency', red_bold)
        sheet.write('D5', ':')

        # Headers
        headers = [
            'Customer', 'Vendor', 'Freight Type', 'Doc Ref#', 'FROM', 'TO',
            'No of Pcs', 'Gross Weight Kgs', 'Vol CBM', 'Total Receivable', 'Total Payable', 'Profit'
        ]
        for col, header in enumerate(headers, start=2):
            sheet.write(6, col, header, header_format)

        # Freight Types
        freight_types = [('LCL', 'B/L#'), ('FCL', 'WB#'), ('LTL', ''), ('FTL', ''), ('COU', ''), ('B.Bulk', '')]
        row = 7
        for freight in freight_types:
            sheet.write(row, 4, freight[0])
            sheet.write(row, 5, freight[1])
            sheet.write(row, 6, 'origin')
            sheet.write(row, 7, 'destination')
            row += 1

        # Totals
        sheet.write(row + 1, 10, 0)
        sheet.write(row + 1, 11, 0)
        sheet.write(row + 1, 12, 0)

        # Notes
        sheet.write(row + 4, 2, '* Doc Ref # here is B/L #, Waybill# for land or Courier Waybill# for couriers shipment')
        sheet.write(row + 5, 2, 'Customer - receivable account name')
        sheet.write(row + 6, 2, 'Vendor - Payable account name')
        sheet.write(row + 8, 2, 'one customer receivable can have multiple vendor like - overseas agent, Shipping line or destination customs broker - please suggest how to manage this.')

        workbook.close()
        output.seek(0)
        report_data = base64.b64encode(output.read())
        output.close()

        # Create Attachment (Private)
        attachment = self.env['ir.attachment'].create({
            'name': 'Cargo_Sea_Freight_Report.xlsx',
            'type': 'binary',
            'datas': report_data,
            'res_model': 'cargo.sea.freight.report',
            'res_id': self.id,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        })

        # Return URL for Download
        download_url = f'/web/content/{attachment.id}?download=true'

        return {
            'type': 'ir.actions.act_url',
            'url': download_url,
            'target': 'self',
        }
