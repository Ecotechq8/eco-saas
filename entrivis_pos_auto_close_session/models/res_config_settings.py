# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    auto_close_session = fields.Boolean(string="Auto Close Session", config_parameter='entrivis_pos_auto_close_session.auto.close.session')
    close_session_hours = fields.Float(string="Close Session Hours", config_parameter='entrivis_pos_auto_close_session.close.session.hours')

    redirect_uri = fields.Char(string="Redirect Uri:-", config_parameter='entrivis_pos_auto_close_session.redirect_uri')
    client_id = fields.Char(string="Client Id:-", config_parameter='entrivis_pos_auto_close_session.client_id')
    client_secret = fields.Char(string="Client Secret:-", config_parameter='entrivis_pos_auto_close_session.client_secret')
