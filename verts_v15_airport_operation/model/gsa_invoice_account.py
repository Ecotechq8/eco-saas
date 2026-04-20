from datetime import timedelta

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class AccountMove(models.Model):
    _inherit = 'account.move'

    gsa_invoice = fields.Boolean(string="GSA Invoice")
    doc_number = fields.Char(string='Doc Number')
    airline_id = fields.Many2one('res.partner', string='Airline')
    year_ref = fields.Char(string='Year Ref')
    bank = fields.Char(string='Bank')
    flt_from = fields.Date(string='Flt From')
    flt_to = fields.Date(string='Flt To')
    remarks = fields.Text(string='Remarks')
    flt_details_ids = fields.One2many('gsa.invoice.flt.details', 'invoice_id', string="Flt Details")
    total_chg_wt = fields.Float(string='Total Chargeable Weight', compute='_compute_total_chg_wt', store=True)
    commission_percentage = fields.Float(string="Commission (%)")
    gsa_invoice_commission = fields.Boolean(string="GSA Invoice Commission")
    cur_rate = fields.Float('Currency Rate.')
    purchase_order_line_ids = fields.Many2many('purchase.order.line', string="Purchase Order Lines")


    @api.onchange('commission_percentage')
    def _onchange_commission_percentage(self):
        for line in self.invoice_line_ids:
            line.price_unit = (line.freight_amount*self.commission_percentage)/100
            line._onchange_price_subtotal()
        self._recompute_dynamic_lines()

    @api.depends('flt_details_ids.chg_wt')
    def _compute_total_chg_wt(self):
        for record in self:
            record.total_chg_wt = sum(line.chg_wt for line in record.flt_details_ids)

    def fetch_flt(self):
        self.ensure_one()
        if not self.flt_from or not self.flt_to:
            raise UserError("Please select a valid date range!")
        self.flt_details_ids.unlink()

        domain = [
            ('flt_date', '>=', self.flt_from),
            ('flt_date', '<=', self.flt_to),
            ('airline_id', '=', self.airline_id.id),
            ('loaded', '=', False),
        ]

        inbound_flights = self.env['inbound.flight'].search(domain)
        if not inbound_flights:
            raise UserError("No flights found for the selected date range.")

        lines = []
        for flight in inbound_flights:
            route_name = flight.route.name[-3:] if flight.route and flight.route.name else ''
            route2_name = flight.route2.name[-3:] if flight.route2 and flight.route2.name else ''

            # route = " / ".join(filter(None, [flight.route.name, flight.route2.name]))
            route = " / ".join(filter(None, [route_name, route2_name]))
            lines.append((0, 0, {
                'flt_date': flight.flt_date,
                'flt_number': flight.flt,
                'route': route,
                'gross_wt': flight.gross_wt or 0.00,
                'chg_wt': flight.chrg_wt or 0.00,
                'flt_details': flight.id,
            }))
            flight.loaded = True

        self.flt_details_ids = lines

    def create_invoice_lines(self):
        self.ensure_one()
        self.invoice_line_ids = [(5, 0, 0)]

        lines = []
        if self.flt_details_ids:
            product_ids = self.env['product.product'].search([('is_commission_applicable', '=', True)], limit=1)
            if not product_ids:
                raise UserError("Please define product first for GSA Commission.")
            lines.append((0, 0, {
                'product_id': product_ids.id,
                'name': product_ids.name,
                'quantity': 1,
                'price_unit': self.total_chg_wt,
                # 'account_id': polines[0].product_id.property_account_income_id.id or polines[
                #     0].product_id.categ_id.property_account_income_categ_id.id,
                # 'freight_amount': freight_total,
                # 'product_uom_id': False,
            }))
            self.invoice_line_ids = lines
        else:
            raise UserError("Flight Details Not found.")


    def button_cancel(self):
        res = super(AccountMove, self).button_cancel()
        for rec in self:
            # Reset the flight loaded flags
            for flt in rec.flt_details_ids:
                if flt.flt_details:
                    flt.flt_details.loaded = False
            if rec.flt_details_ids:
                rec.flt_details_ids.unlink()

            # Reset commission_loaded to False
            if rec.gsa_invoice_commission:
                if rec.purchase_order_line_ids:
                    rec.purchase_order_line_ids.write({'commission_loaded':False})
                    rec.purchase_order_line_ids = [(6, 0, [])]
                rec.invoice_line_ids = [(5, 0, 0)]
        return res

    @api.ondelete(at_uninstall=False)
    def _unlink_move_gsa(self):
        for val in self:
            if val.gsa_invoice_commission:
                if val.purchase_order_line_ids:
                    val.purchase_order_line_ids.write({'commission_loaded': False})
                    val.purchase_order_line_ids = [(6, 0, [])]

            if val.gsa_invoice:
                for flt in val.flt_details_ids:
                    if flt.flt_details:
                        flt.flt_details.loaded = False
                if val.flt_details_ids:
                    val.flt_details_ids.unlink()

    # def fetch_invoice_lines_commission(self):
    #     self.ensure_one()

    #     if not self.flt_from or not self.flt_to:
    #         raise UserError("Please set both 'Flt From' and 'Flt To' before fetching invoice lines.")

    #     if self.commission_percentage == 0:
    #         raise UserError("Please set a valid commission percentage.")

    #     if self.purchase_order_line_ids:
    #         self.purchase_order_line_ids.write({'commission_loaded': False})
    #         self.purchase_order_line_ids = [(6, 0, [])]

    #     self.invoice_line_ids = [(5, 0, 0)]

    #     # Create a dictionary to store start and end dates for each month
    #     month_dates = {}
    #     start_date = self.flt_from
    #     while start_date <= self.flt_to:
    #         month_key = start_date.strftime('%Y-%m')
    #         if month_key not in month_dates:
    #             month_dates[month_key] = {'start_date': start_date, 'end_date': start_date}
    #         else:
    #             month_dates[month_key]['end_date'] = start_date
    #         start_date += timedelta(days=1)

    #     # Fetch purchase order lines for each month
    #     lines = []
    #     for month_key, dates in month_dates.items():
    #         polines = self.env['purchase.order.line'].search([
    #             ('order_id.state', 'in', ['done', 'purchase']),
    #             ('order_id.date_approve', '>=', dates['start_date']),
    #             ('order_id.date_approve', '<=', dates['end_date']),
    #             ('order_id.partner_id', '=', self.partner_id.id),
    #             ('commission_loaded', '=', False),
    #             ('product_id.is_commission_applicable', '=', True),
    #         ])

    #         if polines:
    #             month_name = dates['start_date'].strftime('%b-%Y')
    #             freight_total = sum(line.price_total for line in polines)
    #             commission_price_unit = (freight_total * self.commission_percentage) / 100

    #             lines.append((0, 0, {
    #                 # 'product_id': polines[0].product_id.id,
    #                 'name': month_name,
    #                 'quantity': 1,
    #                 'price_unit': commission_price_unit,
    #                 'account_id': polines[0].product_id.property_account_income_id.id or polines[
    #                     0].product_id.categ_id.property_account_income_categ_id.id,
    #                 'freight_amount': freight_total,
    #                 'product_uom_id': False,
    #             }))
    #             # self.purchase_order_line_ids = polines.ids
    #             self.purchase_order_line_ids = [(4, pid) for pid in polines.ids]
    #             polines.write({'commission_loaded': True})

    #     if not lines:
    #         raise UserError("No commission-applicable lines found.")

    #     self.invoice_line_ids = lines


    def fetch_invoice_lines_commission(self):
        self.ensure_one()

        if not self.flt_from or not self.flt_to:
            raise UserError("Please set both 'Flt From' and 'Flt To' before fetching invoice lines.")

        if self.commission_percentage == 0:
            raise UserError("Please set a valid commission percentage.")


        self.invoice_line_ids = [(5, 0, 0)]

        # Create a dictionary to store start and end dates for each month
        # month_dates = {}
        # start_date = self.flt_from
        # while start_date <= self.flt_to:
        #     month_key = start_date.strftime('%Y-%m')
        #     if month_key not in month_dates:
        #         month_dates[month_key] = {'start_date': start_date, 'end_date': start_date}
        #     else:
        #         month_dates[month_key]['end_date'] = start_date 
        #     start_date += timedelta(days=1)

        # Fetch purchase order lines for each month
        lines = []
        move_line = self.env['account.move.line'].search([
            ('move_id.state', 'in', ['posted']),
            ('move_id.invoice_date', '>=', self.flt_from),
            ('move_id.invoice_date', '<=', self.flt_to),
            ('move_id.partner_id', '=', self.partner_id.id),
            ('move_id.move_type', '=', 'in_invoice'),
            ('exclude_from_invoice_tab', '=', False),
            ('product_id.is_commission_applicable', '=', True),
        ])
        for line in move_line:
            freight_total = line.price_subtotal
            commission_price_unit = (freight_total * self.commission_percentage) / 100
            lines.append((0, 0, {
                'product_id': line.product_id.id,
                'name': line.product_id.name,
                'quantity': 1,
                'price_unit': commission_price_unit,
                'account_id': line.account_id,
                'freight_amount': freight_total,
                # 'product_uom_id': False,
            }))

        if not lines:
            raise UserError("No commission-applicable lines found.")

        self.invoice_line_ids = lines

