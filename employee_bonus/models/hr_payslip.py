from odoo import fields, models, api, _


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    bonus_line_ids = fields.One2many(comodel_name='employee.bonus', inverse_name='payslip_id')

    def compute_sheet(self):
        # Compute your input lines including bonuses before computing the sheet
        self._compute_bonus_input_lines()
        res = super(HrPayslip, self).compute_sheet()
        return res

    def _compute_bonus_input_lines(self):
        for item in self:
            if item.employee_id:
                bonus_ids = self.env['employee.bonus'].search([
                    ('employee_id', '=', item.employee_id.id),
                    ('state', '=', 'approved'),
                    ('date', '>=', item.date_from),
                    ('date', '<=', item.date_to)
                ])

                bonus_needs_to_be_deleted = item.input_line_ids.filtered(
                    lambda x: x.is_bonus and not x.bonus_id)
                bonus_needs_to_be_deleted.unlink()

                for line in bonus_ids:
                    input_line = item.input_line_ids.filtered(lambda x: x.bonus_id.id == line.id)
                    if input_line:
                        input_line.write({
                            'input_type_id': line.bonus_type.input_type_id.id,
                            'name': line.name,
                            'amount': line.amount,
                            'bonus_id': line.id,
                            'is_bonus': True
                        })
                    else:
                        item.input_line_ids = [(0, 0, {
                            'input_type_id': line.bonus_type.input_type_id.id,
                            'name': line.name,
                            'amount': line.amount,
                            'bonus_id': line.id,
                            'is_bonus': True
                        })]
