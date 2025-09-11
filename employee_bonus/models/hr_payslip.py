from odoo import fields, models, api, _


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    bonus_line_ids = fields.One2many(comodel_name='employee.bonus', inverse_name='payslip_id')

    def compute_sheet(self):
        self._compute_input_line_ids()
        res = super(HrPayslip, self).compute_sheet()
        return res

    @api.depends('employee_id', 'contract_id', 'struct_id', 'date_from', 'date_to', 'struct_id')
    def _compute_input_line_ids(self):
        res = super(HrPayslip, self)._compute_input_line_ids()
        for item in self:
            if item.employee_id:
                bonus_ids = self.env['employee.bonus'].search([
                    ('employee_id', '=', item.employee_id.id), ('state', '=', 'approved'),
                    ('date', '>=', item.date_from), ('date', '<=', item.date_to)])

                bonus_needs_to_be_deleted = item.input_line_ids.filtered(
                    lambda x: x.is_bonus == True and not x.bonus_id.id)
                bonus_needs_to_be_deleted.unlink()
                if bonus_ids:
                    for line in bonus_ids:
                        if (line.bonus_type.input_type_id and
                                not line.bonus_type.input_type_id.id in item.input_line_ids.mapped(
                                    "input_type_id").ids):
                            item.input_line_ids = [(0, 0, {
                                'input_type_id': line.bonus_type.input_type_id.id,
                                'name': line.name,
                                'amount': line.amount,
                                'bonus_id': line.id,
                                'is_bonus': True
                            })]
                        else:
                            input_line = item.input_line_ids.filtered(lambda x: x.bonus_id.id == line.id)
                            input_line.write({
                                'input_type_id': line.bonus_type.input_type_id.id,
                                'name': line.name,
                                'amount': line.amount,
                                'bonus_id': line.id,
                                'is_bonus': True
                            })
        return res
