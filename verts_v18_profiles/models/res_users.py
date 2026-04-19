# -*- encoding: utf-8 -*-
##############################################################################

from odoo import api, fields, models, SUPERUSER_ID, exceptions, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import time
import re


class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.depends('groups_id')
    def _compute_share(self):
        for user in self:
            user.share = user.is_user_profile or not user.has_group('base.group_user')

    @api.model
    def _get_default_field_ids(self):
        return self.env['ir.model.fields'].search([
            ('model', 'in', ('res.users', 'res.partner')),
            ('name', 'in', ('action_id', 'menu_id', 'groups_id')),
        ]).ids

    is_user_profile = fields.Boolean('Is User Profile')
    user_profile_id = fields.Many2one('res.users', 'User Profile',
                                      domain=[('id', '!=', SUPERUSER_ID), ('is_user_profile', '=', True)],
                                      context={'active_test': False})
    user_ids = fields.One2many('res.users', 'user_profile_id', 'Users', domain=[('is_user_profile', '=', False)])
    field_ids = fields.Many2many('ir.model.fields', 'res_users_fields_rel', 'user_id', 'field_id', 'Fields to update',
                                 domain=[
                                     ('model', 'in', ('res.users', 'res.partner')),
                                     ('ttype', 'not in', ('one2many',)),
                                     ('name', 'not in', ('is_user_profile', 'user_profile_id',
                                                         'user_ids', 'field_ids', 'view'))],
                                 default=_get_default_field_ids)
    is_update_users = fields.Boolean(string="Update users after creation", default=True,
                                     help="If non checked, users associated to this profile will not be updated after creation")

    _sql_constraints = [
        ('profile_without_profile_id',
         'CHECK( (is_user_profile = TRUE AND user_profile_id IS NULL) OR is_user_profile = FALSE )',
         'Profile users cannot be linked to a profile!'),
    ]
    history_lines = fields.One2many('res.user.history', 'history_lines_id', string='History')

    @api.constrains('user_profile_id')
    def _check_user_profile_id(self):
        admin = self.env.ref('base.user_admin')
        if self.user_profile_id.id == admin.id:
            raise ValidationError(_("You can't use %s as user profile !") % admin.name)

    def _update_from_profile(self, fields=None):
        if not self:
            return
        if len(self.mapped('user_profile_id')) != 1:
            raise UserError(_("_update_from_profile accepts only users linked to a same profile"))
        user_profile = self[0].user_profile_id
        if not fields:
            fields = user_profile.field_ids.mapped('name')
        else:
            fields = set(fields) & set(user_profile.field_ids.mapped('name'))
        if user_profile:
            vals = {}
            for field in fields:
                value = user_profile[field]
                field_type = self._fields[field].type
                if field_type == 'many2one':
                    vals[field] = value.id
                elif field_type == 'many2many':
                    vals[field] = [(6, 0, value.ids)]
                elif field_type == 'one2many':
                    raise UserError(_("_update_from_profile doesn't manage fields.One2many"))
                else:
                    vals[field] = value
            if vals:
                self.write(vals)

    def _update_users_linked_to_profile(self, fields=None):
        for user_profile in self.filtered(lambda user: user.is_user_profile and user.is_update_users):
            user_profile.with_context(active_test=False).mapped('user_ids')._update_from_profile(fields)

    @api.model_create_multi
    def create(self, vals_list):
        records = super(ResUsers, self).create(vals_list)
        for record in records:
            if record.user_profile_id:
                record._update_from_profile()
            if record.is_user_profile:
                record.active = False
                query = 'UPDATE res_partner set active=False WHERE id=%s'
                self._cr.execute(query, (record.partner_id.id,))
        return records

    @api.onchange("name")
    def onchange_name(self):
        if not self.login and (self._context.get('default_is_user_profile', False) or self._context.get(
                'is_user_profile', False)):
            self.login = self.name

    def write(self, vals):
        history_tracking_pool = self.env['res.user.history']
        group_model = self.env['res.groups']

        for record in self:
            # Check for fields that start with "in_group_" indicating group changes
            for key, value in vals.items():
                if key.startswith('in_group_'):
                    # Extract the group ID from the key
                    group_id_match = re.match(r'in_group_(\d+)', key)
                    if group_id_match:
                        group_id = int(group_id_match.group(1))
                        group = group_model.browse(group_id)

                        # Determine if the group is being added or removed based on the boolean value
                        if value:  # Group is being added
                            history_tracking_pool.create({
                                'history_lines_id': record.id,
                                'text': f'Access Right Added: {group.name}',
                                'old_value': '',
                                'new_value': group.name,
                                'updated_date': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                            })
                        else:  # Group is being removed
                            history_tracking_pool.create({
                                'history_lines_id': record.id,
                                'text': f'Access Right Removed: {group.name}',
                                'old_value': group.name,
                                'new_value': 'Remove',
                                'updated_date': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                            })
        # Proceed with the original write operation
        if vals.get('user_profile_id'):
            users_to_update = self.filtered(lambda user: user.user_profile_id.id != vals['user_profile_id'])
        vals = self._remove_reified_groups(vals)
        res = super(ResUsers, self).write(vals)
        if vals.get('user_profile_id'):
            users_to_update._update_from_profile()
        else:
            self._update_users_linked_to_profile(list(vals.keys()))

        return res

    def copy_data(self, default=None):
        self.ensure_one()
        default = default.copy() if default else {}
        default['user_ids'] = []
        if self.is_user_profile:
            default['is_user_profile'] = False
            default['user_profile_id'] = self.id
        return super(ResUsers, self).copy_data(default)

    def copy(self, default=None):
        self.ensure_one()
        res = super(ResUsers, self).copy(default)
        if self._context and 'default_is_user_profile' in self._context:
            res.user_profile_id = False
            res.is_user_profile = True
        return res


class ResUserHistory(models.Model):
    _name = "res.user.history"
    _description = "User History"
    _order = 'updated_date desc, id desc'

    history_lines_id = fields.Many2one('res.users', string='Partner')
    updated_by = fields.Many2one('res.users', string='Updated By', default=lambda self: self.env.user)
    text = fields.Text(string='Label')
    old_value = fields.Char(string='Old Value')
    new_value = fields.Char(string='New Value')
    updated_date = fields.Datetime(string='Date', default=fields.Datetime.now())
