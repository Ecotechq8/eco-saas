# -*- coding: utf-8 -*-

from odoo import models, fields


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    project_ids = fields.Many2many(
        'project.project',
        'employee_project_rel',
        'employee_id',
        'project_id',
        string='Assigned Projects',
        domain=[('active', '=', True)],
    )
