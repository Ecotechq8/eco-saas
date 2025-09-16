# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.depends('invoice_ids.state', 'currency_id', 'amount_total')
    def _compute_invoiced_amount(self):
        for order in self:
            if not order.invoice_ids:
                order.invoiced_amount = 0.0
            else:
                invoices = order.invoice_ids.filtered(lambda x: x.state == 'posted')
                order.invoiced_amount = sum(invoices.mapped('amount_total'))

    move_boq = fields.Boolean(string='Move boq', required=False)
    create_project = fields.Boolean(string='Create Project', required=False)
    invoiced_amount = fields.Monetary(string="Invoiced Amount", store=True, compute='_compute_invoiced_amount')
    progeres_invoice_no = fields.Integer(string='Progeres Invoice Number', required=False)
    con_project_id = fields.Many2one('project.project', string='Project ')
    con_project_name = fields.Char(string='project Name', required=False)
    request_quota_line = fields.One2many(related='opportunity_id.request_quota_line')
    is_need_gm_approve = fields.Boolean(
        string='Need GM Approve',
        required=False)
    state = fields.Selection(selection_add=[
        ('approved', 'Approved'),
        ('om_approve', 'OM Approved'),
        ('om_reject', 'OM Rejected'),
        ('sm_approve', 'SM Approved'),
        ('sm_reject', 'SM Rejected'),
        ('gm_approve', 'GM Approved'),
        ('gm_reject', 'GM Rejected'),
    ], string='Status', readonly=True, copy=False, index=True,
        default='draft', help="Status of quotation.")
    adv_percent = fields.Float(string='Advanced Percent %', )
    retention_percent = fields.Float(string='Retention Percent %')

    @api.constrains('adv_percent', 'retention_percent', 'adv_amount', 'retention_amount', 'amount_total')
    def check_total_percent(self):
        total_percent = self.adv_percent + self.retention_percent
        if total_percent > 100:
            raise UserError(_("The sum of the Advanced Percent and Retention Percent must be less than or = 100%."))

    def _prepare_invoice(self):
        res = super(SaleOrder, self)._prepare_invoice()
        res.update({
            'adv_percent': self.adv_percent,
            'retention_percent': self.retention_percent,
            'is_subcontracting': True,
            'project_id': self.con_project_id.id,
        })
        return res

    def action_om_approve(self):
        self.write({'state': 'om_approve'})

    def action_om_reject(self):
        self.write({'state': 'om_reject'})

    def action_sm_approve(self):
        if self.is_need_gm_approve:
            self.write({'state': 'sm_approve'})
        else:
            self.write({'state': 'approved'})

    def action_sm_reject(self):
        self.write({'state': 'sm_reject'})

    def action_gm_approve(self):
        self.write({'state': 'approved'})

    def action_gm_reject(self):
        self.write({'state': 'gm_reject'})

    def _prepare_project_vals(self):

        project_obj = self.env['project.project']

        vals = {
            'name': self.con_project_name,
            'sale_id': self.id

        }
        self.con_project_id = project_obj.create(vals)

    def action_confirm(self):
        self.write({'state': 'sale'})
        res = super(SaleOrder, self).action_confirm()
        if self.create_project and not self.con_project_id:
            self._prepare_project_vals()
        return res

    def _can_be_confirmed(self):
        self.ensure_one()
        return self.state in {'draft', 'sent', 'approved'}


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def get_last_invoice_quantity(self, product_id):
        invoices = self.order_id.invoice_ids.sorted()
        if not invoices:
            return 0.0
        last_invoice = invoices[0]
        last_qty = last_invoice.invoice_line_ids.filtered(lambda x: x.product_id.id == product_id.id  and x.display_type not in ('line_section', 'line_note')).quantity or 0.0
        return last_qty

    # def get_total_invoice_quantity(self, product_id):
    #
    #     invoices = self.order_id.invoice_ids
    #     if not invoices:
    #         return 0.0
    #     last_qty = sum(invoices.invoice_line_ids.filtered(lambda x: x.product_id.id == product_id.id).mapped('quantity')) or 0.0
    #     return last_qty
    def _prepare_invoice_line(self, **optional_values):
        res = super(SaleOrderLine, self)._prepare_invoice_line(**optional_values)
        res.update({
            'contract_qty': self.product_uom_qty,
            'last_qty': self.get_last_invoice_quantity(self.product_id),
            'total_qty': self.qty_invoiced,

        })
        return res
