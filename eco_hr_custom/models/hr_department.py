from odoo import fields, models, api, _


class HrDepartment(models.Model):
    _inherit = 'hr.department'

    e_resource_calendar_id = fields.Many2one('resource.calendar', check_company=True, string='Working Hours',
                                             domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    e_att_policy_id = fields.Many2one(comodel_name='hr.attendance.policy',
                                      string="Attendance Policy ")
