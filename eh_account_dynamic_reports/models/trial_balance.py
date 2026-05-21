# -*- encoding: utf-8 -*-
##############################################################################
#
# ERP Heritage
# Copyright (C) 2026 (https://www.erpheritage.com.au/)
#
##############################################################################
"""
Trial Balance handler.

Single SQL pass. Conditional aggregation splits the same set of journal
lines into three buckets per account in one scan:

* opening_balance: lines whose date is strictly before date_from.
* period_debit and period_credit: lines whose date falls within
  [date_from, date_to].

Closing balance is then derived in Python as
opening_balance + period_debit - period_credit. The split into debit and
credit display columns happens at presentation time based on the sign of
the underlying balance, which matches accounting convention.

The handler honours all standard filters (companies, journals, partners,
accounts, posted_only, show_zero) by composing them through MoveLineQuery,
so SQL safety, multi company scoping, and cancelled exclusion are inherited
automatically.
"""

from odoo import api, fields, models
from odoo.tools import SQL

from odoo.addons.eh_account_base.tools.sql_builder import MoveLineQuery


class EhTrialBalanceHandler(models.AbstractModel):
    _name = 'eh.account.dynamic.report.handler.trial_balance'
    _inherit = 'eh.account.dynamic.report.handler'
    _description = "Trial Balance report handler"

    REPORT_CODE = 'trial_balance'
    REPORT_NAME = "Trial Balance"

    @api.model
    def compute(self, options):
        date_from = self._extract_date(options, 'date_from')
        date_to = self._extract_date(options, 'date_to')
        company_ids = options.get('company_ids') or [self.env.company.id]
        posted_only = bool(options.get('posted_only', True))
        show_zero = bool(options.get('show_zero', False))
        rows = self._fetch_account_buckets(
            company_ids=company_ids,
            date_from=date_from,
            date_to=date_to,
            posted_only=posted_only,
            options=options,
        )

        lines, totals = self._build_lines_and_totals(rows, show_zero)

        return {
            'columns': self._build_columns(),
            'lines': lines,
            'totals': totals,
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

    # Drill down behaviour comes from the base handler; the default impl
    # already opens filtered journal items for any line whose id is
    # 'account-N'. Trial Balance follows that scheme exactly.

    # ---- internal helpers ----

    def _build_columns(self):
        return [
            {'expression_label': 'account', 'name': "Account",
             'figure_type': 'string'},
            {'expression_label': 'opening_debit', 'name': "Opening DB",
             'figure_type': 'monetary'},
            {'expression_label': 'opening_credit', 'name': "Opening CR",
             'figure_type': 'monetary'},
            {'expression_label': 'period_debit', 'name': "Movement DB",
             'figure_type': 'monetary'},
            {'expression_label': 'period_credit', 'name': "Movement CR",
             'figure_type': 'monetary'},
            {'expression_label': 'closing_debit', 'name': "Closing DB",
             'figure_type': 'monetary'},
            {'expression_label': 'closing_credit', 'name': "Closing CR",
             'figure_type': 'monetary'},
        ]

    def _fetch_account_buckets(
        self, company_ids, date_from, date_to, posted_only, options,
    ):
        query = MoveLineQuery(self.env, company_ids=company_ids)
        # Lines up to date_to participate. We need everything before
        # date_from for the opening balance plus everything in the period
        # for the movement columns.
        query.where_date_range(date_to=date_to)
        if posted_only:
            query.where_posted_only()
        self.apply_common_filters(query, options)

        query.select_field('account_id')
        query.select_account_field('code', alias='account_code')
        query.select_account_field('name', alias='account_name')
        query.select(
            SQL("SUM(CASE WHEN aml.date < %s THEN aml.balance ELSE 0 END)",
                date_from),
            'opening_balance',
        )
        query.select(
            SQL(
                "SUM(CASE WHEN aml.date >= %s AND aml.date <= %s "
                "THEN aml.debit ELSE 0 END)",
                date_from, date_to,
            ),
            'period_debit',
        )
        query.select(
            SQL(
                "SUM(CASE WHEN aml.date >= %s AND aml.date <= %s "
                "THEN aml.credit ELSE 0 END)",
                date_from, date_to,
            ),
            'period_credit',
        )
        # Group by all non aggregated SELECT expressions for portability.
        query.group_by(
            SQL("aml.account_id"),
            SQL("(acc.code_store ->> aml.company_id::text)"),
            SQL("(acc.name ->> 'en_US')"),
        )
        query.order_by_account_field('code', 'ASC')
        return query.execute()

    def _build_lines_and_totals(self, rows, show_zero):
        lines = []
        totals = {
            'opening_debit': 0.0, 'opening_credit': 0.0,
            'period_debit': 0.0, 'period_credit': 0.0,
            'closing_debit': 0.0, 'closing_credit': 0.0,
        }
        for row in rows:
            opening = float(row.get('opening_balance') or 0.0)
            period_debit = float(row.get('period_debit') or 0.0)
            period_credit = float(row.get('period_credit') or 0.0)
            closing = opening + period_debit - period_credit

            opening_debit = opening if opening > 0 else 0.0
            opening_credit = -opening if opening < 0 else 0.0
            closing_debit = closing if closing > 0 else 0.0
            closing_credit = -closing if closing < 0 else 0.0

            sum_all = (opening_debit + opening_credit + period_debit
                       + period_credit + closing_debit + closing_credit)
            if not show_zero and sum_all == 0.0:
                continue

            lines.append({
                'id': "account-%s" % row['account_id'],
                'name': "%s %s" % (row['account_code'], row['account_name']),
                'level': 1,
                'columns': [
                    {'expression_label': 'opening_debit',
                     'value': round(opening_debit, 2)},
                    {'expression_label': 'opening_credit',
                     'value': round(opening_credit, 2)},
                    {'expression_label': 'period_debit',
                     'value': round(period_debit, 2)},
                    {'expression_label': 'period_credit',
                     'value': round(period_credit, 2)},
                    {'expression_label': 'closing_debit',
                     'value': round(closing_debit, 2)},
                    {'expression_label': 'closing_credit',
                     'value': round(closing_credit, 2)},
                ],
                'unfoldable': False,
                'meta': {
                    'account_id': row['account_id'],
                    'account_code': row['account_code'],
                },
            })

            totals['opening_debit'] += opening_debit
            totals['opening_credit'] += opening_credit
            totals['period_debit'] += period_debit
            totals['period_credit'] += period_credit
            totals['closing_debit'] += closing_debit
            totals['closing_credit'] += closing_credit

        totals = {k: round(v, 2) for k, v in totals.items()}
        return lines, totals