class GsaInvoiceFltDetails(models.Model):
    _name = 'gsa.invoice.flt.details'
    _description = 'GSA Invoice FLT Details'
    _order = 'flt_date asc'

    invoice_id = fields.Many2one('account.move', string="Invoice")
    flt_date = fields.Date(string='FLT Date')
    flt_number = fields.Char(string='FLT Number')
    route = fields.Char(string='Route')
    gross_wt = fields.Float(string='Gross Weight')
    chg_wt = fields.Float(string='Chargeable Weight')
    flt_details = fields.Many2one('inbound.flight', string='Inbound Flight')

    @api.ondelete(at_uninstall=False)
    def _unlink_flt_line(self):
        for val in self:
            if val.flt_details:
                val.flt_details.loaded = False


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    commission_percentage = fields.Float(related="move_id.commission_percentage", string="Commission (%)")
    freight_amount = fields.Monetary(string="Freight Amount", currency_field='currency_id')
    # purchase_order_line_id = fields.Many2one('purchase.order.line', string="Purchase Order Line")


    @api.onchange('commission_percentage', 'freight_amount')
    def _onchange_commission_percentage(self):
        for line in self:
            line.price_unit = (line.freight_amount * self.commission_percentage) / 100
            line._onchange_price_subtotal()
            line.move_id._recompute_dynamic_lines()

    # @api.ondelete(at_uninstall=False)
    # def _unlink_ml_commission(self):
    #     for val in self:
    #         if val.purchase_order_line_id:
    #             val.purchase_order_line_id.commission_loaded =False