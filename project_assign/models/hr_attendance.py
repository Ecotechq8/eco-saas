# -*- coding: utf-8 -*-

from odoo import models, fields, api


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    project_ids = fields.Many2many(
        'project.project',
        related='employee_id.project_ids',
        string='Employee Projects',
        store=True,
        readonly=True,
        help='Projects the employee is working on.'
    )
