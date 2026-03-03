# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    is_subcontracting = fields.Boolean(
        string='Is Subcontracting',
        readonly=True)
    project_id = fields.Many2one('project.project', string='Project')

    def _prepare_invoice(self):
        res = super(PurchaseOrder, self)._prepare_invoice()
        res.update({
            'is_subcontracting': True,
        })
        return res


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    def get_last_invoice_quantity(self, product_id):
        invoices = self.order_id.invoice_ids.sorted()
        if not invoices:
            return 0.0
        last_invoice = invoices[0]
        last_qty = last_invoice.invoice_line_ids.filtered(lambda x: x.product_id.id == product_id.id).quantity or 0.0
        return last_qty

    def _prepare_account_move_line(self, move=False):
        res = super(PurchaseOrderLine, self)._prepare_account_move_line(move)
        if not self.order_id.is_subcontracting:
            return res

        res.update({
            'contract_qty': self.product_qty,
            'last_qty': self.get_last_invoice_quantity(self.product_id),
            'total_qty': self.qty_invoiced,

        })
        return res
