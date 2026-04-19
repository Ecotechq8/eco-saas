from odoo import api,fields,models, _
from odoo.exceptions import UserError
# from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP, float_compare


class Bank(models.Model):
    _name = 'res.bank'
    _inherit = 'res.bank'
    _description = "Bank"

    branch = fields.Char(string='Branch')
    bank_name = fields.Many2one('res.bank', string='Bank Name')
    swift_code = fields.Char(string='Swift Code')
    ad_code = fields.Char(string='AD Code')
    prefix = fields.Char(string='Prefix')
    suffix = fields.Char(string='Suffix')
    bic = fields.Char(string='BIC')
    account_payable = fields.Many2one('account.account', string='Account Payable')
    account_receivable = fields.Many2one('account.account', string='Account Receivable')
    identification_id = fields.Many2one('res.bank.identification', string='Identification')


class BankAccountType(models.Model):
    _name = "bank.account.type"
    _description = "Bank Account Type"

    name = fields.Char(string='Account Type', default="Current Account")
    code = fields.Char(string='Account Code', default='CA')
    description = fields.Text(string="Description")


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    check_employee = fields.Boolean(string='Check Employee', default=False)
    state_id = fields.Many2one('res.country.state', string='State', change_default=True)
    inter_id = fields.Many2one('internation.zone', string='International Zone')
    domestic_id = fields.Many2one('domestic.zone', string='Domestic Zone')
    removable = fields.Boolean(string='Removable', default=True)

    def action_create_partner(self):
        """ Create Partner.
        @return: True
        """
        ir_model_data = self.env['ir.model.data']
        form_res = ir_model_data._xmlid_to_res_id('verts_partner_sid.verts_partner_inherit21')
        form_id = form_res and form_res[1] or False
        partner_obj = self.env['res.partner']
        for pick in self:
            part_id = partner_obj.create({
                                        'name': pick.name,
                                        'check_employee': True,
                                        'customer_rank': 1,
                                        'supplier_rank': 1,
                                        'type1': 'user',
                                        'status': 'approved',
                                        })
            pick.write({'check_employee': True})
            return {
                    'view_mode': 'form',
                    'res_model': 'res.partner',
                    'views': [(form_id, 'form')],
                    'type': 'ir.actions.act_window',
                    'name': _('Employee'),
                    'context': {'type1': 'user'},
                    'res_id': part_id,
                 }

    @api.model
    def create(self, data):
        employee_record = super(HrEmployee, self).create(data)
        if 'inter_id' in data and data['inter_id']:
            self.env['hr.employee.list'].create({'employee_id': employee_record.id, 'inter_id': data['inter_id']})
        if 'domestic_id' in data and data['domestic_id']:
            self.env['hr.employee.list'].create({'employee_id': employee_record.id, 'domestic_id':data['domestic_id']})
        try:
            mail_group_id = self.env['ir.model.data']._xmlid_to_res_id('mail.group_all_employees')
            self.env['mail.group'].browse(mail_group_id).message_post(body='Welcome to %s! Please help them take the first steps with OpenERP!' % (employee_record.name))
        except Exception:
            pass  # group deleted: do not push a message
        return employee_record

    @api.onchange('country_id')
    def onchange_country_id(self):
        # Odoo 18: Direct assignment instead of {'value': ...}
        if not self.country_id:
            self.int_region = False
            return
        region_ids = self.env['international.country'].search([('country_name', '=', self.country_id.id)])
        if region_ids:
            self.int_region = region_ids[0]
        
    @api.onchange('state_id')
    def onchange_state_id(self):
        # Odoo 18: Direct assignment instead of {'value': ...}
        if not self.state_id:
            self.domt_region = False
            return
        region_ids = self.env['domestic.state'].search([('state_name', '=', self.state_id.id)])
        if region_ids:
            self.domt_region = region_ids[0]


class InternationZone(models.Model):
    _name = "internation.zone"
    _description = "Employee Internation Zone"

    name = fields.Char(string='International Zone', required=True)
    code = fields.Char(string='Code', required=True)
    note = fields.Text(string='Description')
    short_leave_hours = fields.Float(string='Short Leave Hours')
    working_hours = fields.Float(string='Working Hours')
    international_country_ids = fields.One2many('international.country', 'country_id', string='Countries')
    employee_list_ids = fields.One2many('hr.employee.list', 'inter_id', string='Employee',)

    @api.model
    def create(self, vals):
        inter_region_id = super(InternationZone, self).create(vals)
        for each in inter_region_id.employee_list_ids:
            each.write({'inter_id': inter_region_id.id})
        return inter_region_id

    def write(self, vals):
        if 'employee_list_ids' in vals:
            for each in self.employee_list_ids:
                each.write({'inter_id': False})
        inter_id = super(InternationZone, self).write(vals)
        for each in self.employee_list_ids:
            each.write({'inter_id': self.id})
        return inter_id


