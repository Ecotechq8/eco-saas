# -*- coding: utf-8 -*-


from odoo import api, fields, models, _


class LoanRejectReason(models.TransientModel):
    _name = "reservation.cancel.reason"
    # _name = "loan.reject.reason"

    reason = fields.Text('Reason', required="1")
    type = fields.Selection(
        string='Type',
        selection=[('free', 'Free'),
                   ('amount', 'Amount'), ],
        required=True)
    amount = fields.Float(string='Amount')
    journal_id = fields.Many2one('account.journal', string='Payment Method')

    def cancel_reason(self):
        model = self.env.context.get('active_model')
        active_id = self.env[model].browse(self.env.context.get('active_id'))
        print('active_model', model)
        # active_id = self._context.get('active_id')
        # reserve_id = self.env['property.reservation'].browse(active_id)
        vals = {}
        if model == 'property.reservation':
            active_id.property_id.write({"state": "free"})
            vals.update({'partner_id': active_id.customer_id.id, 'reservation_id': active_id.id})
            active_id.write({"state": "cancel"})
        elif model == 'sale.order':
            vals.update({'partner_id': active_id.partner_id.id, 'reservation_id': active_id.reservation_id.id})
            active_id.property_id.write({"state": "free"})
            active_id.reservation_id.write({"state": "cancel"})
            active_id._action_cancel()

            if active_id.invoice_ids:
                invoices =active_id.invoice_ids.filtered(lambda x: x.state == 'posted')

                for invoice in invoices:
                    action = invoice.action_reverse()
                    reversal_wizard = self.env[action['res_model']].with_context(
                        active_ids=invoice.ids,
                        active_model='account.move',
                    ).create({
                        'journal_id': invoice.journal_id.id,  # Field is not precompute but required
                    })
                    action = reversal_wizard.reverse_moves()
                    reversal_move = self.env['account.move'].browse(action['res_id'])
                    reversal_move.action_post()
        if self.type == 'amount' and self.amount > 0:
            payment_obj = self.env['account.payment']
            vals.update({
                'payment_type': 'inbound',
                'amount': self.amount,
                'project_id': active_id.project_id.id,
                'property_id': active_id.property_id.id,
                'journal_id': self.journal_id.id,
            })
            payment_id = payment_obj.create(vals)
            active_id.cancel_payment_id = payment_id
        active_id.cancel_reason = self.reason
        active_id.write({"state": "cancel"})

        return True
