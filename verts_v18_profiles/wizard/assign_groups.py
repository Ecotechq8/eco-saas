from odoo import api, fields, models


class GroupAssign(models.TransientModel):
    _name = 'group.assign'
    _description = 'Group Assign'

    users_id = fields.Many2many('res.users', string='Profiles')

    def group_assign_action(self):
        group_assign = self.env['res.groups']
        group_ids = group_assign.browse(self._context.get('active_ids'))
        for group in group_ids:
            group.users = self.users_id.ids
