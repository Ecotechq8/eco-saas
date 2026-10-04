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

    @api.depends('number_of_hours', 'contract_id.wage')
    def _compute_amount(self):
        for worked_days in self:
            if not worked_days.contract_id or worked_days.code == 'OUT':
                worked_days.amount = 0.0
                continue
            contract = worked_days.contract_id
            wage_type = getattr(worked_days.payslip_id, 'wage_type', False)
            if wage_type == "hourly":
                hourly_wage = getattr(contract, 'hourly_wage', 0.0)
                worked_days.amount = hourly_wage * worked_days.number_of_hours
            else:
                contract_wage = getattr(contract, 'contract_wage', contract.wage or 0.0)
                sum_hours = getattr(worked_days.payslip_id, 'sum_worked_hours', 0.0) or (worked_days.number_of_hours or 1.0)
                worked_days.amount = (
                    contract_wage * worked_days.number_of_hours / sum_hours
                ) if worked_days.number_of_days > 0 else 0.0

