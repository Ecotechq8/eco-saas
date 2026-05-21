# -*- encoding: utf-8 -*-
##############################################################################
#
# ERP Heritage
# Copyright (C) 2026 (https://www.erpheritage.com.au/)
#
##############################################################################
"""
Cash Flow Statement handler (direct method).

Classifies cash movements into operating, investing, and financing
activities by inspecting the non cash counterparts of each cash affecting
move. The direct method was chosen for v1 because it is more transparent
to SMB readers than the indirect method (which starts from net income and
adjusts), and because it composes naturally with the SQL builder.

Algorithm:

1. Find all moves that have at least one cash account line in the period.
2. For those moves, aggregate non cash line balances by account_type. The
   cash impact attributable to each account_type is SUM(-balance). Because
   each move balances, the sum of -balance over non cash lines equals the
   sum of balance over cash lines.
3. Group account_type buckets into the three activity sections.
4. Add a Net Change line, Opening Cash, Closing Cash, and a Balance Check.

The Balance Check verifies the identity:

    Closing Cash = Opening Cash + Net Change in Cash

If non zero, the underlying ledger has unbalanced postings or there is a
filter inconsistency, and the line surfaces this immediately.

Limitations:

* Only `asset_cash` account_type is considered cash. Credit cards
  (`liability_credit_card`) are treated as financing rather than cash.
  Phase 2 may add a configurable "cash and cash equivalents" set.
* Foreign currency revaluation is mixed in with the activity it affects;
  a more rigorous CFS would isolate FX gains as a non cash adjustment.
"""

from odoo import api, fields, models
from odoo.tools import SQL

from odoo.addons.eh_account_base.tools.sql_builder import MoveLineQuery


