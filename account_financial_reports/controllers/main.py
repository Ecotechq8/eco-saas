# -*- coding: utf-8 -*-
import io
import json
import logging
import base64

from odoo import http, _
from odoo.http import request, content_disposition

_logger = logging.getLogger(__name__)


class FinancialReportController(http.Controller):

    # ─────────────────────────────────────────────────────────────────────────
    # JSON data endpoint (called by OWL component to render the preview)
    # ─────────────────────────────────────────────────────────────────────────

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
            else:
                return {'error': f'Unknown report type: {report_type}'}
        except Exception as e:
            _logger.exception("Error generating report data")
            return {'error': str(e)}

    # ─────────────────────────────────────────────────────────────────────────
    # Excel download endpoint
    # ─────────────────────────────────────────────────────────────────────────

    @http.route('/financial_reports/export_xlsx', type='http', auth='user', methods=['POST'], csrf=True)
    def export_xlsx(self, **kw):
        try:
            options = json.loads(kw.get('options', '{}'))
            engine  = request.env['financial.report.engine']
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
            filename   = self._get_filename(report_type) + '.xlsx'

            return request.make_response(
                xlsx_bytes,
                headers=[
                    ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                    ('Content-Disposition', content_disposition(filename)),
                    ('Content-Length', len(xlsx_bytes)),
                ],
            )
        except ImportError:
            return request.make_response(
                'xlsxwriter is not installed. Run: pip install xlsxwriter',
                status=500,
                headers=[('Content-Type', 'text/plain')],
            )
        except Exception as e:
            _logger.exception("Excel export failed")
            return request.make_response(str(e), status=500,
                                         headers=[('Content-Type', 'text/plain')])

    # ─────────────────────────────────────────────────────────────────────────
    # Excel builders
    # ─────────────────────────────────────────────────────────────────────────

    def _build_excel(self, report_type, data, options):
        import xlsxwriter
        output = io.BytesIO()
        wb = xlsxwriter.Workbook(output, {'in_memory': True})

        # ── Common formats ──────────────────────────────────────────────────
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
        """Return a dict of named xlsxwriter Format objects."""
        def fmt(**kw):
            return wb.add_format(kw)

        return {
            'title': fmt(bold=True, font_size=14, font_color='#FFFFFF',
                         bg_color='#1F4E79', align='center', valign='vcenter'),
            'subtitle': fmt(italic=True, font_size=9, font_color='#595959',
                            align='center'),
            'col_header': fmt(bold=True, font_size=10, font_color='#FFFFFF',
                              bg_color='#2E75B6', align='center', valign='vcenter',
                              border=1, text_wrap=True),
            'section': fmt(bold=True, font_size=11, font_color='#FFFFFF',
                           bg_color='#2E75B6', border=1),
            'group': fmt(bold=True, font_size=10, bg_color='#D6E4F0', border=1),
            'group_num': fmt(bold=True, font_size=10, bg_color='#D6E4F0', border=1,
                             num_format='#,##0.00'),
            'total': fmt(bold=True, font_size=10, bg_color='#BDD7EE', border=1,
                         num_format='#,##0.00'),
            'total_lbl': fmt(bold=True, font_size=10, bg_color='#BDD7EE', border=1),
            'data': fmt(font_size=10, border=1),
            'data_num': fmt(font_size=10, border=1, num_format='#,##0.00'),
            'data_neg': fmt(font_size=10, border=1, num_format='#,##0.00',
                            font_color='#C00000'),
            'data_date': fmt(font_size=10, border=1, num_format='yyyy-mm-dd'),
            'grand_lbl': fmt(bold=True, font_size=11, bg_color='#1F4E79',
                             font_color='#FFFFFF', border=1),
            'grand_num': fmt(bold=True, font_size=11, bg_color='#1F4E79',
                             font_color='#FFFFFF', border=1, num_format='#,##0.00'),
        }

    def _write_title(self, ws, F, title, subtitle, ncols):
        ws.merge_range(0, 0, 0, ncols - 1, title, F['title'])
        ws.set_row(0, 28)
        ws.merge_range(1, 0, 1, ncols - 1, subtitle, F['subtitle'])

    def _num(self, F, value):
        if value is None:
            return 0.0, F['data_num']
        v = float(value)
        return v, (F['data_neg'] if v < 0 else F['data_num'])

    # ── General Ledger ───────────────────────────────────────────────────────
    def _sheet_general_ledger(self, wb, F, data, options):
        ws = wb.add_worksheet('General Ledger')
        cols = ['Date', 'Entry', 'Label', 'Partner', 'Journal', 'Debit', 'Credit', 'Balance']
        widths = [12, 18, 40, 25, 18, 14, 14, 14]
        ncols = len(cols)

        subtitle = self._period_str(options)
        self._write_title(ws, F, 'General Ledger', subtitle, ncols)

        # Headers
        for c, (h, w) in enumerate(zip(cols, widths)):
            ws.write(2, c, h, F['col_header'])
            ws.set_column(c, c, w)
        ws.set_row(2, 20)
        ws.freeze_panes(3, 0)

        row = 3
        for acc in data.get('accounts', []):
            # Account header row
            ws.merge_range(row, 0, row, 4,
                           f"{acc['account_code']} - {acc['account_name']}", F['group'])
            ws.write(row, 5, acc['total_debit'],   F['group_num'])
            ws.write(row, 6, acc['total_credit'],  F['group_num'])
            ws.write(row, 7, acc['total_balance'], F['group_num'])
            row += 1

            running = 0.0
            for line in acc['lines']:
                running += float(line['balance'] or 0)
                date_val = str(line['date']) if line['date'] else ''
                ws.write(row, 0, date_val,               F['data'])
                ws.write(row, 1, line['move_name'] or '', F['data'])
                ws.write(row, 2, line['label']    or '', F['data'])
                ws.write(row, 3, line['partner']  or '', F['data'])
                ws.write(row, 4, line['journal']  or '', F['data'])
                v, f = self._num(F, line['debit'])
                ws.write_number(row, 5, v, F['data_num'])
                v, f = self._num(F, line['credit'])
                ws.write_number(row, 6, v, F['data_num'])
                v, f = self._num(F, running)
                ws.write_number(row, 7, v, f)
                row += 1

        # Grand totals
        gt = data.get('grand_totals', {})
        ws.merge_range(row, 0, row, 4, 'GRAND TOTAL', F['grand_lbl'])
        ws.write_number(row, 5, float(gt.get('debit',   0) or 0), F['grand_num'])
        ws.write_number(row, 6, float(gt.get('credit',  0) or 0), F['grand_num'])
        ws.write_number(row, 7, float(gt.get('balance', 0) or 0), F['grand_num'])

    # ── Trial Balance ────────────────────────────────────────────────────────
    def _sheet_trial_balance(self, wb, F, data, options):
        ws = wb.add_worksheet('Trial Balance')
        cols = ['Code', 'Account Name', 'Opening Balance',
                'Period Debit', 'Period Credit', 'Period Movement', 'Closing Balance']
        widths = [10, 45, 16, 16, 16, 16, 16]
        ncols = len(cols)

        self._write_title(ws, F, 'Trial Balance', self._period_str(options), ncols)
        for c, (h, w) in enumerate(zip(cols, widths)):
            ws.write(2, c, h, F['col_header'])
            ws.set_column(c, c, w)
        ws.set_row(2, 20)
        ws.freeze_panes(3, 2)

        row = 3
        for line in data.get('lines', []):
            ws.write(row, 0, line['account_code'], F['data'])
            ws.write(row, 1, line['account_name'], F['data'])
            for ci, key in enumerate(['open_balance', 'period_debit', 'period_credit',
                                      'period_balance', 'close_balance'], start=2):
                v, f = self._num(F, line[key])
                ws.write_number(row, ci, v, f)
            row += 1

        t = data.get('totals', {})
        ws.write(row, 0, '',        F['grand_lbl'])
        ws.write(row, 1, 'TOTALS', F['grand_lbl'])
        for ci, key in enumerate(['open_balance', 'period_debit', 'period_credit',
                                   'period_balance', 'close_balance'], start=2):
            ws.write_number(row, ci, float(t.get(key, 0) or 0), F['grand_num'])

    # ── Balance Sheet ────────────────────────────────────────────────────────
    def _sheet_balance_sheet(self, wb, F, data, options):
        ws = wb.add_worksheet('Balance Sheet')
        ncols = 3
        widths = [10, 50, 18]
        for c, w in enumerate(widths):
            ws.set_column(c, c, w)

        self._write_title(ws, F, 'Balance Sheet', self._period_str(options), ncols)
        ws.write(2, 0, 'Code',    F['col_header'])
        ws.write(2, 1, 'Account', F['col_header'])
        ws.write(2, 2, 'Balance', F['col_header'])
        ws.set_row(2, 20)
        ws.freeze_panes(3, 0)

        sections_order = ['asset', 'liability', 'equity']
        row = 3
        for key in sections_order:
            sec = data['sections'].get(key, {})
            ws.merge_range(row, 0, row, 1, sec.get('label', key).upper(), F['section'])
            ws.write(row, 2, '', F['section'])
            row += 1
            for acc in sec.get('accounts', []):
                ws.write(row, 0, acc['account_code'], F['data'])
                ws.write(row, 1, acc['account_name'], F['data'])
                v, f = self._num(F, acc['balance'])
                ws.write_number(row, 2, v, f)
                row += 1
            ws.merge_range(row, 0, row, 1, f"Total {sec.get('label','')}", F['total_lbl'])
            ws.write_number(row, 2, float(sec.get('total', 0) or 0), F['total'])
            row += 1

        row += 1
        ws.merge_range(row, 0, row, 1, 'TOTAL ASSETS', F['grand_lbl'])
        ws.write_number(row, 2, float(data.get('total_assets', 0) or 0), F['grand_num'])
        row += 1
        ws.merge_range(row, 0, row, 1, 'TOTAL LIABILITIES + EQUITY', F['grand_lbl'])
        ws.write_number(row, 2, float(data.get('total_liabilities_equity', 0) or 0), F['grand_num'])

    # ── Profit & Loss ────────────────────────────────────────────────────────
    def _sheet_profit_loss(self, wb, F, data, options):
        ws = wb.add_worksheet('Profit & Loss')
        ncols = 3
        widths = [10, 50, 18]
        for c, w in enumerate(widths):
            ws.set_column(c, c, w)

        self._write_title(ws, F, 'Profit & Loss', self._period_str(options), ncols)
        ws.write(2, 0, 'Code',    F['col_header'])
        ws.write(2, 1, 'Account', F['col_header'])
        ws.write(2, 2, 'Balance', F['col_header'])
        ws.set_row(2, 20)
        ws.freeze_panes(3, 0)

        row = 3
        for key in ['income', 'expense']:
            sec = data['sections'].get(key, {})
            ws.merge_range(row, 0, row, 1, sec.get('label', key).upper(), F['section'])
            ws.write(row, 2, '', F['section'])
            row += 1
            for acc in sec.get('accounts', []):
                ws.write(row, 0, acc['account_code'], F['data'])
                ws.write(row, 1, acc['account_name'], F['data'])
                v, f = self._num(F, acc['balance'])
                ws.write_number(row, 2, v, f)
                row += 1
            ws.merge_range(row, 0, row, 1, f"Total {sec.get('label','')}", F['total_lbl'])
            ws.write_number(row, 2, float(sec.get('total', 0) or 0), F['total'])
            row += 1

        row += 1
        net = float(data.get('net_income', 0) or 0)
        ws.merge_range(row, 0, row, 1, 'NET PROFIT / (LOSS)', F['grand_lbl'])
        ws.write_number(row, 2, net, F['grand_num'])

    # ─────────────────────────────────────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────────────────────────────────────

    def _period_str(self, options):
        d_from = options.get('date_from', '')
        d_to   = options.get('date_to',   '')
        if d_from and d_to:
            return f'Period: {d_from} to {d_to}'
        return d_to or d_from or ''

    def _get_filename(self, report_type):
        names = {
            'general_ledger': 'General_Ledger',
            'trial_balance':  'Trial_Balance',
            'balance_sheet':  'Balance_Sheet',
            'profit_loss':    'Profit_and_Loss',
        }
        return names.get(report_type, 'Financial_Report')
