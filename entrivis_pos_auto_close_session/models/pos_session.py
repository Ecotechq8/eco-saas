# -*- coding: utf-8 -*-
from datetime import datetime
import logging

from odoo import models

_logger = logging.getLogger(__name__)


class PosSession(models.Model):
    _inherit = 'pos.session'

    def _action_pos_auto_close_cron(self):
        config_hours = self.env['ir.config_parameter'].sudo().get_param(
            'entrivis_pos_auto_close_session.close.session.hours'
        )
        if not config_hours:
            _logger.info("Auto-close skipped: close.session.hours not configured.")
            return
        try:
            limit_hours = float(config_hours)
        except (TypeError, ValueError):
            _logger.warning("Auto-close skipped: invalid close.session.hours=%r", config_hours)
            return

        now = datetime.now()
        for session in self.search([('state', '=', 'opened')]):
            if not session.start_at:
                continue
            hours_open = (now - session.start_at).total_seconds() / 3600.0
            _logger.info("Session %s open for %.2f h (limit %.2f h)", session.name, hours_open, limit_hours)
            if hours_open >= limit_hours:
                _logger.info("Closing session: %s", session.name)
                session.action_pos_session_closing_control()
