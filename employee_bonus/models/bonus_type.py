from odoo import fields, models, api, _


class BonusType(models.Model):
    _name = 'bonus.type'

    name = fields.Char(string='Bonus Name')
    type = fields.Selection(selection=[('hour', 'Hour'), ('day', 'Day'), ('fixed', 'Amount')])
    overtime_rule_id = fields.Many2one(comodel_name='hr.overtime.rule', string='Overtime Rule')
    input_type_id = fields.Many2one(comodel_name='hr.payslip.input.type', domain="[('is_bonus','=',True)]",
                                    string='Input Type', required=True)
