from odoo import fields, models, api


class BrandCategory(models.Model):
    _name = "brand.category"
    _description = "Brand Category"
    
    name = fields.Char(string='Brand Category Name', required=True)
    brand_category_code = fields.Char(string='Brand Category Code', required=True)
    

class Brand(models.Model):
    _name = "brand"
    _description = "Brand"
    
    name = fields.Char(string='Brand Name', required=True)
    brand_code = fields.Char(string='Brand Code', required=True)
    brand_category_id = fields.Many2one('brand.category', string='Brand Category', required=True)
    brand_category_code = fields.Char(string='Brand Category Code')
    applicable_to = fields.Selection([('customer', 'Customer'),
                                      ('supplier', 'Supplier'),
                                      ('both', 'Both')],
                                     string='Applicable To')

    @api.onchange('brand_category_id')
    def onchange_brand_category_id(self):
        if not self.brand_category_id:
            return 
        self.brand_category_code = self.brand_category_id.brand_category_code

