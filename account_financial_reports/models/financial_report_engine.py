# -*- coding: utf-8 -*-
"""
financial_report_engine.py
Core data layer for all four financial reports.
Works on plain Odoo 18 Community (no account_reports dependency).
Now uses 100% ORM search for schema-safe execution.
"""
import logging
from odoo import models, api, fields, _

_logger = logging.getLogger(__name__)


class FinancialReportEngine(models.AbstractModel):
    _name = 'financial.report.engine'
    _description = 'Financial Report Engine'

    # ─────────────────────────────────────────────────────────────────────────
    # Public entry-points (called by wizard / controller)
    # ─────────────────────────────────────────────────────────────────────────

    @api.model
    def get_general_ledger(self, options):
        """
        General Ledger (Odoo 18 safe). Uses ORM to avoid schema issues.
        """
        domain = [('parent_state', '=', 'posted')]

        if options.get('date_from'):
            domain.append(('date', '>=', options['date_from']))
        if options.get('date_to'):
            domain.append(('date', '<=', options['date_to']))
        if options.get('journal_ids'):
            domain.append(('journal_id', 'in', options['journal_ids']))

        if options.get('analytic_account_ids'):
            analytic_ids = self.env['account.analytic.line'].search([
                ('account_id', 'in', options['analytic_account_ids'])
            ]).ids
            domain.append(('analytic_line_ids', 'in', analytic_ids))

        move_lines = self.env['account.move.line'].search(domain)
        accounts = {}

        for line in move_lines:
            acc = line.account_id
            if acc.id not in accounts:
                accounts[acc.id] = {
                    'account_id': acc.id,
                    'account_code': acc.display_name,
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
                'partner': line.partner_id.name if line.partner_id else '',
                'journal': line.journal_id.name if line.journal_id else '',
                'debit': line.debit,
                'credit': line.credit,
                'balance': line.balance,
            })

            accounts[acc.id]['total_debit'] += line.debit or 0.0
            accounts[acc.id]['total_credit'] += line.credit or 0.0
            accounts[acc.id]['total_balance'] += line.balance or 0.0

        result = sorted(accounts.values(), key=lambda x: x['account_code'])
        grand = {
            'debit': sum(a['total_debit'] for a in result),
            'credit': sum(a['total_credit'] for a in result),
            'balance': sum(a['total_balance'] for a in result),
        }

        return {
            'accounts': result,
            'grand_totals': grand
        }

    @api.model
    def get_trial_balance(self, options):
        """
        Returns one row per account with opening balance, period movements,
        and closing balance. Re-written to use ORM.
        """
        # 1. Build domain for Opening Balance
        domain_open = [('parent_state', '=', 'posted')]
        if options.get('date_from'):
            domain_open.append(('date', '<', options['date_from']))
        if options.get('journal_ids'):
            domain_open.append(('journal_id', 'in', options['journal_ids']))
        if options.get('analytic_account_ids'):
            analytic_ids = self.env['account.analytic.line'].search([
                ('account_id', 'in', options['analytic_account_ids'])
            ]).ids
            domain_open.append(('analytic_line_ids', 'in', analytic_ids))

        # 2. Build domain for Period Movements
        domain_period = [('parent_state', '=', 'posted')]
        if options.get('date_from'):
            domain_period.append(('date', '>=', options['date_from']))
        if options.get('date_to'):
            domain_period.append(('date', '<=', options['date_to']))
        if options.get('journal_ids'):
            domain_period.append(('journal_id', 'in', options['journal_ids']))
        if options.get('analytic_account_ids'):
            analytic_ids = self.env['account.analytic.line'].search([
                ('account_id', 'in', options['analytic_account_ids'])
            ]).ids
            domain_period.append(('analytic_line_ids', 'in', analytic_ids))

        # 3. Fetch data via ORM
        lines_open = self.env['account.move.line'].search(domain_open)
        lines_period = self.env['account.move.line'].search(domain_period)

        accounts = {}

        # Process Opening Balances
        for line in lines_open:
            acc = line.account_id
            if acc.id not in accounts:
                accounts[acc.id] = self._get_empty_trial_balance_dict(acc)
            accounts[acc.id]['open_balance'] += line.balance or 0.0
            accounts[acc.id]['close_balance'] += line.balance or 0.0

        # Process Period Movements
        for line in lines_period:
            acc = line.account_id
            if acc.id not in accounts:
                accounts[acc.id] = self._get_empty_trial_balance_dict(acc)
            accounts[acc.id]['period_debit'] += line.debit or 0.0
            accounts[acc.id]['period_credit'] += line.credit or 0.0
            accounts[acc.id]['period_balance'] += line.balance or 0.0
            accounts[acc.id]['close_balance'] += line.balance or 0.0

        result = sorted(accounts.values(), key=lambda x: x['account_code'])

        totals = {
            'open_balance': sum(r['open_balance'] for r in result),
            'period_debit': sum(r['period_debit'] for r in result),
            'period_credit': sum(r['period_credit'] for r in result),
            'period_balance': sum(r['period_balance'] for r in result),
            'close_balance': sum(r['close_balance'] for r in result),
        }

        return {'lines': result, 'totals': totals}

    @api.model
    def get_balance_sheet(self, options):
        """Returns structured Balance Sheet sections."""
        return self._get_pnl_or_bs(options, report_type='balance_sheet')

    @api.model
    def get_profit_loss(self, options):
        """Returns structured Profit & Loss sections."""
        return self._get_pnl_or_bs(options, report_type='profit_loss')

    # ─────────────────────────────────────────────────────────────────────────
    # Internal helpers
    # ─────────────────────────────────────────────────────────────────────────

    @api.model
    def _get_pnl_or_bs(self, options, report_type):
        """
        Generic builder for Balance Sheet and P&L.
        Re-written to use Odoo ORM instead of Raw SQL.
        """
        domain = [('parent_state', '=', 'posted')]

        if report_type == 'profit_loss':
            # P&L is for movements inside the range
            if options.get('date_from'):
                domain.append(('date', '>=', options['date_from']))
            if options.get('date_to'):
                domain.append(('date', '<=', options['date_to']))
        else:
            # Balance Sheet needs all historical data up until date_to
            if options.get('date_to'):
                domain.append(('date', '<=', options['date_to']))

        if options.get('journal_ids'):
            domain.append(('journal_id', 'in', options['journal_ids']))

        if options.get('analytic_account_ids'):
            analytic_ids = self.env['account.analytic.line'].search([
                ('account_id', 'in', options['analytic_account_ids'])
            ]).ids
            domain.append(('analytic_line_ids', 'in', analytic_ids))

        move_lines = self.env['account.move.line'].search(domain)
        accounts = {}

        for line in move_lines:
            acc = line.account_id
            if acc.id not in accounts:
                accounts[acc.id] = {
                    'account_id': acc.id,
                    'account_code': acc.display_name,
                    'account_name': acc.name,
                    'internal_group': acc.internal_group,
                    'balance': 0.0,
                }
            accounts[acc.id]['balance'] += line.balance or 0.0

        rows = list(accounts.values())

        if report_type == 'balance_sheet':
            return self._structure_balance_sheet(rows)
        else:
            return self._structure_profit_loss(rows)

    def _structure_balance_sheet(self, rows):
        sections = {
            'asset': {'label': _('Assets'), 'accounts': [], 'total': 0.0},
            'liability': {'label': _('Liabilities'), 'accounts': [], 'total': 0.0},
            'equity': {'label': _('Equity'), 'accounts': [], 'total': 0.0},
        }
        for r in rows:
            ig = r.get('internal_group', '')
            bal = r['balance'] or 0.0
            if ig in sections:
                sections[ig]['accounts'].append(r)
                sections[ig]['total'] += bal

        total_assets = sections['asset']['total']
        total_liab_equity = sections['liability']['total'] + sections['equity']['total']
        return {
            'sections': sections,
            'total_assets': total_assets,
            'total_liabilities_equity': total_liab_equity,
        }

    def _structure_profit_loss(self, rows):
        sections = {
            'income': {'label': _('Income'), 'accounts': [], 'total': 0.0},
            'expense': {'label': _('Expenses'), 'accounts': [], 'total': 0.0},
        }
        for r in rows:
            ig = r.get('internal_group', '')
            bal = r['balance'] or 0.0
            if ig in sections:
                sections[ig]['accounts'].append(r)
                sections[ig]['total'] += bal

        # Standard net income deduction
        net_income = sections['income']['total'] - sections['expense']['total']
        return {
            'sections': sections,
            'net_income': net_income,
        }

    def _get_empty_trial_balance_dict(self, acc):
        """Helper to init a trial balance row Dict."""
        return {
            'account_id': acc.id,
            'account_code': acc.display_name,
            'account_name': acc.name,
            'account_type': acc.account_type,
            'open_balance': 0.0,
            'period_debit': 0.0,
            'period_credit': 0.0,
            'period_balance': 0.0,
            'close_balance': 0.0,
        }