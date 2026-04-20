from odoo import api, fields, models, _


class MakersInfo(models.Model):
    _name = "makers.info"
    _description = "Makers Info"

    name = fields.Char(string='Name', required=True)
    full_name = fields.Char(string='Full Name')


class BrandsInfo(models.Model):
    _name = "brands.info"
    _description = "Brands Info"

    name = fields.Char(string='Brand Name', required=True)


class BrandCategory(models.Model):
    _name = "brand.category"
    _description = "Brand Category"

    name = fields.Char(string='Category Name', required=True)
    brand_category_code = fields.Char(string='Category Code')
    description = fields.Text(string='Description')


class Brand(models.Model):
    _name = "brand"
    _description = "Brand"

    name = fields.Char(string='Brand Name', required=True)
    brand_code = fields.Char(string='Brand Code')
    brand_category_id = fields.Many2one('brand.category', string='Category')
    brand_category_code = fields.Char(related='brand_category_id.brand_category_code', string='Category Code', readonly=True)
    applicable_to = fields.Selection([('product', 'Product'), ('service', 'Service'), ('both', 'Both')], string='Applicable To', default='both')


class TermAndCondition(models.Model):
    _name = "term.and.condition"
    _description = "Terms and Conditions"

    name = fields.Char(string='Name', required=True)
    description = fields.Text(string='Description')
    term_and_condition_line = fields.One2many('term.and.condition.line', 'term_id', string='Lines')
    term_and_condition_option_id = fields.Many2one('term.and.condition.option', string='Option')
    is_default = fields.Boolean(string='Is Default', default=False)


class TermAndConditionLine(models.Model):
    _name = "term.and.condition.line"
    _description = "Terms and Conditions Line"

    term_id = fields.Many2one('term.and.condition', string='Term')
    term_and_condition_option_id = fields.Many2one('term.and.condition.option', string='Option')
    sequence = fields.Integer(string='Sequence', default=10)
    name = fields.Char(string='Description', required=True)


class TermAndConditionOption(models.Model):
    _name = "term.and.condition.option"
    _description = "Terms and Conditions Option"

    name = fields.Char(string='Option Name', required=True)
    description = fields.Text(string='Description')
    term_and_condition_id = fields.Many2one('term.and.condition', string='Term')
    is_default = fields.Boolean(string='Is Default', default=False)


class TermAndConditionSet(models.Model):
    _name = "term.and.condition.set"
    _description = "Terms and Conditions Set"

    name = fields.Char(string='Set Name', required=True)
    description = fields.Text(string='Description')
    tc_set_type = fields.Selection([('sale', 'Sale'), ('purchase', 'Purchase')], string='Type', default='sale')
    is_default = fields.Boolean(string='Is Default', default=False)
    tc_set_line = fields.One2many('term.and.condition.set.line', 'set_id', string='Set Lines')


class TermAndConditionSetLine(models.Model):
    _name = "term.and.condition.set.line"
    _description = "Terms and Conditions Set Line"

    set_id = fields.Many2one('term.and.condition.set', string='Set')
    term_and_condition_id = fields.Many2one('term.and.condition', string='Term')
    term_and_condition_option_id = fields.Many2one('term.and.condition.option', string='Option')
    sequence = fields.Integer(string='Sequence', default=10)
    removable = fields.Boolean(string='Removable', default=True)


class PartnerCategories(models.Model):
    _name = "partner.categories"
    _description = "Partner Categories"

    name = fields.Char(string='Category Name', required=True)
    description = fields.Text(string='Description')
    prefix = fields.Char(string='Prefix')
    suffix = fields.Char(string='Suffix')
    sequence_size = fields.Integer(string='Sequence Size', default=10)
    account_receivable = fields.Many2one('account.account', string='Account Receivable')
    account_payable = fields.Many2one('account.account', string='Account Payable')
    type = fields.Selection([('customer', 'Customer'), ('supplier', 'Supplier'), ('both', 'Both')], string='Type', default='both')
