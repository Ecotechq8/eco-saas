from odoo import _, api, fields, models, tools
from odoo.exceptions import UserError, RedirectWarning, ValidationError


class Project(models.Model):
    _inherit = 'project.project'

    request_quota_line = fields.One2many(related='sale_id.opportunity_id.request_quota_line')
    project_request_quota_line = fields.One2many('request.quotation', 'project_id', 'project Product Request')
    sale_id = fields.Many2one('sale.order',string='Sale order',copy=False,readonly=True)
    guarantee_letter_count = fields.Integer(compute="_guarantee_letter_count", string="Guarantee Letters")
    purchase_orders_count = fields.Integer(compute="_purchase_orders_count", string="PO/Subcontracting")
    sale_orders_count = fields.Integer(compute="_sale_orders_count", string="Contracts")
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account')

    def project_create_quotation(self):
        quot_list = []
        so_line = []

        if not self.project_request_quota_line:
            raise UserError(_("No product lines found."))
        if all(req.custom_order_id for req in self.project_request_quota_line):
            raise UserError(_("No product lines found or already created."))
        sale_obj = self.env['sale.order']
        sale_line_obj = self.env['sale.order.line']
        if not self.partner_id:
            raise UserError(_("Please Select customer to create Contract."))
        sale_dict = {'partner_id': self.partner_id.id, 'origin': self.name, 'con_project_id': self.id}
        sale_order = sale_obj.create(sale_dict)
        self.sale_id = sale_order
        quot_list.append(sale_order.id)
        for line in self.project_request_quota_line:
            if not line.display_type:
                so_line += [(0, 0, {
                    'product_id': line.product_id.id,
                    'name': line.name,
                    'product_uom_qty': line.product_uom_qty,
                    'product_uom': line.product_uom.id,
                    'price_unit': line.price_unit,
                    'analytic_distribution':{self.analytic_account_id.id: 100}

                })]
            else:
                so_line += [(0, 0, {
                    'display_type': line.display_type,
                    'name': line.name,
                    'product_id': None,
                    'product_uom_qty': 0,
                    'product_uom': None,
                    'price_unit': 0,

                })]
        sale_order.write({'order_line': so_line})

        result = self.env.ref("sale.action_quotations_with_onboarding")
        action_ref = result or False
        result = action_ref.sudo().read()[0]
        result['domain'] = str([('id', 'in', quot_list)])
        return result


    def action_create_guarantee_letter(self):
        # self.state = 'reserved'

        return {
            "name": _("Guarantee Letter"),
            "view_type": "form",
            "view_mode": "form",
            "res_model": "guarantee.letter",
            "view_id": self.env.ref("eco_construction.view_guarantee_letter_form").id,
            "type": "ir.actions.act_window",
            "context": {
                "form_view_initial_mode": "edit",
                "default_project_id": self.id,
                "default_analytic_account_id": self.analytic_account_id.id,
                # "default_property_id": self.id,
                # "default_property_price": self.list_price,
                # "default_phase_id": self.phase_id.id,
            },
            "target": "current",
        }
    def _guarantee_letter_count(self):
        letter_ids = self.env["guarantee.letter"]
        for rec in self:
            rec.guarantee_letter_count = letter_ids.search_count([("project_id", "=", rec.id)])
    def _purchase_orders_count(self):
        order_ids = self.env["purchase.order"]
        for rec in self:
            rec.purchase_orders_count = order_ids.search_count([("project_id", "=", rec.id)])
    def _sale_orders_count(self):
        order_ids = self.env["sale.order"]
        for rec in self:
            rec.sale_orders_count = order_ids.search_count([("con_project_id", "=", rec.id)])

    def button_view_guarantee_letter(self):
        letter_ids = self.env["guarantee.letter"].search([("project_id", "=", self.id)])
        return {
            "name": _("Guarantee Letters"),
            "domain": [("id", "in", letter_ids.ids)],
            "view_type": "list",
            "view_mode": "list,form",
            "res_model": "guarantee.letter",
            "type": "ir.actions.act_window",
            "nodestroy": True,
            "view_id": False,
            "target": "current",
        }

    def button_view_purchase_orders(self):
        order_ids = self.env["purchase.order"].search([("project_id", "=", self.id)])
        return {
            "name": _("PO/Subcontracting"),
            "domain": [("id", "in", order_ids.ids)],
            "view_type": "list",
            "view_mode": "list,form",
            "res_model": "purchase.order",
            "type": "ir.actions.act_window",
            "nodestroy": True,
            "view_id": False,
            "target": "current",
        }
    def button_view_contract_orders(self):
        order_ids = self.env["sale.order"].search([("con_project_id", "=", self.id)])
        return {
            "name": _("contracts"),
            "domain": [("id", "in", order_ids.ids)],
            "view_type": "list",
            "view_mode": "list,form",
            "res_model": "sale.order",
            "type": "ir.actions.act_window",
            "nodestroy": True,
            "view_id": False,
            "target": "current",
        }