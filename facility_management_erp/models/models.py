from odoo import api, fields, models, _, tools  # type: ignore
from odoo.osv import expression  # type: ignore
from odoo.exceptions import UserError, ValidationError  # type: ignore


READONLY_STATES = {
    'draft': [('readonly', False)],
    'ongoing': [('readonly', True)],
    'completed': [('readonly', True)],
    'cancel': [('readonly', False)],
    }

class FacilityManagement(models.Model):
    _name = 'fm.management'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Facility Management'

    name = fields.Char('Facility Number', store=True, copy=False, default="Draft")
    partner_id = fields.Many2one('res.partner', string='Owner', domain=[('owner_boolean', '=', True)])
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    creation_date = fields.Date(string='Created On', default=lambda self: fields.Date.today())
    unit_line_ids = fields.One2many('fm.unit.lines', 'management_id', string='Unit Line', tracking=True, states=READONLY_STATES)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
        ('cancel', 'Cancel')
    ], default='draft', string='Status', tracking=True)
    invoice_count = fields.Integer(compute='_compute_invoice_count', string="Number of Invoices")
    payment_count = fields.Integer(compute='_compute_payment_count', string="Number of Payments")
    total = fields.Float(compute='_compute_calculation', store=True, string='Total',
                                          tracking=True)
    paid_amount = fields.Float('Paid Amount', readonly=True)
    sum_invoiced = fields.Float('Sum of Invoiced')
    balance_amount = fields.Float('Balance Amount', readonly=True)
    invoice_ids = fields.Many2many('account.move', string='Account Moves')
    is_confirmed = fields.Boolean('Is Confirmed', default=False)


    # def _compute_move_ids(self):
    #     for rec in self:
    #         move = self.env['account.move'].search([('facility_id', '=', self.id), ('move_type', '=', 'out_invoice')])
    #         print("0000", move)
    #         if move:
    #             rec.invoice_ids = move.ids
    #         rec.invoice_ids = False

    @api.depends('unit_line_ids')
    def _compute_calculation(self):
        for rec in self:
            rec.total = sum(rec.unit_line_ids.mapped('total'))

    def _compute_invoice_count(self):
        self.invoice_count = self.env['account.move'].search_count([('facility_id', '=', self.id), ('move_type', '=', 'out_invoice')])

    def _compute_payment_count(self):
        self.payment_count = self.env['account.payment'].search_count([('facility_id', '=', self.id)])

    def confirm_facility_button(self):
        self.is_confirmed = True
        vals = {'state': 'ongoing'}
        if self.name == 'Draft':
            code = self.env['ir.sequence'].next_by_code('facility.code')
            vals['name'] = code
        self.update(vals)

    def done_button(self):
        vals = {'state': 'completed'}
        self.update(vals)

    def cancel_button(self):
        vals = {'state': 'cancel'}
        self.update(vals)

    def set_to_draft_button(self):
        vals = {'state': 'draft'}
        self.update(vals)

    def button_to_create_invoice(self):
        view_id = self.env.ref('facility_management_erp.invoice_create_wizard_view').id
        return {
            'name': _('Create Invoice'),
            'view_type': 'form',
            'view_mode': 'form',
            'views': [(view_id, 'form')],
            'res_model': 'invoice.wizard',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {
                'default_partner_id': self.partner_id.id,
                'default_facility_id': self.id,
                'default_unit_line_ids': [(0, 0, line) for line in self._prepare_unit_line()]

            },
        }
    def _prepare_unit_line(self):
        res = []
        for unpack in self.unit_line_ids:
            res.append({
                'unit_id': unpack.unit_id.id,
                'sqft_id': unpack.sqft_id,
                'squarefeet_pricing': unpack.squarefeet_pricing,
                'total': unpack.total,
                'invoiced': unpack.invoiced,
                'balance_to_be_invoiced': unpack.balance_to_be_invoiced,
                'invoice_amount': unpack.invoice_amount,
                'unit_line_id': unpack.id
            })
        return res

    def button_to_update_payment_summary(self):
        sum_inv = 0.00
        payment_ids = self.env['account.payment'].search([('facility_id', '=', self.id)])
        unit_ids = self.env['fm.unit.lines'].search([('management_id', '=', self.id)])
        for u in unit_ids:
            sum_inv += u.invoiced
        self.sum_invoiced = sum_inv
        payment_sum = 0.00
        if payment_ids:
            for p in payment_ids:
                payment_sum += float(p.amount)
            self.paid_amount = payment_sum
            self.balance_amount = self.sum_invoiced - self.paid_amount

    def open_related_invoices(self):
        account_ids = self.env['account.move'].search([('facility_id', '=', self.id)])
        # self.invoice_ids = account_ids
        action = self.env['ir.actions.act_window']._for_xml_id('account.action_move_out_invoice_type')
        action['domain'] = [('id', 'in', account_ids.ids), ('move_type', '=', 'out_invoice')]
        action['context'] = dict(create=False)
        return action

    def open_related_payments(self):
        payment_ids = self.env['account.payment'].search([('facility_id', '=', self.id)])
        action = self.env['ir.actions.act_window']._for_xml_id('account.action_account_payments')
        action['domain'] = [('id', 'in', payment_ids.ids)]
        action['context'] = dict(create=False)
        return action


