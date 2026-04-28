from odoo import api, fields, models, _
from lxml import etree


class ResPartner(models.Model):
    _inherit = "res.partner"
    
    # def _get_branch(self):
    #     if self.env.user and self.env.user.branch_ids:
    #         return self.env.user.branch_ids[0].id
    #     else:
    #         try:
    #             main_branch = self.env['ir.model.data']._xmlid_to_res_id('verts_v15_basic_masters.main_branch_id')
    #             return main_branch
    #         except:
    #             return
    #
    # branch_id = fields.Many2one('res.branch', string='Branch', default=_get_branch)
    prefer_mode_transport_id = fields.Many2one('mode.transport', string='Preferred Mode of Transport')
    prefer_shipment_vendor_id = fields.Many2one('res.partner', string='Preferred Shipment Vendor')
    city_id = fields.Many2one('cities.basic.masters', string='City')
    
    @api.onchange('city_id')
    def product_id_change(self):
        if self.city_id:
            self.city = self.city_id.name

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        lst = []
        context = self._context or {}
        ir_model_obj = self.env['ir.model.data']
        res = super(ResPartner, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        if self._context.get('uid'):
            user_obj = self.env['res.users'].browse(self._context.get('uid'))
            for branch in user_obj.branch_ids:
                lst.append(branch.id)
        doc = etree.XML(res['arch'])
        for node in doc.xpath("//field[@name='branch_id']"):
            node.set('domain', "[('id', 'in', %s)]" %str(lst))
            res['arch'] = etree.tostring(doc, encoding="unicode")
        return res

