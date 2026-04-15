# -*- coding: utf-8 -*-

from odoo import models, fields


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    project_ids = fields.Many2many(
        'project.project',
        string='Assigned Projects',
        domain=[('active', '=', True)],
    )
