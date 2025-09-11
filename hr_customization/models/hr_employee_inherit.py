# coding: utf-8
from odoo import models, fields, api, _
from datetime import datetime
from collections import namedtuple
from odoo.tools.float_utils import float_round
import datetime
from collections import defaultdict
from datetime import timedelta
from pytz import utc

from odoo import api, fields, models
from odoo.tools import float_utils

# This will generate 16th of days
ROUNDING_FACTOR = 16


class HrEmployeeInherit(models.Model):
    _inherit = 'hr.employee'

    all_leaves_count = fields.Float(string="Number of Leaves")
    all_leaves_from_report = fields.Float(string="Number of Leaves")
    check_report_leave = fields.Boolean(string="Report Leave")
    annual_leave_compute_type = fields.Selection(string="Annual Leave Compute Type",
                                                 selection=[('all_leaves', 'All Leaves Computed'),
                                                            ('some_leaves', 'Some Leaves Computed')])
    sick_leave_remaining_days = fields.Float(string="Sick Leave Remaining Days")

    employee_sick_leave_ids = fields.One2many(comodel_name='employee.sick.leave', inverse_name='employee_id',
                                              readonly=True)

    @api.model
    def get_employee_annual_leave(self):
        for rec in self.env['hr.employee'].search([]):
            contract_obj = self.env['hr.contract'].search([('id', '=', rec.contract_id.id), ('state', '=', 'open')],
                                                          limit=1)
            rec.all_leaves_count += (contract_obj.annual_leave_per_day / 365)

    def get_work_days_data(self, from_datetime, to_datetime, compute_leaves=True, calendar=None, domain=None):
        """
            By default the resource calendar is used, but it can be
            changed using the `calendar` argument.

            `domain` is used in order to recognise the leaves to take,
            None means default value ('time_type', '=', 'leave')

            Returns a dict {'days': n, 'hours': h} containing the
            quantity of working time expressed as days and as hours.
        """
        resource = self.resource_id
        calendar = calendar or self.resource_calendar_id

        # naive datetimes are made explicit in UTC
        if not from_datetime.tzinfo:
            from_datetime = from_datetime.replace(tzinfo=utc)
        if not to_datetime.tzinfo:
            to_datetime = to_datetime.replace(tzinfo=utc)

        # total hours per day: retrieve attendances with one extra day margin,
        # in order to compute the total hours on the first and last days
        from_full = from_datetime - timedelta(days=1)
        to_full = to_datetime + timedelta(days=1)
        intervals = calendar._attendance_intervals(from_full, to_full, resource)
        day_total = defaultdict(float)
        for start, stop, meta in intervals:
            day_total[start.date()] += (stop - start).total_seconds() / 3600

        # actual hours per day
        if compute_leaves:
            intervals = calendar._work_intervals(from_datetime, to_datetime, resource, domain)
        else:
            intervals = calendar._attendance_intervals(from_datetime, to_datetime, resource)
        day_hours = defaultdict(float)
        for start, stop, meta in intervals:
            day_hours[start.date()] += (stop - start).total_seconds() / 3600

        # compute number of days as quarters
        days = sum(
            float_utils.round(ROUNDING_FACTOR * day_hours[day] / day_total[day]) / ROUNDING_FACTOR
            for day in day_hours
        )
        return {
            'days': days,
            'hours': sum(day_hours.values()),
        }


class HrEmployeesPublic(models.Model):
    _inherit = 'hr.employee.public'

    check_report_leave = fields.Boolean(string="Report Leave")
