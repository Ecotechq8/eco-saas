from odoo import _, api, fields, models, tools


class PropertyPhase(models.Model):
    _name = "property.phase"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'image.mixin']

    _description = "Property Phases"

    name = fields.Char(string='Name', required=True)
    phase_number = fields.Char(string='Phase Number', required=True)
    project_id = fields.Many2one("project.project", "Project", required=True)


class PropertyZone(models.Model):
    _name = "property.zone"
    _description = "Property Zone"

    name = fields.Char(string='Name', required=True)
    zone_number = fields.Char(string='Zone Number', required=True)
    project_id = fields.Many2one("project.project", "Project", required=True)
    phase_id = fields.Many2one("property.phase", "Phase", required=True)

    @api.onchange('phase_id')
    def phase_project_id(self):
        self.project_id = self.phase_id.project_id


class PropertyBuilding(models.Model):
    _name = "property.building"
    _description = "Property Building"

    name = fields.Char(string='Name', required=True)
    building_number = fields.Char(string='Building Number', required=True)
    project_id = fields.Many2one("project.project", "Project", required=True)
    phase_id = fields.Many2one("property.phase", "Phase", required=True)
    zone_id = fields.Many2one("property.zone", "Zone", required=True)

    @api.onchange('zone_id')
    def zone_project_id(self):
        self.project_id = self.zone_id.project_id
        self.phase_id = self.zone_id.phase_id


class PropertyBlock(models.Model):
    _name = "property.block"

    name = fields.Char(string='Name', required=True)


class PropertyFloor(models.Model):
    _name = "property.floor"

    name = fields.Char(string='Name', required=True)


class PropertyLevel(models.Model):
    _name = "property.level"

    name = fields.Char(string='Name', required=True)


class ProjectLocation(models.Model):
    _name = "project.location"
    _description = "Project Location"

    name = fields.Char(string='Name', required=True)


class ProjectSource(models.Model):
    _name = "project.source"
    _description = "Project Source"

    name = fields.Char(string='Name', required=True)


class ProjectCategoryType(models.Model):
    _name = "project.category.type"

    name = fields.Char(string='Name', required=True)
