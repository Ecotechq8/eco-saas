from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class Employee(models.Model):
    _inherit = 'hr.employee'

    arabic_name = fields.Char()
    resource_calendar_id = fields.Many2one(tracking=True, related='department_id.e_resource_calendar_id', readonly=False)


    @api.constrains('pin')
    def _check_unique_pin(self):
        for employee in self:
            if employee.pin:
                existing = self.search([
                    ('pin', '=', employee.pin),
                    ('id', '!=', employee.id)
                ], limit=1)
                if existing:
                    raise ValidationError('This PIN is already used by another employee.')

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        args = list(args or [])
        if not name:
            # When no name is provided, call the parent implementation
            return super().name_search(name=name, args=args, operator=operator,
                                       limit=limit)
        # Add search criteria for name, email, and phone
        domain = ['|',
                  ('name', operator, name),
                  ('pin', operator, name)]
        # Combine with existing args
        if args:
            domain = ['&'] + args + domain
        # Use search_fetch to get both IDs and display_name efficiently
        employees = self.search_fetch(domain, ['name'], limit=limit)
        # Return in the expected format: [(id, display_name), ...]
        return [(employee.id, employee.name) for employee in employees]
