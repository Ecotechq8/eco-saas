from odoo import models
import io
import base64
import xlsxwriter

class AirImportCargoSalesReport(models.TransientModel):
    _name = 'air.import.cargo.sales.report'
    _description = 'Air Import Cargo Sales Report Wizard'

    def generate_excel_report(self):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('CSR Export - Buying Carrier')

        # Header Formatting
        header_format = workbook.add_format({
            'bold': True, 'font_color': 'black', 'bg_color': '#DDEBF7',
            'border': 1, 'align': 'center', 'valign': 'vcenter'
        })
        red_format = workbook.add_format({'font_color': 'red', 'bold': True})
        bold_format = workbook.add_format({'bold': True})

        # Title
        worksheet.merge_range('C2:H2', 'Air Import Cargo Sales Report', bold_format)

        # Report Period
        worksheet.write('C4', 'Cargo Sales Report for period :', bold_format)

        # Currency
        worksheet.write('C5', 'Currency', red_format)
        worksheet.write('D5', ':')

        # Notes
        worksheet.write('I4', '* the from and to dates we select to generate this report should appear eg 1 Jan 2025 to 15 Jan 2025')
        worksheet.write('I5', '* should be able to select to generate report in FC or DC currency')

        # Headers
        headers = [
            'Customer', 'Vendor', 'AWB Date', 'AWB #', 'FROM', 'TO', 'No of Pcs',
            'Gross Weight Kgs', 'Chargeable Weight Kgs', 'Vol CBM', 'Rate KWD',
            'Freight', 'Total Other Charges', 'Total Receivable', 'Total Payable',
            'Profit', 'Airline Code'
        ]

        row = 6
        col = 2  # Starting from Column C
        for idx, header in enumerate(headers):
            worksheet.write(row, col + idx, header, header_format)

        # Footer Notes
        worksheet.write('C17', '* This is a report which is for submitting to airlines, hence only net purchase rates only has to be displayed.')

        # Example Totals Row (Optional: Replace with real data if available)
        worksheet.write('J14', 0)
        worksheet.write('N14', 0)
        worksheet.write('O14', 0)
        worksheet.write('P14', 0)
        worksheet.write('Q14', 0)

        workbook.close()
        output.seek(0)
        excel_data = output.read()

        # Create Attachment
        attachment = self.env['ir.attachment'].create({
            'name': 'Air_Import_Cargo_Sales_Report.xlsx',
            'type': 'binary',
            'datas': base64.b64encode(excel_data),
            'res_model': 'air.import.cargo.sales.report',
            'res_id': self.id,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'new',
        }
