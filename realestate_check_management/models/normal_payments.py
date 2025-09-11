from odoo import fields, models, api


class NormalPayments(models.Model):
    _inherit = 'normal.payments'

    project_id = fields.Many2one('project.project','Project',required=False)
    reservation_id = fields.Many2one('property.reservation',string='Reservation')
    property_id = fields.Many2one("product.template", "Property")
    is_construction = fields.Boolean(string='Is_construction', required=False)
    adv_percent = fields.Float(string='Advanced Amount', required=False)
    retention_percent = fields.Float(string='Retention Amount', required=False)
    def action_confirm(self):
        pay_amt = 0
        if self.payment_subtype and self.send_rec_money != 'internal':
            pay_amt = self.amount
        else:
            pay_amt = self.amount1
        move = {
            'name': '/',
            'journal_id': self.payment_method.id,
            'ref': self.receipt_number + "-" + self.description if self.description else self.receipt_number,
            'company_id': self.user_id.company_id.id,
            'normal_payment_id': self.id,
        }

        move_line_name = 'Partner Payment ' + 'Receipt:' + self.receipt_number if self.partner_id else 'Receipt:' + self.receipt_number
        move_line = {
            'name': move_line_name + "-" + self.description if self.description else move_line_name,
            'partner_id': self.partner_id.id,
            'ref': self.receipt_number + "-" + self.description if self.description else self.receipt_number,
            'jebal_con_pay_id': self.id,
            'normal_payment_id': self.id,
        }

        if self.send_rec_money in ['send', 'internal']:
            debit_account = [{'account': self.account_id.id, 'percentage': 100, 'analyitc_id': self.analyitc_id.id, }]
            credit_account = [{'account': self.payment_method.default_account_id.id, 'percentage': 100}]
        else:
            # if self.is_construction:
            #     print('self.is_construction', self.is_construction)
            #     credit_account = [{'account': self.partner_id.adv_customer.id, 'percentage': self.adv_percent, },
            #                       {'account': self.partner_id.customer_retention.id,
            #                        'percentage': self.retention_percent, }]
            #     print('credit_account', credit_account)
            # else:
            credit_account = [{'account': self.account_id.id, 'percentage': 100, }]
            # debit_account = [{'account': self.payment_method.default_account_id.id, 'percentage': 100}]
            debit_account = [{'account': self.payment_method.default_account_id.id, 'percentage': 100,
                              'analyitc_id': self.analyitc_id.id, }]

        self.env['create.moves'].create_move_lines(move=move, move_line=move_line,
                                                   debit_account=debit_account,
                                                   credit_account=credit_account,
                                                   src_currency=self.currency_id,
                                                   amount=pay_amt)
        self.state = 'posted'
        if self.payment_subtype:
            for check in self.pay_check_ids:
                check_line_val = {}
                check_line_val['check_book_id'] = check.check_book_id.id
                check_line_val['check_number'] = check.check_number
                check_line_val['pay_check_id'] = check.id
                check_line_val['check_date'] = check.check_date
                check_line_val['check_bank'] = check.bank.id
                check_line_val['dep_bank'] = check.dep_bank.id
                check_line_val['currency_id'] = self.currency_id.id
                if self.send_rec_money == 'rece':
                    check_line_val['state'] = 'holding'
                    check_line_val['check_type'] = 'rece'
                else:
                    check_line_val['state'] = 'handed'
                    check_line_val['check_type'] = 'pay'
                check_line_val['amount'] = check.amount
                check_line_val['open_amount'] = check.amount
                check_line_val['type'] = 'regular'
                check_line_val['notespayable_id'] = self.payment_method.default_account_id.id
                check_line_val['notes_rece_id'] = self.payment_method.default_account_id.id
                check_line_val['investor_id'] = self.partner_id.id
                check_line_val['journal_id'] = self.payment_method.id
                check.check_management_id = self.env['check.management'].create(check_line_val)
                check.payment_strategy_id.check_management_id = check.check_management_id
        return True


class PaymentsCheckCreate(models.Model):
    _inherit = 'native.payments.check.create'

    payment_strategy_id = fields.Many2one('payment.strategy.line',string='Payment strategy ',copy=False)
