# -*- coding: utf-8 -*-
from datetime import date, timedelta
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError, AccessError
from dateutil.relativedelta import relativedelta
from dateutil.relativedelta import relativedelta


class RentalContract(models.Model):
    _name = 'rental.contract'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "rental.contract"
    _rec_name = "name"

    name = fields.Char(string=_("Reference"), readonly=True)
    date = fields.Date(string=_("Date"))
    user_id = fields.Many2one("res.users", string=_("Responsible"))
    partner_id = fields.Many2one("res.partner", string=_("Tenant"))
    state = fields.Selection([("draft", "Draft"), ("confirmed", "Confirmed"),
                                  ("cancel", "Canceled"),("renew", "Renewed") ,("done", "Done")], string=_("state"), default='draft')
    reservation_id = fields.Many2one("unit.reservation", string=_("Reservation"))
    date_from = fields.Date(string=_("Start Date"))
    date_to = fields.Date(string=_("End Date"))
    rental_fee = fields.Integer(string=_("Rental fee"))
    insurance_fee = fields.Integer(string=_("Insurance fee"))
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company)
    rs_project = fields.Many2one("rs.project", string=_("Project"))
    rs_project_code = fields.Char(string=_("Project Code"))
    no_of_floors = fields.Integer(string=_("Floors"))
    property_owner_id = fields.Many2one("res.partner", string=_("Project Owner"), domain="[('is_owner','=',True)]")
    region = fields.Many2one("regions", string=_("Region"))
    rs_project_unit = fields.Many2one("sub.property", string=_("Project Unit"))
    unit_code = fields.Char(string=_("Unit Code"))
    floor = fields.Char(string=_("Floor"))
    address = fields.Char(string=_("Address"))
    type = fields.Many2one("rs.project.type", string=_("Property Type"))
    status = fields.Many2one("rs.project.status", string=_("Property Status"))
    rs_project_area = fields.Integer(string=_("Project Unit Area m²"))
    rental_line_ids = fields.One2many("rental.contract.line", "rental_contract_id", string=_("Rental Contract Lines"))
    furniture_line_ids = fields.One2many("rental.contract.furniture", "contract_id", string=_("FurnitureLine"))
    rental_attachment_ids = fields.One2many("rental.contract.attachment", "rental_contract_id",
                                            string=_("Rental Attachment"))
    periodicity = fields.Selection([('days', 'Days'), ('weeks', 'Weeks'),
                                    ('months', 'Months'), ('years', 'Years'), ],
                                   string='Recurrence', required=True,
                                   help="Invoice automatically repeat at specified interval", default='months',
                                   tracking=True)
    recurring_interval = fields.Integer(string="Invoicing Period", help="Repeat every (Days/Week/Month/Year)",
                                        required=True, default=1, tracking=True)
    paid = fields.Float(compute='_check_amounts', string='Paid', )
    balance = fields.Float(compute='_check_amounts', string='Balance', )
    amount_total = fields.Float(compute='_check_amounts', string='Total', )
    boolean_make_renewed = fields.Boolean(compute='_boolean_make_renewed')
    boolean_make_done = fields.Boolean(compute='_boolean_make_done')
    property_owners_id = fields.Many2one("res.partner", string=_("Properties Owner"), domain="[('is_owner','=',True)]")
    renewed_contract_id = fields.Many2one('rental.contract', readonly=True, string="Next Contract")
    ann_inc = fields.Float(string="Anual Increase Percantage")
    duration_x = fields.Float(string="Duration")
    duration = fields.Integer()

    @api.depends('date_from', 'duration')
    def _get_end_date_(self):
        for r in self:
            if not (r.date_from and r.duration):
                r.date_to = r.date_from
                continue
            duration = timedelta(days=r.duration, seconds=-1)
            r.date_to = r.date_from + duration

    def _set_end_date(self):
        for r in self:
            if not (r.date_from and r.duration):
                continue

            r.duration = (r.date_to - r.start_borrow).days + 1

    @api.constrains('date_from', 'date_to')
    def _check_date_from_date_to(self):
        """This function,  used as an Odoo model constraint, checks that the contract's start date is before or equal to the end date, raising a validation error if the condition is not met."""
        if self.filtered(lambda d: d.date_to and d.date_from > d.date_to):
            raise ValidationError(_('Contract start date must be less than contract end date.'))

    @api.constrains('recurring_interval')
    def _check_recurring_interval(self):
        """This Odoo model constraint ensures that the 'recurring_interval' is a positive value, raising a validation error if it's less than or equal to zero."""
        for record in self:
            if record.recurring_interval <= 0:
                raise ValidationError(_("The recurring interval must be positive"))

    @api.depends('rental_line_ids', 'rental_line_ids.amount_residual')
    def _check_amounts(self):
        """This function calculates and updates the 'paid,' 'balance,' and 'amount_total' fields based on the 'rental_line_ids' and their 'amount' and 'amount_residual' values, while ensuring that these fields depend on changes in those related fields."""
        total_paid = 0
        total_unpaid = 0
        amount_total = 0
        for rec in self:
            for line in rec.rental_line_ids:
                amount_total += line.amount
                total_unpaid += line.amount_residual
                total_paid += (line.amount - line.amount_residual)

        self.paid = total_paid
        self.balance = total_unpaid
        self.amount_total = amount_total

    @api.onchange('region')
    def onchange_region(self):
        """This Odoo 'onchange' method updates the available options for the 'rs_project' field based on the selected 'region,' retrieving and filtering 'rs_project' records related to the chosen region."""
        if self.region:
            rs_project_ids = self.env['rs.project'].search([('region', '=', self.region.id)])
            rs_projects = []
            for b in rs_project_ids: rs_projects.append(b.id)
            return {'domain': {'rs_project': [('id', 'in', rs_projects)]}}

    @api.onchange('rs_project')
    def onchange_rs_project(self):
        """This Odoo 'onchange' method updates various fields, including 'rs_project_code,' 'no_of_floors,' and 'region,' based on the selected 'rs_project,' and it also filters 'rs_project' options based on the 'state' and the chosen 'rs_project.'"""
        if self.rs_project:
            units = self.env['sub.property'].search(
                [('rs_project_id', '=', self.rs_project.id), ('state', '=', 'free')])
            unit_ids = []
            for u in units: unit_ids.append(u.id)
            rs_project = self.env['rs.project'].browse(self.rs_project.id)
            code = rs_project.code
            no_of_floors = rs_project.no_of_floors
            region = rs_project.region.id
            if rs_project:
                self.rs_project_code = code
                self.region = region
                self.no_of_floors = no_of_floors
                return {'domain': {'rs_project_unit': [('id', 'in', unit_ids)]}}

    @api.onchange('rs_project_unit')
    def onchange_unit(self):
        """This 'onchange' method populates various fields based on the selected 'rs_project_unit' and constructs a 'full_address' by concatenating address components, updating multiple related fields in the process."""
        full_address = ""
        if self.rs_project_unit.street:
            full_address += self.rs_project_unit.street
        if self.rs_project_unit.street2:
            if full_address:
                full_address += ", " + self.rs_project_unit.street2
            else:
                full_address += self.rs_project_unit.street2
        if self.rs_project_unit.city:
            if full_address:
                full_address += ", " + self.rs_project_unit.city
            else:
                full_address += self.rs_project_unit.city
        if self.rs_project_unit.zip:
            if full_address:
                full_address += ", " + self.rs_project_unit.zip
            else:
                full_address += self.rs_project_unit.zip

        self.unit_code = self.rs_project_unit.code
        self.floor = self.rs_project_unit.floor
        self.type = self.rs_project_unit.ptype.id
        self.address = full_address
        self.status = self.rs_project_unit.status.id
        self.rs_project_area = self.rs_project_unit.rs_project_area
        self.rs_project = self.rs_project_unit.rs_project_id.id
        self.region = self.rs_project_unit.region.id
        self.rental_fee = self.rs_project_unit.rental_fee
        self.insurance_fee = self.rs_project_unit.insurance_fee
        self.property_owners_id = self.rs_project_unit.partner_id

    def action_confirm(self):
        """This function confirms a contract and performs various checks, updates the state of related objects, and creates payment records for the insurance fee and invoices for rental lines."""
        if not self.partner_id:
            raise UserError(_('You can not confirm a contract with no Tenant selected!'))

        if not self.rs_project_unit:
            raise UserError(_('You can not confirm a contract with no rs_project_unit selected!'))

        if not self.date_from:
            raise UserError(_('You can not confirm a contract with no start date!'))

        if not self.date_to:
            raise UserError(_('You can not confirm a contract with no end date!'))

        if self.rental_fee <= 0:
            raise UserError(_('You can not confirm a contract with no rental fee!'))

        if not self.rental_line_ids:
            raise UserError(_('You can not confirm a contract with no rental line!'))

        else:
            self.rs_project_unit.write({'state': 'on_lease'})
            self.write({'state': 'confirmed'})
            self.reservation_id.state = 'contracted'
            if self.insurance_fee:
                payment = self.env['account.payment'].create({
                    'payment_type': 'inbound',
                    'payment_method_id': self.env.ref('account.account_payment_method_manual_in').id,
                    'partner_type': 'customer',
                    'partner_id': self.partner_id.id,
                    'amount': self.insurance_fee,
                    'ref': self.name,
                })
                payment.action_post()
            for line in self.rental_line_ids:
                line.make_invoice()

    def action_mark_done(self):
        for record in self:
            if record.state == 'confirmed' and record.date_to <= fields.Date.today()and all(line.payment_state == "paid" for line in record.rental_line_ids):
                record.write({'state': 'done'})
            else:
                # Handle case when conditions are not met
                pass

    def action_cancel(self):
        """This function cancels a contract, updates the state of related rs_project units and invoices, and sets the contract's state to 'cancel.'"""
        for rec in self:
            rec.rs_project_unit.write({'state': 'free'})
            self.write({'state': 'cancel'})
        for line in self.rental_line_ids:
            line.invoice_id.button_draft()
            line.invoice_id.button_cancel()

    def calc_ann_inc(self, date_from, date_to, rental_fee, ann_inc):
        years_no = relativedelta(date_to, date_from).years
        new_rent_fee = rental_fee
        for y in range(years_no):
            new_rent_fee += (new_rent_fee * ann_inc)
        return new_rent_fee

    def action_calculate(self):
        """This function calculates rental lines based on the contract's periodicity, start and end dates, and rental fee, generating line items with appropriate dates and amounts, and then associates these lines with the contract."""
        for rec in self:
            # rec.rental_line_ids = None
            for line in rec.rental_line_ids:
                self.write({'rental_line_ids': [(2, line.id, False)]})
            rental_fee = rec.rental_fee
            inc_rate = rec.ann_inc
            rental_lines = []
            if rec.periodicity and rec.date_from and rec.date_to:
                n = 1
                date_from = rec.date_from
                date_to = rec.date_to
                new_date = date_from
                periodicity = rec.periodicity

                if periodicity == 'days':
                    total_days = (date_to - date_from).days
                    full_days = int(total_days / int(rec.recurring_interval))
                    fractional_days = round((total_days / int(rec.recurring_interval)) - full_days, 4)

                    for d in range(full_days):
                        rental_lines.append(
                            (0, 0, {
                                'serial': d,
                                'amount': rec.calc_ann_inc(rec.date_from, new_date, rental_fee,inc_rate),
                                'date': new_date,
                                'name': ('Rental Fee')
                            }))
                        d += 1
                        new_date += timedelta(days=int(rec.recurring_interval))

                    if fractional_days > 0:
                        fractional_fee = fractional_days * rec.calc_ann_inc(rec.date_from, new_date, rental_fee, inc_rate)
                        rental_lines.append(
                            (0, 0, {
                                'serial': d + 1,
                                'amount': fractional_fee,
                                'date': new_date,
                                'name': ('Rental Fee (Fractional)')
                            }))

                elif periodicity == 'weeks':
                    total_weeks = (date_to - date_from).days // 7
                    total_weeks = total_weeks / int(rec.recurring_interval)
                    full_weeks = int(total_weeks)
                    fractional_week = round(total_weeks - full_weeks, 4)

                    for w in range(full_weeks):
                        rental_lines.append(
                            (0, 0, {
                                'serial': w,
                                'amount': rec.calc_ann_inc(rec.date_from, new_date, rental_fee,inc_rate),
                                'date': new_date,
                                'name': ('Rental Fee')
                            }))
                        w += int(rec.recurring_interval)
                        new_date += timedelta(weeks=int(rec.recurring_interval))

                    if fractional_week > 0:
                        fractional_fee = fractional_week * rec.calc_ann_inc(rec.date_from, new_date, rental_fee,inc_rate) # Adjust for fractional week
                        rental_lines.append(
                            (0, 0, {
                                'serial': w+1,
                                'amount': fractional_fee,
                                'date': new_date,
                                'name': ('Rental Fee (Fractional)')
                            }))

                elif periodicity == 'months':
                    months_diff = (date_to.year - date_from.year) * 12 + date_to.month - date_from.month
                    day_from = int(date_from.strftime('%d'))
                    day_to = int(date_to.strftime('%d'))
                    total_months = months_diff
                    if day_to > day_from:
                        total_months = months_diff + round(((day_to - day_from) / 30), 4)
                    elif day_from > day_to:
                        total_months = months_diff - round(((day_from - day_to) / 30), 4)
                    total_months = total_months / int(rec.recurring_interval)
                    full_months = int(total_months)
                    fractional_months = round(total_months - full_months, 4)
                    for m in range(full_months):
                        rental_lines.append(
                            (0, 0, {
                                'serial': m,
                                'amount': rec.calc_ann_inc(rec.date_from, new_date, rental_fee,inc_rate),
                                'date': new_date,
                                'name': ('Rental Fee')
                            }))
                        m += int(rec.recurring_interval)
                        new_date += relativedelta(months=int(rec.recurring_interval))
                    if fractional_months > 0:
                        fractional_fee = fractional_months * rec.calc_ann_inc(rec.date_from, new_date, rental_fee,inc_rate)
                        rental_lines.append(
                            (0, 0, {
                                'serial': m+1,
                                'amount': fractional_fee,
                                'date': new_date,
                                'name': ('Rental Fee (Fractional)')
                            }))
                elif periodicity == 'years':
                    years_diff = (date_to.year - date_from.year) + ((date_to.month - date_from.month) / 12)
                    day_from = int(date_from.strftime('%d'))
                    day_to = int(date_to.strftime('%d'))
                    total_year = years_diff
                    if day_to > day_from:
                        total_year = years_diff + round(((day_to - day_from) / 365), 4)
                    elif day_from > day_to:
                        total_year = years_diff - round(((day_from - day_to) / 365), 4)
                    total_year = total_year / int(rec.recurring_interval)
                    int_years_diff = int(total_year)
                    fractional_years = round(total_year - int_years_diff, 4)
                    for y in range(int_years_diff):
                        rental_lines.append(
                            (0, 0, {
                                'serial': y,
                                'amount': rec.calc_ann_inc(rec.date_from, new_date, rental_fee,inc_rate),
                                'date': new_date,
                                'name': ('Rental Fee')
                            }))
                        y += int(rec.recurring_interval)
                        new_date += relativedelta(years=int(rec.recurring_interval))
                    if fractional_years > 0:
                        total_remaining_fee = fractional_years * rec.calc_ann_inc(rec.date_from, new_date, rental_fee,inc_rate)
                        rental_lines.append(
                            (0, 0, {
                                'serial': y+1,
                                'amount': total_remaining_fee,
                                'date': new_date,
                                'name': ('Rental Fee (Partial Months and Days)')
                            }))
                        n += 1
                rec.write({'rental_line_ids': rental_lines})

    @api.onchange("date_to" , "state" , "rental_line_ids.payment_state")
    def _boolean_make_done(self):
        for record in self:
            if (
                    isinstance(record.date_to, date)
                    and record.date_to <= date.today()
                    and all(line.payment_state == "paid" for line in record.rental_line_ids)
                    and record.state == 'confirmed'
            ):
                record.boolean_make_done = True
            else:
                record.boolean_make_done = False

    @api.onchange("date_to", "rental_line_ids.payment_state")
    def _boolean_make_renewed(self):
        """This 'onchange' method sets the 'boolean_make_renewed' field to 'True' if the 'date_to' matches the current date
        and all lines' 'payment_state' are 'paid'; otherwise, it sets it to 'False'."""
        for record in self:
            last_line = record.rental_line_ids[-1] if record.rental_line_ids else None
            if (
                    last_line
                    and last_line.date
                    and isinstance(last_line.date, date)
                    and last_line.date <= date.today()
                    and all(line.payment_state == "paid" for line in record.rental_line_ids)
                    and record.state == 'confirmed'
            ):
                record.boolean_make_renewed = True
            else:
                record.boolean_make_renewed = False

    def make_renewed(self):
        """This function creates a renewed rental contract, setting its state to 'renew' and populating its fields with values from the current contract, while also changing the state of the related rs_project unit to 'reserved' if applicable."""
        self.state = 'renew'
        # Calculate the new 'date_from' based on periodicity
        if self.periodicity == 'days':
            delta = timedelta(days=1)
        elif self.periodicity == 'weeks':
            delta = timedelta(weeks=1)
        elif self.periodicity == 'months':
            delta = relativedelta(months=1)
        elif self.periodicity == 'years':
            delta = relativedelta(years=1)
        else:
            # Handle an unknown periodicity (you may raise an exception, set a default, or choose another strategy)
            delta = timedelta(days=1)

        # Calculate the new 'date_from'
        if self.rental_line_ids:
            last_date = max(line.date for line in self.rental_line_ids)
            new_date_from = last_date + delta
        else:
            # Handle the case where there are no rental_line_ids
            new_date_from = date.today()
        vals = {
            'name': self.name,
            'state': 'draft',
            'date_from': new_date_from,
            'date': date.today(),
            'user_id': self.user_id.id,
            'rental_fee': self.rental_fee,
            'insurance_fee': self.insurance_fee,
            'reservation_id': self.reservation_id.id,
            'partner_id': self.partner_id.id,
            'rs_project': self.rs_project.id,
            'rs_project_code': self.rs_project_code,
            'no_of_floors': self.no_of_floors,
            'property_owner_id': self.property_owner_id.id,
            'region': self.region.id,
            'rs_project_unit': self.rs_project_unit.id,
            'unit_code': self.unit_code,
            'floor': self.floor,
            'address': self.address,
            'type': self.type.id,
            'status': self.status.id,
            'rs_project_area': self.rs_project_area,
        }
        new_rental_contract_post = self.env['rental.contract'].create(vals)
        self.renewed_contract_id = new_rental_contract_post
        if self.rs_project_unit:
            self.rs_project_unit.state = 'reserved'

        return new_rental_contract_post


    @api.model
    def create(self, vals):
        """This method creates a new rental contract by generating a unique 'name' using an Odoo sequence and then calling the superclass 'create' method to create the contract with the provided values."""
        vals['name'] = self.env['ir.sequence'].next_by_code('rental.contract')
        contract = super(RentalContract, self).create(vals)
        return contract

    def unlink(self):
        """This method allows the deletion of rental contracts in the 'draft' state, raising a user error if the contract is in any other state."""
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_('You can not delete a contract not in draft state'))
            super(RentalContract, rec).unlink()

    def make_update_furniture(self):
        """This function updates the 'furniture_line_ids' by clearing existing lines and populating it with furniture details from the selected 'rs_project_unit,' if available."""
        self.furniture_line_ids = [(5, 0, 0)]
        if self.rs_project_unit:
            furniture_lines = []
            for furniture in self.rs_project_unit.furniture_ids:
                furniture_lines.append((0, 0, {
                    'product_id': furniture.product_id.id,
                    'description': furniture.description,
                    'list_price': furniture.list_price,
                    'product_qty': furniture.product_qty,
                }))
            self.furniture_line_ids = furniture_lines

    @api.onchange('rs_project_unit')
    def _onchange_rs_project_unit(self):
        """This 'onchange' method updates the 'furniture_line_ids' by clearing existing lines and populating it with furniture details from the selected 'rs_project_unit,' if available."""
        self.furniture_line_ids = [(5, 0, 0)]
        if self.rs_project_unit:
            furniture_lines = []
            for furniture in self.rs_project_unit.furniture_ids:
                furniture_lines.append((0, 0, {
                    'product_id': furniture.product_id.id,
                    'description': furniture.description,
                    'list_price': furniture.list_price,
                    'product_qty': furniture.product_qty,
                }))
            self.furniture_line_ids = furniture_lines


