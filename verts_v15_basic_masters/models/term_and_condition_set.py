from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class TermAndConditionSet(models.Model):
    _name = "term.and.condition.set"
    _description = "Term And Condition Set"

    name = fields.Char(string='Name', required=True)
    is_default = fields.Boolean(string='Is Default', default=False, help='Set Terms & Condition Set in Default')
    tc_set_type = fields.Selection([('sale', 'Sales Order'),
                                    ('purchase', 'Purchase Order'),
                                    ('cust_invoice', 'Customer Invoice'),
                                    ('vend_invoice', 'Vendor Invoice')],
                                   string='Type')
    tc_set_line = fields.One2many('tc.set.lines', 'tc_set_id', string='Terms And Condition Set Lines')

    @api.constrains('is_default')
    def onchange_is_default(self):
        obj_ids = self.env['term.and.condition.set'].search([])
        sale_check = obj_ids.filtered(lambda r: r.is_default == True and r.tc_set_type == 'sale')
        if len(sale_check) > 1:
            raise ValidationError("Only Select One Default Sale Order Terms and Conditions Set")
        pur_check = obj_ids.filtered(lambda r: r.is_default == True and r.tc_set_type == 'purchase')
        if len(pur_check) > 1:
            raise ValidationError("Only Select One Default Purchase Order Terms and Conditions Set")
        cust_check = obj_ids.filtered(lambda r: r.is_default == True and r.tc_set_type == 'cust_invoice')
        if len(cust_check) > 1:
            raise ValidationError("Only Select One Default Customer Invoice Terms and Conditions Set")
        vend_check = obj_ids.filtered(lambda r: r.is_default == True and r.tc_set_type == 'vend_invoice')
        if len(vend_check) > 1:
            raise ValidationError("Only Select One Default Vendor Invoice Terms and Conditions Set")


class TcSetLines(models.Model):
    _name = "tc.set.lines"
    _description = "Tc Set Lines"
    
    tc_set_id = fields.Many2one('term.and.condition.set', string='Terms And Condition Set Id')
    term_and_condition_id = fields.Many2one('term.and.condition', string='Condition')
    removable = fields.Selection([('yes', 'Yes'), ('no', 'No')], default='no',
                                 help='If user is allowed to remove this condition in the form such as SO/PO etc then choose it as Yes.',
                                 string='Removable')


