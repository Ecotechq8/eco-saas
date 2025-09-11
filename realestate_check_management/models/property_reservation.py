from odoo import fields, models, api


class PropertyReservation(models.Model):
    _inherit = 'property.reservation'

    check_bank_payment_id = fields.Many2one('normal.payments', string='check bank payment', )

    def action_check_contract(self):

        for line in self.payment_strategy_line_ids:
            if line.journal_id.type == 'bank':
                line.create_payment()

        self.write({"state": "check"})
