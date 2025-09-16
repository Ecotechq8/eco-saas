# -*- coding: utf-8 -*-
from odoo import api, fields, models, _, tools  # type: ignore
from odoo.osv import expression  # type: ignore
from odoo.exceptions import UserError, ValidationError  # type: ignore


class FacilityProperty(models.Model):
    _name = 'fm.property'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Facility Property'

    name = fields.Char(string='Property', required=True)
    owner_id = fields.Many2one('res.partner', string='Property Owner', domain=[('owner_boolean', '=', True)])
    unit_count = fields.Integer(compute='_compute_unit_count', string="Number of Units")

    def _compute_unit_count(self):
        self.unit_count = self.env['fm.unit'].search_count([('property_id', '=', self.id)])

    def open_related_units(self):
        unit_ids = self.env['fm.unit'].search([('property_id', '=', self.id)])
        action = self.env['ir.actions.act_window']._for_xml_id('facility_management_erp.action_view_fm_unit')
        action['domain'] = [('id', 'in', unit_ids.ids)]
        action['context'] = dict(create=False)
        return action

    def unlink(self):
        for record in self:
            if record.name:
                used = self.env['fm.unit'].search_count([('property_id', '=', record.id)])
                if used > 0:
                    raise ValidationError("Cannot delete this record as the field is being used in another model.")
        return super(FacilityProperty, self).unlink()

class FacilityUnit(models.Model):
    _name = 'fm.unit'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Facility Unit'

    name = fields.Char('Name of Unit', required=True, tracking=True)
    property_id = fields.Many2one('fm.property', string='Property Name', required=True, tracking=True)
    owner_id = fields.Many2one('res.partner', string='Unit Owner', tracking=True, required=True, domain=[('owner_boolean', '=', True)])
    sqft = fields.Float('Squarefeet', tracking=True)

    def create_product(self):
        vals = {
            'name': self.name,
        }

        product_id = self.env['product.product'].create(vals)
        self.update({
            'product_id': product_id.id
        })
    product_id = fields.Many2one('product.product', string='Product', copy=False)

    def unlink(self):
        for record in self:
            if record.name:
                used = self.env['fm.unit.lines'].search_count([('unit_id', '=', record.id)])
                if used > 0:
                    raise ValidationError("Cannot delete this record as the field is being used in another model.")
        return super(FacilityUnit, self).unlink()



