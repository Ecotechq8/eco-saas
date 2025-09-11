# -*- coding: utf-8 -*-


from odoo import api, fields, models, _


class LoanRejectReason(models.TransientModel):
    _name = "wizard.create.purchase.order"

    type = fields.Selection(
        string='Contract Type',
        selection=[('consultation', 'Consultation'),
                   ('design', 'Design'),
                   ('construction', 'Construction'),
                   ('other', 'Other'),
                   ],
        required=True)
    partner_id = fields.Many2one('res.partner', string='Vendor/Subcontractor', required=True)

    def action_create_po(self):
        model = self.env.context.get('active_model')
        active_id = self.env[model].browse(self.env.context.get('active_id'))
        po_dict = {'partner_id': self.partner_id.id,'is_subcontracting':True,'project_id': active_id.id}
        po_line = []
        purchase_order = self.env['purchase.order'].create(po_dict)
        if self.type == 'other' and active_id.project_request_quota_line:
            for line in active_id.project_request_quota_line:
                if not line.display_type:
                    po_line += [(0, 0, {
                        'product_id': line.product_id.id,
                        'product_qty': line.product_uom_qty,
                        # 'order_id': purchase_order.id,
                        'product_uom': line.product_uom.id,
                        'price_unit': line.price_unit,
                         'analytic_distribution':{active_id.analytic_account_id.id: 100}

                    })]
                else:
                    po_line += [(0, 0, {
                        'display_type': line.display_type,
                        'name': line.name,
                        'product_id': None,
                        'product_qty': 0,
                        # 'order_id': purchase_order.id,
                        'product_uom': None,
                        'price_unit': 0,

                    })]

            purchase_order.update({'order_line': po_line})
        result = self.env.ref("purchase.purchase_rfq")
        action_ref = result or False
        result = action_ref.sudo().read()[0]
        result['domain'] = str([('id', 'in', [purchase_order.id])])
        return result
