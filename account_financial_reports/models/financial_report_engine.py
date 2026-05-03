# -*- coding: utf-8 -*-
"""
financial_report_engine.py
Core data layer for all four financial reports.
Works on plain Odoo 18 Community (no account_reports dependency).
"""
import logging
from collections import defaultdict
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
        Cybrosys-style General Ledger (Odoo 18 safe)
        Uses ORM instead of raw SQL to avoid schema issues.
        """

        # -----------------------------
        # Build domain
        # -----------------------------
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

        # -----------------------------
        # Fetch data
        # -----------------------------
        move_lines = self.env['account.move.line'].search(domain)

        # -----------------------------
        # Group by account
        # -----------------------------
        accounts = {}

        for line in move_lines:
            acc = line.account_id

            if acc.id not in accounts:
                accounts[acc.id] = {
                    'account_id': acc.id,
                    # SAFE: display_name works regardless of schema
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

        # -----------------------------
        # Sort results
        # -----------------------------
        result = sorted(accounts.values(), key=lambda x: x['account_code'])

        # -----------------------------
        # Grand totals
        # -----------------------------
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
        and closing balance.
        """
        params_open, where_open = self._build_where(
            options,
            include_date_range=False,
            before_date_from=True
        )
        params_period, where_period = self._build_where(
            options,
            include_date_range=True
        )

        # Opening balances (BEFORE date_from)
        opening_sql = f"""
            SELECT
                aa.id                AS account_id,
                aa.code              AS account_code,
                aa.name              AS account_name,
                aa.account_type      AS account_type,
                SUM(aml.debit)       AS debit,
                SUM(aml.credit)      AS credit,
                SUM(aml.balance)     AS balance
            FROM account_move_line aml
            JOIN account_account aa ON aa.id = aml.account_id
            JOIN account_move am    ON am.id = aml.move_id
            WHERE am.state = 'posted'
              {where_open}
            GROUP BY aa.id, aa.account_code, aa.name, aa.account_type
        """

        # Period movements
        period_sql = f"""
            SELECT
                aa.id                AS account_id,
                aa.account_code      AS account_code,
                aa.name              AS account_name,
                aa.account_type      AS account_type,
                SUM(aml.debit)       AS debit,
                SUM(aml.credit)      AS credit,
                SUM(aml.balance)     AS balance
            FROM account_move_line aml
            JOIN account_account aa ON aa.id = aml.account_id
            JOIN account_move am    ON am.id = aml.move_id
            WHERE am.state = 'posted'
              {where_period}
            GROUP BY aa.id, aa.account_code, aa.name, aa.account_type
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
            close_bal = open_bal + per_bal

            result.append({
                'account_id': aid,
                'account_code': base.get('account_code', ''),
                'account_name': base.get('account_name', ''),
                'account_type': base.get('account_type', ''),
                'open_balance': open_bal,
                'period_debit': per_deb,
                'period_credit': per_cred,
                'period_balance': per_bal,
                'close_balance': close_bal,
            })

        result.sort(key=lambda x: x['account_code'])

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
        Uses account type (internal_group) to classify accounts.
        """
        params, where = self._build_where(options, include_date_range=(report_type == 'profit_loss'))

        query = f"""
            SELECT
                aa.id              AS account_id,
                aa.account_code            AS account_code,
                aa.name            AS account_name,
                aa.internal_group  AS internal_group,
                SUM(aml.balance)   AS balance
            FROM account_move_line aml
            JOIN account_account aa ON aa.id = aml.account_id
            JOIN account_move    am ON am.id = aml.move_id
            WHERE am.state = 'posted'
              {where}
            GROUP BY aa.id, aa.account_code, aa.name, aa.internal_group
            ORDER BY aa.account_code
        """
        self.env.cr.execute(query, params)
        rows = self.env.cr.dictfetchall()

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
            if ig == 'asset':
                sections['asset']['accounts'].append(r)
                sections['asset']['total'] += bal
            elif ig == 'liability':
                sections['liability']['accounts'].append(r)
                sections['liability']['total'] += bal
            elif ig == 'equity':
                sections['equity']['accounts'].append(r)
                sections['equity']['total'] += bal
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
            if ig == 'income':
                sections['income']['accounts'].append(r)
                sections['income']['total'] += bal
            elif ig == 'expense':
                sections['expense']['accounts'].append(r)
                sections['expense']['total'] += bal
        net_income = sections['income']['total'] - sections['expense']['total']
        return {
            'sections': sections,
            'net_income': net_income,
        }

    @api.model
    def _build_where(self, options, include_date_range=True, before_date_from=False):
        """
        Build a WHERE clause fragment and params dict from filter options.
        Returns (params, where_string).
        """
        where_parts = []
        params = {}

        company_id = options.get('company_id') or self.env.company.id
        where_parts.append("aml.company_id = %(company_id)s")
        params['company_id'] = company_id

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

        # Journal filter
        journal_ids = options.get('journal_ids') or []
        if journal_ids:
            where_parts.append("aml.journal_id = ANY(%(journal_ids)s)")
            params['journal_ids'] = list(journal_ids)

        # Analytic Account filter (analytic_distribution is a jsonb field in Odoo 17/18)
        analytic_ids = options.get('analytic_account_ids') or []
        if analytic_ids:
            # Match any line whose analytic_distribution keys include one of the selected IDs
            analytic_conditions = " OR ".join(
                f"aml.analytic_distribution ? %(analytic_{i})s"
                for i in range(len(analytic_ids))
            )
            where_parts.append(f"({analytic_conditions})")
            for i, aid in enumerate(analytic_ids):
                params[f'analytic_{i}'] = str(aid)

        where = ("AND " + " AND ".join(where_parts)) if where_parts else ""
        return params, where
