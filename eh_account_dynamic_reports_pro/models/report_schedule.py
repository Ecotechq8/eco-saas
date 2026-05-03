# -*- encoding: utf-8 -*-
##############################################################################
#
# ERP Heritage
# Copyright (C) 2026 (https://www.erpheritage.com.au/)
#
##############################################################################
"""
eh.report.schedule: cron driven email delivery of dynamic reports.

A schedule binds a report record + an options dict + a recipient list +
a recurrence (daily, weekly, monthly). The cron _cron_run_due runs hourly
and dispatches every schedule whose next_run is past. Each delivery
generates an attachment (XLSX, PDF, or both) and emails it via mail.mail.

Failure handling:

* Delivery exceptions are caught per schedule. The error is logged on the
  schedule (last_error, last_run_status='error') and the next_run is still
  advanced so a single bad schedule does not freeze the queue.
* If a recipient list is empty at delivery time, the schedule errors with
  a clear message rather than silently sending to nobody.

Attachment lifecycle:

* Attachments are created on ir.attachment with a 30 day retention hint
  (cleanup is the user's responsibility; we do not auto delete).
* The execution audit row from the orchestrator captures the exact options
  used, so a recipient can verify the render is reproducible.
"""

import base64
import json
import logging

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class EhReportSchedule(models.Model):
    _name = 'eh.report.schedule'
    _description = "Scheduled report email delivery"
    _order = 'next_run asc, id asc'
    _inherit = ['mail.thread']

    name = fields.Char(required=True, tracking=True)
    active = fields.Boolean(default=True, tracking=True)

    user_id = fields.Many2one(
        'res.users',
        required=True,
        default=lambda self: self.env.user,
        index=True,
    )
    company_id = fields.Many2one(
        'res.company',
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )
    report_id = fields.Many2one(
        'eh.account.dynamic.report',
        required=True,
        ondelete='cascade',
        index=True,
    )

    options_json = fields.Text(
        required=True,
        default='{}',
        help="JSON serialised options dict applied at delivery time.",
    )

    interval = fields.Integer(default=1, required=True)
    interval_unit = fields.Selection(
        [
            ('day', "Day(s)"),
            ('week', "Week(s)"),
            ('month', "Month(s)"),
        ],
        default='month',
        required=True,
    )
    next_run = fields.Datetime(
        required=True,
        default=fields.Datetime.now,
        index=True,
    )
    last_run = fields.Datetime(readonly=True)
    last_run_status = fields.Selection(
        [
            ('success', "Success"),
            ('error', "Error"),
        ],
        readonly=True,
    )
    last_error = fields.Text(readonly=True)
    last_attachment_count = fields.Integer(default=0, readonly=True)

    delivery_format = fields.Selection(
        [
            ('xlsx', "XLSX"),
            ('pdf', "PDF"),
            ('both', "XLSX + PDF"),
        ],
        default='xlsx',
        required=True,
    )

    recipient_user_ids = fields.Many2many(
        'res.users',
        'eh_report_schedule_user_rel',
        'schedule_id',
        'user_id',
        string="User Recipients",
    )
    recipient_partner_ids = fields.Many2many(
        'res.partner',
        'eh_report_schedule_partner_rel',
        'schedule_id',
        'partner_id',
        string="Partner Recipients",
    )
    recipient_emails = fields.Char(
        help="Additional comma separated email addresses.",
    )

    subject = fields.Char(
        required=True,
        default="Scheduled Report",
        translate=True,
    )
    body = fields.Html(translate=True)

    _positive_interval = models.Constraint(
        'check(interval > 0)',
        'Schedule interval must be a positive integer.',
    )

    # ---- public actions ----

    def action_run_now(self):
        """Run the schedule immediately. Useful for testing the cadence
        without waiting for the cron tick."""
        for schedule in self:
            try:
                schedule._send_now()
                schedule._advance_next_run()
            except Exception as exc:
                schedule._record_failure(exc)
                raise
        return True

    def action_pause(self):
        for schedule in self:
            schedule.active = False
        return True

    def action_resume(self):
        for schedule in self:
            schedule.active = True
        return True

    @api.model
    def _cron_run_due(self):
        """Runner entry point for ir.cron. Dispatches every active
        schedule whose next_run is in the past.

        Per schedule failures are isolated; one bad schedule does not
        break the rest of the run.
        """
        now = fields.Datetime.now()
        due = self.search([
            ('active', '=', True),
            ('next_run', '<=', now),
        ])
        for schedule in due:
            try:
                schedule._send_now()
                schedule._advance_next_run()
            except Exception as exc:
                _logger.warning(
                    "eh.report.schedule %s failed: %s",
                    schedule.id, exc,
                )
                schedule._record_failure(exc)
                # Still advance so the next cron pass does not retry the
                # same broken schedule until manually fixed.
                try:
                    schedule._advance_next_run()
                except Exception:
                    pass
        return True

    # ---- internals ----

    def _send_now(self):
        self.ensure_one()
        options = self._parse_options()
        emails = self._resolve_recipient_emails()
        if not emails:
            raise UserError(_(
                "Schedule '%s' has no recipient emails configured.",
            ) % self.name)
        attachments = self._build_attachments(options)
        if not attachments:
            raise UserError(_("Could not build any attachment for delivery."))

        body_html = self.body or self._default_body_html(options)
        mail_vals = {
            'subject': self.subject,
            'body_html': body_html,
            'email_to': ','.join(emails),
            'email_from': (
                self.env.company.email
                or self.user_id.email
                or self.env.user.email
                or False
            ),
            'auto_delete': False,
            'attachment_ids': [(0, 0, att) for att in attachments],
        }
        mail = self.env['mail.mail'].sudo().create(mail_vals)
        mail.send()

        self.write({
            'last_run': fields.Datetime.now(),
            'last_run_status': 'success',
            'last_error': False,
            'last_attachment_count': len(attachments),
        })
        return True

    def _record_failure(self, exc):
        self.ensure_one()
        self.write({
            'last_run': fields.Datetime.now(),
            'last_run_status': 'error',
            'last_error': str(exc)[:8000],
        })

    def _advance_next_run(self):
        self.ensure_one()
        delta = self._compute_delta()
        base = self.last_run or fields.Datetime.now()
        self.next_run = base + delta

    def _compute_delta(self):
        if self.interval_unit == 'day':
            return relativedelta(days=self.interval)
        if self.interval_unit == 'week':
            return relativedelta(weeks=self.interval)
        return relativedelta(months=self.interval)

    def _parse_options(self):
        try:
            return json.loads(self.options_json or '{}')
        except ValueError:
            return {}

    def _resolve_recipient_emails(self):
        """Combine user, partner, and free text email lists. Returns a
        deduplicated, comma free list of email addresses."""
        emails = set()
        for user in self.recipient_user_ids:
            if user.email:
                emails.add(user.email.strip())
        for partner in self.recipient_partner_ids:
            if partner.email:
                emails.add(partner.email.strip())
        if self.recipient_emails:
            for raw in self.recipient_emails.split(','):
                stripped = raw.strip()
                if stripped:
                    emails.add(stripped)
        return sorted(e for e in emails if e and '@' in e)

    def _build_attachments(self, options):
        attachments = []
        report = self.report_id
        today_str = fields.Date.context_today(self).isoformat()

        if self.delivery_format in ('xlsx', 'both'):
            xlsx_bytes = report.render_xlsx(options)
            attachments.append({
                'name': "%s_%s.xlsx" % (report.code, today_str),
                'datas': base64.b64encode(xlsx_bytes),
                'mimetype': (
                    'application/vnd.openxmlformats-officedocument'
                    '.spreadsheetml.sheet'
                ),
            })
        if self.delivery_format in ('pdf', 'both'):
            try:
                pdf_bytes = report.render_pdf(options)
                attachments.append({
                    'name': "%s_%s.pdf" % (report.code, today_str),
                    'datas': base64.b64encode(pdf_bytes),
                    'mimetype': 'application/pdf',
                })
            except Exception as exc:
                _logger.warning(
                    "PDF rendering failed for schedule %s: %s",
                    self.id, exc,
                )
                if self.delivery_format == 'pdf':
                    raise
        return attachments

    def _default_body_html(self, options):
        report = self.report_id
        date_block = options.get('date') or {}
        period = ''
        if date_block.get('date_from') and date_block.get('date_to'):
            period = " for the period %s to %s" % (
                date_block['date_from'], date_block['date_to'],
            )
        return (
            "<p>Hello,</p>"
            "<p>Please find attached the latest <strong>%(name)s</strong>%(period)s.</p>"
            "<p>This is an automated delivery from your scheduled report.</p>"
            "<p>Generated by ERP Heritage Accounting.</p>"
        ) % {
            'name': report.name or '',
            'period': period,
        }
