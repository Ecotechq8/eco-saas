# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import UserError, RedirectWarning, ValidationError


class CrmLead(models.Model):
    _inherit = "crm.lead"

    request_quota_line = fields.One2many('request.quotation', 'lead_id', 'Product Request')
    procurement_approval = fields.Selection(
        string='Procurement Approval',
        selection=[
            ('draft', 'Draft'),
            ('approve', 'Approved'),
            ('reject', 'Rejected')
            , ], default='draft')

    def action_approve_boq(self):
        self.procurement_approval = 'approve'

    def action_reject_boq(self):
        self.procurement_approval = 'reject'

    def action_reset_to_draft(self):
        self.procurement_approval = 'draft'

    def custom_create_quotation(self):
        quot_list = []
        so_line = []
        move_boq_to_sale_order = self.env["ir.config_parameter"].sudo().get_param("move_boq_to_sale_order")
        # for rec in self:
        if not self.request_quota_line:
            raise UserError(_("No product lines found."))
        if all(req.custom_order_id for req in self.request_quota_line):
            raise UserError(_("No product lines found or already created."))
        sale_obj = self.env['sale.order']
        sale_line_obj = self.env['sale.order.line']
        if not self.partner_id:
            raise UserError(_("Please create customer and link on oppotunity to create quote."))
        sale_dict = {'partner_id': self.partner_id.id,
                     'origin': self.name,
                     'opportunity_id': self.id,
                     'move_boq': move_boq_to_sale_order,
                     }
        sale_order = sale_obj.create(sale_dict)
        quot_list.append(sale_order.id)
        if move_boq_to_sale_order:
            for line in self.request_quota_line:
                if not line.display_type:
                    so_line += [(0, 0, {
                        'product_id': line.product_id.id,
                        'name': line.name,
                        'product_uom_qty': line.product_uom_qty,
                        'product_uom': line.product_uom.id,
                        'price_unit': line.price_unit,

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

    # result = self.env.ref('sale.action_orders')
        result = self.env.ref("sale.action_quotations_with_onboarding")
        action_ref = result or False
        result = action_ref.sudo().read()[0]
        result['domain'] = str([('id', 'in', quot_list)])
        return result
