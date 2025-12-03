from odoo import fields, models, api, _


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    penalty_line_ids = fields.One2many(comodel_name='penalty.request', inverse_name='payslip_id')

    def compute_sheet(self):
        self._compute_penalty_input_lines()
        return super(HrPayslip, self).compute_sheet()

    def _compute_penalty_input_lines(self):
        for item in self:
            if item.employee_id:
                penalty_ids = self.env['penalty.request.payment'].search([
                    ('employee_id', '=', item.employee_id.id),
                    ('penalty_id.state', '=', 'approved'),
                    ('date', '>=', item.date_from),
                    ('date', '<=', item.date_to)
                ])

                penalty_needs_to_be_deleted = item.input_line_ids.filtered(
                    lambda x: x.is_penalty
                )
                penalty_needs_to_be_deleted.unlink()

                for line in penalty_ids:
                    input_line = item.input_line_ids.filtered(
                        lambda x: x.penalty_payment_id.id == line.id
                    )
                    if input_line:
                        input_line.write({
                            'input_type_id': line.penalty_id.input_type_id.id,
                            'name': line.name,
                            'amount': line.amount,
                            'penalty_payment_id': line.id,
                            'is_penalty': True
                        })
                    else:
                        item.input_line_ids = [(0, 0, {
                            'input_type_id': line.penalty_id.input_type_id.id,
                            'name': line.name,
                            'amount': line.amount,
                            'penalty_payment_id': line.id,
                            'is_penalty': True
                        })]
