from odoo import fields, models, api
from datetime import datetime
from odoo import _
from odoo.exceptions import UserError, ValidationError
    
class WizChangePolQty(models.TransientModel):
    _name = "wiz.change.pol.qty"  
    _description = "Pol Qty"

    qty = fields.Float('Qty')
    pol_id = fields.Many2one('purchase.order.line',string='POL')
    
    @api.model
    def default_get(self, fields):
        res = super(WizChangePolQty, self).default_get(fields)
        pol_id = self._context.get('active_id')
        pol_pool = self.env['purchase.order.line']
        if 'pol_id' in fields:
            pol_obj = pol_pool.browse(pol_id)
            if pol_obj.po_created_through_pol:
                raise UserError(_("You cannot change qty because PO Created for this product[%s].")%(pol_obj.product_id.name))
            if pol_obj.status != 'Confirm':
                raise UserError(_("Please confirm the POL first for product [%s].") % pol_obj.product_id.name)
            res.update({'pol_id':pol_id,'qty':pol_obj.product_qty})
        return res
    

    def action_change_qty(self):
        if self.pol_id:
            self.pol_id.product_qty = self.qty
            
    
    
    
