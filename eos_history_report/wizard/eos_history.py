import xlsxwriter
from io import BytesIO
from odoo import models, api

class BalanceHistoryReport(models.AbstractModel):
    _name = 'report.eos_history_report.balance_history_excel_report'
    _inherit = 'report.report_xlsx.abstract'

    # def get_excel_report(self):
    @api.model
    def generate_xlsx_report(self, workbook, data, objs):
        records = self.env['balance.history'].browse(data.get('ids'))

        # Create an in-memory output file for the new workbook
        worksheet = workbook.add_worksheet('Balance History')
        # Define the header format
        header_format = workbook.add_format({'bold': True, 'border': 1})
        # Write the header row
        headers = [
            'Employee', 'Joining Date', 'Total Salary',
            'Date From', 'Date To', 'EOS Segment', 

            "Opening Balance Leave Days","Opening Balance Leave Amount",

            'Leave Monthly','Leave Monthly Value', 

            'Time off request days','Time off request amount', 

            "Ending Balance Leave (Days)","Ending Balance Leave (Amount)",

            'EOS Opening Balance (Days)', 'EOS Opening Balance (Amount)',

            'EOS Allowance (Days)', 'EOS Allowance (Amount)',


            'ESB Paid (Days)', 'ESB Paid (Amount)',
            'ESB Ending Balance (Days)', 'ESB Ending Balance (Amount)',
        ]
        for col_num, header in enumerate(headers):
            worksheet.write(0, col_num, header, header_format)

        # Fetch balance history records
        # records = self.env['balance.history'].search([])
        # Write data rows
        for row_num, record in enumerate(records, start=1):
            worksheet.write(row_num, 0, record.employee.name or '')
            worksheet.write(row_num, 1, record.joining_date.strftime("%Y-%m-%d") or '')
            worksheet.write(row_num, 2, record.total_salary or 0)
            worksheet.write(row_num, 3, record.date_from.strftime("%Y-%m-%d") or '')
            worksheet.write(row_num, 4, record.date_to.strftime("%Y-%m-%d") or '')
            worksheet.write(row_num, 5, record.eos_segment.display_name or '')

            worksheet.write(row_num, 6, record.opening_balance_leave_days or 0)
            worksheet.write(row_num, 7, record.opening_balance_leave_amount or 0)

            worksheet.write(row_num, 8, record.leave_monthly or 0)
            worksheet.write(row_num, 9, record.leave_monthly_value or 0)

            worksheet.write(row_num, 10, record.time_off_request_days or 0)
            worksheet.write(row_num, 11, record.time_off_request_amount or 0)

            worksheet.write(row_num, 12, record.ending_balance_leave_days or 0)
            worksheet.write(row_num, 13, record.ending_balance_leave_amount or 0)

            worksheet.write(row_num, 14, record.opening_balance_eos_days or 0)
            worksheet.write(row_num, 15, record.opening_balance_eos_amount or 0)

            worksheet.write(row_num, 16, record.eos_allowance_days or 0)
            worksheet.write(row_num, 17, record.eos_allowance_amount or 0)


            worksheet.write(row_num, 18, record.esb_paid_days or 0)
            worksheet.write(row_num, 19, record.esb_paid_amount or 0)

            worksheet.write(row_num, 20, record.ending_balance_eos_days or 0)
            worksheet.write(row_num, 21, record.ending_balance_eos_amount or 0)


        # Close the workbook
        # workbook.close()

        # # Return the Excel file content
        # output.seek(0)
        # return output.read()

