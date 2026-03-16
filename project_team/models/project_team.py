# See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class ProjectProject(models.Model):
    _inherit = 'project.project'

    members_ids = fields.Many2many(
        'hr.employee',
        'project_employee_rel',
        'project_id',
        'employee_id',
        string='Project Members'
    )
    team_id = fields.Many2one('crm.team', "Project Team",
                              domain=[('type_team', '=', 'project')])

    @api.onchange('team_id')
    def _get_team_members(self):
        employees = self.env['hr.employee'].search([
            ('user_id', 'in', self.team_id.team_members_ids.ids)
        ])
        self.members_ids = [(6, 0, employees.ids)]
