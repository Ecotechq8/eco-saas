# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class SubProperty(models.Model):
    _name = 'sub.property'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'sub.property'

    name = fields.Char('Name')
    code = fields.Char(string='Code', required=True)
    partner_id = fields.Many2one('res.partner', 'Owner', domain="[('is_owner','=',True)]")
    video_url = fields.Char('Video URL')
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company)
    rs_project_id = fields.Many2one('rs.project', string="Project")
    street = fields.Char(string=_('Street'))
    street2 = fields.Char(string=_('Street2'))
    city = fields.Char(string=_('City'))
    country_id = fields.Many2one('res.country')
    zip = fields.Char(string=_('Zip'))
    state_id = fields.Many2one('res.country.state')
    region = fields.Many2one('regions', related='rs_project_id.region', string='Region', store='True')
    state = fields.Selection([('free', 'Available'),
                              ('reserved', 'Booked'),
                              ('on_lease', 'Leased'),
                              ('sold', 'Sold'),
                              ], 'State', default='free')

    ptype = fields.Many2one('rs.project.type', 'Property Type')
    rental_fee = fields.Integer('Rental Fee')
    insurance_fee = fields.Integer('Insurance Fee')
    status = fields.Many2one('rs.project.status', 'Property Status')
    rs_project_area = fields.Integer('Project Unit Area m^2')
    rs_project_area_net = fields.Integer('Net Area m^2')
    land_area = fields.Integer('Gross Area m^2')
    constructed = fields.Date('Construction Date')
    air_condition = fields.Selection([
        ('unknown', 'Unknown'),
        ('central', 'Central'),
        ('partial', 'Partial'),
        ('none', 'None')])
    rooms = fields.Integer('Rooms')
    bathrooms = fields.Integer('Bathrooms')
    telephone = fields.Boolean()
    internet = fields.Boolean()
    pricing = fields.Integer('Selling Price')
    floor = fields.Char('Floor')
    surface = fields.Integer('Surface')
    garage = fields.Integer('Garage Included')
    garden = fields.Integer('Garden m^2')
    balcony = fields.Integer('Balconies m^2')
    solar_electric = fields.Boolean('Solar Electric System')
    heating_source = fields.Selection([
        ('unknown', 'Unknown'),
        ('electricity', 'Electricity'),
        ('wood', 'Wood'),
        ('pellets', 'Pellets'),
        ('oil', 'Oil'),
        ('gas', 'Gas'),
        ('district', 'District Heating')])
    desc = fields.Many2one('rs.project.desc', 'Description')
    electricity_meter = fields.Char('Electricity Meter')
    water_meter = fields.Char('Water Meter')
    north = fields.Char('Northern border by')
    south = fields.Char('Southern border by')
    east = fields.Char('Eastern border by')
    west = fields.Char('Western border by')
    license_code = fields.Char('License Code')
    license_date = fields.Date('License Date')
    date_added = fields.Date('Date Added to Notarization')
    license_notarization = fields.Char('License Notarization')
    note = fields.Text()
    marker_color = fields.Char()
    date_localization = fields.Char(readonly=True)
    furniture_ids = fields.One2many('furniture', 'property_id')
    property_attachment_ids = fields.One2many('property.attachment.line', 'prop_attachment_id')
    reservation_count = fields.Integer(compute='_reservation_count', string='Reservation Count', )
    sub_property_images_ids = fields.One2many('sub.property.image', 'sub_property_id')
    image = fields.Image()

    #This SQL constraint enforces uniqueness on the 'code' field, ensuring that no duplicate values are allowed for this field in the database.
    _sql_constraints = [
        ('unique_code', 'UNIQUE (code)', 'The code field must be unique.'),
    ]

    @api.onchange('rs_project_id')
    def onchange_region(self):
        """This method updates address-related fields, such as 'street,' 'street2,' 'city,' 'country_id,' and 'zip,' based on the selected 'rs_project_id.'"""
        if self.rs_project_id:
            self.street = self.rs_project_id.street
            self.street2 = self.rs_project_id.street2
            self.city = self.rs_project_id.city
            self.country_id = self.rs_project_id.country_id.id
            self.zip = self.rs_project_id.zip

    def make_reservation(self):
        """This function creates a reservation for a rs_project unit, updating various fields, and then opens the reservation record in the Odoo user interface for further interaction."""
        full_address = ""
        if self.street:
            full_address += self.street
        if self.street2:
            if full_address:
                full_address += ", " + self.street2
            else:
                full_address += self.street2
        if self.city:
            if full_address:
                full_address += ", " + self.city
            else:
                full_address += self.city
        if self.zip:
            if full_address:
                full_address += ", " + self.zip
            else:
                full_address += self.zip
        if self.state_id:
            if full_address:
                full_address += ", " + self.state_id
            else:
                full_address += self.state_id
        for unit in self:
            code = unit.code
            rs_project_unit = unit.id
            address = full_address
            floor = unit.floor
            pricing = unit.pricing
            type = unit.ptype.id
            status = unit.status.id
            rs_project = unit.rs_project_id.id
            rs_project_code = unit.rs_project_id.code
            region = unit.region.id
            rs_project_area = unit.rs_project_area
            unit.state = 'reserved'
        reservation = self.env['unit.reservation']
        reservation_id = reservation.create({'region': region,
                                             'rs_project_code': rs_project_code,
                                             'rs_project': rs_project,
                                             'unit_code': code,
                                             'floor': floor,
                                             'pricing': pricing,
                                             'type': type,
                                             'address': address,
                                             'status': status,
                                             'rs_project_area': rs_project_area,
                                             'rs_project_unit': rs_project_unit})
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'unit.reservation',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'res_id': reservation_id.id,
        }

    def view_reservations(self):
        """This function retrieves and displays a list of reservations associated with the selected rs_project units in the Odoo user interface, allowing users to view and manage the reservations."""
        reservation = self.env['unit.reservation']
        reservations_ids = reservation.search([('rs_project_unit', '=', self.ids)])
        reservations = []
        for re in reservations_ids: reservations.append(re.id)
        return {
            'name': _('Reservation'),
            'domain': [('id', 'in', reservations)],
            'view_type': 'form',
            'view_mode': 'list,form',
            'res_model': 'unit.reservation',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'target': 'current',
        }

    def _reservation_count(self):
        """This function calculates and updates the 'reservation_count' field with the count of reservations associated with the rs_project unit."""
        reservation = self.env['unit.reservation']
        for unit in self:
            reservations_ids = reservation.search([('rs_project_unit', '=', unit.id)])
            unit.reservation_count = len(reservations_ids)

    def transfer_furniture_products(self):
        """This function transfers furniture products from one location to another by creating a stock transfer order, validating it, and updating the status of the related furniture reservation lines accordingly."""
        lines_stock = []
        location_id = int(self.env['ir.config_parameter'].sudo().get_param('nthub_realestate.location_id'))
        location_dest_id = int(self.env['ir.config_parameter'].sudo().get_param('nthub_realestate.location_dest_id'))
        if not location_id:
            raise UserError(_('Please set source location from setting!'))
        if not location_dest_id:
            raise UserError(_('Please set destination location from setting!'))


        for rec in self:
            if rec.furniture_ids:
                for line in rec.furniture_ids:
                    if not line.product_id:
                        raise UserError(_("You cannot validate a transfer if no Products are reserved."))
                    if not line.product_qty:
                        raise UserError(_("You cannot validate a transfer if no quantities are reserved."))
                    if line.transfer == False and line.check == True:
                        lines_stock.append((0, 0, {
                            'name': line.product_id.name,
                            'product_id': line.product_id.id,
                            'product_uom': line.product_id.uom_id.id,
                            'location_id': location_id,
                            'location_dest_id': location_dest_id,
                            'product_uom_qty': line.product_qty,
                            'quantity_done': line.product_qty,
                        }))
                        transfer_order = self.env['stock.picking'].create({
                            'picking_type_id': self.env.ref('stock.picking_type_internal').id,
                            'location_id': location_id,
                            'location_dest_id': location_dest_id,
                            'immediate_transfer': True,
                            'move_ids_without_package': lines_stock
                        })
                        transfer_order.button_validate()
                        line.transfer = True
                        line.check = False
            else:
                raise UserError(_("You cannot validate a transfer if no Products are reserved."))

    def action_transfer_reverse(self):
        """This function performs a reverse transfer of reserved furniture products by creating a stock transfer order, validating it, and updating the status of the related furniture reservation lines accordingly."""
        lines_stock = []
        location_id = int(self.env['ir.config_parameter'].sudo().get_param('nthub_realestate.location_id'))
        location_dest_id = int(self.env['ir.config_parameter'].sudo().get_param('nthub_realestate.location_dest_id'))

        if not location_id:
            raise UserError(_('Please set source location from setting!'))
        if not location_dest_id:
            raise UserError(_('Please set destination location from setting!'))

        for rec in self:
            if rec.furniture_ids:
                for line in rec.furniture_ids:
                    if not line.product_id:
                        raise UserError(_("You cannot validate a reverse if no Products are reserved."))
                    if not line.product_qty:
                        raise UserError(_("You cannot validate a reverse if no quantities are reserved."))
                    if line.transfer == True and line.check == True:
                        lines_stock.append((0, 0, {
                            'name': line.product_id.name,
                            'product_id': line.product_id.id,
                            'product_uom': line.product_id.uom_id.id,
                            'location_id': location_dest_id,
                            'location_dest_id': location_id,
                            'product_uom_qty': line.product_qty,
                            'quantity_done': line.product_qty,
                        }))
                        transfer_order = self.env['stock.picking'].create({
                            'picking_type_id': self.env.ref('stock.picking_type_internal').id,
                            'location_id': location_dest_id,
                            'location_dest_id': location_id,
                            'immediate_transfer': True,
                            'move_ids_without_package': lines_stock
                        })
                        transfer_order.button_validate()
                        line.transfer = False
                        line.check = False
            else:
                raise UserError(_("You cannot validate a transfer if no Products are reserved."))


