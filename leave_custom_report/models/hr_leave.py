from odoo import fields, models, api, _

from datetime import timedelta
from datetime import date

class HrLeave(models.Model):
    _inherit = 'hr.leave'

    contract_id = fields.Many2one(comodel_name='hr.contract', compute='get_contract_id')

    @api.depends('employee_id')
    def get_contract_id(self):
        for item in self:
            item.contract_id = False
            if item.employee_id:
                contract = self.env['hr.contract'].search([('employee_id', '=', item.employee_id.id)], limit=1)
                if contract:
                    item.contract_id = contract.id

    last_return_leave_date = fields.Date(compute='get_last_date')


    def find_first_matching_weekday(self, contract, start_date,days_of_week):
        # Get the sorted list of weekdays from attendance_ids
        days_of_week = list(map(int, days_of_week))
        current_date = start_date
        while True:
            # Check if the current date's weekday is in the list of days_of_week
            if current_date.weekday() in days_of_week:
                return current_date
            # Increment by one day
            current_date += timedelta(days=1)

    @api.depends('employee_id')
    def get_last_date(self):
        for rec in self:
            rec.last_return_leave_date = False
            if rec.employee_id:
                contract = self.env['hr.contract'].search([
                    ('employee_id','=',rec.employee_id.id),
                    ('state','=','open'),
                ],limit=1)
                if contract:
                    days_of_week = list(set(contract.resource_calendar_id.attendance_ids.mapped("dayofweek")))
                    days_of_week.sort()
                    current_date = rec.request_date_to+ timedelta(days=1)
                    matching_date = self.find_first_matching_weekday(contract, current_date,days_of_week)
                    if matching_date:
                        rec.last_return_leave_date = matching_date

    address_in_leave = fields.Char()
