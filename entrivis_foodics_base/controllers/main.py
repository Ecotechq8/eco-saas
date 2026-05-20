# -*- coding: utf-8 -*-

import logging
from odoo.http import request
from odoo.addons.web.controllers.home import Home as WebHome
from odoo import http

_logger = logging.getLogger(__name__)


class Home(WebHome):

    @http.route()
    def web_client(self, s_action=None, **kw):
        res = super().web_client(kw)
        if kw and kw.get('state') and kw.get('code'):
            connector = request.env['foodic.connector'].search([('foodics_state_code', '=', kw.get('state'))])
            connector.code = kw.get('code')
            connector.generate_access_token()
            base_url = request.env['ir.config_parameter'].sudo().get_param(
                'web.base.url') + f"web#id={connector.id}&model=foodic.connector&view_type=form"
            _logger.info('---------------- redirect url : %s' % (base_url))
            return request.redirect(base_url)
        return res