class UnitLines(models.Model):
    _name = 'fm.unit.lines'
    _description = 'Facility Unit Lines'

    @api.model_create_multi
    def default_get(self, fields):
        res = super(UnitLines, self).default_get(fields)
        values = self.env['res.config.settings'].default_get(list(self.env['res.config.settings'].fields_get()))
        squarefeet_pricing = values['squarefeet_pricing']
        res['squarefeet_pricing'] = squarefeet_pricing
        return res

    def _default_currency_id(self):
        return self.env.company.currency_id.id

    management_id = fields.Many2one('fm.management', string='Facility ID', tracking=True)
    partner_id = fields.Many2one(related='management_id.partner_id', string='Owner', tracking=True)
    unit_id = fields.Many2one('fm.unit', string='Units', tracking=True)
    sqft_id = fields.Float(related='unit_id.sqft', string='Squarefeet', tracking=True)
    squarefeet_pricing = fields.Float(string='Squarefeet Pricing')
    total = fields.Float('Tax Excluded', compute='_compute_total', store=True, tracking=True)
    tax_ids = fields.Many2many(related='unit_id.product_id.taxes_id', string='Taxes')
    vat_amount = fields.Float('VAT Amount', compute='_compute_amount', store=True)
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self._default_currency_id())
    total_with_tax = fields.Float('Total', compute='_compute_amount', store=True, tracking=True)
    invoiced = fields.Float('Invoiced', compute='_compute_total_amount_invoiced', store=True, tracking=True)
    balance_to_be_invoiced = fields.Float('Balance to Invoice', compute='_compute_balanced_invoice', store=True, copy=False, tracking=True)
    # collected_amount = fields.Float('Collected Amount', tracking=True)
    # total_due = fields.Float('Total Due', compute='_compute_total_due', store=True, tracking=True)
    invoice_amount = fields.Float(string='Invoice Amount', store=True)
    invoice_line_ids = fields.Many2many(comodel_name='account.move.line', relation='unit_line_ids_invoice_line_ids_rel', column1='unit_line_ids', column2='invoice_line_ids', compute='_compute_invoice_line_ids', store=True, readonly=False, string="Invoice Lines", copy=False)
    product_uom = fields.Many2one(comodel_name='uom.uom', string="Unit of Measure", compute='_compute_product_uom', store=True, readonly=False, precompute=True, ondelete='restrict')

    @api.depends('management_id.invoice_ids')
    def _compute_invoice_line_ids(self):
        for record in self:
            line_list = []
            if record.management_id.invoice_ids:
                for u in record.management_id.invoice_ids:
                    for line in u.invoice_line_ids:
                        line_list.append(line)
                        print("lllllllll", line_list)

            else:
                record.invoice_line_ids = False

    # @api.depends('management_id.invoice_ids')
    # def _compute_invoice_line_ids(self):
    #     for record in self:
    #         if record.management_id.invoice_ids:
    #             for u in record.management_id.invoice_ids:
    #                 for line in u.invoice_line_ids:
    #                     line_list = []
    #                     if record.unit_id.product_id.id == line.product_id.id:
    #                         line_list.append(line.id)
    #                         print("if line list", line_list)
    #                         record.invoice_line_ids = line_list
    #                         print("rrrrrrrrrrrrrrrrrrr", record.invoice_line_ids)
    #                     else:
    #                         print("else line list", line.id)
    #         else:
    #             record.invoice_line_ids = False


    @api.depends('unit_id.product_id')
    def _compute_product_uom(self):
        for line in self:
            if not line.product_uom or (line.unit_id.product_id.uom_id.id != line.product_uom.id):
                line.product_uom = line.unit_id.product_id.uom_id


    @api.depends('invoice_line_ids.price_total')
    def _compute_total_amount_invoiced(self):
        for line in self:
            invoiced = 0.0
            for invoice_line in line._get_invoice_lines():
                if invoice_line.move_id.state != 'cancel' and invoice_line.move_id.move_type == 'out_invoice':
                    invoiced += invoice_line.product_uom_id._compute_quantity(invoice_line.price_total, line.product_uom)
            line.invoiced = invoiced

    def _get_invoice_lines(self):
        self.ensure_one()
        return self.invoice_line_ids

