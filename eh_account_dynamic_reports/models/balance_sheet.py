# -*- encoding: utf-8 -*-
##############################################################################
#
# ERP Heritage
# Copyright (C) 2026 (https://www.erpheritage.com.au/)
#
##############################################################################
"""
Balance Sheet handler.

Cumulative point in time snapshot at date_to. Three top level sections
(ASSETS, LIABILITIES, EQUITY) rendered as a hierarchical tree with
subsections per Odoo account-type family, plus three computed lines
(Current Year Earnings, Liabilities + Equity, Balance Check).

date_from is intentionally ignored: a balance sheet is a snapshot, not a
period activity report. Only date_to drives the cumulative aggregation.
The wizard still supplies date_from because the same wizard form is shared
across reports; the handler simply does not use it.

Hierarchical layout::

    ASSETS
      Current Assets (group)
        Bank and Cash Accounts ... Total Bank and Cash Accounts
        Receivables            ... Total Receivables
        Current Assets         ... Total Current Assets
        Prepayments            ... Total Prepayments
        Total Current Assets   (group subtotal)
      Plus Fixed Assets        ... Total Fixed Assets
      Plus Non-current Assets  ... Total Non-current Assets
      Total ASSETS

    LIABILITIES
      Current Liabilities (group)
        Current Liabilities    ... Total Current Liabilities
        Payables               ... Total Payables
        Total Current Liabilities (group subtotal)
      Plus Non-current Liabilities ... Total Non-current Liabilities
      Total LIABILITIES

    EQUITY
      equity account lines
      Total EQUITY
      Current Year Earnings

    LIABILITIES + EQUITY
    Balance Check

Sign convention:

* Asset accounts: debit balance is positive. sign=+1.
* Liability accounts: credit balance is positive in display. sign=-1.
* Equity accounts: credit balance is positive in display. sign=-1.
* Current Year Earnings: sum of -balance over income+expense accounts up
  to date_to. Equivalent to (income - expenses) before year end close.

Balance Check identity:

    Total Assets = Total Liabilities + Total Equity + Current Year Earnings

If Balance Check is not zero, the ledger has unbalanced postings or there
is a date or filter mismatch. The line is shown to the user so any drift
is immediately visible.

Localizations can _inherit this handler and override ASSET_GROUPS /
LIABILITY_GROUPS to add, remove, or rename subsections to match a local
chart of accounts convention.
"""

from odoo import api, fields, models


