import base64

from odoo import fields, models, api
from odoo.exceptions import UserError
import xlwt
from io import BytesIO
from odoo import models


class CvCsrReport(models.Model):
    _name = 'cv.csr.report'
    _description = 'CV CSR Report'
    _rec_name = "sequence"

    TYPE_SELECTION = [
        ('customer', 'Customer'),
        ('vendor', 'Vendor'),
    ]

    type = fields.Selection(TYPE_SELECTION, string="Type", required=True)
    partner_id = fields.Many2one('res.partner', string='Customer', domain=[])
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    date = fields.Date(string="Date")
    date_from = fields.Date(string='Date From')
    date_to = fields.Date(string='Date To')
    remarks = fields.Text(string='Remarks')
    # currency_id = fields.Many2one(
    #     'res.currency',
    #     string='Currency',
    #     required=True,
    #     default=lambda self: self.env.company.currency_id.id
    # )
    # currency_id = fields.Many2one('res.currency', string='Currency', compute='_compute_currency_id', store=True)
    commission_percentage = fields.Float(string="Commission (%)")
    cv_line_ids = fields.One2many('cv.csr.report.line', 'report_id', string="Lines")
    invoice_payment_term_id = fields.Many2one('account.payment.term', string='Payment Terms', check_company=True)
    purchase_order_line_ids = fields.Many2many('purchase.order.line', string="Purchase Order Lines")

    STATE_SELECTION = [
        ('draft', 'Draft'),
        ('posted', 'Posted'),
    ]

    state = fields.Selection(STATE_SELECTION, string="Status", default='draft', readonly=True)
    sequence = fields.Char(string='Reference', readonly=True, copy=False, default='New')
    file_data = fields.Binary("Excel File", readonly=True)
    file_name = fields.Char("File Name", readonly=True)

    # @api.depends('partner_id')
    # def _compute_currency_id(self):
    #     for record in self:
    #         record.currency_id = record.partner_id.currency_id if record.partner_id else False

    def action_generate_excel(self):
        self.ensure_one()

        workbook = xlwt.Workbook()
        sheet = workbook.add_sheet('CSR Report')

        # === Styles ===
        style_title = xlwt.easyxf('font: bold 1, height 280; align: horiz center')
        style_sub_header = xlwt.easyxf('font: bold 1;')
        style_header = xlwt.easyxf(
            'font: bold 1; borders: bottom thin, top thin, left thin, right thin; align: horiz center; '
            'pattern: pattern solid, fore_colour 22'
        )
        style_center = xlwt.easyxf('borders: left thin, right thin; align: horiz center')
        style_right = xlwt.easyxf('borders: left thin, right thin; align: horiz right')
        style_total_center = xlwt.easyxf(
            'font: bold 1; borders: top thin, bottom double, left thin, right thin; align: horiz center; '
            'pattern: pattern solid, fore_colour 22'
        )
        style_total_right = xlwt.easyxf(
            'font: bold 1; borders: top thin, bottom double, left thin, right thin; align: horiz right; '
            'pattern: pattern solid, fore_colour 22'
        )

        row = 0

        # === Header ===
        sheet.write_merge(row, row, 0, 11, "BAHMAN INTERNATIONAL CARGO", style_title)
        row += 1
        sheet.write_merge(row, row, 0, 11, "CARGO DIVISION", style_title)
        row += 2
        sheet.write_merge(row, row, 0, 11, "Cargo Sales Report", style_sub_header)
        row += 1

        sheet.write(row, 0, "Airline", style_sub_header)
        sheet.write(row, 1, self.partner_id.name or '')
        row += 1

        sheet.write(row, 0, "Period", style_sub_header)
        sheet.write(row, 1, f"{self.date_from.strftime('%d %b %Y')} to {self.date_to.strftime('%d %b %Y')}")
        row += 1

        # Currency from partner_id
        currency_name = self.partner_id.property_purchase_currency_id.name or ''
        sheet.write(row, 0, "Currency", style_sub_header)
        sheet.write(row, 1, currency_name)
        row += 2

        # === Table Header ===
        headers = [
            'Date', 'Agent', 'MAWB Prefix', 'MAWB', 'Destination', 'Gross Weight',
            'Chargeable Weight', 'Rate', 'Freight', 'Other Charges', 'Total', 'GSA Commission'
        ]
        for col, h in enumerate(headers):
            sheet.write(row, col, h, style_header)
        row += 1

        # === Data Rows ===
        total_gross = total_chargeable = total_freight = total_other = total_total = total_commission = 0.0

        is_kwd = currency_name == 'KWD'
        digits = 3 if is_kwd else 2

        for line in self.cv_line_ids:
            # First 4 columns → center
            sheet.write(row, 0, line.date.strftime('%d-%m-%Y'), style_center)
            sheet.write(row, 1, line.agent_id.name or '', style_center)
            sheet.write(row, 2, self.partner_id.airline_no or '', style_center)
            sheet.write(row, 3, line.mawb or '', style_center)
            # Rest → right
            sheet.write(row, 4, line.destination_code or '', style_right)
            sheet.write(row, 5, f"{line.gross_weight:.2f}", style_right)
            sheet.write(row, 6, f"{line.chargeable_weight:.2f}", style_right)
            sheet.write(row, 7, f"{line.rate:.{digits}f}", style_right)
            sheet.write(row, 8, f"{line.air_freight:.{digits}f}", style_right)
            sheet.write(row, 9, f"{line.other_charges:.{digits}f}", style_right)
            sheet.write(row, 10, f"{line.total_amount:.{digits}f}", style_right)
            sheet.write(row, 11, f"{line.amount:.{digits}f}", style_right)

            total_gross += line.gross_weight or 0.0
            total_chargeable += line.chargeable_weight or 0.0
            total_freight += line.air_freight or 0.0
            total_other += line.other_charges or 0.0
            total_total += line.total_amount or 0.0
            total_commission += line.amount or 0.0
            row += 1

        # === Totals Row ===
        sheet.write(row, 0, "Total", style_total_center)
        sheet.write(row, 5, f"{total_gross:.2f}", style_total_right)
        sheet.write(row, 6, f"{total_chargeable:.2f}", style_total_right)
        sheet.write(row, 8, f"{currency_name} {total_freight:.{digits}f}", style_total_right)
        sheet.write(row, 9, f"{currency_name} {total_other:.{digits}f}", style_total_right)
        sheet.write(row, 10, f"{currency_name} {total_total:.{digits}f}", style_total_right)
        sheet.write(row, 11, f"{currency_name} {total_commission:.{digits}f}", style_total_right)

        # === Column Widths ===
        for i in range(12):
            sheet.col(i).width = 4000

        # === Save & Download ===
        fp = BytesIO()
        workbook.save(fp)
        data = base64.b64encode(fp.getvalue())
        fp.close()

        filename = f'CSR_Report_{self.id}.xls'
        self.write({
            'file_data': data,
            'file_name': filename,
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f"/web/content?model=cv.csr.report&id={self.id}&field=file_data&filename_field=file_name&download=true",
            'target': 'self',
        }

    @api.model
    def create(self, vals):
        if vals.get('sequence', 'New') == 'New':
            vals['sequence'] = self.env['ir.sequence'].next_by_code('cv.csr.report') or 'New'
        return super(CvCsrReport, self).create(vals)

    def action_post(self):
        for rec in self:
            rec.state = 'posted'

    def action_reset_to_draft(self):
        for rec in self:
            rec.state = 'draft'

    @api.onchange('type')
    def _onchange_type(self):
        if self.type == 'vendor':
            return {'domain': {'partner_id': [('supplier_rank', '>', 0)]}}
        elif self.type == 'customer':
            return {'domain': {'partner_id': [('customer_rank', '>', 0)]}}
        return {}

    def fetch_cv_csv_lines_commission(self):
        self.ensure_one()

        if not self.date_from or not self.date_to:
            raise UserError("Please set both 'Date From' and 'Date To' before fetching data.")

        if not self.partner_id:
            raise UserError("Please select a Customer or Vendor to fetch orders.")

        if self.type == 'vendor' and not self.commission_percentage:
            raise UserError("Please set a valid commission percentage.")

        self.cv_line_ids = [(5, 0, 0)]  # Clear previous lines
        lines = []

        if self.type == 'customer':
            cargo_orders = self.env['cargo.order'].search([
                ('partner_id', '=', self.partner_id.id),
                ('date_order', '>=', self.date_from),
                ('date_order', '<=', self.date_to),
            ])

            if not cargo_orders:
                raise UserError("No Cargo orders found for the selected partner and date range.")

            for cargo in cargo_orders:
                air_freight_total = 0.0
                other_charges_total = 0.0

                for line in cargo.order_line:
                    if line.product_id and line.product_id.name and line.product_id.name.strip().lower() == 'air freight':
                        air_freight_total += line.price_subtotal
                    else:
                        other_charges_total += line.price_subtotal

                gross_weight = cargo.total_gross_weight or 0.0
                chargeable_weight = cargo.total_chargeable_weight or 0.0
                rate = round(air_freight_total / chargeable_weight, 2) if chargeable_weight else 0.0
                commission_amount = (
                                                air_freight_total * self.commission_percentage) / 100.0 if self.commission_percentage else 0.0

                mawb_value = ''
                if cargo.mode == 'air':
                    mawb_value = cargo.mawb.awb_no if cargo.mawb and cargo.mawb.awb_no else ''
                else:
                    mawb_value = cargo.mawb_land or ''

                lines.append((0, 0, {
                    'date': cargo.date_order,
                    'agent_id': cargo.agent_id.id,
                    'mawb': mawb_value,
                    'destination_code': cargo.port_of_discharge_id.code,
                    'gross_weight': gross_weight,
                    'chargeable_weight': chargeable_weight,
                    'rate': rate,
                    'air_freight': air_freight_total,
                    'other_charges': other_charges_total,
                    'total_amount': air_freight_total + other_charges_total,
                    'commission_percentage': self.commission_percentage or 0.0,
                    'amount': commission_amount,
                    'currency_id': self.partner_id.property_purchase_currency_id.id or self.env.company.currency_id.id,
                }))

        elif self.type == 'vendor':
            vendor_bills = self.env['account.move'].search([
                ('partner_id', '=', self.partner_id.id),
                ('move_type', '=', 'in_invoice'),
                ('flight_date_1', '>=', self.date_from),
                ('flight_date_1', '<=', self.date_to),
                ('state', '=', 'posted'),
            ])

            if not vendor_bills:
                raise UserError("No Vendor Bills found for the selected partner and date range.")

            for bill in vendor_bills:
                air_freight_total = 0.0
                other_charges_total = 0.0

                for line in bill.invoice_line_ids:
                    if line.product_id and line.product_id.name and line.product_id.name.strip().lower() == 'air freight':
                        air_freight_total += line.price_subtotal
                    else:
                        other_charges_total += line.price_subtotal

                gross_weight = bill.total_gross_weight or 0.0
                chargeable_weight = bill.total_chargeable_weight or 0.0
                rate = round(air_freight_total / chargeable_weight, 2) if chargeable_weight else 0.0
                commission_amount = (air_freight_total * self.commission_percentage) / 100.0

                mawb_value = ''
                if bill.mode == 'air':
                    mawb_value = bill.mawb.awb_no if bill.mawb and bill.mawb.awb_no else ''
                else:
                    mawb_value = bill.mawb_land or ''

                lines.append((0, 0, {
                    'date': bill.flight_date_1,
                    'agent_id': bill.agent_id.id,
                    'mawb': mawb_value,
                    'destination_code': bill.port_of_discharge_id.code if bill.port_of_discharge_id else '',
                    'gross_weight': gross_weight,
                    'chargeable_weight': chargeable_weight,
                    'rate': rate,
                    'air_freight': air_freight_total,
                    'other_charges': other_charges_total,
                    'total_amount': air_freight_total + other_charges_total,
                    'commission_percentage': self.commission_percentage,
                    'amount': commission_amount,
                    'currency_id': self.partner_id.property_purchase_currency_id.id or self.env.company.currency_id.id,
                }))

        if not lines:
            raise UserError("No valid data found in the selected date range.")

        self.cv_line_ids = lines


class CvCsrReportLine(models.Model):
    _name = 'cv.csr.report.line'
    _description = 'CV CSR Report Line'

    report_id = fields.Many2one('cv.csr.report', string="Report")
    date = fields.Date(string="Date")
    agent_id = fields.Many2one('res.partner', string="Agent")
    mawb = fields.Char(string="MAWB")
    destination_code = fields.Char(string="Destination Code")
    gross_weight = fields.Float(string="Gross Weight")
    chargeable_weight = fields.Float(string="Chargeable Weight")
    rate = fields.Float(string="Rate")
    air_freight = fields.Float(string="Air Freight")
    other_charges = fields.Monetary(string="Other Charges", currency_field='currency_id')
    total_amount = fields.Monetary(string="Total Amount", compute="_compute_total_amount", store=True, currency_field='currency_id')
    commission_percentage = fields.Float(string="Commission (%)")
    amount = fields.Monetary(string="Commission Amount", store=True, currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', string="Currency")
    type = fields.Selection(related='report_id.type', store=False)

    @api.depends('air_freight', 'other_charges')
    def _compute_total_amount(self):
        for rec in self:
            rec.total_amount = (rec.air_freight or 0.0) + (rec.other_charges or 0.0)

    # @api.depends('rate', 'commission_percentage')
    # def _compute_amount(self):
    #     for rec in self:
    #         rec.amount = (rec.rate or 0.0) * (rec.commission_percentage or 0.0) / 100.0