class RentalContractLine(models.Model):
    _name = 'rental.contract.line'
    _description = "rental.contract.line"
    _rec_name = "name"

    date = fields.Date(string=_("Due Date"), required=True)
    name = fields.Char(string=_("Reference"), required=True)
    serial = fields.Char('#')
    amount = fields.Float(string=_("Amount"), required=True)
    amount_residual = fields.Monetary(string='Amount Due', currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', string='Currency')
    invoice_id = fields.Many2one('account.move', string='Invoice', )
    payment_state = fields.Selection(related='invoice_id.payment_state', readonly=True, store=True)
    invoice_state = fields.Selection(related='invoice_id.state', readonly=True, store=True)
    rental_contract_id = fields.Many2one("rental.contract", string=_("Rental Contract"))
    customer_id = fields.Many2one('res.partner', string="Tenant", related='rental_contract_id.partner_id', store=True)
    reference = fields.Char(string="Reference", related='rental_contract_id.name', store=True)
    make_stat_paid = fields.Boolean(compute="_compute_make_stat_paid", store=True)

    @api.depends('payment_state', 'date')
    def _compute_make_stat_paid(self):
        for rec in self:
            if rec.payment_state != "paid" and rec.date <= date.today():
                rec.make_stat_paid = True
            else:
                rec.make_stat_paid = False

    def make_invoice(self):
        """This function creates an invoice in the 'out_invoice' type, associating it with a rental contract, and populates it with relevant details, including the journal, partner, and invoice lines, then posts the invoice and links it to the rental line."""
        for rec in self:
            account_move = self.env['account.move']
            journal_pool = self.env['account.journal']
            journal = journal_pool.search([('type', '=', 'sale')], limit=1)
            account_in = int(self.env['ir.config_parameter'].sudo().get_param('nthub_realestate.rental_settlement_account'))
            if not account_in:
                raise UserError(_('Please set income account for rental from setting!'))
            invoice = account_move.create({
                'journal_id': journal.id,
                'partner_id': rec.rental_contract_id.partner_id.id,
                'move_type': 'out_invoice',
                'rental_line_id': rec.id,
                'invoice_date_due': rec.date,
                'ref': (rec.rental_contract_id.name + ' - ' + rec.name),
                'invoice_line_ids': [(0, None, {
                    'name': (rec.rental_contract_id.name + ' - ' + rec.name),
                    'quantity': 1,
                    'account_id': account_in,
                    'price_unit': rec.amount, })]
            })
            invoice.action_post()
            self.invoice_id = invoice.id

    def view_invoice(self):
        """This function retrieves and displays the invoice associated with the current rental line for viewing in the Odoo user interface."""
        move = self.env['account.move'].sudo().search([('rental_line_id', '=', self.id)])
        return {
            'name': _('Invoice'),
            'view_type': 'form',
            'res_id': move.id,
            'view_mode': 'form',
            'res_model': 'account.move',
            'type': 'ir.actions.act_window',
            'target': 'current',
        }


class RentalContractFurniture(models.Model):
    _name = 'rental.contract.furniture'
    _description = "rental contract furniture"

    product_id = fields.Many2one("product.product", string=_("Product"), domain="[('furniture', '=', True)]")
    description = fields.Char(string=_('Description'))
    list_price = fields.Float(related="product_id.list_price")
    contract_id = fields.Many2one("rental.contract")
    product_qty = fields.Integer(string=_("Quantity"), default=1)


class RentalAttachmentLine(models.Model):
    _name = 'rental.contract.attachment'
    _description = "rental.attachment.line"

    name = fields.Char(string=_("Name"))
    file = fields.Binary(string=_("File"))
    rental_contract_id = fields.Many2one("rental.contract", string=_("Rental Contract"))
