# -*- coding: utf-8 -*-
import io, json
from odoo import http
from odoo.http import request, content_disposition


class FinancialReportController(http.Controller):

    @http.route('/financial_reports/data', type='json', auth='user')
    def get_data(self, options):
        engine = request.env['financial.report.engine']
        rt = options.get('report_type')
        if rt == 'profit_loss': return engine.get_profit_loss(options)
        if rt == 'balance_sheet': return engine.get_balance_sheet(options)
        if rt == 'general_ledger': return engine.get_general_ledger(options)
        return engine.get_trial_balance(options)

    @http.route('/financial_reports/export_xlsx', type='http', auth='user')
    def export_xlsx(self, options, **kw):
        options = json.loads(options)
        data = self.get_data(options)
        output = io.BytesIO()
        import xlsxwriter
        wb = xlsxwriter.Workbook(output)
        ws = wb.add_worksheet('Financial Report')

        # Formats
        head = wb.add_format(
            {'bold': True, 'bg_color': '#1F4E79', 'font_color': 'white', 'border': 1, 'align': 'center'})
        num = wb.add_format({'num_format': '#,##0.00', 'border': 1})
        bold_num = wb.add_format({'bold': True, 'num_format': '#,##0.00', 'border': 1, 'bg_color': '#DDEBF7'})

        if data.get('report_type') == 'general_ledger':
            # Handle GL (standard layout)
            headers = ['Date', 'Entry', 'Label', 'Partner', 'Journal', 'Debit', 'Credit', 'Balance']
            for i, h in enumerate(headers): ws.write(0, i, h, head)
            row = 1
            for acc in data['accounts']:
                ws.merge_range(row, 0, row, 4, f"{acc['account_code']} {acc['account_name']}", head)
                ws.write(row, 5, acc['total_debit'], head)
                ws.write(row, 6, acc['total_credit'], head)
                ws.write(row, 7, acc['total_balance'], head)
                row += 1
                for line in acc['lines']:
                    ws.write(row, 0, str(line['date']), num)
                    ws.write(row, 1, line['move_name'], num)
                    ws.write(row, 2, line['label'], num)
                    ws.write(row, 3, line['partner'], num)
                    ws.write(row, 4, line['journal'], num)
                    ws.write(row, 5, line['debit'], num)
                    ws.write(row, 6, line['credit'], num)
                    ws.write(row, 7, line['balance'], num)
                    row += 1
        else:
            # Handle Matrix Reports (BS / P&L)
            cols = data.get('columns', [])
            ws.write(0, 0, 'Code', head);
            ws.write(0, 1, 'Account', head)
            for i, c in enumerate(cols): ws.write(0, 2 + i, c, head)
            ws.write(0, 2 + len(cols), 'Total', head)

            row = 1
            for skey, sec in data.get('sections', {}).items():
                ws.merge_range(row, 0, row, 2 + len(cols), sec['label'].upper(), head)
                row += 1
                for r in sec['rows']:
                    ws.write(row, 0, r['code'], num);
                    ws.write(row, 1, r['name'], num)
                    for i, c in enumerate(cols): ws.write(row, 2 + i, r['col_balances'][c], num)
                    ws.write(row, 2 + len(cols), r['total'], num)
                    row += 1
                # Totals
                ws.write(row, 1, 'Total ' + sec['label'], bold_num)
                for i, c in enumerate(cols): ws.write(row, 2 + i, sec['totals'][c], bold_num)
                ws.write(row, 2 + len(cols), sec['total'], bold_num)
                row += 2

        wb.close()
        output.seek(0)
        return request.make_response(output.read(), [
            ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
            ('Content-Disposition', content_disposition('Report.xlsx'))
        ])