class EhCashFlowHandler(models.AbstractModel):
    _name = 'eh.account.dynamic.report.handler.cash_flow'
    _inherit = 'eh.account.dynamic.report.handler.sectioned'
    _description = "Cash Flow Statement report handler"

    REPORT_CODE = 'cash_flow'
    REPORT_NAME = "Cash Flow Statement"

    CASH_TYPES = ('asset_cash',)

    OPERATING_TYPES = (
        'income', 'income_other',
        'expense', 'expense_depreciation', 'expense_direct_cost',
        'asset_receivable', 'liability_payable',
        'asset_current', 'liability_current',
    )
    INVESTING_TYPES = (
        'asset_fixed', 'asset_non_current', 'asset_prepayments',
    )
    FINANCING_TYPES = (
        'liability_non_current', 'liability_credit_card',
        'equity', 'equity_unaffected',
    )

    ACCOUNT_TYPE_LABELS = {
        'income': "Income",
        'income_other': "Other Income",
        'expense': "Expenses",
        'expense_depreciation': "Depreciation",
        'expense_direct_cost': "Direct Costs",
        'asset_receivable': "Receivables",
        'liability_payable': "Payables",
        'asset_current': "Other Current Assets",
        'liability_current': "Other Current Liabilities",
        'asset_fixed': "Fixed Assets",
        'asset_non_current': "Non Current Assets",
        'asset_prepayments': "Prepayments",
        'liability_non_current': "Long Term Liabilities",
        'liability_credit_card': "Credit Cards",
        'equity': "Equity",
        'equity_unaffected': "Current Year Earnings",
    }

    @api.model
    def compute(self, options):
        date_from = self._extract_date(options, 'date_from')
        date_to = self._extract_date(options, 'date_to')
        company_ids = options.get('company_ids') or [self.env.company.id]
        posted_only = bool(options.get('posted_only', True))
        show_zero = bool(options.get('show_zero', False))

        cash_move_ids = self._fetch_cash_active_move_ids(
            company_ids=company_ids,
            date_from=date_from, date_to=date_to,
            posted_only=posted_only, options=options,
        )
        impacts_by_type = self._fetch_cash_impacts(
            move_ids=cash_move_ids,
            company_ids=company_ids,
            posted_only=posted_only, options=options,
        ) if cash_move_ids else {}

        operating_total = round(
            self._sum_types(impacts_by_type, self.OPERATING_TYPES), 2,
        )
        investing_total = round(
            self._sum_types(impacts_by_type, self.INVESTING_TYPES), 2,
        )
        financing_total = round(
            self._sum_types(impacts_by_type, self.FINANCING_TYPES), 2,
        )
        net_change = round(
            operating_total + investing_total + financing_total, 2,
        )

        opening_cash = round(self._fetch_cash_balance(
            company_ids=company_ids,
            cutoff_date=date_from, posted_only=posted_only, before=True,
        ), 2)
        closing_cash = round(self._fetch_cash_balance(
            company_ids=company_ids,
            cutoff_date=date_to, posted_only=posted_only, before=False,
        ), 2)
        balance_check = round(
            closing_cash - opening_cash - net_change, 2,
        )

        lines = []
        lines.extend(self._render_section(
            "Operating Activities", 'operating',
            self.OPERATING_TYPES, impacts_by_type,
            section_total=operating_total, show_zero=show_zero,
        ))
        lines.extend(self._render_section(
            "Investing Activities", 'investing',
            self.INVESTING_TYPES, impacts_by_type,
            section_total=investing_total, show_zero=show_zero,
        ))
        lines.extend(self._render_section(
            "Financing Activities", 'financing',
            self.FINANCING_TYPES, impacts_by_type,
            section_total=financing_total, show_zero=show_zero,
        ))
        lines.append(self._computed_line(
            'net_change_in_cash', "Net Change in Cash",
            net_change, kind='net_change',
        ))
        lines.append(self._computed_line(
            'opening_cash_balance', "Opening Cash Balance",
            opening_cash, kind='cash_balance',
        ))
        lines.append(self._computed_line(
            'closing_cash_balance', "Closing Cash Balance",
            closing_cash, kind='cash_balance',
        ))
        lines.append(self._computed_line(
            'cash_balance_check', "Balance Check",
            balance_check, kind='balance_check',
        ))

        return {
            'columns': self._build_two_column_layout(),
            'lines': lines,
            'totals': {
                'operating': operating_total,
                'investing': investing_total,
                'financing': financing_total,
                'net_change_in_cash': net_change,
                'opening_cash_balance': opening_cash,
                'closing_cash_balance': closing_cash,
                'balance_check': balance_check,
            },
            'generated_at': fields.Datetime.now().isoformat(),
            'meta': {
                'report_code': self.REPORT_CODE,
                'date_from': self._iso_date(date_from),
                'date_to': self._iso_date(date_to),
                'company_ids': sorted(int(c) for c in company_ids),
                'posted_only': posted_only,
                'show_zero': show_zero,
            },
        }

    # ---- internal helpers ----

    def _fetch_cash_active_move_ids(
        self, company_ids, date_from, date_to, posted_only, options,
    ):
        query = MoveLineQuery(self.env, company_ids=company_ids)
        query.where_date_range(date_from=date_from, date_to=date_to)
        query.where_account_types(self.CASH_TYPES)
        if posted_only:
            query.where_posted_only()
        self.apply_common_filters(query, options)
        # GROUP BY produces unique move_ids without needing DISTINCT.
        query.select_field('move_id')
        query.group_by('move_id')
        return [r['move_id'] for r in query.execute()]

    def _fetch_cash_impacts(
        self, move_ids, company_ids, posted_only, options,
    ):
        if not move_ids:
            return {}
        query = MoveLineQuery(self.env, company_ids=company_ids)
        if posted_only:
            query.where_posted_only()
        query.join_account()
        query.where_raw(SQL("acc.account_type != %s", 'asset_cash'))
        query.where_raw(SQL("aml.move_id IN %s", tuple(move_ids)))
        if options.get('journal_ids'):
            query.where_journals(options['journal_ids'])
        if options.get('partner_ids'):
            query.where_partners(options['partner_ids'])
        if options.get('analytic_account_ids'):
            query.where_analytic_accounts(options['analytic_account_ids'])
        if options.get('analytic_plan_ids'):
            query.where_analytic_plans(options['analytic_plan_ids'])

        query.select_account_field('account_type', alias='account_type')
        query.select(SQL("SUM(-aml.balance)"), 'cash_impact')
        query.group_by(SQL("acc.account_type"))

        rows = query.execute()
        return {
            r['account_type']: float(r['cash_impact'] or 0.0)
            for r in rows
        }

    def _fetch_cash_balance(
        self, company_ids, cutoff_date, posted_only, before,
    ):
        """Sum balance on cash accounts.

        before=True: lines strictly before cutoff_date (used for opening).
        before=False: lines up to and including cutoff_date (closing).
        """
        query = MoveLineQuery(self.env, company_ids=company_ids)
        query.where_account_types(self.CASH_TYPES)
        if posted_only:
            query.where_posted_only()
        if before:
            query.where_raw(SQL("aml.date < %s", cutoff_date))
        else:
            query.where_date_range(date_to=cutoff_date)
        query.select(SQL("COALESCE(SUM(aml.balance), 0)"), 'balance')
        rows = query.execute()
        if not rows:
            return 0.0
        return float(rows[0].get('balance') or 0.0)

    @staticmethod
    def _sum_types(impacts_by_type, types):
        return sum(impacts_by_type.get(t, 0.0) for t in types)

    def _render_section(
        self, name, section_id, types, impacts_by_type,
        section_total, show_zero,
    ):
        lines = [self._section_header_line(name, section_id)]
        for t in types:
            amount = round(impacts_by_type.get(t, 0.0), 2)
            if not show_zero and amount == 0.0:
                continue
            label = self.ACCOUNT_TYPE_LABELS.get(
                t, t.replace('_', ' ').title(),
            )
            lines.append({
                'id': "section-%s-line-%s" % (section_id, t),
                'name': label,
                'level': 1,
                'columns': [
                    {'expression_label': 'amount', 'value': amount},
                ],
                'unfoldable': False,
                'meta': {
                    'kind': 'section_line',
                    'section_id': section_id,
                    'account_type': t,
                },
            })
        lines.append(self._section_total_line(
            "Total %s" % name, section_total, section_id=section_id,
        ))
        return lines
