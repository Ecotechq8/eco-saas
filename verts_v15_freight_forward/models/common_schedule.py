# -*- coding: utf-8 -*-
# Copyright 2021 Verts Services India Pvt Ltd.
# http://www.verts.co.in


from odoo import api,fields,models, _
from odoo.exceptions import UserError


class CommonSchedule(models.Model):
    _name = "common.schedule"
    _description = 'Common Schedule'

    name =  fields.Char(string="Schedule Name")
    report_at_time = fields.Selection([('pre_shipment', 'Pre Shipment'), ('post_shipment', 'Post Shipment')], string='Report at Time')
    req_from = fields.Selection([('other', 'Other'), ('self', 'Self')], string='Requirement From')
    country_specific = fields.Boolean(string="Country Specific")
    port_of_loading_specific = fields.Boolean(string="Port of Loading Specific")


class ProductMixVariants(models.Model):
    _name = "product.mix.variants"
    _description = 'Product Mix Variants'
    _rec_name = 'qc_parameter_id'

    qc_parameter_id = fields.Many2one('qc.parameter', string="QC Parameter")
    value = fields.Char(string="Value")

    def name_get(self):
        result = []
        for obj in self:
            name = obj.qc_parameter_id.name + '-' + str(obj.value)
            result.append((obj.id, name))
        return result


class ExportPackingType(models.Model):
    _name = 'export.packing.type'
    _description = 'Export Packing Type'

    name = fields.Char('Name')
