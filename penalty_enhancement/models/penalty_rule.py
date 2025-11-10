from odoo import fields, models, api, _


class PenaltyRle(models.Model):
    _name = 'penalty.rule'

    name = fields.Char(string='name', required=True)
    number_of_days = fields.Integer()
    penalty_type = fields.Selection(selection=[('amount', 'Amount'), ('days', 'Days'), ('hours', 'Hours')],
                                    required=True)
    line_ids = fields.One2many(comodel_name='hr.penalty.rule',
                               inverse_name='penalty_id',
                               string='Penalty In Periods')
    type_of_approval = fields.Selection(selection=[('normal', 'Normal'), ('portal', 'Portal')], default='normal')
    # input_type_id = fields.Many2one(comodel_name='hr.payslip.input.type', domain="[('is_penalty','=',True)]",
    #                                 string='Input Type', required=True)
    #

class HrPenaltyRule(models.Model):
    _name = 'hr.penalty.rule'

    penalty_id = fields.Many2one(comodel_name='penalty.rule')
    rate = fields.Float(string='Rate', required=True, digits=(12, 3))
    counter = fields.Selection(string="Times", selection=[
        ('1', 'First Time'),
        ('2', 'Second Time'),
        ('3', 'Third Time'),
        ('4', 'Fourth Time'),
        ('5', 'Fifth Time')], required=True)
