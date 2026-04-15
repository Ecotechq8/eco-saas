# -*- coding: utf-8 -*-

from odoo import models, fields


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    project_ids = fields.Many2many(
        comodel_name='project.project',
        relation='employee_project_rel',
        column1='employee_id',
        column2='project_id',
        string='Assigned Projects',
        domain=[('active', '=', True)],
    )
