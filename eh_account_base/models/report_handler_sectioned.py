# -*- encoding: utf-8 -*-
##############################################################################
#
# ERP Heritage
# Copyright (C) 2026 (https://www.erpheritage.com.au/)
#
##############################################################################
"""
Intermediate handler base for section based reports.

Profit and Loss, Balance Sheet, and other "sections of accounts" reports
share the same shape:

* One or more sections, each containing a header line, one line per
  contributing account, and a section total.
* Per account aggregation comes from a single SQL pass per section,
  composed via MoveLineQuery.
* Optional aggregate scalars (Current Year Earnings on a Balance Sheet,
  for example) come from a smaller SQL pass with no group by.

Concrete handlers _inherit this model and call the helpers; they decide
which sections to render, how the totals roll up, and which line ids to
issue. Trial Balance and General Ledger do NOT inherit this base because
their layout differs.
"""

from datetime import timedelta

from odoo import api, models
from odoo.tools import SQL

from odoo.addons.eh_account_base.tools.sql_builder import MoveLineQuery


class EhAccountDynamicReportSectionedHandler(models.AbstractModel):
    _name = 'eh.account.dynamic.report.handler.sectioned'
    _inherit = 'eh.account.dynamic.report.handler'
    _description = "Base for section based dynamic report handlers"

    # ---- column layout ----

    @api.model
    def _build_two_column_layout(self, label_name="Description",
                                 amount_name="Amount"):
        """Return the standard two column layout: label on the left,
        monetary amount on the right. Most section based reports use this.
        """
        return [
            {'expression_label': 'account', 'name': label_name,
             'figure_type': 'string'},
            {'expression_label': 'amount', 'name': amount_name,
             'figure_type': 'monetary'},
        ]

    @api.model
    def _build_comparative_column_layout(
        self, label_name="Description", current_label="Current",
        prior_label="Prior", variance_label="Variance",
        variance_pct_label="Var %",
    ):
        """Return the comparative four-column layout: label + current
        amount + prior amount + variance + variance %. Used when
        options['comparison'] is set.
        """
        return [
            {'expression_label': 'account', 'name': label_name,
             'figure_type': 'string'},
            {'expression_label': 'amount', 'name': current_label,
             'figure_type': 'monetary'},
            {'expression_label': 'prior_amount', 'name': prior_label,
             'figure_type': 'monetary'},
            {'expression_label': 'variance', 'name': variance_label,
             'figure_type': 'monetary'},
            {'expression_label': 'variance_pct', 'name': variance_pct_label,
             'figure_type': 'percentage'},
        ]

    # ---- comparison helpers ----

    @api.model
    def _resolve_comparison_dates(self, mode, date_from, date_to):
        """Return (prior_from, prior_to, label) for a given comparison mode.

        Modes supported:
        * 'previous_period' shifts the [date_from, date_to] window backward
          by exactly its length minus one day, so a January window compares
          against December.
        * 'previous_year' shifts both ends back by one calendar year. A
          leap-day input (Feb 29) is shifted to Feb 28 of the prior year.

        Returns (None, None, '') for any other mode (no comparison).
        """
        if mode == 'previous_period':
            length = (date_to - date_from).days + 1
            prior_to = date_from - timedelta(days=1)
            prior_from = prior_to - timedelta(days=length - 1)
            return prior_from, prior_to, "Previous period"
        if mode == 'previous_year':
            try:
                prior_from = date_from.replace(year=date_from.year - 1)
            except ValueError:
                prior_from = date_from.replace(
                    year=date_from.year - 1, day=date_from.day - 1,
                )
            try:
                prior_to = date_to.replace(year=date_to.year - 1)
            except ValueError:
                prior_to = date_to.replace(
                    year=date_to.year - 1, day=date_to.day - 1,
                )
            return prior_from, prior_to, "Same period last year"
        return None, None, ""

    @staticmethod
    def _safe_pct(prior, current):
        """Variance percentage that does not divide by zero. Returns the
        difference as a fraction (1.0 = 100%) so the figure_type 'percentage'
        renders it correctly. With a zero prior, returns 1.0 if the current
        is non-zero (full overrun) and 0.0 otherwise.
        """
        if prior:
            return (current - prior) / abs(prior)
        if current:
            return 1.0
        return 0.0

    @api.model
    def merge_comparative_lines(self, current_lines, prior_lines):
        """Merge two single-amount line lists into multi-column lines.

        Both inputs are line lists as produced by the section helpers
        below; matching is by line.id. The output extends each current
        line's `columns` with the prior-period amount, the variance, and
        the variance percentage. Lines that exist in only one of the
        inputs receive zero on the missing side.
        """
        prior_by_id = {l['id']: l for l in prior_lines}
        merged = []
        seen = set()
        for cur in current_lines:
            seen.add(cur['id'])
            cur_amount = self._line_first_value(cur)
            prior = prior_by_id.get(cur['id'])
            prior_amount = self._line_first_value(prior) if prior else 0.0
            variance = round((cur_amount or 0.0) - (prior_amount or 0.0), 2)
            new_line = dict(cur)
            new_line['columns'] = [
                {'expression_label': 'amount', 'value': cur_amount},
                {'expression_label': 'prior_amount', 'value': prior_amount},
                {'expression_label': 'variance', 'value': variance},
                {'expression_label': 'variance_pct',
                 'value': self._safe_pct(prior_amount, cur_amount)},
            ]
            merged.append(new_line)
        # Lines that exist only in the prior period: emit them with a
        # zero current amount so the user sees that the activity has
        # ceased.
        for prior_id, prior in prior_by_id.items():
            if prior_id in seen:
                continue
            prior_amount = self._line_first_value(prior)
            new_line = dict(prior)
            new_line['columns'] = [
                {'expression_label': 'amount', 'value': 0.0},
                {'expression_label': 'prior_amount', 'value': prior_amount},
                {'expression_label': 'variance', 'value': -prior_amount},
                {'expression_label': 'variance_pct', 'value': -1.0},
            ]
            merged.append(new_line)
        return merged

    @staticmethod
    def _line_first_value(line):
        if not line:
            return 0.0
        cols = line.get('columns') or []
        if not cols:
            return 0.0
        return cols[0].get('value') or 0.0

    # ---- query helpers ----

    @api.model
    def _fetch_grouped_account_totals(
        self, account_types=None, company_ids=None,
        date_from=None, date_to=None,
        posted_only=True, options=None, sign=1,
    ):
        """Run a per account aggregation and return a list of dicts.

        Each result dict has keys: account_id, account_code, account_name,
        amount. The amount is the sum of balance for the matching journal
        lines, multiplied by sign. Sign is +1 for naturally debit accounts
        (assets, expenses) and -1 for naturally credit accounts (income,
        liabilities, equity), so amounts always present as positive in the
        report.
        """
        options = options or {}
        company_ids = company_ids or [self.env.company.id]
        query = MoveLineQuery(self.env, company_ids=company_ids)
        query.where_date_range(date_from=date_from, date_to=date_to)
        if posted_only:
            query.where_posted_only()
        if account_types:
            query.where_account_types(account_types)
        self.apply_common_filters(query, options)

        query.select_field('account_id')
        query.select_account_field('code', alias='account_code')
        query.select_account_field('name', alias='account_name')
        query.select(SQL("SUM(aml.balance)"), 'balance')
        query.group_by(
            SQL("aml.account_id"),
            SQL("(acc.code_store ->> aml.company_id::text)"),
            query._translated_account_name_sql(),
        )
        query.order_by_account_field('code', 'ASC')

        rows = query.execute()
        return [
            {
                'account_id': r['account_id'],
                'account_code': r['account_code'],
                'account_name': r['account_name'],
                'amount': float(r['balance'] or 0.0) * sign,
            }
            for r in rows
        ]

    @api.model
    def _fetch_aggregate_balance(
        self, account_types=None, company_ids=None,
        date_from=None, date_to=None,
        posted_only=True, options=None, sign=1,
    ):
        """Return a scalar: sum of balance with the given filters, multiplied
        by sign. No group by. Useful for computed lines like Current Year
        Earnings on a Balance Sheet.
        """
        options = options or {}
        company_ids = company_ids or [self.env.company.id]
        query = MoveLineQuery(self.env, company_ids=company_ids)
        query.where_date_range(date_from=date_from, date_to=date_to)
        if posted_only:
            query.where_posted_only()
        if account_types:
            query.where_account_types(account_types)
        self.apply_common_filters(query, options)

        query.select(SQL("SUM(aml.balance)"), 'balance')
        rows = query.execute()
        if not rows:
            return 0.0
        return float(rows[0].get('balance') or 0.0) * sign

    # ---- line factories ----

    @api.model
    def _render_account_lines(self, rows, show_zero=False):
        """Convert grouped account totals into report line dicts."""
        lines = []
        for r in rows:
            amount = round(r['amount'], 2)
            if not show_zero and amount == 0.0:
                continue
            lines.append({
                'id': "account-%s" % r['account_id'],
                'name': "%s %s" % (r['account_code'], r['account_name']),
                'level': 1,
                'columns': [
                    {'expression_label': 'amount', 'value': amount},
                ],
                'unfoldable': False,
                'meta': {
                    'account_id': r['account_id'],
                    'account_code': r['account_code'],
                },
            })
        return lines

    @api.model
    def _section_header_line(self, name, section_id):
        # Empty string instead of None for the value: keeps the cell
        # blank in the OWL renderer and the PDF/XLSX exporter, but is
        # also serialisable through XML-RPC (where None is rejected
        # unless allow_none=True is set on the Marshaller, which the
        # Odoo default Marshaller does not).
        return {
            'id': "section-%s-header" % section_id,
            'name': name,
            'level': 0,
            'columns': [{'expression_label': 'amount', 'value': ''}],
            'unfoldable': False,
            'meta': {'kind': 'section_header', 'section_id': section_id},
        }

    @api.model
    def _section_total_line(self, name, total, section_id):
        return {
            'id': "section-%s-total" % section_id,
            'name': name,
            'level': 0,
            'columns': [
                {'expression_label': 'amount', 'value': round(total, 2)},
            ],
            'unfoldable': False,
            'meta': {'kind': 'section_total', 'section_id': section_id},
        }

    @api.model
    def _computed_line(self, line_id, name, amount, kind='computed'):
        """Standalone computed line (Net Profit, Current Year Earnings,
        Balance Check, etc.). Sits at level 0 in bold.
        """
        return {
            'id': line_id,
            'name': name,
            'level': 0,
            'columns': [
                {'expression_label': 'amount', 'value': round(amount, 2)},
            ],
            'unfoldable': False,
            'meta': {'kind': kind},
        }
