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
    progeres_invoice_no = fields.Integer(string='Progress Invoice Number', required=False)
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
            'sale_id': self.id,
            'account_id': self.env['account.analytic.account'].create({'name': self.con_project_name,
                                                                       'plan_id': self.env[
                                                                           'account.analytic.plan'].search(
                                                                           [('name', '=', 'Project')]).id}).id
        }
        self.con_project_id = project_obj.create(vals)

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        if self.create_project and not self.con_project_id:
            self._prepare_project_vals()
        return res

    def _can_be_confirmed(self):
        self.ensure_one()
        return self.state in {'draft', 'sent', 'approved'}

    def _confirmation_error_message(self):
        """ Return whether order can be confirmed or not if not then returm error message. """
        self.ensure_one()
        if self.state not in {'draft', 'sent', 'approved'}:
            return _("Some orders are not in a state requiring confirmation.")
        if any(
                not line.display_type
                and not line.is_downpayment
                and not line.product_id
                for line in self.order_line
        ):
            return _("A line on these orders missing a product, you cannot confirm it.")

        return False

    def action_create_guarantee_letter(self):
        return {
            "name": _("Guarantee Letter"),
            "view_type": "form",
            "view_mode": "form",
            "res_model": "guarantee.letter",
            "view_id": self.env.ref("eco_construction.view_guarantee_letter_form").id,
            "type": "ir.actions.act_window",
            "context": {
                "form_view_initial_mode": "edit",
                "default_project_id": self.con_project_id.id,
            },
            "target": "current",
        }


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"


    def _get_posted_customer_invoices(self):
        self.ensure_one()
        invoices = self.order_id.invoice_ids.filtered(
            lambda m: m.move_type == "out_invoice" and m.state == "posted"
        )
        return invoices.sorted(
            key=lambda m: (m.invoice_date or m.date or fields.Date.today(), m.id)
        )

    def get_last_invoice_quantity(self, product_id):
        self.ensure_one()

        invoices = self._get_posted_customer_invoices()
        if not invoices:
            return 0.0

        last_invoice = invoices[-1]

        lines = last_invoice.invoice_line_ids.filtered(
            lambda l: l.product_id.id == product_id.id and not l.display_type
        )
        return sum(lines.mapped("quantity")) or 0.0

    def _get_total_invoiced_qty_posted_for_this_sol(self):
        self.ensure_one()

        posted_lines = self.invoice_lines.filtered(
            lambda l: l.move_id.state == "posted" and l.move_id.move_type == "out_invoice"
        )
        return sum(posted_lines.mapped("quantity")) or 0.0


    def _prepare_invoice_line(self, **optional_values):
        """
        Keep Odoo default invoicing cycle, only add metadata fields safely.
        """
        res = super()._prepare_invoice_line(**optional_values)

        # Only write if these custom fields exist on account.move.line
        aml_fields = self.env["account.move.line"]._fields
        values = {}

        if "contract_qty" in aml_fields:
            values["contract_qty"] = self.product_uom_qty

        if "last_qty" in aml_fields:
            values["last_qty"] = self.get_last_invoice_quantity(self.product_id)

        if "total_qty" in aml_fields:
            values["total_qty"] = self._get_total_invoiced_qty_posted_for_this_sol()

        if values:
            res.update(values)

        return res
