# -*- coding: utf-8 -*-
# Copyright 2021 Verts Services India Pvt Ltd.
# http://www.verts.co.in

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = "stock.picking"
    
    is_export = fields.Boolean('Export Delivery Order')
    qc_pro_specification_line = fields.One2many('order.qc.specification.line', 'picking_id', string='QC Product Specification Line')
#     schedule_lines = fields.One2many('sale.schedule.line', 'export_do_id', 'Schedule Lines')
    

class StockMove(models.Model):
    _inherit = "stock.move"
    
    packing_type = fields.Many2one('export.packing.type', string="Packing Type")
    bag_box_qty = fields.Float(string="Bag/Box Qty.")
        
