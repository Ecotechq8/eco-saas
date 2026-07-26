from odoo import models, fields, _

class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    is_cheque = fields.Boolean(string="Payment by Cheque?")
    cheque_number = fields.Char(string="Cheque Number")
    cheque_date = fields.Date(string="Cheque Date")
    drawn_on = fields.Char(string="Drawn On")

    def _create_payments(self):
        payments = super()._create_payments()

        # Write your new fields to the created payments
        payments.write({
            'is_cheque': self.is_cheque,
            'cheque_number': self.cheque_number,
            'cheque_date': self.cheque_date,
            'drawn_on': self.drawn_on,
        })

        return payments
