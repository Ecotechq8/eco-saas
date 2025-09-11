from odoo import models, fields, api, _


class LoansLines(models.Model):
    _name = 'reimbursement.loans.line'

    name = fields.Char()
    date = fields.Date()
    type = fields.Many2one(comodel_name='employee.loan.type')
    amount = fields.Float()
    amount_paid = fields.Float()
    amount_remaining = fields.Float()
    installment_amount = fields.Float()
    loan_id = fields.Many2one(comodel_name='employee.loan')
    reimbursement_id = fields.Many2one(comodel_name='compensation.request')
