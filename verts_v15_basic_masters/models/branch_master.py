from datetime import datetime, date
from odoo import tools, api, fields, models, _
import odoo


class BranchMaster(models.Model):
    _name = "branch.master"
    _description = "Branch Master"
    
    name = fields.Char(string='Branch', required=True)
    description = fields.Text(string='Description')
    company_id = fields.Many2one('res.company', string="Company")
    street = fields.Char(string='Street')
    street2 = fields.Char(string='Street2')
    zip = fields.Char(string='Zip')
    city = fields.Char(string='City')
    state_id = fields.Many2one('res.country.state', string="State")
    country_id = fields.Many2one('res.country', string="Country")
    email = fields.Char(string='Email')
    website = fields.Char(string='Website')
    phone = fields.Char(string='Phone')
    pan_no = fields.Char(string='PAN No.')
    cin_no = fields.Char(string='CIN No.')
    gstin_no = fields.Char(string='GSTIN')
    branch_code = fields.Char(string='Branch Code')
    branch_format = fields.Char(string='Branch Format')
    logo_branch = fields.Binary(string="Branch Logo", attachment=True, default=lambda self: self._get_default_image(False, True))
    
    @api.model
    def _get_default_image(self, is_company, colorize=False):
        img_path = odoo.modules.get_module_resource(
            'base', 'static/img', 'avatar.png')
        with open(img_path, 'rb') as f:
            image = f.read()
        # colorize user avatars
        # if not is_company:
        #     image = tools.image_colorize(image)

    @api.onchange('state_id')
    def _onchange_state_id(self):
        if self.state_id and self.state_id.country_id:
            self.country_id = self.state_id.country_id.id
        
    @api.onchange('company_id')
    def _onchange_company_id(self):
        ir_model_fields_obj = self.env['ir.model.fields']
        ir_model_pan_no_fields_id = ir_model_fields_obj.search([('name', '=', 'pan_no'),('model_id.model', '=', 'res.company')])
        ir_model_cin_no_fields_id = ir_model_fields_obj.search([('name', '=', 'cin_no'),('model_id.model', '=', 'res.company')])
        ir_model_gstin_no_fields_id = ir_model_fields_obj.search([('name', '=', 'gstin_no'),('model_id.model', '=', 'res.company')])
        self.street = self.company_id.street
        self.street2 = self.company_id.street2
        self.zip = self.company_id.zip
        self.city = self.company_id.city
        self.state_id = self.company_id.state_id.id
        self.country_id = self.company_id.country_id.id
        self.email = self.company_id.email
        self.website = self.company_id.website
        self.phone = self.company_id.phone
        if ir_model_pan_no_fields_id:
            self.pan_no = self.company_id.pan_no
        if ir_model_cin_no_fields_id:
            self.cin_no = self.company_id.cin_no
        if ir_model_gstin_no_fields_id:
            self.gstin_no = self.company_id.gstin_no

