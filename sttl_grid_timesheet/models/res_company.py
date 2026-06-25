# -*- coding: utf-8 -*-

from odoo import _, api, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    @api.model
    def _ensure_missing_internal_projects(self):
        companies = self.sudo().search([('internal_project_id', '=', False)])
        internal_names = list({'Internal', _('Internal')})
        for company in companies:
            project = self.env['project.project'].sudo().with_context(active_test=False).search([
                ('company_id', '=', company.id),
                ('name', 'in', internal_names),
            ], limit=1)
            if project:
                project.write({'active': True, 'allow_timesheets': True})
                company.internal_project_id = project
            else:
                company._create_internal_project_task()
        return True
