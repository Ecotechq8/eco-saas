from odoo import models, fields , api


class ResCompany(models.Model):
    _inherit = 'res.company'
    
    gstin_no = fields.Char(string='GSTIN')
    pan_no = fields.Char(string='PAN No')
    about_us = fields.Html(string="About Us")

    cin_no = fields.Char(string="CIN")
    bank_account_id = fields.Many2one('account.journal', string="Account No")
    bank_id = fields.Many2one('res.bank', "Bank" , related='partner_account_id.bank_id')
    partner_account_id = fields.Many2one('res.partner.bank', "Account No")
    # bank_branch_id = fields.Many2one('res.bank', string="Bank Branch")
    # ifsc_code = fields.Char('IFSC Code')
    # swift_code = fields.Char('SWIFT Code')
    # registered_street = fields.Char('Registered Street')
    # registered_street2 = fields.Char('Registered Street2')
    # registered_zip = fields.Char('Registered Zip')
    # registered_city = fields.Char('Registered City')
    # registered_state_id = fields.Many2one('res.country.state', string="Registered State")
    # registered_country_id = fields.Many2one('res.country', string="Reg Country")

