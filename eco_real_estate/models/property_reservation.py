import calendar
import datetime
from datetime import date, datetime, timedelta

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.translate import _
from dateutil.relativedelta import relativedelta


class PropertyReservation(models.Model):
    _name = "property.reservation"
    _description = "Property Reservation"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    state = fields.Selection([
        ("draft", "Draft"),
        ("req_exception", "Request For Exception"),
        ("approve_exception", "Exception Approved"),
        ("reject_exception", "Exception Rejected"),
        ("reserved", "Reserved"),
        ("contract_ini", "Contract Initialized"),
        ("contract_rev", "Contract Reviewed"),
        ("check", "Check Received"),
        ("contracted", "Contracted"),
        ("cancel", "canceled"),

    ],
        "Status", default="draft", tracking=True)
    name = fields.Char(string='Name', readonly=True)
    reservation_date = fields.Date(string='Reservation Date',default=fields.Date.context_today)
    # Property details
    project_id = fields.Many2one('project.project', "Project")
    phase_id = fields.Many2one("property.phase", "Phase")
    property_id = fields.Many2one("product.template", "Property")
    type = fields.Many2one(string='Type', related='property_id.project_categ_type')
    discount_type = fields.Selection([("percentage", "Percentage"), ("amount", "Amount")], default="amount")
    discount = fields.Float("Discount")
    payment_strategy = fields.Many2one('account.payment.term', string='Payment Strategy', required=True)
    payment_term_ids = fields.Many2many(related='project_id.payment_term_ids')
    property_price = fields.Float("Property Price", readonly=True)
    net_price = fields.Float("Net Price", compute='_compute_net_price', store=True)
    
    # Sales details
    sale_id = fields.Many2one('sale.order', "Contract")
    sales_type = fields.Selection([
        ("direct", "Direct"),
        ("indirect", "Indirect"),
        ("individual", "Individual Broker"),
        ("client", "Client Referral"),
        ("resale", "Resale"),
        ("upgrade", "Upgrade"),
        ("supplier_sale", "Supplier Through Sales"),
        ("supplier_company", "Supplier Through Company"),
    ],
        "Sales Type", default="direct", )

    sales_agent_type = fields.Selection([
        ("freelancer", "Freelancer"),
        ("referral", "Referral"),
        ("exclusive", "Broker [Exclusive]"),
        ("no_exclusive", "Broker [None Exclusive]"),
    ], "Sales Agent Type")
    sales_agent = fields.Many2one('res.partner', string='Sales Agent', required=False)
    source = fields.Selection([
        ("facebook", "Facebook"),
        ("call", "Call Center"),
        ("web", "Website"),
        ("broker", "Broker"),
        ("referral", "Referral"),
        ("ambassador", "Ambassador"),
        ("other", "Other"),
        ("self_gen", "Self Generated"),
    ], "Source")
    user_id = fields.Many2one('res.users', string='Salesperson', required=False)
    team_id = fields.Many2one('crm.team', string='Sales Team', required=False)
    first_check_no = fields.Integer(string='First check no', )

    maintenance_based_on = fields.Selection(
        string='Maintenance Based on',
        selection=[('reservation', 'Reservation Date'),
                   ('contract', 'Contract Date'),
                   ('delivery', 'Delivery Date'),
                   ],default='reservation' )
    maintenance_date  = fields.Date(
        string='Maintenance Date',
        required=True)
    # Customer Details
    customer_id = fields.Many2one('res.partner', 'Customer', required=True)
    street = fields.Char(related='customer_id.street')
    phone = fields.Char(related='customer_id.phone')
    mobile = fields.Char(related='customer_id.mobile')
    email = fields.Char(related='customer_id.email')
    function = fields.Char(string='Job Position', related='customer_id.function')
    country_id = fields.Many2one(related='customer_id.country_id', string='Nationality')
    id_type = fields.Selection(related='customer_id.id_type')

    id_number = fields.Char(related='customer_id.id_number')
    image_1920 = fields.Binary(related='customer_id.image_1920')
    customer_photo_id = fields.Binary('Photo')

    # page fields
    reservation_conditions = fields.Text(string="Reservation Conditions", required=False)
    exp_request = fields.Text(string="Exception Request", required=False)
    payment_attachment_ids = fields.One2many('ir.attachment', 'property_pay_id', string='Payment_attachment_ids')
    legal_paper_ids = fields.One2many('ir.attachment', inverse_name='property_legal_id', string='Legal Paper ', )
    # Payment for others
    other_partner_id = fields.Many2one('res.partner', 'Other Partner')
    partner_id_type = fields.Selection(related='other_partner_id.id_type')
    partner_id_number = fields.Char(related='other_partner_id.id_number')
    partner_photo_id = fields.Binary('Photo')
    partner_country_id = fields.Many2one(related='other_partner_id.country_id', string='Nationality')
    partner_date = fields.Date(string='date', required=False)
    # cancel reason
    cancel_payment_id = fields.Many2one('account.payment', 'Cancel payment ')
    cancel_reason = fields.Text('Cancel Reason')

    ##### Payments Page ############
    payment_strategy_line_ids = fields.One2many('payment.strategy.line', 'reservation_id',
                                                string='Payment strategy Lines',
                                                required=False)

    ############## Buttons Methods  ########################
    def action_request_exception(self):
        if not self.exp_request:
            raise UserError(_("You must add an exception request first !"))
        self.write({"state": "req_exception"})

    def action_approve_exception(self):
        self.write({"state": "approve_exception"})

    def action_reject_exception(self):
        self.write({"state": "reject_exception"})

    def action_reserve(self):

        self.write({"state": "reserved"})
        self.property_id.write({"state": "reserved"})

    def action_initialize_contract(self):
        self.write({"state": "contract_ini"})

    def action_review_contract(self):

        self.write({"state": "contract_rev"})

    def action_check_contract(self):
        self.write({"state": "check"})

    def action_contracted(self):
        sale_order = self.env['sale.order']
        product = self.env['product.product']

        sale_id = sale_order.create({
            'partner_id': self.customer_id.id,
            'user_id': self.user_id.id,
            'team_id': self.team_id.id,
            'project_id': self.project_id.id,
            'property_id': self.property_id.id,
            'reservation_id': self.id,
            'payment_term_id': self.payment_strategy.id,
            'order_line': [(0, 0, {
                'product_id': product.search([('product_tmpl_id', '=', self.property_id.id)], limit=1).id,
                'product_uom_qty': 1,
                'price_unit': self.net_price,
            })]
        })
        if sale_id:
            self.sale_id = sale_id
        self.write({"state": "contracted"})
        self.property_id.write({"state": "contract"})

    # def action_cancel_wizard(self):
    #         self.write({"state": "cancel"})

    ############ constrains Methods #############################
    @api.constrains("net_price", "property_id")
    def _check_min_price_with_net_price(self):
        if self.net_price < self.property_id.min_price:
            raise UserError(
                _("Total Price after discount '%s' is more Than min price '%s' of property that you selected",
                  self.property_id.min_price, self.net_price))

    @api.constrains("payment_strategy")
    def _create_payment_strategy_line(self):
        if self.first_check_no == 0:
            raise UserError(_("You must write First check number !"))
        if self.payment_strategy:
            # for rec in self.payment_strategy.line_ids:
            vals = []
            check_no = self.first_check_no
            all_percent = 0.0
            serial = 1
            for rec in self.payment_strategy.line_ids:
                result = {
                    'description': rec.description,
                    'journal_id': rec.journal_id.id,
                    'reservation_id': self.id,
                    'type': rec.type,
                    'value_amount': rec.value_amount / 100 * self.net_price,
                    'percent': rec.value_amount ,
                    'payment_date': fields.Date.today() + relativedelta(days=rec.nb_days),
                    'all_percent': rec.value_amount + all_percent,
                    'serial': serial ,
                }
                serial += 1
                all_percent += rec.value_amount
                if rec.type == 'maintenance':
                    result.update({'payment_date':self.maintenance_date + relativedelta(days=rec.nb_days)})
                if rec.journal_id.type == 'bank':
                    result.update({'check_no':str(check_no)})
                    check_no += 1
                vals.append(result)
            self.env['payment.strategy.line'].create(vals)

    ############ onchange Methods #############################

    @api.onchange('discount_type')
    def _onchange_discount_type(self):
        if self.discount_type:
            self.discount = 0.0

    ############ depend Methods #############################

    @api.depends('discount', 'discount_type', 'property_price')
    def _compute_net_price(self):
        self.net_price = self.property_price
        if self.discount_type == 'amount':
            self.net_price -= self.discount
        else:
            self.net_price -= self.property_price * (self.discount / 100)

    ### odoo override Methods #############
    @api.model
    def create(self, vals):
        if vals.get("name", "New") == "New":
            vals["name"] = (
                    self.env["ir.sequence"].next_by_code(
                        "property.reservation") or "New"
            )
        result = super(PropertyReservation, self).create(vals)
        return result
