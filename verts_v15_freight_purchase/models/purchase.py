# -*- coding: utf-8 -*-
# Copyright 2021 Verts Services India Pvt Ltd.
# http://www.verts.co.in

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    # mode = fields.Selection([
    #     ('air', 'Air'),
    #     ('sea', 'Sea'),
    #     ('land', 'land')], string='Mode')
    enquiry = fields.Char(string="Enquiry Number")
    total_volume = fields.Float(string='Total Volume')

    # import_export = fields.Selection([
    #     ('import', 'Import'),
    #     ('export', 'Export')], string='Import/Export')
    # customer_id = fields.Many2one('res.partner', string="Customer")
    # goods_category_id = fields.Many2one('export.product.category', string='Goods Category')
    # stuffing_point_id = fields.Many2one('ports', string="Stuffing Point")
    # port_of_discharge_id = fields.Many2one('ports', string="Point of Discharge")
    # port_of_loading_id = fields.Many2one('ports', string="Point of Loading")
    # incoterm_id = fields.Many2one('account.incoterms', string="Shipment (Inco) Terms")
    # service_type = fields.Many2one('service.type', string="Service Type")
    # total_pieces = fields.Float(string='Total Pieces')
    # total_gross_weight = fields.Float(string='Total Gross Weight')
    # total_cbm = fields.Float(string='Total CBM')
    # total_value = fields.Float(string='Total Value')

    req_quot_id = fields.Many2one("request.for.quotation", "Request For Quoation")
    quote_comp_id = fields.Many2one('quote.comparision', string='Quote Id')


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    status = fields.Selection([('Confirm', 'Confirm'), ('Cancelled', 'Cancelled')], string='Status')

    def action_confirm(self):
        if self.po_created_through_pol:
            raise UserError(_("You cannot confirm because PO Created for this product[%s].") % (self.product_id.name))
        if self.status == 'Cancelled':
            raise UserError(_("Cancelled line cannot be confirm."))
        self.write({'status': 'Confirm'})

    def action_cancel(self):
        if self.po_created_through_pol:
            raise UserError(_("You cannot cancel because PO Created for this product[%s].") % (self.product_id.name))
        if self.status == 'Confirm':
            raise UserError(_("Confirm line cannot be cancel."))
        self.write({'status': 'Cancelled'})
