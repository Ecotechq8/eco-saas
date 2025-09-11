from odoo import _, api, fields, models, tools


class Project(models.Model):
    _inherit = 'project.project'

    project_number = fields.Char(string='Project Number', required=False)
    site_receiving_date = fields.Date(string='Site Receiving Date', required=False)
    delivery_date = fields.Date(string='Delivery Date', required=False)
    city = fields.Many2one('res.country.state', string='City', required=False)
    phase_ids = fields.One2many('property.phase', 'project_id', string='Phases', required=False)
    property_ids = fields.One2many("product.template", 'project_id', string="Properties")
    zone_ids = fields.One2many("property.zone", 'project_id', string="Zones")
    building_ids = fields.One2many("property.building", 'project_id', string="Building")
    location_id = fields.Many2one('project.location', string='Project Location', required=False)
    source_id = fields.Many2one('project.source', string='Project Source', required=False)
    plot_area = fields.Char(string='Plot Area', required=False)
    height = fields.Char(string='Height', required=False)
    project_categ_type_ids = fields.Many2many('project.category.type', string='Project Type')

    payment_term_ids = fields.Many2many('account.payment.term', string='Payment Term',
                                        domain="[('state','=','approve')]")
