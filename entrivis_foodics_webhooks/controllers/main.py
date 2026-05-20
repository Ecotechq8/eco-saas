# -*- coding: utf-8 -*-

import logging
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class VCSController(http.Controller):
    _webhook_url = '/foodics/pos_orders'

    @http.route('/foodics/pos_orders', type='json', auth='public', methods=['POST'], csrf=False)
    def get_foodics_pos_order(self, **kwargs):
        """ Get order from foodics and create in odoo """
        data = request.jsonrequest
        _logger.info("---------------- START ORDER SYNC WEB-HOOK ---------------------")
        _logger.info('---------------- DATA : %s'%(data))
        connector = request.env['foodic.connector'].search([('state', '=', 'authenticated')], limit=1)
        connector.sudo().sync_pos_orders(data)
        _logger.info("---------------- END ORDER SYNC WEB-HOOK ---------------------")
        return {'result': 'success'}
