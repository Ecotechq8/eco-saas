from odoo import models, fields, api, _


class HrPayslipWorkedDays(models.Model):
    _inherit = 'hr.payslip.worked_days'

    work_entry_type_id = fields.Many2one(
        'hr.work.entry.type',
        string='Work Entry Type',
        help="Specifies the type of work entry linked to this line.",
    )
    custom_number_of_hours = fields.Float(
        string='Number of Hours',
        compute='_compute_custom_number_of_hours',
        store=False,
    )

    @api.depends('number_of_days')
    def _compute_custom_number_of_hours(self):
        for rec in self:
            hours = 0
            if rec.contract_id and rec.contract_id.resource_calendar_id:
                hours = rec.number_of_days * rec.contract_id.resource_calendar_id.total_worked_hours
            rec.custom_number_of_hours = hours

    @api.depends(
        'is_paid',
        'is_credit_time',
        'number_of_hours',
        'payslip_id',
        'contract_id.wage',
        'payslip_id.sum_worked_hours'
    )
    def _compute_amount(self):
        for worked_days in self.filtered(lambda wd: not wd.payslip_id.edited):
            if not worked_days.contract_id or worked_days.code == 'OUT':
                worked_days.amount = 0
                continue

            contract = worked_days.payslip_id.contract_id
            if worked_days.payslip_id.wage_type == "hourly":
                worked_days.amount = contract.hourly_wage * worked_days.number_of_hours
            else:
                if worked_days.number_of_days > 0:
                    worked_days.amount = (
                        contract.contract_wage * worked_days.number_of_hours /
                        (worked_days.payslip_id.sum_worked_hours or 1)
                    )
                else:
                    worked_days.amount = 0
