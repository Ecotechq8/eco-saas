# -*- coding: utf-8 -*-
import io
import json
import logging
from odoo import http, _
from odoo.http import request, content_disposition

_logger = logging.getLogger(__name__)


class FinancialReportController(http.Controller):

    @http.route('/financial_reports/data', type='json', auth='user', methods=['POST'])
    def get_report_data(self, options, **kw):
        engine = request.env['financial.report.engine']
        report_type = options.get('report_type')
        try:
            if report_type == 'general_ledger':
                return engine.get_general_ledger(options)
            elif report_type == 'trial_balance':
                return engine.get_trial_balance(options)
            elif report_type == 'balance_sheet':
                return engine.get_balance_sheet(options)
            elif report_type == 'profit_loss':
                return engine.get_profit_loss(options)
            return {'error': f'Unknown report type: {report_type}'}
        except Exception as e:
            _logger.exception("Error generating report data")
            return {'error': str(e)}

    @http.route('/financial_reports/export_xlsx', type='http', auth='user', methods=['POST'], csrf=True)
    def export_xlsx(self, **kw):
        try:
            options = json.loads(kw.get('options', '{}'))
            engine = request.env['financial.report.engine']
            report_type = options.get('report_type', '')

            if report_type == 'general_ledger':
                data = engine.get_general_ledger(options)
            elif report_type == 'trial_balance':
                data = engine.get_trial_balance(options)
            elif report_type == 'balance_sheet':
                data = engine.get_balance_sheet(options)
            elif report_type == 'profit_loss':
                data = engine.get_profit_loss(options)
            else:
                return request.make_response('Unknown report type', status=400)

            xlsx_bytes = self._build_excel(report_type, data, options)
            filename = self._get_filename(report_type) + '.xlsx'

            return request.make_response(
                xlsx_bytes,
                headers=[
                    ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                    ('Content-Disposition', content_disposition(filename)),
                    ('Content-Length', len(xlsx_bytes)),
                ],
            )
        except Exception as e:
            _logger.exception("Excel export failed")
            return request.make_response(str(e), status=500, headers=[('Content-Type', 'text/plain')])

    def _build_excel(self, report_type, data, options):
        import xlsxwriter
        output = io.BytesIO()
        wb = xlsxwriter.Workbook(output, {'in_memory': True})
        F = self._make_formats(wb)

        if report_type == 'general_ledger':
            self._sheet_general_ledger(wb, F, data, options)
        elif report_type == 'trial_balance':
            self._sheet_trial_balance(wb, F, data, options)
        elif report_type == 'balance_sheet':
            self._sheet_balance_sheet(wb, F, data, options)
        elif report_type == 'profit_loss':
            self._sheet_profit_loss(wb, F, data, options)

        wb.close()
        output.seek(0)
        return output.read()

    def _make_formats(self, wb):
        def fmt(**kw): return wb.add_format(kw)

        return {
            'title': fmt(bold=True, font_size=14, font_color='#FFFFFF', bg_color='#1F4E79', align='center',
                         valign='vcenter'),
            'subtitle': fmt(italic=True, font_size=9, font_color='#595959', align='center'),
            'col_header': fmt(bold=True, font_size=10, font_color='#FFFFFF', bg_color='#2E75B6', align='center',
                              border=1),
            'section': fmt(bold=True, font_size=11, font_color='#FFFFFF', bg_color='#2E75B6', border=1),
            'group': fmt(bold=True, font_size=10, bg_color='#D6E4F0', border=1),
            'data': fmt(font_size=10, border=1),
            'data_num': fmt(font_size=10, border=1, num_format='#,##0.00'),
            'total': fmt(bold=True, font_size=10, bg_color='#BDD7EE', border=1, num_format='#,##0.00'),
            'grand_lbl': fmt(bold=True, font_size=11, bg_color='#1F4E79', font_color='#FFFFFF', border=1),
            'grand_num': fmt(bold=True, font_size=11, bg_color='#1F4E79', font_color='#FFFFFF', border=1,
                             num_format='#,##0.00'),
        }

    def _sheet_balance_sheet(self, wb, F, data, options):
        ws = wb.add_worksheet('Balance Sheet')
        journals = data.get('journal_columns', [])

        # Determine total columns: Code + Name + [Journals] + Total
        ncols = 3 + len(journals)
        ws.set_column(0, 0, 10)  # Code
        ws.set_column(1, 1, 40)  # Account
        for i in range(len(journals) + 1):
            ws.set_column(2 + i, 2 + i, 15)

        self._write_title(ws, F, 'Balance Sheet', self._period_str(options), ncols)

        # Dynamic Headers
        ws.write(2, 0, 'Code', F['col_header'])
        ws.write(2, 1, 'Account', F['col_header'])
        col = 2
        for j_name in journals:
            ws.write(2, col, j_name, F['col_header'])
            col += 1
        ws.write(2, col, 'Total Balance', F['col_header'])

        row = 3
        sections_order = ['asset', 'liability', 'equity']
        for key in sections_order:
            sec = data['sections'].get(key, {})
            ws.merge_range(row, 0, row, ncols - 1, sec.get('label', key).upper(), F['section'])
            row += 1

            for acc in sec.get('accounts', []):
                ws.write(row, 0, acc['account_code'], F['data'])
                ws.write(row, 1, acc['account_name'], F['data'])
                col = 2
                for j_name in journals:
                    val = acc.get('journal_balances', {}).get(j_name, 0.0)
                    ws.write_number(row, col, val, F['data_num'])
                    col += 1
                ws.write_number(row, col, acc.get('total_balance', 0.0), F['data_num'])
                row += 1

            # Section Totals
            ws.write(row, 0, '', F['total'])
            ws.write(row, 1, f"Total {sec.get('label', '')}", F['total'])
            col = 2
            for j_name in journals:
                ws.write_number(row, col, sec['journal_totals'].get(j_name, 0.0), F['total'])
                col += 1
            ws.write_number(row, col, sec.get('total', 0.0), F['total'])
            row += 1

        # Grand Totals
        row += 1
        ws.merge_range(row, 0, row, ncols - 2, 'TOTAL ASSETS', F['grand_lbl'])
        ws.write_number(row, ncols - 1, data.get('total_assets', 0.0), F['grand_num'])
        row += 1
        ws.merge_range(row, 0, row, ncols - 2, 'TOTAL LIABILITIES + EQUITY', F['grand_lbl'])
        ws.write_number(row, ncols - 1, data.get('total_liabilities_equity', 0.0), F['grand_num'])

    def _sheet_profit_loss(self, wb, F, data, options):
        ws = wb.add_worksheet('Profit & Loss')
        journals = data.get('journal_columns', [])
        ncols = 3 + len(journals)

        ws.set_column(0, 0, 10)
        ws.set_column(1, 1, 40)
        for i in range(len(journals) + 1):
            ws.set_column(2 + i, 2 + i, 15)

        self._write_title(ws, F, 'Profit & Loss', self._period_str(options), ncols)

        # Dynamic Headers
        ws.write(2, 0, 'Code', F['col_header'])
        ws.write(2, 1, 'Account', F['col_header'])
        col = 2
        for j_name in journals:
            ws.write(2, col, j_name, F['col_header'])
            col += 1
        ws.write(2, col, 'Total Balance', F['col_header'])

        row = 3
        for key in ['income', 'expense']:
            sec = data['sections'].get(key, {})
            ws.merge_range(row, 0, row, ncols - 1, sec.get('label', key).upper(), F['section'])
            row += 1

            for acc in sec.get('accounts', []):
                ws.write(row, 0, acc['account_code'], F['data'])
                ws.write(row, 1, acc['account_name'], F['data'])
                col = 2
                for j_name in journals:
                    val = acc.get('journal_balances', {}).get(j_name, 0.0)
                    ws.write_number(row, col, val, F['data_num'])
                    col += 1
                ws.write_number(row, col, acc.get('total_balance', 0.0), F['data_num'])
                row += 1

            # Totals
            ws.write(row, 0, '', F['total'])
            ws.write(row, 1, f"Total {sec.get('label', '')}", F['total'])
            col = 2
            for j_name in journals:
                ws.write_number(row, col, sec['journal_totals'].get(j_name, 0.0), F['total'])
                col += 1
            ws.write_number(row, col, sec.get('total', 0.0), F['total'])
            row += 1

        row += 1
        ws.merge_range(row, 0, row, ncols - 2, 'NET PROFIT / (LOSS)', F['grand_lbl'])
        ws.write_number(row, ncols - 1, data.get('net_income', 0.0), F['grand_num'])

    # Standard methods for Trial Balance and General Ledger (Fixed for consistency)
    def _sheet_trial_balance(self, wb, F, data, options):
        ws = wb.add_worksheet('Trial Balance')
        cols = ['Code', 'Account Name', 'Opening', 'Period Debit', 'Period Credit', 'Movement', 'Closing']
        ncols = len(cols)
        self._write_title(ws, F, 'Trial Balance', self._period_str(options), ncols)
        for c, h in enumerate(cols):
            ws.write(2, c, h, F['col_header'])
            ws.set_column(c, c, 15)

        row = 3
        for line in data.get('lines', []):
            ws.write(row, 0, line['account_code'], F['data'])
            ws.write(row, 1, line['account_name'], F['data'])
            ws.write_number(row, 2, line['open_balance'], F['data_num'])
            ws.write_number(row, 3, line['period_debit'], F['data_num'])
            ws.write_number(row, 4, line['period_credit'], F['data_num'])
            ws.write_number(row, 5, line['period_balance'], F['data_num'])
            ws.write_number(row, 6, line['close_balance'], F['data_num'])
            row += 1

    def _sheet_general_ledger(self, wb, F, data, options):
        ws = wb.add_worksheet('General Ledger')
        cols = ['Date', 'Entry', 'Label', 'Partner', 'Journal', 'Debit', 'Credit', 'Balance']
        ncols = len(cols)
        self._write_title(ws, F, 'General Ledger', self._period_str(options), ncols)
        for c, h in enumerate(cols):
            ws.write(2, c, h, F['col_header'])
            ws.set_column(c, c, 15)

        row = 3
        for acc in data.get('accounts', []):
            ws.merge_range(row, 0, row, 4, f"{acc['account_code']} {acc['account_name']}", F['group'])
            ws.write_number(row, 5, acc['total_debit'], F['group'])
            ws.write_number(row, 6, acc['total_credit'], F['group'])
            ws.write_number(row, 7, acc['total_balance'], F['group'])
            row += 1
            for line in acc['lines']:
                ws.write(row, 0, str(line['date']), F['data'])
                ws.write(row, 1, line['move_name'], F['data'])
                ws.write(row, 2, line['label'], F['data'])
                ws.write(row, 3, line['partner'], F['data'])
                ws.write(row, 4, line['journal'], F['data'])
                ws.write_number(row, 5, line['debit'], F['data_num'])
                ws.write_number(row, 6, line['credit'], F['data_num'])
                ws.write_number(row, 7, line['balance'], F['data_num'])
                row += 1

    def _write_title(self, ws, F, title, subtitle, ncols):
        ws.merge_range(0, 0, 0, ncols - 1, title, F['title'])
        ws.merge_range(1, 0, 1, ncols - 1, subtitle, F['subtitle'])

    def _period_str(self, options):
        f, t = options.get('date_from', ''), options.get('date_to', '')
        return f"Period: {f} to {t}" if f and t else (t or f or '')

    def _get_filename(self, report_type):
        return report_type.replace('_', ' ').title().replace(' ', '_')
