from odoo import fields, models, api


class PaymentStrategyLine(models.Model):
    _inherit = 'payment.strategy.line'

    check_payment_id = fields.Many2one('normal.payments', string='cash payment', )

    def create_payment(self):
        payment_obj = self.env['normal.payments']

        if self.value_amount > 0:
            vals = {
                'send_rec_money': 'rece',
                'partner_id': self.reservation_id.customer_id.id,
                'account_id': self.reservation_id.customer_id.property_account_receivable_id.id,
                'amount1': self.value_amount,
                'project_id': self.reservation_id.project_id.id,
                'property_id': self.reservation_id.property_id.id,
                'reservation_id': self.reservation_id.id,
                'payment_method': self.journal_id.id,
                'receipt_number': self.check_no,
            }
            if self.journal_id.type == 'cash':
                payment_id = payment_obj.create(vals)
                self.check_payment_id = payment_id
            elif self.journal_id.type == 'bank':
                line_vals = [(0, 0, {
                    'check_date': self.payment_date,
                    'amount': self.value_amount,
                    'check_number': self.check_no,
                    'payment_strategy_id': self.id,
                })]
                print('line_vals',line_vals)
                if self.reservation_id.check_bank_payment_id:
                    self.reservation_id.check_bank_payment_id.update(
                        {'pay_check_ids': line_vals}
                    )
                    self.check_payment_id = self.reservation_id.check_bank_payment_id
                else:
                    vals.update({'pay_check_ids': line_vals, 'is_bank_recieved': True})
                    payment_id = payment_obj.create(vals)
                    self.check_payment_id = payment_id
                    self.reservation_id.check_bank_payment_id = payment_id

    check_management_id = fields.Many2one('check.management', string='Check management')

