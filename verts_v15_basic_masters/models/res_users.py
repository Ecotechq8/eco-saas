from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError


class ResUsers(models.Model):
    _inherit = "res.users"
    
    # branch_ids = fields.Many2many('res.branch', string='Branches', required=False)
    digital_signature_type = fields.Selection([('draw', 'Draw'), ('image_upload', 'Image Upload')], default='draw', string='Digital Signature Type')
    digital_signature = fields.Binary(string='Draw Digital Signature')
    digital_signature_upload = fields.Binary(string='Digital Signature Upload', help="This field holds the image used as avatar for this contact, limited to 10x10px",)
    branch_ids = fields.Many2many('res.branch', string='Allowed Branches',
                                  domain="[('company_id', '=', company_ids)]")
    branch_id = fields.Many2one("res.branch", string='Default Branch',
                                default=False,
                                domain="[('id', '=', branch_ids)]")
    is_director = fields.Boolean(string="Director")

    @api.constrains('branch_id')
    def branch_constrains(self):
        """branch constrains"""
        company = self.env.company
        for user in self:
            if user.branch_id and user.branch_id.company_id != company:
                raise UserError(_("Sorry! The selected Branch does "
                                             "not belong to the current Company"
                                             " '%s'", company.name))

    # def _get_default_warehouse_id(self):
    #     """methode to get default warehouse id"""
    #     if self.property_warehouse_id:
    #         return self.property_warehouse_id
    #     # !!! Any change to the following search domain should probably
    #     # be also applied in sale_stock/models/sale_order.py/_init_column.
    #     if len(self.env.user.branch_ids) == 1:
    #         warehouse = self.env['stock.warehouse'].search([
    #             ('branch_id', '=', self.env.user.branch_id.id)], limit=1)
    #         if not warehouse:
    #             warehouse = self.env['stock.warehouse'].search([
    #                 ('branch_id', '=', False)], limit=1)
    #         if not warehouse:
    #             error_msg = _(
    #                 "No warehouse could be found in the '%s' branch",
    #                 self.env.user.branch_id.name
    #             )
    #             raise UserError(error_msg)
    #         return warehouse
    #     else:
    #         return self.env['stock.warehouse'].search([
    #             ('company_id', '=', self.env.company.id)], limit=1)
    
    @api.model
    def create(self, vals):
        # Odoo 18: image_resize_images removed, Binary field handles resize via max_width/max_height
        res = super(ResUsers, self).create(vals)
        return res

    def write(self, values):
        # Odoo 18: image_resize_images removed, Binary field handles resize automatically
        return super(ResUsers, self).write(values)
    
    
class IrMailServer(models.Model):
    """Represents an SMTP server, able to send outgoing emails, with SSL and TLS capabilities."""
    _inherit = "ir.mail_server"
    _description = "Mail Server"
 
    smtp_user = fields.Char(string='Username', help="Optional username for SMTP authentication", groups='base.group_user')
    smtp_pass = fields.Char(string='Password', help="Optional password for SMTP authentication", groups='base.group_user')
