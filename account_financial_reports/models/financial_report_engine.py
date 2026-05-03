# -*- coding: utf-8 -*-
"""
financial_report_engine.py
Core data layer for all four financial reports.
Works on plain Odoo 18 Community.
"""
import logging
from odoo import models, api, fields, _

_logger = logging.getLogger(__name__)


class FinancialReportEngine(models.AbstractModel):
    _name = 'financial.report.engine'
    _description = 'Financial Report Engine'

    @api.model
    def get_general_ledger(self, options):
        domain = [('parent_state', '=', 'posted')]
        if options.get('date_from'):
            domain.append(('date', '>=', options['date_from']))
        if options.get('date_to'):
            domain.append(('date', '<=', options['date_to']))
        if options.get('journal_ids'):
            domain.append(('journal_id', 'in', options['journal_ids']))

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
        return {'accounts': result, 'grand_totals': grand}

    @api.model
    def get_trial_balance(self, options):
        params_open, where_open = self._build_where(options, include_date_range=False, before_date_from=True)
        params_period, where_period = self._build_where(options, include_date_range=True)

        # Odoo 18 safe: Use aa.code
        account_select = "COALESCE(aa.code, aa.name)"

        opening_sql = f"""
            SELECT aa.id AS account_id, {account_select} AS account_code, aa.name AS account_name,
                   aa.account_type, SUM(aml.balance) AS balance
            FROM account_move_line aml
            JOIN account_account aa ON aa.id = aml.account_id
            JOIN account_move am ON am.id = aml.move_id
            WHERE am.state = 'posted' {where_open}
            GROUP BY aa.id, aa.code, aa.name, aa.account_type
        """
        period_sql = f"""
            SELECT aa.id AS account_id, {account_select} AS account_code, aa.name AS account_name,
                   aa.account_type, SUM(aml.debit) AS debit, SUM(aml.credit) AS credit, SUM(aml.balance) AS balance
            FROM account_move_line aml
            JOIN account_account aa ON aa.id = aml.account_id
            JOIN account_move am ON am.id = aml.move_id
            WHERE am.state = 'posted' {where_period}
            GROUP BY aa.id, aa.code, aa.name, aa.account_type
        """

        self.env.cr.execute(opening_sql, params_open)
        opening_rows = {r['account_id']: r for r in self.env.cr.dictfetchall()}
        self.env.cr.execute(period_sql, params_period)
        period_rows = {r['account_id']: r for r in self.env.cr.dictfetchall()}

        all_ids = set(opening_rows) | set(period_rows)
        result = []
        for aid in all_ids:
            op = opening_rows.get(aid, {})
            pr = period_rows.get(aid, {})
            base = pr if pr else op
            open_bal = op.get('balance', 0.0) or 0.0
            per_deb = pr.get('debit', 0.0) or 0.0
            per_cred = pr.get('credit', 0.0) or 0.0
            per_bal = pr.get('balance', 0.0) or 0.0
            result.append({
                'account_id': aid,
                'account_code': base.get('account_code', ''),
                'account_name': base.get('account_name', ''),
                'open_balance': open_bal,
                'period_debit': per_deb,
                'period_credit': per_cred,
                'period_balance': per_bal,
                'close_balance': open_bal + per_bal,
            })
        result.sort(key=lambda x: x['account_code'])
        return {'lines': result, 'totals': {k: sum(r[k] for r in result) for k in
                                            ['open_balance', 'period_debit', 'period_credit', 'period_balance',
                                             'close_balance']}}

    @api.model
    def get_balance_sheet(self, options):
        return self._get_pnl_or_bs(options, report_type='balance_sheet')

    @api.model
    def get_profit_loss(self, options):
        return self._get_pnl_or_bs(options, report_type='profit_loss')

    @api.model
    def _get_pnl_or_bs(self, options, report_type):
        params, where = self._build_where(options, include_date_range=(report_type == 'profit_loss'))

        # FIXED: Using aa.code instead of aa.account_code
        query = f"""
            SELECT
                aa.id              AS account_id,
                aa.code            AS account_code,
                aa.name            AS account_name,
                aa.internal_group  AS internal_group,
                SUM(aml.balance)   AS balance
            FROM account_move_line aml
            JOIN account_account aa ON aa.id = aml.account_id
            JOIN account_move    am ON am.id = aml.move_id
            WHERE am.state = 'posted'
              {where}
            GROUP BY aa.id, aa.code, aa.name, aa.internal_group
            ORDER BY aa.code
        """
        self.env.cr.execute(query, params)
        rows = self.env.cr.dictfetchall()

        if report_type == 'balance_sheet':
            return self._structure_balance_sheet(rows)
        return self._structure_profit_loss(rows)

    def _structure_balance_sheet(self, rows):
        sections = {
            'asset': {'label': _('Assets'), 'accounts': [], 'total': 0.0},
            'liability': {'label': _('Liabilities'), 'accounts': [], 'total': 0.0},
            'equity': {'label': _('Equity'), 'accounts': [], 'total': 0.0},
        }
        for r in rows:
            ig = r.get('internal_group', '')
            if ig in sections:
                sections[ig]['accounts'].append(r)
                sections[ig]['total'] += (r['balance'] or 0.0)

        return {
            'sections': sections,
            'total_assets': sections['asset']['total'],
            'total_liabilities_equity': sections['liability']['total'] + sections['equity']['total'],
        }

    def _structure_profit_loss(self, rows):
        sections = {
            'income': {'label': _('Income'), 'accounts': [], 'total': 0.0},
            'expense': {'label': _('Expenses'), 'accounts': [], 'total': 0.0},
        }
        for r in rows:
            ig = r.get('internal_group', '')
            if ig in sections:
                sections[ig]['accounts'].append(r)
                sections[ig]['total'] += (r['balance'] or 0.0)

        # In P&L, Credit (Income) is usually negative in DB, Expenses positive.
        # We adjust the math based on how your chart of accounts stores balances.
        net_income = (sections['income']['total'] + sections['expense']['total']) * -1
        return {'sections': sections, 'net_income': net_income}

    @api.model
    def _build_where(self, options, include_date_range=True, before_date_from=False):
        where_parts = ["aml.company_id = %(company_id)s"]
        params = {'company_id': options.get('company_id') or self.env.company.id}

        if include_date_range:
            if options.get('date_from'):
                where_parts.append("am.date >= %(date_from)s")
                params['date_from'] = options['date_from']
            if options.get('date_to'):
                where_parts.append("am.date <= %(date_to)s")
                params['date_to'] = options['date_to']

        if before_date_from and options.get('date_from'):
            where_parts.append("am.date < %(date_from_open)s")
            params['date_from_open'] = options['date_from']

        if options.get('journal_ids'):
            where_parts.append("aml.journal_id = ANY(%(journal_ids)s)")
            params['journal_ids'] = list(options['journal_ids'])

        where = "AND " + " AND ".join(where_parts)
        return params, where