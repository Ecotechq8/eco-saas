# -*- coding: utf-8 -*-
import logging
from odoo import models, api, fields, _

_logger = logging.getLogger(__name__)


class FinancialReportEngine(models.AbstractModel):
    _name = 'financial.report.engine'
    _description = 'Financial Report Engine'

    @api.model
    def get_general_ledger(self, options):
        # ... (General Ledger remains mostly same, but ensure it works with ORM)
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
                    'lines': [], 'total_debit': 0.0, 'total_credit': 0.0, 'total_balance': 0.0,
                }
            accounts[acc.id]['lines'].append({
                'date': line.date, 'move_name': line.move_name, 'label': line.name,
                'partner': line.partner_id.name or '', 'journal': line.journal_id.name or '',
                'debit': line.debit, 'credit': line.credit, 'balance': line.balance,
            })
            accounts[acc.id]['total_debit'] += line.debit
            accounts[acc.id]['total_credit'] += line.credit
            accounts[acc.id]['total_balance'] += line.balance

        return {'accounts': sorted(accounts.values(), key=lambda x: x['account_code'])}

    @api.model
    def get_trial_balance(self, options):
        # Similar logic as P&L/BS could be applied here if you want Journal columns in Trial Balance
        # For now, keeping your working ORM version
        return super(FinancialReportEngine, self).get_trial_balance(options)

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

        accounts = {}
        used_journals = set()

        for line in move_lines:
            acc = line.account_id
            j_name = line.journal_id.name or 'Unknown'
            used_journals.add(j_name)

            if acc.id not in accounts:
                accounts[acc.id] = {
                    'account_id': acc.id,
                    'account_code': acc.code or '',  # Using ORM .code is safe
                    'account_name': acc.name,
                    'internal_group': acc.internal_group,
                    'journal_balances': {},  # Store balance per journal
                    'total_balance': 0.0,
                }

            accounts[acc.id]['journal_balances'][j_name] = accounts[acc.id]['journal_balances'].get(j_name,
                                                                                                    0.0) + line.balance
            accounts[acc.id]['total_balance'] += line.balance

        # Get sorted list of journal names for columns
        journal_columns = sorted(list(used_journals))
        rows = list(accounts.values())

        if report_type == 'balance_sheet':
            res = self._structure_balance_sheet(rows, journal_columns)
        else:
            res = self._structure_profit_loss(rows, journal_columns)

        res['journal_columns'] = journal_columns  # Pass this to Excel/JS
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
                    sections[ig]['journal_totals'][j] += r['journal_balances'].get(j, 0.0)

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
                    sections[ig]['journal_totals'][j] += r['journal_balances'].get(j, 0.0)

        # Reverse sign for income for presentation if needed, but keeping standard math here
        net_income = sections['income']['total'] - sections['expense']['total']
        return {
            'sections': sections,
            'net_income': net_income,
        }