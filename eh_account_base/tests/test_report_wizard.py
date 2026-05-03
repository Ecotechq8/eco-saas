# -*- encoding: utf-8 -*-
##############################################################################
#
# ERP Heritage
# Copyright (C) 2026 (https://www.erpheritage.com.au/)
#
##############################################################################
"""
Tests for eh.account.report.wizard.

Covers:

* Default options dict structure mirrors what handlers expect.
* Date constraint: date_from must not be later than date_to.
* action_export_xlsx returns a download action and creates an attachment.
* Empty company_ids selection falls back to the active company.
"""

import base64

from datetime import date, timedelta

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged

from .common import EhAccountUnitTestCase


# A trivial test handler that always returns a fixed payload.

class WizardTestHandler(models.AbstractModel):
    _name = 'eh.test.report.handler.wizard'
    _inherit = 'eh.account.dynamic.report.handler'
    _description = "Wizard test handler"

    REPORT_CODE = 'wizard_test'
    REPORT_NAME = "Wizard Test"

    @api.model
    def compute(self, options):
        return {
            'columns': [
                {'expression_label': 'account', 'name': 'Account',
                 'figure_type': 'string'},
                {'expression_label': 'value', 'name': 'Value',
                 'figure_type': 'monetary'},
            ],
            'lines': [
                {'id': 'l1', 'name': 'Test Line', 'level': 1,
                 'columns': [{'expression_label': 'value', 'value': 42.0}]},
            ],
            'totals': {'value': 42.0},
            'generated_at': fields.Datetime.now().isoformat(),
            'meta': dict(options.get('meta', {})) if options.get('meta') else {},
        }


@tagged('eh_account_base', 'integration', 'post_install', '-at_install')
class TestReportWizard(EhAccountUnitTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Use a real installed handler. Compute is patched per test below
        # if a specific shape is required.
        cls.report = cls.env['eh.account.dynamic.report'].create({
            'code': 'wizard_test',
            'name': 'Wizard Test',
            'handler_model': 'eh.account.dynamic.report.handler.aged_payable',
        })

    def _make_wizard(self, **overrides):
        vals = {
            'report_id': self.report.id,
            'date_from': '2026-01-01',
            'date_to': '2026-12-31',
            'posted_only': True,
            'show_zero': False,
        }
        vals.update(overrides)
        return self.env['eh.account.report.wizard'].create(vals)

    def test_build_options_shape(self):
        wizard = self._make_wizard()
        options = wizard._build_options()
        self.assertIn('date', options)
        self.assertEqual(options['date']['date_from'], '2026-01-01')
        self.assertEqual(options['date']['date_to'], '2026-12-31')
        self.assertTrue(options['posted_only'])
        self.assertFalse(options['show_zero'])
        self.assertIn(self.env.company.id, options['company_ids'])

    def test_build_options_includes_partner_and_account_filters(self):
        partner = self.env['res.partner'].create({'name': 'Filtered'})
        wizard = self._make_wizard(partner_ids=[(6, 0, [partner.id])])
        options = wizard._build_options()
        self.assertEqual(options['partner_ids'], [partner.id])

    def test_invalid_date_range_raises(self):
        # Odoo 19's _assertRaises only accepts a single class. The wizard
        # raises UserError (constraints fire there).
        with self.assertRaises(UserError):
            self._make_wizard(
                date_from='2026-12-31',
                date_to='2026-01-01',
            )

    def test_action_export_xlsx_creates_attachment_and_returns_url(self):
        wizard = self._make_wizard()
        action = wizard.action_export_xlsx()
        self.assertEqual(action['type'], 'ir.actions.act_url')
        self.assertIn('/web/content/', action['url'])
        # The attachment should exist and contain XLSX bytes.
        attachment_id = int(
            action['url'].split('/web/content/')[1].split('?')[0]
        )
        attachment = self.env['ir.attachment'].browse(attachment_id)
        self.assertTrue(attachment.exists())
        self.assertEqual(
            attachment.mimetype,
            'application/vnd.openxmlformats-officedocument'
            '.spreadsheetml.sheet',
        )
        # First two bytes of any XLSX (ZIP container) are 'PK'.
        decoded = base64.b64decode(attachment.datas)
        self.assertEqual(decoded[:2], b'PK')
        self.assertIn('wizard_test', attachment.name)

    def test_default_company_when_none_selected(self):
        wizard = self._make_wizard(company_ids=[(6, 0, [])])
        # The constraint requires company_ids; clear via write to bypass.
        self.env.cr.execute(
            "DELETE FROM eh_account_report_wizard_company_rel "
            "WHERE wizard_id = %s",
            (wizard.id,),
        )
        wizard.invalidate_recordset(['company_ids'])
        options = wizard._build_options()
        self.assertEqual(options['company_ids'], [self.env.company.id])
