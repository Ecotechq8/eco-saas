# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class LoanRejectReason(models.TransientModel):
    _name = "wizard.create.purchase.order"

    type = fields.Selection(
        string='Contract Type',
        selection=[('consultation', 'Consultation'),
                   ('design', 'Design'),
                   ('construction', 'Construction'),
                   ('other', 'Other')],
        required=True)

    partner_id = fields.Many2one('res.partner', string='Vendor/Subcontractor', required=True)

    def action_create_po(self):
        model = self.env.context.get('active_model')

        if model == 'sale.order':
            active_id = self.env[model].browse(self.env.context.get('active_id'))

            po_dict = {
                'partner_id': self.partner_id.id,
                'is_subcontracting': True,
                'project_id': active_id.con_project_id.id
            }

            po_line = []
            purchase_order = self.env['purchase.order'].create(po_dict)

            if self.type == 'other' and active_id.request_quota_line:
                for line in active_id.request_quota_line:

                    if not line.display_type:
                        po_line += [(0, 0, {
                            'product_id': line.product_id.id,
                            'product_qty': line.product_uom_qty,
                            'boq_qty': line.product_uom_qty,
                            'product_uom': line.product_uom.id,
                            'price_unit': line.price_unit,
                        })]

                    else:
                        po_line += [(0, 0, {
                            'display_type': line.display_type,
                            'name': line.name,
                            'product_id': False,
                            'product_qty': 0,
                            'product_uom': False,
                            'price_unit': 0,
                        })]

                purchase_order.update({'order_line': po_line})

        if model == 'project.project':
            active_id = self.env[model].browse(self.env.context.get('active_id'))

            po_dict = {
                'partner_id': self.partner_id.id,
                'is_subcontracting': True,
                'project_id': active_id.id
            }

            po_line = []
            purchase_order = self.env['purchase.order'].create(po_dict)

            if self.type == 'other' and active_id.project_request_quota_line:
                for line in active_id.project_request_quota_line:

                    if not line.display_type:
                        po_line += [(0, 0, {
                            'product_id': line.product_id.id,
                            'product_qty': line.product_uom_qty,
                            'max_qty': line.product_uom_qty,
                            'product_uom': line.product_uom.id,
                            'price_unit': line.price_unit,
                        })]
                    else:
                        po_line += [(0, 0, {
                            'display_type': line.display_type,
                            'name': line.name,
                            'product_id': False,
                            'product_qty': 0,
                            'product_uom': False,
                            'price_unit': 0,
                        })]

                purchase_order.update({'order_line': po_line})

        result = self.env.ref("purchase.purchase_rfq")
        result = result.sudo().read()[0]
        result['domain'] = str([('id', 'in', [purchase_order.id])])
        return result


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    max_qty = fields.Float(string="Max Quantity")

    @api.constrains('product_qty')
    def _check_qty_not_exceed_boq(self):
        for line in self:
            if line.max_qty and line.product_qty > line.max_qty:
                raise ValidationError(
                    "Quantity cannot be greater than BOQ quantity.\n\n"
                    f"Allowed: {line.max_qty}"
                )
