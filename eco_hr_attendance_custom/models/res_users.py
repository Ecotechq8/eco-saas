# -*- coding: utf-8 -*-

from odoo import fields, models
from odoo.exceptions import UserError
from odoo.tools.translate import _


class ResUsers(models.Model):
    _inherit = 'res.users'

    show_attendance_confirm_actions = fields.Boolean(
        string='Show Attendance Confirm Actions',
        compute='_compute_show_attendance_confirm_actions',
        inverse='_inverse_show_attendance_confirm_actions',
        search='_search_show_attendance_confirm_actions',
        compute_sudo=True,
    )

    def _attendance_confirm_actions_group(self):
        return self.env.ref(
            'eco_hr_attendance_custom.group_attendance_confirmation_actions',
            raise_if_not_found=False,
        )

    def _compute_show_attendance_confirm_actions(self):
        group = self._attendance_confirm_actions_group()
        for user in self:
            user.show_attendance_confirm_actions = bool(group and group in user.groups_id)

    def _inverse_show_attendance_confirm_actions(self):
        group = self._attendance_confirm_actions_group()
        if not group:
            raise UserError(_('The attendance confirmation security group is missing.'))

        for user in self:
            if user.show_attendance_confirm_actions:
                user.sudo().write({'groups_id': [(4, group.id)]})
            else:
                user.sudo().write({'groups_id': [(3, group.id)]})

    def _search_show_attendance_confirm_actions(self, operator, value):
        if operator not in ('=', '!='):
            raise UserError(_('Unsupported search operator for attendance confirmation actions.'))

        group = self._attendance_confirm_actions_group()
        user_ids = group.users.ids if group else []
        positive = (operator == '=' and value) or (operator == '!=' and not value)
        return [('id', 'in' if positive else 'not in', user_ids)]
