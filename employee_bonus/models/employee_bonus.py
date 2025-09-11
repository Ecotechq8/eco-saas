from odoo import fields, models, api, _
from odoo.exceptions import UserError


class EmployeeBonus(models.Model):
    _name = 'employee.bonus'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    @api.model
    def _get_employee(self):
        employee_id = self.env['hr.employee'].search(
            [('user_id', '=', self.env.user.id), ('company_id', 'in', self.env.user.company_ids.ids)], limit=1)
        return employee_id

    name = fields.Char()
    bonus_type = fields.Many2one(comodel_name='bonus.type', required=True)
    type_of_bonus = fields.Selection(related='bonus_type.type', store=True)
    date = fields.Date()
    value = fields.Float(digits=(12, 3))
    amount = fields.Float(string='Bonus Amount', compute='get_bonus_amount', digits=(12, 3))
    note = fields.Text()
    employee_id = fields.Many2one(comodel_name='hr.employee', default=_get_employee)
    department_id = fields.Many2one(comodel_name='hr.department', related='employee_id.department_id')
    contract_id = fields.Many2one(comodel_name='hr.contract', related='employee_id.contract_id')

    payslip_id = fields.Many2one(comodel_name='hr.payslip')

    # New fields
    time = fields.Float(digits=(12, 3))
    rate = fields.Float(compute='get_rate', readonly=True, digits=(12, 3))
    total_hours = fields.Float(compute='get_bonus_amount', digits=(12, 3))
    day = fields.Float(digits=(12, 3))

    state = fields.Selection(selection=[('draft', 'Draft'), ('emp_mang_submit', 'Manager Submit'),
                                        ('approved', 'Approved'),
                                        ('rejected', 'Rejected')], default='draft')

    def reject_button(self):
        for rec in self:
            rec.state = 'rejected'

    def hr_manager_approve(self):
        self.write({'state': 'approved'})

    def employee_manager_approve(self):
        self.write({'state': 'emp_mang_submit'})

    def get_rate(self):
        for rec in self:
            rec.rate = rec.bonus_type.overtime_rule_id.rate if rec.bonus_type.overtime_rule_id else 0.0

    @api.ondelete(at_uninstall=False)
    def _unlink_if_correct_states(self):
        for bonus in self:
            if bonus.state == 'approved':
                raise UserError(_('You cannot delete a bonus that is approved'))

    @api.depends('contract_id', 'value')
    def get_bonus_amount(self):
        for rec in self:
            rec.amount, rec.total_hours = 0.0, 0.0
            if rec.bonus_type.type == 'hour':
                rec.total_hours = (rec.time * rec.rate)
                rec.amount = rec.total_hours * rec.contract_id.hour_value
            elif rec.bonus_type.type == 'day':
                rec.amount = rec.day * rec.contract_id.day_value * rec.bonus_type.overtime_rule_id.rate
            elif rec.bonus_type.type == 'fixed':
                rec.amount = rec.value
