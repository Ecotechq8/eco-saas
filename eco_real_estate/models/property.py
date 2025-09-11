from odoo import _, api, fields, models, tools


class Property(models.Model):
    _inherit = ["product.template"]
    _description = "Property"
    _order = "sequence, id"

    state = fields.Selection([
        ("blocked", "Blocked"),
        ("free", "Available"),
        ("no_available", "Not Available"),
        ("reserved", "Reserved"),
        ("contract", "Contracted"),
        ("deliver", "Delivered"),
    ],
        "Status", default="free",tracking=True)

    sequence = fields.Integer("Sequ.")

    partner_id = fields.Many2one("res.partner", "Owner")
    property_date = fields.Date("Date", default=fields.Date.context_today)
    has_garden = fields.Boolean(string='Has Garden', required=False)
    has_pool = fields.Boolean(string='Has Pool ', required=False)
    has_garage = fields.Boolean(string='Has Garage', required=False)
    address = fields.Char("Address")
    phase_id = fields.Many2one("property.phase", "Phase")
    zone_id = fields.Many2one('property.zone', string='Zone', required=False)
    building_id = fields.Many2one('property.building', string='Building', required=False)
    block_id = fields.Many2one('property.block', string='Block', required=False)
    floor_id = fields.Many2one('property.floor', string='Floor', required=False)

    level_id = fields.Many2one('property.level', string='Level', required=False)
    min_price = fields.Float(
        string='Min Price',
        required=False)

    note = fields.Html("Notes")
    description = fields.Text("Description")
    license_code = fields.Char("License Code", size=16)
    license_date = fields.Date("License Date")
    date_added = fields.Date("Date Added to Notarization")
    license_location = fields.Char("License Notarization")

    maintenance_type = fields.Selection(selection=[("fix", "Fix Cost"), ("sft", "Per SFT")], default="fix")
    maintenance_charges = fields.Float()
    property_area = fields.Float("Property Size (Sq. ft)", digits=(16, 8))
    unit_of_measure = fields.Selection([("m", "m²"), ("yard", "Yard²")], default="m", required=True)
    converted_area = fields.Float("Converted Size", digits=(16, 8))

    partner_from = fields.Date("Purchase Date")
    partner_to = fields.Date("Sale Date")

    property_project_id = fields.Many2one("project.project", "Project" ,required=True)  # project_worksite_id
    # project_type = fields.Selection(string='Project Type', related='property_project_id.project_type')
    project_categ_type = fields.Many2one('project.category.type', string='Project Type', required=True)
    project_categ_type_ids = fields.Many2many(related='property_project_id.project_categ_type_ids')

    contact_ids = fields.Many2many("res.partner", string="Contacts")

    # project_type = fields.Selection(selection=PROJECT_WORKSITE_TYPE + [('shop', 'Shop')], default="tower")
    floor_area = fields.Float("Floor Area (SQM)")
    bedroom_no = fields.Integer("Bedroom No")
    discount_type = fields.Selection([("percentage", "Percentage"), ("amount", "Amount")])
    discount = fields.Float("Discount")

    property_price_type = fields.Selection(selection=[("fix", "Fix Cost"), ("sft", "Per SFT")], default="sft")
    price_per_m = fields.Float("Base Price")
    project_area = fields.Float("Project Area")
    tax_base_amount = fields.Float("Tax Base Amount")

    # Property
    is_property = fields.Boolean("Property")


    is_shop = fields.Boolean(default=False)
    doc_charges = fields.Float("Doc Charges")

    total_area= fields.Float('Total Area',required=False)
    total_open_area= fields.Float('Total Open Area',required=False)
    plot_area= fields.Float('Plot Area',required=False)
    indoor_area= fields.Float('Indoor Area',required=False)
    covered_terrace= fields.Float('Covered Terrace',required=False)
    total_covered_terrace= fields.Float('Total Covered Terrace',required=False)
    court_yard= fields.Float('Court Yard',required=False)
    open_terrace = fields.Float('Open Terrace',required=False)
    balcony_area = fields.Float('Balcony Area',required=False)
    has_sea_view = fields.Boolean('Sea View',required=False)
    has_lagoon_view = fields.Boolean('Lagoon View',required=False)
    has_landscape_view = fields.Boolean('Landscape View',required=False)
    # Smart buttons fields
    def _reservation_count(self):
        property_reservation = self.env["property.reservation"]
        for rec in self:
            rec.reservation_count = property_reservation.search_count([("property_id", "=", rec.id)])

    reservation_count = fields.Integer(compute="_reservation_count", string="Reservation")

    _sql_constraints = [
        (
            "unique_property_code",
            "UNIQUE (default_code')",
            "Property code must be unique!",
        ),
    ]

    def set_property_to_available(self):
        self.state = 'free'
    def set_property_to_block(self):
        self.state = 'blocked'

    def set_property_to_not_available(self):
        self.state = 'no_available'

    # Buttons Methods
    def action_create_reservation(self):
        # self.state = 'reserved'

        return {
            "name": _("Property Reservation"),
            "view_type": "form",
            "view_mode": "form",
            "res_model": "property.reservation",
            "view_id": self.env.ref("eco_real_estate.property_reservation_form_view").id,
            "type": "ir.actions.act_window",
            "context": {
                "form_view_initial_mode": "edit",
                "default_project_id": self.property_project_id.id,
                "default_property_id": self.id,
                "default_property_price": self.list_price,
                "default_phase_id": self.phase_id.id,
            },
            "target": "current",
        }

    def button_view_reservation(self):
        reservation_ids = self.env["property.reservation"].search([("property_id", "=", self.id)])
        return {
            "name": _("Reservation"),
            "domain": [("id", "in", reservation_ids.ids)],
            "view_type": "list",
            "view_mode": "list,form",
            "res_model": "property.reservation",
            "type": "ir.actions.act_window",
            "nodestroy": True,
            "view_id": False,
            "target": "current",
        }


    # depend methods