class Furniture(models.Model):
    _name = 'furniture'
    _description = "furniture"

    product_id = fields.Many2one("product.product", string=_("Product"), domain="[('furniture', '=', True)]")
    description = fields.Char(string=_('Description'), compute="_description_get", default=" ")
    list_price = fields.Float(related="product_id.list_price")
    property_id = fields.Many2one("sub.property")
    product_qty = fields.Integer(string=_("Quantity"), default=1)
    transfer = fields.Boolean('Transfer', default=False)
    check = fields.Boolean()

    @api.depends("product_id.name", "product_id.default_code")
    def _description_get(self):
        """This function to make description of furniture"""
        for record in self:
            if not record.product_id.default_code:
                descriptions = str(record.product_id.name)
                record.description = descriptions
            else:
                descriptions = str([record.product_id.default_code]) + str(record.product_id.name)
                record.description = descriptions


class PropertyAttachmentLine(models.Model):
    _name = 'property.attachment.line'
    _description = "property.attachment.line"

    name = fields.Char(string=_("Name"))
    file = fields.Binary(string=_("File"))
    prop_attachment_id = fields.Many2one("sub.property")


class SubPropertyImage(models.Model):
    _name = 'sub.property.image'
    _description = "sub.property.image"

    name = fields.Char(string=_("Image Name"), required=True)
    video_url = fields.Char(string=_("Video URL"))
    image = fields.Image()
    sub_property_id = fields.Many2one("sub.property")
