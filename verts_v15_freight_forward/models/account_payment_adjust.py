from odoo import api, fields, models, _
from odoo.exceptions import UserError
from . import convert_number_to_word


class AccountPaymentInvoices(models.Model):
    _name = 'account.payment.invoice'

    invoice_id = fields.Many2one('account.move', string='Invoice')
    payment_id = fields.Many2one('account.payment', string='Payment')
    currency_id = fields.Many2one(related='invoice_id.currency_id')
    origin = fields.Char(related='invoice_id.invoice_origin')
    date_invoice = fields.Date(related='invoice_id.invoice_date')
    date_due = fields.Date(related='invoice_id.invoice_date_due')
    payment_state = fields.Selection(related='payment_id.state', store=True)
    reconcile_amount = fields.Monetary(string='Reconcile Amount')
    amount_total = fields.Monetary(related="invoice_id.amount_total")
    residual = fields.Monetary(related="invoice_id.amount_residual")
    is_select = fields.Boolean()
    is_reconciled = fields.Boolean()


class AccountPaymentAdjusted(models.Model):
    _name = 'account.payment.adjusted'

    invoice_id = fields.Many2one('account.move', string='Invoice')
    payment_id = fields.Many2one('account.payment', string='Payment')
    currency_id = fields.Many2one('res.currency')
    origin = fields.Char()
    date_invoice = fields.Date()
    date_due = fields.Date()
    reconcile_amount = fields.Monetary(string='Reconcile Amount')
    partial_id = fields.Many2one('account.partial.reconcile')


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    invoice_id = fields.Many2one('account.move', string='Invoice')
    price_unit = fields.Monetary(string='Price Unit', currency_field='currency_id')


    def reconcile(self):
        ''' Reconcile the current move lines all together.
        :return: A dictionary representing a summary of what has been done during the reconciliation:
                * partials:             A recorset of all account.partial.reconcile created during the reconciliation.
                * full_reconcile:       An account.full.reconcile record created when there is nothing left to reconcile
                                        in the involved lines.
                * tax_cash_basis_moves: An account.move recordset representing the tax cash basis journal entries.
        '''
        results = {}

        if not self:
            return results

        # List unpaid invoices
        not_paid_invoices = self.move_id.filtered(
            lambda move: move.is_invoice(include_receipts=True) and move.payment_state not in ('paid', 'in_payment')
        )

        # ==== Check the lines can be reconciled together ====
        company = None
        account = None
        # print("===self==", self)
        for line in self:
            if line.reconciled:
                raise UserError(_("You are trying to reconcile some entries that are already reconciled."))
            if not line.account_id.reconcile and line.account_id.account_type != 'asset_cash':
                raise UserError(_("Account %s does not allow reconciliation. First change the configuration of this account to allow it.")
                                % line.account_id.display_name)
            if line.move_id.state != 'posted':
                raise UserError(_('You can only reconcile posted entries.'))
            if company is None:
                company = line.company_id
            elif line.company_id != company:
                raise UserError(_("Entries doesn't belong to the same company: %s != %s")
                                % (company.display_name, line.company_id.display_name))
            if account is None:
                account = line.account_id
            elif line.account_id != account:
                raise UserError(_("Entries are not from the same account: %s != %s")
                                % (account.display_name, line.account_id.display_name))

        sorted_lines = self.sorted(key=lambda line: (line.date_maturity or line.date, line.currency_id))

        # ==== Collect all involved lines through the existing reconciliation ====

        involved_lines = sorted_lines
        involved_partials = self.env['account.partial.reconcile']
        current_lines = involved_lines
        current_partials = involved_partials
        while current_lines:
            current_partials = (current_lines.matched_debit_ids + current_lines.matched_credit_ids) - current_partials
            involved_partials += current_partials
            current_lines = (current_partials.debit_move_id + current_partials.credit_move_id) - current_lines
            involved_lines += current_lines

        # ==== Create partials ====

        partial_amount = self.env.context.get('amount', False)
        if partial_amount:
            reconcile = sorted_lines._prepare_reconciliation_partials()
            if reconcile:
                reconcile[0].update({
                    'amount': partial_amount, 
                    'debit_amount_currency': partial_amount, 
                    'credit_amount_currency': partial_amount,
                })
        else:
            reconcile = sorted_lines._prepare_reconciliation_partials()
        # print('----->>>>>reconcile------',reconcile)
        partials = self.env['account.partial.reconcile'].create(reconcile)
        # Track newly created partials.
        results['partials'] = partials
        involved_partials += partials

        # ==== Create entries for cash basis taxes ====

        is_cash_basis_needed = account.account_type in ('asset_receivable', 'liability_payable')
        if is_cash_basis_needed and not self._context.get('move_reverse_cancel'):
            tax_cash_basis_moves = partials._create_tax_cash_basis_moves()
            results['tax_cash_basis_moves'] = tax_cash_basis_moves

        # ==== Check if a full reconcile is needed ====

        if involved_lines[0].currency_id and all(line.currency_id == involved_lines[0].currency_id for line in involved_lines):
            is_full_needed = all(line.currency_id.is_zero(line.amount_residual_currency) for line in involved_lines)
        else:
            is_full_needed = all(line.company_currency_id.is_zero(line.amount_residual) for line in involved_lines)
        if is_full_needed:

            # ==== Create the exchange difference move ====

            if self._context.get('no_exchange_difference'):
                exchange_move = None
            else:
                exchange_move = involved_lines._create_exchange_difference_move()
                if exchange_move:
                    exchange_move_lines = exchange_move.line_ids.filtered(lambda line: line.account_id == account)

                    # Track newly created lines.
                    involved_lines += exchange_move_lines

                    # Track newly created partials.
                    exchange_diff_partials = exchange_move_lines.matched_debit_ids \
                                             + exchange_move_lines.matched_credit_ids
                    involved_partials += exchange_diff_partials
                    results['partials'] += exchange_diff_partials

                    exchange_move._post(soft=False)

            # ==== Create the full reconcile ====

            results['full_reconcile'] = self.env['account.full.reconcile'].create({
                'exchange_move_id': exchange_move and exchange_move.id,
                'partial_reconcile_ids': [(6, 0, involved_partials.ids)],
                'reconciled_line_ids': [(6, 0, involved_lines.ids)],
            })

        # Trigger action for paid invoices
        not_paid_invoices\
            .filtered(lambda move: move.payment_state in ('paid', 'in_payment'))\
            .action_invoice_paid()

        return results