# _sql_constraints = [('unique_unit_id', 'unique(unit_id)', "This Unit is already chosen !")]

    # @api.constrains('invoiced', 'total_with_tax')
    # def check_invoice_amount(self):
    #     for rec in self:
    #         if rec.invoiced and rec.total_with_tax:
    #             if rec.invoiced > rec.total_with_tax:
    #                 raise ValidationError('Invoice Amount should be less than or equal to Balance to Invoice Amount')

    # @api.constrains('invoice_amount')
    # def check_invoice_amount(self):
    #     for rec in self:
    #         if rec.balance_to_be_invoiced:
    #             if rec.invoice_amount > rec.balance_to_be_invoiced:
    #                 raise ValidationError('Invoice Amount should be less than or equal to Balance to Invoice Amount')


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

    @api.depends('squarefeet_pricing','sqft_id')
    def _compute_total(self):
        for rec in self:
            rec.total = rec.squarefeet_pricing * rec.sqft_id

    @api.depends('total_with_tax', 'invoiced')
    def _compute_balanced_invoice(self):
        for rec in self:
            rec.balance_to_be_invoiced = rec.total_with_tax - rec.invoiced


    # @api.depends('collected_amount', 'invoiced')
    # def _compute_total_due(self):
    #     for rec in self:
    #         rec.total_due = rec.invoiced - rec.collected_amount


class ResPartner(models.Model):
    _inherit = 'res.partner'

    customer_boolean = fields.Boolean('Customer', default=False)
    owner_boolean = fields.Boolean('Owner', default=False)

class AccountMove(models.Model):
    _inherit = 'account.move'

    facility_id = fields.Many2one('fm.management', string='Facility ID', tracking=True, readonly=True)

    def action_register_payment(self):
        res = super(AccountMove,self).action_register_payment()
        res['context'] = {
            'active_model': 'account.move',
            'active_ids': self.ids,
            'default_facility_id': self.facility_id.id,
        }
        return res

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    unit_line_id = fields.Many2one('fm.unit.lines', string='Facility Unit Line id')
    fm_unit_line_ids = fields.Many2many('fm.unit.lines', 'unit_line_ids_invoice_line_ids_rel', 'invoice_line_ids', 'unit_line_ids', compute='_compute_fm_unit_line_ids', store=True, string='Unit Lines', readonly=True, copy=False)

    @api.depends('unit_line_id')
    def _compute_fm_unit_line_ids(self):
        for rec in self:
            rec.fm_unit_line_ids = False
            if rec.unit_line_id:
                rec.fm_unit_line_ids = [rec.unit_line_id.id]
                # rec.unit_line_id.invoice_line_ids = self

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    facility_id = fields.Many2one('fm.management', string='Facility ID', tracking=True, readonly=True)

class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    facility_id = fields.Many2one('fm.management', string='Facility ID', tracking=True, readonly=True)

    # def action_create_payments(self):
    #     payments = self._create_payments()
    #     res = super(AccountPaymentRegister,self).action_create_payments()
    #     if self.facility_id:
    #         acc_payment = self.env['account.payment'].search([('id', 'in', payments.ids)])
    #         print("accccc", acc_payment)
    #     return res
