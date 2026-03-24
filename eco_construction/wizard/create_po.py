from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class LoanRejectReason(models.TransientModel):
    _name = "wizard.create.purchase.order"

    type = fields.Selection(
        string='Contract Type',
        selection=[
            ('consultation', 'Consultation'),
            ('design', 'Design'),
            ('construction', 'Construction'),
            ('other', 'Other')
        ],
        required=True)

    partner_id = fields.Many2one('res.partner', string='Vendor/Subcontractor', required=True)

    def action_create_po(self):
        model = self.env.context.get('active_model')
        active_id = self.env[model].browse(self.env.context.get('active_id'))

        po_line = []

        # ================= PROJECT =================
        if model == 'project.project':

            # ❌ REMOVE TYPE CONDITION (important)
            if active_id.project_request_quota_line:
                for line in active_id.project_request_quota_line:

                    # skip empty products
                    if not line.product_id:
                        continue

                    if not line.display_type:
                        po_line.append((0, 0, {
                            'product_id': line.product_id.id,
                            'name': line.product_id.display_name,
                            'product_qty': line.product_uom_qty,
                            'max_qty': line.product_uom_qty,
                            'product_uom': line.product_uom.id,
                            'price_unit': line.price_unit or 0,
                        }))
                    else:
                        po_line.append((0, 0, {
                            'display_type': line.display_type,
                            'name': line.name,
                        }))

        # ================= CREATE PO =================
        po_dict = {
            'partner_id': self.partner_id.id,
            'is_subcontracting': True,
            'project_id': active_id.id,
            'order_line': po_line,
        }

        purchase_order = self.env['purchase.order'].create(po_dict)

        # ================= DEBUG (important) =================
        print("LINES CREATED:", po_line)

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
                    f"Quantity cannot exceed BOQ quantity.\nAllowed: {line.max_qty}"
                )


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    state = fields.Selection(
        selection_add=[
            ('planning', 'Planning Approval'),
            ('operation', 'Operation Approval'),
            ('general', 'General Manager Approval'),
        ],
        ondelete={
            'planning': 'set default',
            'operation': 'set default',
            'general': 'set default',
        }
    )

    def action_planning_approve(self):
        for rec in self:
            rec.state = 'planning'

    def action_operation_approve(self):
        for rec in self:
            rec.state = 'operation'

    def action_general_approve(self):
        for rec in self:
            rec.state = 'general'

    def button_confirm(self):
        for rec in self:
            if rec.state != 'general':
                raise ValidationError("You must get General Manager approval first.")
        return super().button_confirm()
