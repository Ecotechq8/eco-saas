from odoo import fields, models, api



class PaymentStrategyLine(models.Model):
    _name = 'payment.strategy.line'
    _description = 'Payment Strategy For Payment'
    _order = 'payment_date ASC'

    description = fields.Char(
        string='Description')
    journal_id = fields.Many2one('account.journal', string='Payment Method')
    type = fields.Selection(
        string='Type',
        selection=[('installment', 'Installment'),
                   ('deposit', 'Deposit'),
                   ('maintenance', 'Maintenance'),
                   ])
    reservation_id = fields.Many2one('property.reservation',string='Reservation_id')
    payment_date = fields.Date(
        string='Payment Date', )
    payment_id = fields.Many2one('account.payment', string='Payment ',required=False)
    check_no = fields.Char(
        string='Check Number',
        required=False)

    value_amount = fields.Float(string='Amount')
    percent = fields.Float(string='Percent(%)', required=False)
    all_percent = fields.Float(
        string='Percent',
        required=False)
    serial = fields.Integer(
        string='Serial', 
        required=False)
    def create_payment(self):
        if self.value_amount > 0:
            payment_obj = self.env['account.payment']
            payment_id = payment_obj.create({
                'payment_type':'inbound',
                'partner_id':self.reservation_id.customer_id.id,
                'amount':self.value_amount,
                'project_id':self.reservation_id.project_id.id,
                'property_id':self.reservation_id.property_id.id,
                'reservation_id':self.reservation_id.id,
                'journal_id':self.journal_id.id,
                'check_no':self.check_no,
            })
            self.payment_id = payment_id