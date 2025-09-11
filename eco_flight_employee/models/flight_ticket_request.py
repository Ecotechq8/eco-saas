from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class FlightTicketRequest(models.Model):
    _name = 'flight.ticket.request'
    _description = 'Flight Ticket'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(
        string='Reference',
        required=True,
        copy=False,
        readonly=True,
        default='New'
    )
    employee_id = fields.Many2one(
        string='Employee',
        comodel_name='hr.employee',
        required=True,
    )
    contract_id = fields.Many2one(
        string="Contract",
        comodel_name='hr.contract',
        store=True
    )
    request_date = fields.Date(
        string="Request Date",
        default=fields.Date.today
    )
    departure_time = fields.Datetime(
        string="Departure Time"
    )
    flight_id = fields.Many2one(
        string="Flight Agent",
        comodel_name='res.partner',
        domain=[('is_flight_agent', '=', True)]
    )
    class_type = fields.Char(
        string="Class"
    )
    amount_untaxed = fields.Monetary(
        string="Ticket Amount",
        currency_field='currency_id'
    )
    tax_ids = fields.Many2many(
        string="Taxes",
        comodel_name='account.tax',
    )

    amount_total = fields.Monetary(
        string="Amount With VAT",
        compute='_compute_amount_after_tax',
        store=True,
        currency_field='currency_id'
    )
    currency_id = fields.Many2one(
        string='Currency',
        comodel_name='res.currency',
        default=lambda self: self.env.company.currency_id
    )
    number_of_ticket = fields.Integer(
        string='Number Of Tickets',
        default=1
    )
    remaining_ticket = fields.Integer(
        string="Remaining Ticket Count",
        compute="_compute_remaining_ticket_count",
        store=True
    )
    state = fields.Selection(
        string='Status',
        selection=[
            ('draft', 'Draft'),
            ('submit_for_approval', 'Submit for approval'),
            ('approval', 'Approval'),
            ('confirmed', 'Confirmed'),
        ],
        default='draft',
        tracking=True
    )
    ticket_type = fields.Selection(
        string='Ticket Type',
        selection=[
            ('payment', 'Payment'),
            ('flight_company', 'Flight Company'),
            ('payslip', 'Payslip'),
        ],
        default='',
        tracking=True
    )

    ticket_request_count = fields.Integer(
        string="Ticket Requests",
        compute='compute_ticket_request_count'
    )
    allowed_employee_ids = fields.Many2many(
        comodel_name='hr.employee',
        string='Allowed Employees',
        store=False,
        compute='_compute_allowed_employees'
    )

    vendor_bill_id = fields.Many2one(
        comodel_name='account.move',
        string="Vendor Bill",
        readonly=True,
        copy=False
    )
    payment_id = fields.Many2one(
        comodel_name='account.payment',
        string="Payment",
        readonly=True,
        copy=False
    )

    @api.depends('amount_untaxed', 'tax_ids')
    def _compute_amount_after_tax(self):
        for rec in self:
            tax_amount = 0.0
            if rec.tax_ids:
                tax_result = rec.tax_ids.compute_all(rec.amount_untaxed, currency=rec.currency_id)
                tax_amount = tax_result['total_included']
            else:
                tax_amount = rec.amount_untaxed
            rec.amount_total = tax_amount

    @api.depends('employee_id')
    def _compute_allowed_employees(self):
        employee_ids = self.env['air.ticket.line'].search([]).mapped('employee_id.id')
        for rec in self:
            rec.allowed_employee_ids = [(6, 0, employee_ids)]

    @api.constrains('number_of_ticket')
    def _check_ticket_within_remaining(self):
        for rec in self:
            if rec.number_of_ticket > rec.remaining_ticket:
                raise ValidationError(_(
                    "The number of tickets requested (%s) exceeds the remaining ticket count (%s)."
                ) % (rec.number_of_ticket, rec.remaining_ticket))

    @api.depends('employee_id', 'contract_id', 'number_of_ticket')
    def _compute_remaining_ticket_count(self):
        for rec in self:
            rec.remaining_ticket = 0
            if rec.employee_id:
                contract = rec.contract_id or rec.employee_id.contract_id
                if contract:
                    total_tickets = contract.ticket_count or 0
                    confirmed_requests = self.env['flight.ticket.request'].search([
                        ('employee_id', '=', rec.employee_id.id),
                        ('state', '=', 'confirmed')
                    ])
                    used_tickets = sum(r.number_of_ticket for r in confirmed_requests)
                    rec.remaining_ticket = total_tickets - used_tickets

    @api.depends('employee_id')
    def compute_ticket_request_count(self):
        for rec in self:
            rec.ticket_request_count = self.env['flight.ticket.request'].search_count([
                ('employee_id', '=', rec.employee_id.id)
            ])

    def open_ticket_request_action_list(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Air Ticket Requests'),
            'res_model': 'flight.ticket.request',
            'view_mode': 'list,form',
            'domain': [('employee_id', '=', self.employee_id.id)],
            'context': {'default_employee_id': self.employee_id.id},
        }

    # Auto-generate reference
    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('flight.ticket.request') or 'New'
        record = super().create(vals)
        return record

    def action_submit_for_approval(self):
        for ticket in self:
            ticket.state = 'submit_for_approval'

    def action_approval(self):
        for ticket in self:
            ticket.state = 'approval'

    def action_confirm(self):
        for ticket in self:
            ticket.state = 'confirmed'
            ticket._compute_remaining_ticket_count()

    def action_cancel(self):
        for ticket in self:
            ticket.state = 'draft'

    def action_register_payment(self):
        self.ensure_one()

        # Match partner by employee name
        partner = self.env['res.partner'].search([
            ('name', '=', self.employee_id.name)
        ], limit=1)

        if not partner:
            raise ValidationError(_("No matching partner found for employee: %s") % self.employee_id.name)

        payment = self.env['account.payment'].create({
            'partner_id': partner.id,
            'amount': self.amount_untaxed,
            'payment_type': 'outbound',
            'partner_type': 'supplier',
            'payment_method_id': self.env.ref('account.account_payment_method_manual_out').id,
            'currency_id': self.currency_id.id,
        })

        self.payment_id = payment.id

        return {
            'type': 'ir.actions.act_window',
            'name': _('Register Payment'),
            'res_model': 'account.payment',
            'res_id': payment.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_create_vendor_bill(self):
        self.ensure_one()
        if not self.flight_id:
            raise ValidationError(_("Please select a flight agent (vendor)."))

        config = self.env['ir.config_parameter'].sudo()
        product = self.env['product.product'].browse(int(config.get_param('eco_flight_employee.air_ticket_product_id')))
        if not product:
            raise ValidationError(_("Please configure the Air Ticket Product in settings."))

        bill = self.env['account.move'].create({
            'move_type': 'in_invoice',
            'partner_id': self.flight_id.id,
            'invoice_date': fields.Date.today(),
            'currency_id': self.currency_id.id,
            'invoice_line_ids': [
                (0, 0, {
                    'product_id': product.id,
                    'name': product.name or 'Air Ticket',
                    'quantity': self.number_of_ticket,
                    'price_unit': self.amount_untaxed,
                    'tax_ids': [(6, 0, self.tax_ids.ids)],
                    'account_id': product.property_account_expense_id.id or
                                  product.categ_id.property_account_expense_categ_id.id
                })
            ],
        })

        self.vendor_bill_id = bill.id

    def action_view_vendor_bill(self):
        self.ensure_one()
        if not self.vendor_bill_id:
            raise ValidationError(_("No vendor bill has been created yet."))

        return {
            'type': 'ir.actions.act_window',
            'name': _('Vendor Bill'),
            'res_model': 'account.move',
            'res_id': self.vendor_bill_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
