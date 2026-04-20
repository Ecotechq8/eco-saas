from odoo import api, models, fields, _
from odoo.exceptions import UserError



class GsaInvoice(models.Model):
    _name = 'gsa.invoice'
    _description = 'GSA Invoice'

    name = fields.Char(
        string="Invoice No.",
        tracking=True,
        required=True, copy=False, readonly=False,
        index='trigram',
        default=lambda self: _('New'))
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    date = fields.Date(string='Date', default=fields.Date.context_today)
    doc_number = fields.Char(string='Doc Number')
    airline_id = fields.Many2one('air.line',string='Airline')
    # airline = fields.Char(string='Airline')
    year_ref = fields.Char(string='Year Ref')
    bank = fields.Char(string='Bank')
    flt_from = fields.Date(string='Flt From')
    flt_to = fields.Date(string='Flt To')
    customer_id = fields.Many2one('res.partner', string='Customer')
    remarks = fields.Text(string='Remarks')
    flt_details_ids = fields.One2many('gsa.invoice.flt.details', 'invoice_id', string="Flt Details")
    invoice_line_ids = fields.One2many('gsa.invoice.line', 'invoice_id')

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('gsa.invoice') or 'New'
        return super(GsaInvoice, self).create(vals)

    # @api.onchange('airline_code')
    # def _onchange_airline_code(self):
    #     if self.airline_code:
    #         self.airline = self.airline_code.name
    #     else:
    #         self.airline = False

    def fetch_flt(self):
        # Clear existing lines first
        self.fit_details_ids = [(5, 0, 0)]

        if not self.flt_from or not self.flt_to:
            raise UserError("Please select a valid date range!")

        domain = [
            ('flt_date', '>=', self.flt_from),
            ('flt_date', '<=', self.flt_to),
            ('airline_id', '=', self.airline_id.id)
        ]

        inbound_flights = self.env['inbound.flight'].search(domain)
        if not inbound_flights:
            raise UserError("No flights found for the selected date range.")

        line_values = []
        for flight in inbound_flights:
            route = ""
            if flight.route and flight.route2:
                route = f"{flight.route.name} / {flight.route2.name}"
            elif flight.route:
                route = flight.route.name
            elif flight.route2:
                route = flight.route2.name
            line_values.append((0, 0, {
                'flt_date': flight.flt_date,  # Changed from flt_date to date
                'flt_number': flight.flt,
                'route': route,
                'gross_wt': flight.gross_wt or 0.00,
                'chg_wt': flight.chrg_wt or 0.00,
            }))
        # Directly set the lines
        self.flt_details_ids = line_values


class GSAInvoiceFltDetails(models.Model):
    _name = 'gsa.invoice.flt.details'
    _description = 'GSA Invoice Flt Details'

    invoice_id = fields.Many2one('gsa.invoice', string="Invoice", ondelete="cascade")
    flt_date = fields.Date(string="Flt Date")
    flt_number = fields.Char(string="Flt #")
    route = fields.Char(string="Route")
    gross_wt = fields.Float(string="Gross WT")
    chg_wt = fields.Float(string="Chg WT")

class GSAInvoiceLine(models.Model):
    _name = 'gsa.invoice.line'
    _description = 'GSA Invoice Line'

    invoice_id = fields.Many2one('gsa.invoice', string="Invoice", ondelete="cascade")
    product_id = fields.Many2one('product.product', string="Product")
    quantity = fields.Float(string="Quantity")
    price_unit = fields.Float(string="Unit Price")
    amount = fields.Float(string="Amount", compute="_compute_amount", store=True)
    currency_id = fields.Many2one('res.currency', string="Currency", default=lambda self: self.env.company.currency_id)
    exchange_rate = fields.Float(string="Exchange Rate", default=1.0)
    subtotal = fields.Float(string="Subtotal", compute="_compute_subtotal", store=True)

