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
        active_id = self.env[model].browse(self.env.context.get('active_id'))

        po_line = []

        # ================= SALE ORDER =================
        if model == 'sale.order':

            if self.type == 'other' and active_id.request_quota_line:
                for line in active_id.request_quota_line:

                    if not line.display_type:
                        po_line.append((0, 0, {
                            'product_id': line.product_id.id,
                            'name': line.product_id.name,
                            'product_qty': line.product_uom_qty,
                            'max_qty': line.product_uom_qty,
                            'product_uom': line.product_uom.id,
                            'price_unit': line.price_unit,
                        }))
                    else:
                        po_line.append((0, 0, {
                            'display_type': line.display_type,
                            'name': line.name,
                        }))

            po_dict = {
                'partner_id': self.partner_id.id,
                'is_subcontracting': True,
                'project_id': active_id.con_project_id.id,
                'order_line': po_line,
            }

            purchase_order = self.env['purchase.order'].create(po_dict)

        # ================= PROJECT =================
        elif model == 'project.project':

            if self.type == 'other' and active_id.project_request_quota_line:
                for line in active_id.project_request_quota_line:

                    if not line.display_type:
                        po_line.append((0, 0, {
                            'product_id': line.product_id.id,
                            'name': line.product_id.name,
                            'product_qty': line.product_uom_qty,
                            'max_qty': line.product_uom_qty,
                            'product_uom': line.product_uom.id,
                            'price_unit': line.price_unit,
                        }))
                    else:
                        po_line.append((0, 0, {
                            'display_type': line.display_type,
                            'name': line.name,
                        }))

            po_dict = {
                'partner_id': self.partner_id.id,
                'is_subcontracting': True,
                'project_id': active_id.id,
                'order_line': po_line,
            }

            purchase_order = self.env['purchase.order'].create(po_dict)

        # ================= OPEN PO =================
        result = self.env.ref("purchase.purchase_rfq").sudo().read()[0]
        result['domain'] = [('id', 'in', [purchase_order.id])]
        return result


# ================= VALIDATION =================
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

    # OPTIONAL UX IMPROVEMENT
    @api.onchange('product_qty')
    def _onchange_product_qty(self):
        for line in self:
            if line.max_qty and line.product_qty > line.max_qty:
                line.product_qty = line.max_qty
                return {
                    'warning': {
                        'title': "Warning",
                        'message': f"Max allowed quantity is {line.max_qty}"
                    }
                }


