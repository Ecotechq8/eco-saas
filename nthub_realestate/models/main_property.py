# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class MainProperty(models.Model):
    _name = 'rs.project'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'main.property'

    name = fields.Char('Name')
    code = fields.Char(string='Code', required=True)
    region = fields.Many2one('regions', 'Region')
    partner_id = fields.Many2one('res.partner', 'Owner', domain="[('is_owner','=',True)]")
    purchase_date = fields.Date()
    launching_date = fields.Date()
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company)
    property_type = fields.Many2one('rs.project.type')
    property_status = fields.Many2one('rs.project.status')
    rs_project_area = fields.Integer('Property Area m^2')
    land_area = fields.Integer('Land Area m^2')
    constructed = fields.Date('Construction Date')
    lift = fields.Integer('Passenger Elevators')
    lift_f = fields.Integer('Freight Elevators')
    pricing = fields.Integer('Price')
    no_of_floors = fields.Integer('Floors')
    props_per_floor = fields.Integer('Units Per Floor')
    surface = fields.Integer('Surface')
    garage = fields.Integer('Garage Included')
    garden = fields.Integer('Garden m^2')
    north = fields.Char('Northern border by')
    south = fields.Char('Southern border by')
    east = fields.Char('Eastern border by')
    west = fields.Char('Western border by')
    license_code = fields.Char('License Code')
    license_date = fields.Date('License Date')
    date_added = fields.Date('Date Added to Notarization')
    license_notarization = fields.Char('License Notarization')
    note = fields.Text()
    subproperties_ids = fields.One2many('sub.property', 'rs_project_id')
    rs_project_attachment_ids = fields.One2many('rs.project.attachment.line','rs_project_attachment_id')
    rs_project_image_ids = fields.One2many('rs.project.images', 'rs_project_id')
    rs_project_floor_plans = fields.One2many('rs.project.floor.plans', 'rs_project_id')
    sub_properties_created = fields.Boolean('Sub Properties Created', default=False)
    street = fields.Char(string=_('Street'))
    street2 = fields.Char(string=_('Street2'))
    city = fields.Char(string=_('City'))
    country_id = fields.Many2one('res.country')
    zip = fields.Char(string=_('Zip'))
    state_id = fields.Many2one('res.country.state')
    image = fields.Image(_("Image"))
    quantity = fields.Integer(string="Quantity", compute='get_propreties_number')
    total_projects_sold = fields.Integer(compute="total_projects_sold_state")
    count_of_proprety = fields.Integer(compute="count_of_proprety_project")

    _sql_constraints = [
        ('unique_code', 'UNIQUE (code)', 'The code field must be unique.'),
    ]
    
    def get_propreties_number(self):
        self.quantity = len(self.subproperties_ids)
        wn_obj = self.env['sub.property']
        own_ids = wn_obj.search_count([('rs_project_id', '=', self.id)])

    @api.depends("subproperties_ids", "subproperties_ids.pricing")
    def total_projects_sold_state(self):
        for rec in self:
            rec.total_projects_sold = sum(
                rec.subproperties_ids.filtered(lambda x: x.state == "sold").mapped("pricing"))

    @api.depends("subproperties_ids")
    def count_of_proprety_project(self):
        for rec in self:
            rec.count_of_proprety = len(rec.subproperties_ids.filtered(lambda x: x.state == "sold"))
        
    def get_number_propreties(self):
        return {
            'name': _('property'),
            'domain': [('rs_project_id', '=', self.id)],
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'sub.property',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'target': 'current',
        }

    @api.onchange('region')
    def onchange_region(self):
        """
        This method is When the 'region' field is changed, this method ensures that the 'street', 'street2', 'city',
        'country_id', and 'zip' fields are updated accordingly.
        """
        if self.region:
            self.street = self.region.street
            self.street2 = self.region.street2
            self.city = self.region.city
            self.country_id = self.region.country_id.id
            self.zip = self.region.zip

    def generate_subproperties(self):
        """
            This method generates subproperties based on the specified number of floors and units per floor.
             It clears existing subproperties before creating new ones.
        """
        if self.no_of_floors and self.props_per_floor:
            # It first checks if 'no_of_floors' and 'props_per_floor' are both filled.
            for do in self.subproperties_ids:
                do.unlink()
            for floor in range(1, self.no_of_floors + 1):
                for unit in range(1, self.props_per_floor + 1):
                    subproperty_name = f'{self.code}-{floor}-{unit}'
                    subproperty = {
                        'name': subproperty_name,
                        'code': subproperty_name,
                        'rs_project_id': self.id,
                        'ptype': self.property_type.id,
                        'status': self.property_status.id,
                        'region': self.region.id,
                        'street': self.street,
                        'street2': self.street2,
                        'country_id': self.country_id,
                        'zip': self.zip,
                        'state_id': self.state_id.id,
                        'floor': str(floor),
                    }
                    self.env['sub.property'].create(subproperty)
            self.sub_properties_created = True
        else:
            # ValidationError: If any of the required fields (Name, Number of floors, Units per floor) is not filled.
            raise ValidationError("please fill all required fields. (Name , Number of floors, Units per floor)")


class RsProjectAttachmentLine(models.Model):
    _name = 'rs.project.attachment.line'
    _description = "rs.project.attachment.line"

    name = fields.Char(string=_("Name"))
    file = fields.Binary(string=_("File"))
    rs_project_attachment_id = fields.Many2one("rs.project", string="Project")


class RsProjectImage(models.Model):
    _name = 'rs.project.images'
    _description = "rs.project.images"

    name = fields.Char(string=_("Image Name"), required=True)
    video_url = fields.Char(string=_("Video URL"))
    image = fields.Image()
    rs_project_id = fields.Many2one("rs.project",string="Project")


class RsProjectFloorPlans(models.Model):
    _name = 'rs.project.floor.plans'
    _description = "rs.project.floor.plans"

    name = fields.Char(string=_("Image Name"), required=True)
    video_url = fields.Char(string=_("Video URL"))
    image = fields.Image()
    rs_project_id = fields.Many2one("rs.project", string="Project")