class DomesticZone(models.Model):
    _name = "domestic.zone"
    _description = "Employee Domestic zone"

    name = fields.Char(string='Domestic Zone', required=True)
    country_id = fields.Many2one('res.country', string='Country')
    code = fields.Char(string='Code', required=True)
    note = fields.Text(string='Description')
    zone_type = fields.Selection([('state', 'State'), ('city', ' City'), ], string='Zone Type')
    domestic_state_line = fields.One2many('domestic.state', 'state_id', string='State')
    domestic_city_line = fields.One2many('domestic.city', 'city_id', string='City')
    employee_list_ids = fields.One2many('hr.employee.list', 'domestic_id', string='Employees')
    working_hours = fields.Float(string='Working Hours')
    short_leave_hours = fields.Float(string='Short Leave Hours')
    domestic_region_bool = fields.Boolean(string='Dont Delete')

    @api.model
    def create(self, vals):
        domestic_region_id = super(DomesticZone, self).create(vals)
        for each in domestic_region_id.employee_list_ids:
            each.employee_id.write({'domestic_id': domestic_region_id.id})
        return domestic_region_id

    def write(self, vals):
        if 'employee_list_ids' in vals:
            for each in self.employee_list_ids:
                each.employee_id.write({'domestic_id': False})
        inter_id = super(DomesticZone, self).write(vals)
        for each in self.employee_list_ids:
            each.employee_id.write({'domestic_id': self.id})
        return inter_id


class InternationalCountry(models.Model):
    _name = "international.country"
    _description = "International Country"

    country_id = fields.Many2one('internation.zone', string='Country')
    country_name = fields.Many2one('res.country', string='Country Name')
    country_code = fields.Char(related='country_name.code', string="Country Code", readonly="1")

    @api.onchange('country_name')
    def onchange_country_id(self):
        # Odoo 18: Direct assignment instead of {'value': ...}
        if not self.country_name:
            self.country_code = False
            return
        self.country_code = self.country_name.code
        

class DomesticState(models.Model):
    _name = "domestic.state"
    _description = "Domestic State"

    state_id = fields.Many2one('domestic.zone', string='State')
    state_name = fields.Many2one('res.country.state', string='State Name')
    state_code = fields.Char(related='state_name.code', string="State Code", readonly="1")
    domestic_region_bool_line = fields.Boolean(string='Dont Delete')
    
    # def unlink(self):
    #     for rec in self:
    #         if rec.domestic_region_bool_line:
    #             raise UserError(_('You can not delete this record'))
    #     return super(domestic_state, rec).unlink()
      
    @api.onchange('state_name')
    def onchange_state_id(self):
        # Odoo 18: Direct assignment instead of {'value': ...}
        if not self.state_name:
            self.state_code = False
            return
        self.state_code = self.state_name.code


class DomesticCity(models.Model):
    _name = "domestic.city"
    _description = "Domestic City"

    city_id = fields.Many2one('domestic.zone', string='City')
    city_name = fields.Many2one('cities.basic.masters', string='City Name')


class HrEmployeeList(models.Model):
    _name = "hr.employee.list"
    _description = "Employee List"
    
    employee_id = fields.Many2one('hr.employee', string='Employee')
    domestic_id = fields.Many2one('domestic.zone', string='Domestic Region')
    inter_id = fields.Many2one('internation.zone', string='International Region')
    

class BasicMasters(models.Model):
    _name = "basic.masters"
    _description = "Basic Masters"
    _rec_name = "divisions_bu"
    
    divisions_bu = fields.Char(string= 'Divisions/BU', required=True)


class ResStateZone(models.Model):
    _name = "res.state.zone"
    _description = "Res State Zone"

    name = fields.Char(string="Name", required=True)
    country_id = fields.Many2one('res.country', string="Country", required=True)
    state_id = fields.Many2one('res.country.state', string="State", required=True)


class ResZoneDistrict(models.Model):
    _name = 'res.zone.district'
    _description = "Res Zone District"

    name = fields.Char(string="Name", required=True)
    country_id = fields.Many2one('res.country', string="Country", required=True)
    state_id = fields.Many2one('res.country.state', string="State", required=True)
    zone_id = fields.Many2one('res.state.zone', string="Zone/Circle")


