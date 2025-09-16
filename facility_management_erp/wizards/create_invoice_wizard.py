from odoo import api, fields, models, _, tools, Command # type: ignore
from odoo.osv import expression # type: ignore
from odoo.exceptions import UserError, ValidationError  # type: ignore



class CreateInvoiceWizard(models.TransientModel):
    _name = "invoice.wizard"
    _description = "Invoice Creation Wizard"

    date = fields.Date(string='Date',required=True, default=lambda self: fields.Date.today())
    partner_id = fields.Many2one('res.partner', string='Customer', readonly=True)
    facility_id = fields.Many2one('fm.management', string='Facility ID')
    type_selection = fields.Selection([
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly')], string='Type', required=True, tracking=True)

    # unit_line_ids = fields.One2many('fm.unit.lines', compute='_compute_unit_line_ids', string='Unit Line', tracking=True)
    unit_line_ids = fields.One2many('unit.lines.wizard','wizard_id', string='Unit Line', tracking=True)
    balance_to_be_invoiced = fields.Float(compute='_compute_calculation', store=True, string='Balance to Invoice', tracking=True)
    is_clicked = fields.Boolean('Is Clicked', default=False)


    @api.onchange('type_selection')
    def onchange_type_selection(self):
        if self.type_selection == 'monthly':
            for x in self.unit_line_ids:
                if x.total and x.total != 0:
                    total = x.total
                    x.invoice_amount = total/12
                else:
                    x.invoice_amount = 0.00

        elif self.type_selection == 'quarterly':
            for x in self.unit_line_ids:
                if x.total and x.total != 0:
                    total = x.total
                    x.invoice_amount = total/4
                else:
                    x.invoice_amount = 0.00

        if self.type_selection == 'yearly':
            for x in self.unit_line_ids:
                if x.total and x.total != 0:
                    total = x.total
                    x.invoice_amount = total
                else:
                    x.invoice_amount = 0.00

    @api.onchange('type_selection')
    def onchange_type_selection_field(self):
        if self.type_selection == 'monthly':
            for x in self.facility_id.unit_line_ids:
                if x.total and x.total != 0:
                    total = x.total
                    x.invoice_amount = total / 12
                else:
                    x.invoice_amount = 0.00

        elif self.type_selection == 'quarterly':
            for x in self.facility_id.unit_line_ids:
                if x.total and x.total != 0:
                    total = x.total
                    x.invoice_amount = total / 4
                else:
                    x.invoice_amount = 0.00

        if self.type_selection == 'yearly':
            for x in self.facility_id.unit_line_ids:
                if x.total and x.total != 0:
                    total = x.total
                    x.invoice_amount = total
                else:
                    x.invoice_amount = 0.00

    @api.depends('unit_line_ids')
    def _compute_calculation(self):
        for rec in self:
            rec.balance_to_be_invoiced = sum(rec.unit_line_ids.mapped('balance_to_be_invoiced'))

    def button_create_invoice(self):
        move_list = []
        self.is_clicked = True
        move_id = self.env['account.move'].search(
            [('facility_id', '=', self.id), ('move_type', '=', 'out_invoice')])
        if move_id:
            move_id.invoice_line_ids = [(0, 0, line) for line in self._prepare_out_invoice_line()]
        else:
            move_id = self.env['account.move'].create({
                'name': '/',
                'partner_id': self.partner_id.id,
                'invoice_date': self.date,
                'move_type': 'out_invoice',
                'facility_id': self.facility_id.id,
                'invoice_line_ids': [(0, 0, line) for line in self._prepare_out_invoice_line()]
            })

        move = self.env['account.move'].search([('facility_id', '=', self.facility_id.id), ('move_type', '=', 'out_invoice')])
        self.facility_id.invoice_ids = [(6, 0, move.ids)]


    def _prepare_out_invoice_line(self):
        res = []
        for unpack in self.unit_line_ids:
            res.append({
                'product_id': unpack.unit_id.product_id.id,
                'name': unpack.unit_id.product_id.name,
                'quantity': 1,
                'price_unit': unpack.invoice_amount,
                'tax_ids': unpack.unit_id.product_id.taxes_id.ids,
                'unit_line_id': unpack.unit_line_id.id,
            })
        return res


class UnitLinesWizard(models.TransientModel):
    _name = 'unit.lines.wizard'
    _description = 'Unit Lines Wizard'

    @api.model_create_multi
    def default_get(self, fields):
        res = super(UnitLinesWizard, self).default_get(fields)
        values = self.env['res.config.settings'].default_get(list(self.env['res.config.settings'].fields_get()))
        squarefeet_pricing = values['squarefeet_pricing']
        res['squarefeet_pricing'] = squarefeet_pricing
        return res

    def _default_currency_id(self):
        return self.env.company.currency_id.id

    unit_line_id = fields.Many2one('fm.unit.lines', string='Facility Unit Line id')
    management_id = fields.Many2one('fm.management', string='Facility ID', tracking=True)
    wizard_id = fields.Many2one('invoice.wizard', string='Wizard ID', tracking=True)
    partner_id = fields.Many2one(related='wizard_id.partner_id', string='Owner', tracking=True)
    unit_id = fields.Many2one('fm.unit', string='Units', tracking=True)
    sqft_id = fields.Float(related='unit_id.sqft', string='Squarefeet', tracking=True)
    squarefeet_pricing = fields.Float(string='Squarefeet Pricing')
    total = fields.Float('Tax Excluded', compute='_compute_total', store=True, tracking=True)
    tax_ids = fields.Many2many(related='unit_id.product_id.taxes_id', string='Taxes')
    vat_amount = fields.Float('VAT Amount', compute='_compute_amount', store=True)
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self._default_currency_id())
    total_with_tax = fields.Float('Total', compute='_compute_amount', store=True, tracking=True)
    invoiced = fields.Float('Invoiced', tracking=True)
    balance_to_be_invoiced = fields.Float('Balance to Invoice', compute='_compute_balanced_invoice', store=True,
                                          copy=False, tracking=True)
    invoice_amount = fields.Float(string='Invoice Amount', store=True)

    @api.constrains('invoice_amount', 'balance_to_be_invoiced')
    def check_invoice_amount(self):
        for rec in self:
            if rec.balance_to_be_invoiced:
                if rec.invoice_amount > rec.balance_to_be_invoiced:
                    raise ValidationError('Invoice Amount should be less than or equal to Balance to Invoice Amount')

    @api.depends('tax_ids')
    def _compute_amount(self):
        for line in self:
            taxes = line.tax_ids.compute_all(**line._prepare_compute_all_values())
            line.update({
                'vat_amount': taxes['total_included'] - taxes['total_excluded'],
                'total_with_tax': taxes['total_included'],
            })

    def _prepare_compute_all_values(self):
        self.ensure_one()
        return {
            'price_unit': self.total,
            'currency': self.currency_id,
        }

    @api.depends('squarefeet_pricing', 'sqft_id')
    def _compute_total(self):
        for rec in self:
            rec.total = rec.squarefeet_pricing * rec.sqft_id

    @api.depends('total_with_tax', 'invoiced')
    def _compute_balanced_invoice(self):
        for rec in self:
            rec.balance_to_be_invoiced = rec.total_with_tax - rec.invoiced


