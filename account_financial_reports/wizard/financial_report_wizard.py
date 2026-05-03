# -*- coding: utf-8 -*-
import json
from odoo import models, fields, api, _


class FinancialReportWizard(models.TransientModel):
    _name = 'financial.report.wizard'
    _description = 'Financial Report Wizard'

    report_type = fields.Selection([
        ('general_ledger',  'General Ledger'),
        ('trial_balance',   'Trial Balance'),
        ('balance_sheet',   'Balance Sheet'),
        ('profit_loss',     'Profit & Loss'),
    ], string='Report', required=True, default='general_ledger')

    date_from = fields.Date(
        string='From Date',
        default=lambda self: fields.Date.today().replace(month=1, day=1),
    )
    date_to = fields.Date(
        string='To Date',
        default=fields.Date.today,
    )

    journal_ids = fields.Many2many(
        'account.journal',
        string='Journals',
        help='Leave empty to include all journals',
    )

    analytic_account_ids = fields.Many2many(
        'account.analytic.account',
        string='Analytic Accounts',
        help='Leave empty to include all analytic accounts',
    )

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True,
    )

    def _build_options(self):
        return {
            'report_type':          self.report_type,
            'date_from':            str(self.date_from) if self.date_from else False,
            'date_to':              str(self.date_to)   if self.date_to   else False,
            'journal_ids':          self.journal_ids.ids,
            'analytic_account_ids': self.analytic_account_ids.ids,
            'company_id':           self.company_id.id,
        }

    def action_view_report(self):
        """Open the report preview in the browser."""
        self.ensure_one()
        options = self._build_options()
        return {
            'type': 'ir.actions.client',
            'tag':  'financial_report_preview',
            'name': self._get_report_title(),
            'params': {
                'wizard_id':   self.id,
                'options':     options,
                'report_type': self.report_type,
            },
        }

    def _get_report_title(self):
        titles = {
            'general_ledger': _('General Ledger'),
            'trial_balance':  _('Trial Balance'),
            'balance_sheet':  _('Balance Sheet'),
            'profit_loss':    _('Profit & Loss'),
        }
        return titles.get(self.report_type, _('Financial Report'))
