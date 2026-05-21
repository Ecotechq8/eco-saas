# -*- encoding: utf-8 -*-
##############################################################################
#
# ERP Heritage
# Copyright (C) 2026 (https://www.erpheritage.com.au/)
#
##############################################################################
"""
Profit and Loss handler.

Period income statement with three sections (Income, Cost of Revenue,
Expenses), a Gross Profit subtotal, and a Net Profit row. Inherits the
sectioned handler base, so query, line, and section formatting come for
free.

Sign convention:

* Income accounts carry credit balances (negative). The sectioned base
  query is called with sign=-1 to flip the display to a positive amount.
* Cost of Revenue and Expense accounts carry debit balances (positive);
  sign=+1.
* Gross Profit = Total Income - Cost of Revenue.
* Net Profit = Gross Profit - Total Expenses.

Section structure:

* Income (account_type in 'income', 'income_other')
* Total Income (subtotal)
* Cost of Revenue (account_type in 'expense_direct_cost')
* Gross Profit (computed)
* Expenses (account_type in 'expense', 'expense_depreciation')
* Total Expenses (subtotal)
* Net Profit (computed)

Localizations can _inherit this handler to add more sections (Other
Income, etc.) or override the account_type tuples to match local chart
of accounts conventions.
"""

from odoo import api, fields, models


class EhProfitAndLossHandler(models.AbstractModel):
    _name = 'eh.account.dynamic.report.handler.profit_and_loss'
    _inherit = 'eh.account.dynamic.report.handler.sectioned'
    _description = "Profit and Loss report handler"

    REPORT_CODE = 'profit_and_loss'
    REPORT_NAME = "Profit and Loss"

    INCOME_TYPES = ('income', 'income_other')
    COST_OF_REVENUE_TYPES = ('expense_direct_cost',)
    EXPENSE_TYPES = ('expense', 'expense_depreciation')

    @api.model
    def compute(self, options):
        date_from = self._extract_date(options, 'date_from')
        date_to = self._extract_date(options, 'date_to')
        company_ids = options.get('company_ids') or [self.env.company.id]
        posted_only = bool(options.get('posted_only', True))
        show_zero = bool(options.get('show_zero', False))
        comparison = options.get('comparison') or 'none'

        lines, totals = self._build_period_lines(
            options=options,
            company_ids=company_ids,
            date_from=date_from, date_to=date_to,
            posted_only=posted_only, show_zero=show_zero,
        )

        meta = {
            'report_code': self.REPORT_CODE,
            'date_from': self._iso_date(date_from),
            'date_to': self._iso_date(date_to),
            'company_ids': sorted(int(c) for c in company_ids),
            'posted_only': posted_only,
            'show_zero': show_zero,
            'comparison': comparison,
        }

        if comparison and comparison != 'none':
            prior_from, prior_to, prior_label = self._resolve_comparison_dates(
                comparison, date_from, date_to,
            )
            if prior_from and prior_to:
                prior_lines, prior_totals = self._build_period_lines(
                    options=options,
                    company_ids=company_ids,
                    date_from=prior_from, date_to=prior_to,
                    posted_only=posted_only, show_zero=show_zero,
                )
                merged = self.merge_comparative_lines(lines, prior_lines)
                meta['prior_date_from'] = self._iso_date(prior_from)
                meta['prior_date_to'] = self._iso_date(prior_to)
                meta['comparison_label'] = prior_label
                return {
                    'columns': self._build_comparative_column_layout(
                        label_name="Account",
                        current_label="%s to %s" % (
                            self._iso_date(date_from),
                            self._iso_date(date_to),
                        ),
                        prior_label="%s to %s" % (
                            self._iso_date(prior_from),
                            self._iso_date(prior_to),
                        ),
                    ),
                    'lines': merged,
                    'totals': {
                        'income': totals['income'],
                        'cost_of_revenue': totals['cost_of_revenue'],
                        'gross_profit': totals['gross_profit'],
                        'expenses': totals['expenses'],
                        'net_profit': totals['net_profit'],
                        'amount': totals['net_profit'],
                        'prior_income': prior_totals['income'],
                        'prior_cost_of_revenue':
                            prior_totals['cost_of_revenue'],
                        'prior_gross_profit': prior_totals['gross_profit'],
                        'prior_expenses': prior_totals['expenses'],
                        'prior_net_profit': prior_totals['net_profit'],
                    },
                    'generated_at': fields.Datetime.now().isoformat(),
                    'meta': meta,
                }

        return {
            'columns': self._build_two_column_layout(),
            'lines': lines,
            'totals': {
                'income': totals['income'],
                'cost_of_revenue': totals['cost_of_revenue'],
                'gross_profit': totals['gross_profit'],
                'expenses': totals['expenses'],
                'net_profit': totals['net_profit'],
                'amount': totals['net_profit'],
            },
            'generated_at': fields.Datetime.now().isoformat(),
            'meta': meta,
        }

    @api.model
    def _build_period_lines(
        self, options, company_ids, date_from, date_to,
        posted_only, show_zero,
    ):
        """Compute one period's section lines and totals."""
        income_rows = self._fetch_grouped_account_totals(
            account_types=self.INCOME_TYPES, sign=-1,
            company_ids=company_ids,
            date_from=date_from, date_to=date_to,
            posted_only=posted_only, options=options,
        )
        cost_of_revenue_rows = self._fetch_grouped_account_totals(
            account_types=self.COST_OF_REVENUE_TYPES, sign=+1,
            company_ids=company_ids,
            date_from=date_from, date_to=date_to,
            posted_only=posted_only, options=options,
        )
        expense_rows = self._fetch_grouped_account_totals(
            account_types=self.EXPENSE_TYPES, sign=+1,
            company_ids=company_ids,
            date_from=date_from, date_to=date_to,
            posted_only=posted_only, options=options,
        )

        income_total = round(sum(r['amount'] for r in income_rows), 2)
        cost_of_revenue_total = round(
            sum(r['amount'] for r in cost_of_revenue_rows), 2,
        )
        gross_profit = round(income_total - cost_of_revenue_total, 2)
        expense_total = round(sum(r['amount'] for r in expense_rows), 2)
        net_profit = round(gross_profit - expense_total, 2)

        lines = []
        lines.append(self._section_header_line("Income", section_id='income'))
        lines.extend(self._render_account_lines(income_rows, show_zero))
        lines.append(self._section_total_line(
            "Total Income", income_total, section_id='income',
        ))
        lines.append(self._section_header_line(
            "Cost of Revenue", section_id='cost_of_revenue',
        ))
        lines.extend(self._render_account_lines(
            cost_of_revenue_rows, show_zero,
        ))
        lines.append(self._section_total_line(
            "Total Cost of Revenue", cost_of_revenue_total,
            section_id='cost_of_revenue',
        ))
        lines.append(self._computed_line(
            'gross_profit', "Gross Profit", gross_profit,
            kind='computed_total',
        ))
        lines.append(self._section_header_line(
            "Expenses", section_id='expenses',
        ))
        lines.extend(self._render_account_lines(expense_rows, show_zero))
        lines.append(self._section_total_line(
            "Total Expenses", expense_total, section_id='expenses',
        ))
        lines.append(self._computed_line(
            'net_profit', "Net Profit", net_profit, kind='net_profit',
        ))
        return lines, {
            'income': income_total,
            'cost_of_revenue': cost_of_revenue_total,
            'gross_profit': gross_profit,
            'expenses': expense_total,
            'net_profit': net_profit,
        }