class EhBalanceSheetHandler(models.AbstractModel):
    _name = 'eh.account.dynamic.report.handler.balance_sheet'
    _inherit = 'eh.account.dynamic.report.handler.sectioned'
    _description = "Balance Sheet report handler"

    REPORT_CODE = 'balance_sheet'
    REPORT_NAME = "Balance Sheet"

    # Inner subsections of the "Current Assets" group, in display order.
    CURRENT_ASSET_SUBSECTIONS = (
        # (section_id, label, total_label, account_types)
        ('bank_cash', "Bank and Cash Accounts",
         "Total Bank and Cash Accounts", ('asset_cash',)),
        ('receivables', "Receivables", "Total Receivables",
         ('asset_receivable',)),
        ('current_assets_inner', "Current Assets", "Total Current Assets",
         ('asset_current',)),
        ('prepayments', "Prepayments", "Total Prepayments",
         ('asset_prepayments',)),
    )
    # Top-level groups under ASSETS, after the Current Assets group.
    OTHER_ASSET_GROUPS = (
        ('fixed_assets', "Plus Fixed Assets", "Total Fixed Assets",
         ('asset_fixed',)),
        ('non_current_assets', "Plus Non-current Assets",
         "Total Non-current Assets", ('asset_non_current',)),
    )
    # Inner subsections of the "Current Liabilities" group.
    CURRENT_LIABILITY_SUBSECTIONS = (
        ('current_liabilities_inner', "Current Liabilities",
         "Total Current Liabilities",
         ('liability_current', 'liability_credit_card')),
        ('payables', "Payables", "Total Payables", ('liability_payable',)),
    )
    OTHER_LIABILITY_GROUPS = (
        ('non_current_liabilities', "Plus Non-current Liabilities",
         "Total Non-current Liabilities", ('liability_non_current',)),
    )
    EQUITY_TYPES = ('equity', 'equity_unaffected')
    INCOME_TYPES = ('income', 'income_other')
    EXPENSE_TYPES = ('expense', 'expense_depreciation', 'expense_direct_cost')

    @api.model
    def compute(self, options):
        date_to = self._extract_date(options, 'date_to')
        company_ids = options.get('company_ids') or [self.env.company.id]
        posted_only = bool(options.get('posted_only', True))
        show_zero = bool(options.get('show_zero', False))
        comparison = options.get('comparison') or 'none'

        lines, totals = self._build_snapshot_lines(
            options=options, company_ids=company_ids, date_to=date_to,
            posted_only=posted_only, show_zero=show_zero,
        )
        meta = {
            'report_code': self.REPORT_CODE,
            'date_to': self._iso_date(date_to),
            'company_ids': sorted(int(c) for c in company_ids),
            'posted_only': posted_only,
            'show_zero': show_zero,
            'comparison': comparison,
        }

        if comparison and comparison != 'none':
            # For a snapshot report we compare against an as-of point in
            # the past: end of prior period (period mode) or one year
            # earlier (year mode). date_from is unused so we treat
            # date_to as both ends of a zero-width window for the
            # date-shift maths.
            prior_from, prior_to, prior_label = self._resolve_comparison_dates(
                comparison, date_to, date_to,
            )
            if prior_to:
                prior_lines, prior_totals = self._build_snapshot_lines(
                    options=options, company_ids=company_ids,
                    date_to=prior_to,
                    posted_only=posted_only, show_zero=show_zero,
                )
                merged = self.merge_comparative_lines(lines, prior_lines)
                meta['prior_date_to'] = self._iso_date(prior_to)
                meta['comparison_label'] = prior_label
                return {
                    'columns': self._build_comparative_column_layout(
                        label_name="Account",
                        current_label="As at %s" % self._iso_date(date_to),
                        prior_label="As at %s" % self._iso_date(prior_to),
                    ),
                    'lines': merged,
                    'totals': dict(totals, **{
                        'prior_assets': prior_totals['assets'],
                        'prior_liabilities': prior_totals['liabilities'],
                        'prior_equity': prior_totals['equity'],
                    }),
                    'generated_at': fields.Datetime.now().isoformat(),
                    'meta': meta,
                }

        return {
            'columns': self._build_two_column_layout(),
            'lines': lines,
            'totals': totals,
            'generated_at': fields.Datetime.now().isoformat(),
            'meta': meta,
        }

    @api.model
    def _build_subsection(
        self, options, company_ids, date_to, posted_only, show_zero,
        section_id, header_label, total_label, account_types, sign,
        header_level, total_level, account_level,
    ):
        """Render one (header, account lines, total) subsection and return
        (lines, subtotal). Empty subsections collapse to just the header
        and a zero subtotal so the hierarchy is still visible when a
        company has no accounts of that type.
        """
        rows = self._fetch_grouped_account_totals(
            account_types=account_types, sign=sign,
            company_ids=company_ids,
            date_to=date_to,
            posted_only=posted_only, options=options,
        )
        subtotal = round(sum(r['amount'] for r in rows), 2)
        lines = [self._section_header_line(
            header_label, section_id=section_id, level=header_level,
        )]
        lines.extend(self._render_account_lines(
            rows, show_zero, level=account_level,
        ))
        lines.append(self._section_total_line(
            total_label, subtotal, section_id=section_id, level=total_level,
        ))
        return lines, subtotal

    @api.model
    def _build_snapshot_lines(
        self, options, company_ids, date_to, posted_only, show_zero,
    ):
        fetch_kwargs = {
            'options': options,
            'company_ids': company_ids,
            'date_to': date_to,
            'posted_only': posted_only,
            'show_zero': show_zero,
        }

        lines = []

        # -------------------- ASSETS --------------------
        asset_section_lines = [self._section_header_line(
            "ASSETS", section_id='assets', level=0,
        )]

        # Current Assets group (level 1 wrapper around 4 level-2 subsections).
        current_assets_lines = [self._section_header_line(
            "Current Assets", section_id='current_assets', level=1,
        )]
        current_assets_subtotal = 0.0
        for sec_id, label, total_label, types in (
            self.CURRENT_ASSET_SUBSECTIONS
        ):
            sub_lines, sub_total = self._build_subsection(
                section_id=sec_id, header_label=label,
                total_label=total_label, account_types=types, sign=+1,
                header_level=2, total_level=2, account_level=3,
                **fetch_kwargs,
            )
            current_assets_lines.extend(sub_lines)
            current_assets_subtotal += sub_total
        current_assets_subtotal = round(current_assets_subtotal, 2)
        current_assets_lines.append(self._section_total_line(
            "Total Current Assets", current_assets_subtotal,
            section_id='current_assets', level=1,
        ))
        asset_section_lines.extend(current_assets_lines)

        other_asset_total = 0.0
        for sec_id, label, total_label, types in self.OTHER_ASSET_GROUPS:
            group_lines, group_total = self._build_subsection(
                section_id=sec_id, header_label=label,
                total_label=total_label, account_types=types, sign=+1,
                header_level=1, total_level=1, account_level=2,
                **fetch_kwargs,
            )
            asset_section_lines.extend(group_lines)
            other_asset_total += group_total

        asset_total = round(current_assets_subtotal + other_asset_total, 2)
        asset_section_lines.append(self._section_total_line(
            "Total ASSETS", asset_total, section_id='assets', level=0,
        ))
        lines.extend(asset_section_lines)

        # -------------------- LIABILITIES --------------------
        liab_section_lines = [self._section_header_line(
            "LIABILITIES", section_id='liabilities', level=0,
        )]

        current_liab_lines = [self._section_header_line(
            "Current Liabilities", section_id='current_liabilities', level=1,
        )]
        current_liab_subtotal = 0.0
        for sec_id, label, total_label, types in (
            self.CURRENT_LIABILITY_SUBSECTIONS
        ):
            sub_lines, sub_total = self._build_subsection(
                section_id=sec_id, header_label=label,
                total_label=total_label, account_types=types, sign=-1,
                header_level=2, total_level=2, account_level=3,
                **fetch_kwargs,
            )
            current_liab_lines.extend(sub_lines)
            current_liab_subtotal += sub_total
        current_liab_subtotal = round(current_liab_subtotal, 2)
        current_liab_lines.append(self._section_total_line(
            "Total Current Liabilities", current_liab_subtotal,
            section_id='current_liabilities', level=1,
        ))
        liab_section_lines.extend(current_liab_lines)

        other_liab_total = 0.0
        for sec_id, label, total_label, types in self.OTHER_LIABILITY_GROUPS:
            group_lines, group_total = self._build_subsection(
                section_id=sec_id, header_label=label,
                total_label=total_label, account_types=types, sign=-1,
                header_level=1, total_level=1, account_level=2,
                **fetch_kwargs,
            )
            liab_section_lines.extend(group_lines)
            other_liab_total += group_total

        liability_total = round(current_liab_subtotal + other_liab_total, 2)
        liab_section_lines.append(self._section_total_line(
            "Total LIABILITIES", liability_total,
            section_id='liabilities', level=0,
        ))
        lines.extend(liab_section_lines)

        # -------------------- EQUITY --------------------
        equity_rows = self._fetch_grouped_account_totals(
            account_types=self.EQUITY_TYPES, sign=-1,
            company_ids=company_ids, date_to=date_to,
            posted_only=posted_only, options=options,
        )
        equity_total = round(sum(r['amount'] for r in equity_rows), 2)
        current_year_earnings = round(self._fetch_aggregate_balance(
            account_types=self.INCOME_TYPES + self.EXPENSE_TYPES,
            company_ids=company_ids, date_to=date_to,
            posted_only=posted_only, options=options, sign=-1,
        ), 2)

        lines.append(self._section_header_line(
            "EQUITY", section_id='equity', level=0,
        ))
        lines.extend(self._render_account_lines(
            equity_rows, show_zero, level=1,
        ))
        lines.append(self._section_total_line(
            "Total EQUITY", equity_total, section_id='equity', level=0,
        ))
        lines.append(self._computed_line(
            'current_year_earnings', "Current Year Earnings",
            current_year_earnings, kind='current_year_earnings',
        ))

        # -------------------- LIABILITIES + EQUITY + Balance Check ------
        total_equity_liabilities = round(
            liability_total + equity_total + current_year_earnings, 2,
        )
        balance_check = round(asset_total - total_equity_liabilities, 2)
        lines.append(self._computed_line(
            'total_equity_liabilities', "LIABILITIES + EQUITY",
            total_equity_liabilities, kind='computed_total',
        ))
        lines.append(self._computed_line(
            'balance_check', "Balance Check",
            balance_check, kind='balance_check',
        ))

        return lines, {
            'assets': asset_total,
            'current_assets': current_assets_subtotal,
            'liabilities': liability_total,
            'current_liabilities': current_liab_subtotal,
            'equity': equity_total,
            'current_year_earnings': current_year_earnings,
            'total_equity_liabilities': total_equity_liabilities,
            'balance_check': balance_check,
        }
