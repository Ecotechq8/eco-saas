from odoo import fields, models, api, _


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    penalty_line_ids = fields.One2many(comodel_name='penalty.request', inverse_name='payslip_id')

    def compute_sheet(self):
        self._compute_input_line_ids()
        res = super(HrPayslip, self).compute_sheet()
        return res

    # @api.depends('employee_id', 'contract_id', 'struct_id', 'date_from', 'date_to', 'struct_id')
    # def _compute_input_line_ids(self):
    #     res = super(HrPayslip, self)._compute_input_line_ids()
    #     for item in self:
    #         if item.employee_id:
    #             penalty_ids = self.env['penalty.request.payment'].search([
    #                 ('employee_id', '=', item.employee_id.id), ('penalty_id.state', '=', 'approved'),
    #                 ('date', '>=', item.date_from), ('date', '<=', item.date_to)])
    #
    #             penalty_needs_to_be_deleted = item.input_line_ids.filtered(
    #                 lambda x: x.is_penalty == True and not x.penalty_payment_id.id)
    #             penalty_needs_to_be_deleted.unlink()
    #
    #             if penalty_ids:
    #                 for line in penalty_ids:
    #                     if not line.id in item.input_line_ids.mapped("penalty_payment_id").ids:
    #                         item.input_line_ids = [(0, 0, {
    #                             'input_type_id': line.penalty_id.input_type_id.id,
    #                             'name': line.name,
    #                             'amount': line.amount,
    #                             'penalty_payment_id': line.id,
    #                             'is_penalty': True
    #                         })]
    #                     else:
    #                         input_line = item.input_line_ids.filtered(lambda x: x.penalty_payment_id.id == line.id)
    #                         input_line.write({
    #                             'input_type_id': line.penalty_id.input_type_id.id,
    #                             'name': line.name,
    #                             'amount': line.amount,
    #                             'penalty_payment_id': line.id,
    #                             'is_penalty': True
    #                         })
    #     return res
