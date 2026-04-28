from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class TermAndConditionOption(models.Model):
    _name = "term.and.condition.option"
    _description = "Term And Condition Option"

    name = fields.Char(string='Name', help='Terms & Condition Name', required=True)
    term_and_condition_id = fields.Many2one('term.and.condition', string='Terms And Condition')
    is_default = fields.Boolean(string="Is Default")

    @api.constrains('is_default')
    def onchange_is_default(self):
        tnc_ids = self.env['term.and.condition'].search([])
        for tnc in tnc_ids:
            obj_ids = self.env['term.and.condition.option'].search([
                ('term_and_condition_id', '=', tnc.id),
                ('is_default', '=', True)
            ])
            if len(obj_ids) > 1:
                raise ValidationError("Only Select One Default Terms and Conditions Option")

