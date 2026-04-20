from odoo import api, fields, models, _


class TermAndCondition(models.Model):
    _name = "term.and.condition"
    _description = "Term And Condition"
    
    name = fields.Char(string='Name', help='Terms & Condition name', required=True)
    term_and_condition_line = fields.One2many('term.and.condition.lines', 'term_and_condition_id', string='Terms And Condition Lines')


class TermAndConditionLines(models.Model):
    _name = "term.and.condition.lines"   
    _description = "Term And Condition Lines"

    term_and_condition_id = fields.Many2one('term.and.condition', string='Terms And Condition Id')
    term_and_condition_option_id = fields.Many2one('term.and.condition.option', string='Terms And Condition Option')

