# -*- encoding: utf-8 -*-
##############################################################################
#
# ERP Heritage
# Copyright (C) 2026 (https://www.erpheritage.com.au/)
#
##############################################################################
"""
eh.account.report.wizard: transient model that gathers report parameters
from the user and triggers the render and export pipeline.

Generic enough to drive every dynamic report. Concrete report addons add
window actions that pre fill report_id via context, so the user lands on a
form already scoped to a single report.
"""

import base64

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class EhAccountReportWizard(models.TransientModel):
    _name = 'eh.account.report.wizard'
    _description = "ERP Heritage report run wizard"

    report_id = fields.Many2one(
        'eh.account.dynamic.report',
        required=True,
        ondelete='cascade',
    )
    report_code = fields.Char(related='report_id.code', readonly=True)

    date_from = fields.Date(
        required=True,
        default=lambda self: fields.Date.today().replace(day=1),
    )
    date_to = fields.Date(
        required=True,
        default=fields.Date.today,
    )

    company_ids = fields.Many2many(
        'res.company',
        'eh_account_report_wizard_company_rel',
        'wizard_id', 'company_id',
        required=True,
        default=lambda self: self.env.company,
    )
    journal_ids = fields.Many2many(
        'account.journal',
        'eh_account_report_wizard_journal_rel',
        'wizard_id', 'journal_id',
    )
    partner_ids = fields.Many2many(
        'res.partner',
        'eh_account_report_wizard_partner_rel',
        'wizard_id', 'partner_id',
    )
    account_ids = fields.Many2many(
        'account.account',
        'eh_account_report_wizard_account_rel',
        'wizard_id', 'account_id',
    )

    posted_only = fields.Boolean(default=True)
    show_zero = fields.Boolean(default=False)

    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        for rec in self:
            if rec.date_from and rec.date_to and rec.date_from > rec.date_to:
                raise ValidationError(_(
                    "Date From cannot be later than Date To.",
                ))

    def _build_options(self):
        self.ensure_one()
        company_ids = self.company_ids.ids or [self.env.company.id]
        return {
            'date': {
                'mode': 'range',
                'date_from': self.date_from.isoformat(),
                'date_to': self.date_to.isoformat(),
            },
            'company_ids': company_ids,
            'journal_ids': self.journal_ids.ids,
            'partner_ids': self.partner_ids.ids,
            'account_ids': self.account_ids.ids,
            'posted_only': bool(self.posted_only),
            'show_zero': bool(self.show_zero),
        }

    def action_export_xlsx(self):
        self.ensure_one()
        options = self._build_options()
        content = self.report_id.render_xlsx(options)
        filename = "%s_%s_to_%s.xlsx" % (
            self.report_id.code,
            self.date_from.isoformat(),
            self.date_to.isoformat(),
        )
        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'type': 'binary',
            'datas': base64.b64encode(content),
            'mimetype': (
                'application/vnd.openxmlformats-officedocument'
                '.spreadsheetml.sheet'
            ),
            'res_model': self._name,
            'res_id': self.id,
        })
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % attachment.id,
            'target': 'self',
        }