class CitiesBasicMasters(models.Model):
    _name = "cities.basic.masters"
    _description = "Cities Basic Masters"
    
    name = fields.Char(string='City Name', required=True)
    state_id = fields.Many2one('res.country.state', string='State')
    country_id = fields.Many2one('res.country', string='Country')
    district_id = fields.Many2one('res.zone.district', string="District")
    cities_bool = fields.Boolean(string='Dont Delete')

    @api.onchange('district_id')
    def onchange_district_id(self):
        if not self.district_id:
            return
        self.country_id = self.district_id.country_id.id
        self.state_id = self.district_id.state_id.id

    @api.onchange('state_id')
    def onchange_state_id(self):
        if not self.state_id:
            return
        self.country_id = self.state_id.country_id.id

    def unlink(self):
        for rec in self:
            if rec.cities_bool:
                raise UserError(_('You can not delete this record'))
        return super(CitiesBasicMasters, self).unlink()

    def write(self, vals):
        if vals.get('name'):
            vals['name']=(vals['name']).title()
        result = super(CitiesBasicMasters, self).write(vals)
        return result

    @api.model
    def create(self, vals):
        if vals.get('name'):
            vals['name']=(vals['name']).title()
        result = super(CitiesBasicMasters, self).create(vals)
        return result


class AreasBasicMasters(models.Model):
    _name = "areas.basic.masters"
    _description = "Areas Basic Masters"

    name = fields.Char(string='Area Name', required=True)
    city_id = fields.Many2one('cities.basic.masters', string='City')


class ModeTransport(models.Model):
    _name = "mode.transport"
    _description = "Mode Transport"
    _rec_name = "mode_of_transport"
    
    mode_of_transport = fields.Char(string='Mode of Transport', required=True)
    mode_transport_bool = fields.Boolean(string='Dont Delete')
    
    def unlink(self):
        for rec in self:
            if rec.mode_transport_bool:
                raise UserError(_('You can not delete this record'))
        return super(ModeTransport, self).unlink()
    

class Ports(models.Model):
    _name = "ports"
    _description = "Ports"
    
    name = fields.Char(string='Port Name')
    port_type_id = fields.Many2one('mode.transport', string="Port Type")
    ports_bool = fields.Boolean(string='Dont Delete')
    street = fields.Char(string='Address ')
    street2 = fields.Char(string='Street2')
    zip = fields.Char(string='Zip', change_default=True)
    city = fields.Many2one('cities.basic.masters', string='City')
    state_id = fields.Many2one("res.country.state", string='State')
    country_id = fields.Many2one('res.country', string='Country')
    port_load_bool = fields.Boolean(string='Port of Loading')
    port_discharge_bool = fields.Boolean(string='Port of Discharge')
    expected_trans_days = fields.Integer(string='Expected Transit Days')
    incoming_trans_days = fields.Integer(string='Incoming Transit Days', help="Expected Number of days to reach shipment from your vendor location to your location.")
    delivery_trans_days = fields.Integer(string='Delivery Transit Days', help="Expected Number of days to reach shipment from your location to your client’s location.")

    def unlink(self):
        for rec in self:
            if rec.ports_bool:
                raise UserError(_('You can not delete this record'))
        return super(Ports, self).unlink()


class ContainerType(models.Model):
    _name = "container.type"
    _description = "Container Type"

    name = fields.Char(string='Container Type')
    capacity = fields.Float(string='Container Capacity')
    description = fields.Char(string='Description')
    sequence_size = fields.Integer(string='Sequence Size', default=10)

    # def name_get(self):
    #     result = []
    #     for record in self:
    #         container_type = str(record.name) + '[' + str(record.capacity) + ']'
    #         result.append((record.id, container_type))
    #     return result

    # @api.model
    # def name_search(self, name, args=None, operator='ilike', limit=None):
    #     recs = self.search(['|', ('name', operator, name), ('capacity', operator, name)] + args, limit=limit)
    #     return recs.name_get()


class PointOfStuffing(models.Model):
    _name = "point.of.stuffing"
    _description = "Point Of Stuffing"

    name = fields.Char(string='Name')
    country_id = fields.Many2one('res.country', string='Country')
    state_id = fields.Many2one('res.country.state', string='State')
    city_id = fields.Many2one('cities.basic.masters', string='City')


class ResIndustry(models.Model):
    _name = 'res.industry'
    _description = "Industry"

    name = fields.Char(string='Industry')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)
    type = fields.Selection([('internal', 'Internal'), ('external', 'External')], string='Type', default='internal')
    is_default = fields.Boolean(string='Is Default', default=False)



