# -*- coding: utf-8 -*-
# Copyright 2021 Verts Services India Pvt Ltd.
# http://www.verts.co.in

import base64
from io import BytesIO
import xlwt
import xlrd
from odoo import models, fields, api
from datetime import datetime, timedelta
from odoo import _
from odoo.exceptions import UserError
from odoo.tools.misc import DEFAULT_SERVER_DATE_FORMAT


class MeisReportWiz(models.TransientModel):
    _name = 'meis.report.wiz'
    _description = 'Meis Report Wiz'

    from_date = fields.Date(string="From Date")
    to_date = fields.Date(string="To Date")

    def get_meis_data(self):
        '''Get MEIS Report on tree view'''
        # meis_report_line = self.env['meis.report.line']
        line_lst = []
        if self.from_date and self.to_date:
            invoice_ids = self.env['account.invoice'].search([('is_export', '=', True), ('is_meis_invoice', '=', True), ('type', '=', 'out_invoice'), ('date_invoice', '>=', self.from_date),('date_invoice', '<=', self.to_date)])
            # invoice_ids = self.env['account.invoice'].search([('type', '=', 'out_invoice'), ('date_invoice', '>=', self.from_date),('date_invoice', '<=', self.to_date)])
            if invoice_ids:
                sr_no = 1
                for inv in invoice_ids:
                    payment_ids = self.env['payment.term.line'].search([('invoice_id', '=', inv.id)])
                    payment_terms = ''
                    if payment_ids:
                        for pay in payment_ids:
                            payment_terms += pay.payment_id.name + ','
                    res = {'sr_no': sr_no,
                           'invoice_fc_value': (inv.amount_total) * inv.cur_rate or False,
                           'payment_terms': payment_terms}
                    inv.write(res)
                    line_lst.append(inv.id)
                    sr_no += 1

        return {'name': _('MEIS Report'),
                'view_mode': 'list',
                'view_id': self.env.ref('verts_v15_freight_forward.meis_report_account_invoice_tree_view').id,
                'view_type': 'form',
                'res_model': 'account.invoice',
                'limit': 99999999,
                'type': 'ir.actions.act_window',
                'target': 'current',
                'domain': [('id', 'in', line_lst)],
                }




