# -*- coding: utf-8 -*-
from odoo import models, fields, api
import datetime
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)


class PosSession(models.Model):
    _inherit = 'pos.session'

    def _action_pos_auto_close_cron(self):
        session_ids = self.search([('state', '=', 'opened')])
        for session in session_ids:
            _logger.info("Checking session: %s", session.start_at)
            start_at = datetime.strptime(str(session.start_at), "%Y-%m-%d %H:%M:%S")  # convert into datetime fromat
            start_date_time = datetime.strptime(str(start_at), "%Y-%m-%d %H:%M:%S")
            start_time = start_date_time.time()  # convert into string format and extract time only
            date_time_now = datetime.now()
            time_now = datetime.now().strftime("%H:%M:%S")
            _logger.info("Time now: %s, Session start time: %s", time_now, start_time)
            delta = date_time_now - start_date_time
            sec = delta.total_seconds()
            hours = sec / (60 * 60)
            _logger.info('Difference in hours: %s', hours)
            config_hours = self.env['ir.config_parameter'].get_param('entrivis_pos_auto_close_session.close.session.hours')
            _logger.info('Config hours: %s', config_hours)
            if hours >= float(config_hours):
                _logger.info("Closing session: %s", session.name)
                session.action_pos_session_closing_control()