class AccountMove(models.Model):
    _inherit = 'account.move'


    def update_all_adjustment(self, partial_id):
        self.payment_id.update_adjust_amount()
        adjusted_invoice_ids = self.payment_id.adjusted_invoice_ids.filtered(lambda r:r.partial_id.id == partial_id)
        adjusted_invoice_ids.unlink()

    def js_remove_outstanding_partial(self, partial_id):
        ''' Called by the 'payment' widget to remove a reconciled entry to the present invoice.

        :param partial_id: The id of an existing partial reconciled with the current invoice.
        '''
        self.update_all_adjustment(partial_id)
        return super(AccountMove, self).js_remove_outstanding_partial(partial_id)

    def payments_widget_to_reconcile(self):
        for move in self:
            pay_term_lines = move.line_ids\
                .filtered(lambda line: line.account_id.account_type in ('asset_receivable', 'liability_payable'))
            domain = [
                ('account_id', 'in', pay_term_lines.account_id.ids),
                ('parent_state', '=', 'posted'),
                ('partner_id', '=', move.commercial_partner_id.id),
                ('payment_id', '=', move.payment_id.id),
            ]
            if move.is_inbound():
                domain.append(('balance', '<', 0.0))
            else:
                domain.append(('balance', '>', 0.0))        
            amount_totals = 0
            for line in self.env['account.move.line'].search(domain):

                if line.currency_id == move.currency_id:
                    # Same foreign currency.
                    amount = abs(line.amount_residual_currency)
                else:
                    # Different foreign currencies.
                    amount = move.company_currency_id._convert(
                        abs(line.amount_residual),
                        move.currency_id,
                        move.company_id,
                        line.date,
                    )

                amount_totals += amount
            return amount_totals


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    payment_invoice_ids = fields.One2many('account.payment.invoice', 'payment_id', string="Customer Invoices")
    adjusted_invoice_ids = fields.One2many('account.payment.adjusted', 'payment_id', string="Customer Invoices")
    unadjust_amount = fields.Float(string="Unadjust Amount", compute="update_adjust_amount", store=True)
    adjusted_amount = fields.Float(string="Adjusted Amount", compute="update_adjust_amount", store=True)
    issued_by = fields.Many2one('res.users', string='Issued By', readonly=True)
    prepared_on = fields.Datetime(string='Prepared On', readonly=True)
    is_cheque = fields.Boolean(string='Payment by Cheque?')
    cheque_number = fields.Char(string='Cheque Number')
    cheque_date = fields.Date(string='Cheque Date')
    drawn_on = fields.Char(string='Drawn On')

    def _get_amount_in_words(self):
        self.ensure_one()
        wGenerator = convert_number_to_word.Number2Words()
        amt_en = wGenerator.convertNumberToWords(
            round(self.amount), self.currency_id)
        return convert_number_to_word.textwrap.fill(amt_en, 50)

    def action_post(self):
        res = super(AccountPayment, self).action_post()
        for payment in self:
            payment.issued_by = self.env.user
            payment.prepared_on = fields.Datetime.now()
        return res

    def print_payment_receipt(self):
        self.ensure_one()
        return self.env.ref('verts_v15_freight_forward.payment_receipt_report_id').report_action(self)

    def print_payment_voucher(self):
        self.ensure_one()
        return self.env.ref('verts_v15_freight_forward.payment_voucher_report_id').report_action(self)

    @api.depends('adjusted_invoice_ids', 'payment_invoice_ids', 'move_id', 'reconciled_bill_ids')
    def update_adjust_amount(self):
        for payment in self:
            # For Unadjusted Amount
            unadjust = payment.move_id.payments_widget_to_reconcile()
            payment.unadjust_amount = unadjust
            # For Adjusted Amount
            adjusted = sum(payment.adjusted_invoice_ids.mapped('reconcile_amount'))
            payment.adjusted_amount = adjusted

    def get_vendor_invoices(self):
        self.payment_invoice_ids = [(6, 0, [])]
        if self.payment_type in ['inbound', 'outbound'] and self.partner_type and self.partner_id and self.currency_id:
            if self.payment_type == 'inbound' and self.partner_type == 'customer':
                invoice_type = 'out_invoice'
            elif self.payment_type == 'outbound' and self.partner_type == 'customer':
                invoice_type = 'out_refund'
            elif self.payment_type == 'outbound' and self.partner_type == 'supplier':
                invoice_type = 'in_invoice'
            else:
                invoice_type = 'in_refund'
            invoice_recs = self.env['account.move'].search([
                ('partner_id', 'child_of', self.partner_id.id), 
                ('state', '=', 'posted'), 
                ('move_type', '=', invoice_type), 
                ('payment_state', '!=', 'paid'), 
                ('currency_id', '=', self.currency_id.id)])
            payment_invoice_values = []
            for invoice_rec in invoice_recs:
                payment_invoice_values.append([0, 0, {'invoice_id': invoice_rec.id}])
            self.payment_invoice_ids = payment_invoice_values

    def adjust_manual(self):
        for payment in self:
            payment_invoice_ids = payment.payment_invoice_ids.filtered(lambda r:r.is_select and not r.is_reconciled)
            if payment_invoice_ids:
                if payment.amount < sum(payment_invoice_ids.mapped('reconcile_amount')):
                    raise UserError(_("The sum of the reconcile amount of listed invoices are greater than payment's amount...!"))
                if payment.unadjust_amount != 0.0:
                    if payment.unadjust_amount < sum(payment_invoice_ids.mapped('reconcile_amount')):
                        raise UserError(_("The sum of the reconcile amount of listed invoices are greater than payment's unadjust amount...!"))
                if payment.adjusted_amount == payment.amount:
                    raise UserError(_("Adjust amount limit exceeded...!"))
            else:
                raise UserError(_("You have to select invoice line to reconcile...!"))

            flag = False
            for line_id in payment_invoice_ids:
                if not line_id.reconcile_amount:
                    continue
                if line_id.residual >= line_id.reconcile_amount:
                    self.ensure_one()
                    partial_id = []
                    if payment.payment_type == 'inbound':
                        lines = payment.move_id.line_ids.filtered(lambda line: line.credit > 0)
                        lines += line_id.invoice_id.line_ids.filtered(lambda line: line.account_id == lines[0].account_id and not line.reconciled)
                        reconcile = lines.with_context(amount=line_id.reconcile_amount).reconcile()
                        if reconcile:
                            if reconcile.get('partials'):
                                partial_id.append(reconcile.get('partials').id)
                    elif payment.payment_type == 'outbound':
                        lines = payment.move_id.line_ids.filtered(lambda line: line.debit > 0)
                        lines += line_id.invoice_id.line_ids.filtered(lambda line: line.account_id == lines[0].account_id and not line.reconciled)
                        reconcile = lines.with_context(amount=line_id.reconcile_amount).reconcile()
                        if reconcile:
                            if reconcile.get('partials'):
                                partial_id.append(reconcile.get('partials').id)
                    line_id.write({
                        'is_reconciled' : True
                        })
                    self.env['account.payment.adjusted'].create({
                            'invoice_id': line_id.invoice_id.id,
                            'partial_id': partial_id[0],
                            'payment_id': line_id.payment_id.id,
                            'currency_id': line_id.currency_id.id,
                            'origin' : line_id.origin,
                            'date_invoice' : line_id.date_invoice,
                            'date_due' : line_id.date_due,
                            'reconcile_amount' : line_id.reconcile_amount,
                        })
                    unadjust = payment.move_id.payments_widget_to_reconcile()
                    self.unadjust_amount = unadjust
                    self.adjusted_amount += line_id.reconcile_amount
                    flag = True
                else:
                    raise UserError(_("reconcile amount can't be greater then due amount...!"))
            if flag:
                payment.get_vendor_invoices()
                return {
                    'effect': {
                        'type': 'rainbow_man',
                        'message': _("Amount successfully adjusted....!"),
                    }
               }


