# -*- coding: utf-8 -*-
import logging
from odoo import models, api, fields, _

_logger = logging.getLogger(__name__)


class FinancialReportEngine(models.AbstractModel):
    _name = 'financial.report.engine'
    _description = 'Financial Report Engine'

    # ─────────────────────────────────────────────────────────────────────────
    # General Ledger
    # ─────────────────────────────────────────────────────────────────────────
    @api.model
    def get_general_ledger(self, options):
        domain = [('parent_state', '=', 'posted')]
        if options.get('date_from'): domain.append(('date', '>=', options['date_from']))
        if options.get('date_to'): domain.append(('date', '<=', options['date_to']))
        if options.get('journal_ids'): domain.append(('journal_id', 'in', options['journal_ids']))

        move_lines = self.env['account.move.line'].search(domain)
        accounts = {}

        for line in move_lines:
            acc = line.account_id
            if acc.id not in accounts:
                accounts[acc.id] = {
                    'account_id': acc.id,
                    'account_code': acc.code or acc.display_name,
                    'account_name': acc.name,
                    'lines': [],
                    'total_debit': 0.0,
                    'total_credit': 0.0,
                    'total_balance': 0.0,
                }
            accounts[acc.id]['lines'].append({
                'line_id': line.id,
                'move_name': line.move_name,
                'date': line.date,
                'label': line.name,
                'partner': line.partner_id.name or '',
                'journal': line.journal_id.name or '',
                'debit': line.debit,
                'credit': line.credit,
                'balance': line.balance,
            })
            accounts[acc.id]['total_debit'] += line.debit
            accounts[acc.id]['total_credit'] += line.credit
            accounts[acc.id]['total_balance'] += line.balance

        result = sorted(accounts.values(), key=lambda x: x['account_code'])
        return {
            'accounts': result,
            'grand_totals': {
                'debit': sum(a['total_debit'] for a in result),
                'credit': sum(a['total_credit'] for a in result),
                'balance': sum(a['total_balance'] for a in result),
            }
        }

    # ─────────────────────────────────────────────────────────────────────────
    # Trial Balance (FIXED: No more super() call)
    # ─────────────────────────────────────────────────────────────────────────
    @api.model
    def get_trial_balance(self, options):
        # 1. Opening Balance Domain (Before start date)
        domain_open = [('parent_state', '=', 'posted')]
        if options.get('date_from'):
            domain_open.append(('date', '<', options['date_from']))
        if options.get('journal_ids'):
            domain_open.append(('journal_id', 'in', options['journal_ids']))

        # 2. Period Domain (Within range)
        domain_period = [('parent_state', '=', 'posted')]
        if options.get('date_from'): domain_period.append(('date', '>=', options['date_from']))
        if options.get('date_to'): domain_period.append(('date', '<=', options['date_to']))
        if options.get('journal_ids'): domain_period.append(('journal_id', 'in', options['journal_ids']))

        accounts = {}

        # Process Opening
        lines_open = self.env['account.move.line'].search(domain_open)
        for line in lines_open:
            aid = line.account_id.id
            if aid not in accounts: accounts[aid] = self._empty_tb_row(line.account_id)
            accounts[aid]['open_balance'] += line.balance

        # Process Period
        lines_period = self.env['account.move.line'].search(domain_period)
        for line in lines_period:
            aid = line.account_id.id
            if aid not in accounts: accounts[aid] = self._empty_tb_row(line.account_id)
            accounts[aid]['period_debit'] += line.debit
            accounts[aid]['period_credit'] += line.credit
            accounts[aid]['period_balance'] += line.balance

        # Finalize
        result = []
        for aid in accounts:
            row = accounts[aid]
            row['close_balance'] = row['open_balance'] + row['period_balance']
            result.append(row)

        result.sort(key=lambda x: x['account_code'])

        totals = {k: sum(r[k] for r in result) for k in
                  ['open_balance', 'period_debit', 'period_credit', 'period_balance', 'close_balance']}
        return {'lines': result, 'totals': totals}

    def _empty_tb_row(self, acc):
        return {
            'account_id': acc.id,
            'account_code': acc.code or acc.display_name,
            'account_name': acc.name,
            'open_balance': 0.0,
            'period_debit': 0.0,
            'period_credit': 0.0,
            'period_balance': 0.0,
            'close_balance': 0.0,
        }

    # ─────────────────────────────────────────────────────────────────────────
    # Balance Sheet & Profit Loss (With Dynamic Journal Columns)
    # ─────────────────────────────────────────────────────────────────────────
    @api.model
    def get_balance_sheet(self, options):
        return self._get_pnl_or_bs(options, report_type='balance_sheet')

    @api.model
    def get_profit_loss(self, options):
        return self._get_pnl_or_bs(options, report_type='profit_loss')

    @api.model
    def _get_pnl_or_bs(self, options, report_type):
        domain = [('parent_state', '=', 'posted')]
        if report_type == 'profit_loss':
            if options.get('date_from'): domain.append(('date', '>=', options['date_from']))
            if options.get('date_to'): domain.append(('date', '<=', options['date_to']))
        else:
            if options.get('date_to'): domain.append(('date', '<=', options['date_to']))

        if options.get('journal_ids'):
            domain.append(('journal_id', 'in', options['journal_ids']))

        move_lines = self.env['account.move.line'].search(domain)

        accounts_map = {}
        used_journals = set()

        for line in move_lines:
            acc = line.account_id
            j_name = line.journal_id.name or 'Misc'
            used_journals.add(j_name)

            if acc.id not in accounts_map:
                accounts_map[acc.id] = {
                    'account_id': acc.id,
                    'account_code': acc.code or '',
                    'account_name': acc.name,
                    'internal_group': acc.internal_group,
                    'journal_balances': {},
                    'total_balance': 0.0,
                }

            acc_data = accounts_map[acc.id]
            acc_data['journal_balances'][j_name] = acc_data['journal_balances'].get(j_name, 0.0) + line.balance
            acc_data['total_balance'] += line.balance

        journal_columns = sorted(list(used_journals))
        rows = list(accounts_map.values())

        if report_type == 'balance_sheet':
            res = self._structure_balance_sheet(rows, journal_columns)
        else:
            res = self._structure_profit_loss(rows, journal_columns)

        res['journal_columns'] = journal_columns
        return res

    def _structure_balance_sheet(self, rows, journal_columns):
        sections = {
            'asset': {'label': _('Assets'), 'accounts': [], 'journal_totals': {j: 0.0 for j in journal_columns},
                      'total': 0.0},
            'liability': {'label': _('Liabilities'), 'accounts': [],
                          'journal_totals': {j: 0.0 for j in journal_columns}, 'total': 0.0},
            'equity': {'label': _('Equity'), 'accounts': [], 'journal_totals': {j: 0.0 for j in journal_columns},
                       'total': 0.0},
        }
        for r in rows:
            ig = r.get('internal_group')
            if ig in sections:
                sections[ig]['accounts'].append(r)
                sections[ig]['total'] += r['total_balance']
                for j in journal_columns:
                    sections[ig]['journal_totals'][j] += r.get('journal_balances', {}).get(j, 0.0)

        return {
            'sections': sections,
            'total_assets': sections['asset']['total'],
            'total_liabilities_equity': sections['liability']['total'] + sections['equity']['total'],
        }

    def _structure_profit_loss(self, rows, journal_columns):
        sections = {
            'income': {'label': _('Income'), 'accounts': [], 'journal_totals': {j: 0.0 for j in journal_columns},
                       'total': 0.0},
            'expense': {'label': _('Expenses'), 'accounts': [], 'journal_totals': {j: 0.0 for j in journal_columns},
                        'total': 0.0},
        }
        for r in rows:
            ig = r.get('internal_group')
            if ig in sections:
                sections[ig]['accounts'].append(r)
                sections[ig]['total'] += r['total_balance']
                for j in journal_columns:
                    sections[ig]['journal_totals'][j] += r.get('journal_balances', {}).get(j, 0.0)

        # Presentation: Income is usually credit (negative in DB).
        # For P&L reports, positive Net Income is usually (Income - Expenses).
        # Depending on your CoA, you might need: net_income = (sections['income']['total'] + sections['expense']['total']) * -1
        net_income = (sections['income']['total'] - sections['expense']['total']) * -1
        return {
            'sections': sections,
            'net_income': net_income,
        }