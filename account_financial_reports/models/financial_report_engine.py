# -*- coding: utf-8 -*-
from odoo import models, api, fields, _
import logging

_logger = logging.getLogger(__name__)


class FinancialReportEngine(models.AbstractModel):
    _name = 'financial.report.engine'
    _description = 'Financial Report Engine'

    @api.model
    def _get_analytics(self, options, company_id):
        ana_ids = options.get('analytic_account_ids') or []
        domain = [('company_id', 'in', [company_id, False])]
        if ana_ids:
            domain.append(('id', 'in', ana_ids))
        return self.env['account.analytic.account'].search(domain, order="name asc")

    @api.model
    def get_general_ledger(self, options):
        company_id = options.get('company_id') or self.env.company.id
        self = self.with_company(company_id)
        domain = [('parent_state', '=', 'posted')]
        if options.get('date_from'): domain.append(('date', '>=', options['date_from']))
        if options.get('date_to'): domain.append(('date', '<=', options['date_to']))

        # Analytic filter for GL (standard row-based)
        ana_ids = options.get('analytic_account_ids') or []
        if ana_ids:
            ana_clauses = [f"analytic_distribution ? '{aid}'" for aid in ana_ids]
            domain.append(('|' * (len(ana_clauses) - 1),) + tuple(ana_clauses))

        move_lines = self.env['account.move.line'].search(domain)
        accounts = {}
        for line in move_lines:
            acc = line.account_id
            if acc.id not in accounts:
                accounts[acc.id] = {'account_code': acc.code, 'account_name': acc.name, 'lines': [], 'total_debit': 0.0,
                                    'total_credit': 0.0, 'total_balance': 0.0}
            accounts[acc.id]['lines'].append({
                'date': line.date, 'move_name': line.move_name, 'label': line.name,
                'partner': line.partner_id.name or '', 'journal': line.journal_id.name,
                'debit': line.debit, 'credit': line.credit, 'balance': line.balance
            })
            accounts[acc.id]['total_debit'] += line.debit
            accounts[acc.id]['total_credit'] += line.credit
            accounts[acc.id]['total_balance'] += line.balance

        res = sorted(accounts.values(), key=lambda x: x['account_code'] or '')
        return {'accounts': res, 'report_type': 'general_ledger',
                'grand_totals': {'debit': sum(a['total_debit'] for a in res),
                                 'credit': sum(a['total_credit'] for a in res),
                                 'balance': sum(a['total_balance'] for a in res)}}

    @api.model
    def get_trial_balance(self, options):
        return self._get_matrix_data(options, 'trial_balance')

    @api.model
    def get_balance_sheet(self, options):
        return self._get_matrix_data(options, 'balance_sheet')

    @api.model
    def get_profit_loss(self, options):
        return self._get_matrix_data(options, 'profit_loss')

    @api.model
    def _get_matrix_data(self, options, report_type):
        company_id = options.get('company_id') or self.env.company.id
        self = self.with_company(company_id)

        analytics = self._get_analytics(options, company_id)
        ana_map = {str(a.id): a.name for a in analytics}
        ana_names = [a.name for a in analytics]

        # Structure First: Load all relevant accounts
        acc_domain = []
        if report_type == 'profit_loss':
            acc_domain.append(('internal_group', 'in', ['income', 'expense']))
        elif report_type == 'balance_sheet':
            acc_domain.append(('internal_group', 'in', ['asset', 'liability', 'equity']))

        all_accounts = self.env['account.account'].search(acc_domain, order="code asc")
        data_map = {acc.id: {'code': acc.code, 'name': acc.name, 'group': acc.internal_group,
                             'col_balances': {n: 0.0 for n in ana_names}, 'total': 0.0} for acc in all_accounts}

        # Query Lines
        line_domain = [('parent_state', '=', 'posted')]
        if options.get('date_to'): line_domain.append(('date', '<=', options['date_to']))
        if report_type == 'profit_loss' and options.get('date_from'): line_domain.append(
            ('date', '>=', options['date_from']))

        move_lines = self.env['account.move.line'].search(line_domain)
        for line in move_lines:
            if line.account_id.id in data_map:
                dist = line.analytic_distribution or {}
                for aid, weight in dist.items():
                    if aid in ana_map:
                        name = ana_map[aid]
                        amt = (line.balance * weight) / 100.0
                        data_map[line.account_id.id]['col_balances'][name] += amt
                        data_map[line.account_id.id]['total'] += amt

        rows = list(data_map.values())
        if report_type == 'profit_loss': return self._structure_pl(rows, ana_names)
        return self._structure_bs(rows, ana_names)

    def _structure_pl(self, rows, cols):
        sections = {
            'income': {'label': 'Income', 'rows': [r for r in rows if r['group'] == 'income'],
                       'totals': {c: 0.0 for c in cols}, 'total': 0.0},
            'expense': {'label': 'Expenses', 'rows': [r for r in rows if r['group'] == 'expense'],
                        'totals': {c: 0.0 for c in cols}, 'total': 0.0},
        }
        for k in sections:
            for r in sections[k]['rows']:
                sections[k]['total'] += r['total']
                for c in cols: sections[k]['totals'][c] += r['col_balances'][c]
        return {'sections': sections, 'columns': cols, 'report_type': 'profit_loss',
                'net_income': (sections['income']['total'] + sections['expense']['total']) * -1}

    def _structure_bs(self, rows, cols):
        sections = {
            'asset': {'label': 'Assets', 'rows': [r for r in rows if r['group'] == 'asset'],
                      'totals': {c: 0.0 for c in cols}, 'total': 0.0},
            'liability': {'label': 'Liabilities', 'rows': [r for r in rows if r['group'] == 'liability'],
                          'totals': {c: 0.0 for c in cols}, 'total': 0.0},
            'equity': {'label': 'Equity', 'rows': [r for r in rows if r['group'] == 'equity'],
                       'totals': {c: 0.0 for c in cols}, 'total': 0.0},
        }
        for k in sections:
            for r in sections[k]['rows']:
                sections[k]['total'] += r['total']
                for c in cols: sections[k]['totals'][c] += r['col_balances'][c]
        return {'sections': sections, 'columns': cols, 'report_type': 'balance_sheet',
                'total_assets': sections['asset']['total'],
                'total_liab_equity': sections['liability']['total'] + sections['equity']['total']}