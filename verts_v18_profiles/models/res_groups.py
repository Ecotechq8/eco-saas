# -*- encoding: utf-8 -*-

from odoo import api, fields, models


class IrModel(models.Model):
    _inherit = 'ir.model'

    def _get_first_level_relations(self):
        Fields = self.env['ir.model.fields']
        field_recs = Fields.search([
            ('ttype', 'in', ('many2one', 'one2many', 'many2many')),
            ('model_id', 'in', self.ids),
        ])
        return self.search([('model', 'in', field_recs.mapped('relation'))])

    def _get_relations(self, level=1):
        """
        Return models linked to models given in params
        If you don't want limit the relations level, indicate level = -1
        """
        relations = self
        while self and level:
            self = self._get_first_level_relations() - relations
            relations |= self
            level -= 1
        return relations


class ResGroups(models.Model):
    _inherit = 'res.groups'

    active = fields.Boolean(default=True)

    def _update_users(self, vals):
        if vals.get('users'):
            Users = self.env['res.users']
            user_profiles = Users.browse()
            for item in vals['users']:
                user_ids = []
                if item[0] == 6:
                    user_ids = item[2]
                elif item[0] == 4:
                    user_ids = [item[1]]
                users = Users.browse(user_ids)
                user_profiles |= users.filtered(lambda user: user.is_user_profile)
                user_profiles |= users.mapped('user_profile_id')
            if user_profiles:
                user_profiles._update_users_linked_to_profile()

    def write(self, vals):
        group_ids_to_unlink = []
        group_ids_to_link = []
        res = {}
        if vals.get('implied_ids'):
            for group in self:
                vals2 = dict(vals)
                for item in vals2['implied_ids']:
                    if item[0] == 6:
                        group_ids_to_unlink.extend(list(set(group.implied_ids.ids) - set(item[2])))
                        group_ids_to_link.extend(list(set(item[2]) - set(group.implied_ids.ids)))
                    elif item[0] == 5:
                        group_ids_to_unlink.extend(list(set(group.implied_ids.ids)))
                    elif item[0] == 4:
                        group_ids_to_link.append(item[1])
                    elif item[0] == 3:
                        group_ids_to_unlink.append(item[1])
                res = super(ResGroups, group).write(vals2)
                group._update_users(vals2)
                # Update group for all users depending of this group, in order to add new implied groups to their groups
                groups_id = [(4, subgroup_id) for subgroup_id in group_ids_to_link] + \
                    [(3, subgroup_id) for subgroup_id in group_ids_to_unlink]
                group.with_context(active_test=False).users.write({'groups_id': groups_id})
        else:
            res = super(ResGroups, self).write(vals)
            self._update_users(vals)
        return res

    def button_complete_access_controls(self):
        """Create access rules for the first level relation models of access rule models not only in readonly"""
        def filter_rule(rule):
            return rule.perm_write or rule.perm_create or rule.perm_unlink
        Access = self.env['ir.model.access']
        for group in self:
            models = group.model_access.filtered(filter_rule).mapped('model_id')
            for model in models._get_relations(self._context.get('relations_level', 1)):
                Access.create({
                    'name': '%s %s' % (model.model, group.name),
                    'model_id': model.id,
                    'group_id': group.id,
                    'perm_read': True,
                    'perm_write': False,
                    'perm_create': False,
                    'perm_unlink': False,
                })
        return True

    @api.model
    def update_user_groups_view(self):
        user_context = dict(self._context)
        if 'active_test' in user_context:
            del user_context['active_test']
        new_env = self.env(context=user_context)
        return super(ResGroups, self.with_env(env=new_env)).update_user_groups_view()
