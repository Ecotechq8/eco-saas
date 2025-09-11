from odoo import fields, models, api, _
from odoo.exceptions import ValidationError, UserError
from contextlib import contextmanager
from odoo.tools import format_amount

class AccountMove(models.Model):
    _inherit = 'account.move'

    is_subcontracting = fields.Boolean(
        string='Is Subcontracting',
        readonly=True)
    adv_percent = fields.Float(string='Advanced Percent %', )
    retention_percent = fields.Float(string='Retention Percent %')
    adv_amount = fields.Float(string='Adv_amount', compute='_compute_adv_amount',store=True)
    retention_amount = fields.Float(string='Adv_amount', compute='_compute_retention_amount',store=True)
    guarantee_letter_id = fields.Many2one('guarantee.letter',string='Guarantee letter',copy=False)
    from_date = fields.Date(string='From Date', required=False)
    to_date = fields.Date(string='To Date', required=False)
    project_id = fields.Many2one('project.project', string='Project ',readonly=True)
    @api.depends('amount_untaxed', 'adv_percent')
    def _compute_adv_amount(self):
        for rec in self:
            rec.adv_amount = 0.0
            if rec.adv_percent > 0:
                rec.adv_amount = rec.amount_untaxed * (rec.adv_percent / 100)

    @api.depends('amount_untaxed', 'retention_percent')
    def _compute_retention_amount(self):
        for rec in self:
            rec.retention_amount = 0.0
            if rec.retention_percent > 0:
                rec.retention_amount = rec.amount_untaxed * (rec.retention_percent / 100)


    def action_post(self):
        for move in self.filtered(lambda m: m.state == 'draft' and m.is_invoice(include_receipts=True) and m.is_subcontracting):
                # 1. Get existing receivable lines
                receivable_lines = move.line_ids.filtered(lambda l: l.account_type == 'asset_receivable')
                receivable_lines.unlink()


                # 2. Extract values from the original line
                currency = move.currency_id or move.company_currency_id
                total_debit = move.amount_untaxed

                if total_debit > 0:
                    # 3. Split amount into two equal parts (with proper rounding)
                    amount1 = currency.round(total_debit) - (move.adv_amount + move.retention_amount)
                    adv_amount = currency.round(move.adv_amount)  # Ensures sum matches original
                    retention_amount = currency.round(move.retention_amount)  # Ensures sum matches original
                    # 4. Create two new lines to replace the original
                    self.env['account.move.line'].create([
                        {
                            'move_id': move.id,
                            'account_id': move.partner_id.property_account_receivable_id.id,
                            'partner_id': move.partner_id.id,
                            'name': move.name or '',
                            'debit': amount1,
                            'credit': 0.0,
                            'currency_id': move.currency_id.id,
                            'amount_currency': amount1,
                            # 'date_maturity': line.date_maturity,
                        },
                        {
                            'move_id': move.id,
                            'account_id': move.partner_id.adv_customer.id,
                            'partner_id': move.partner_id.id,
                            'name': _('Advanced Payment'),
                            'debit': adv_amount,
                            'credit': 0.0,
                            'currency_id': move.currency_id.id,
                            'amount_currency': adv_amount,
                            # 'date_maturity': line.date_maturity,
                        },
                        {
                            'move_id': move.id,
                            'account_id': move.partner_id.customer_retention.id,
                            'partner_id': move.partner_id.id,
                            'name': _('Retention Amount'),
                            'debit': retention_amount,
                            'credit': 0.0,
                            'currency_id': move.currency_id.id,
                            'amount_currency': retention_amount,
                            # 'date_maturity': line.date_maturity,
                        }
                    ])
                    # 5. Remove the original line to avoid duplication

            # 6. Post the move using standard logic
        return super(AccountMove, self).action_post()

    @contextmanager
    def _check_balanced(self, container):
        ''' Assert the move is fully balanced debit = credit.
        An error is raised if it's not the case.
        '''
        with self._disable_recursion(container, 'check_move_validity', default=True, target=False) as disabled:
            yield
            if disabled:
                return

        unbalanced_moves = self._get_unbalanced_moves(container)
        if unbalanced_moves and not self.is_subcontracting:
            error_msg = _("An error has occurred.")
            for move_id, sum_debit, sum_credit in unbalanced_moves:
                move = self.browse(move_id)
                error_msg += _(
                    "\n\n"
                    "The move (%s) is not balanced.\n"
                    "The total of debits equals %s and the total of credits equals %s.\n"
                    "You might want to specify a default account on journal \"%s\" to automatically balance each move.",
                    move.display_name,
                    format_amount(self.env, sum_debit, move.company_id.currency_id),
                    format_amount(self.env, sum_credit, move.company_id.currency_id),
                    move.journal_id.name)
            raise UserError(error_msg)
class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    @api.depends('contract_qty', 'quantity')
    def _compute_progeres(self):
        for line in self:
            line.progeres = (line.quantity / line.contract_qty) * 100 if line.contract_qty else 0.0

    @api.depends('contract_qty', 'last_qty')
    def _compute_last_progeres(self):
        for line in self:
            line.last_progeres = (line.last_qty / line.contract_qty) * 100 if line.contract_qty else 0.0

    @api.depends('contract_qty', 'total_qty')
    def _compute_total_progeres(self):
        for line in self:
            line.total_progeres = (line.total_qty / line.contract_qty) * 100 if line.contract_qty else 0.0

    contract_qty = fields.Float(string='Contract QTY')
    progeres = fields.Float(string='Progeres %', compute='_compute_progeres', store=True, precompute=True)
    last_qty = fields.Float(string='Last QTY')
    last_progeres = fields.Float(string='Last Progeres %', compute='_compute_last_progeres', store=True,
                                 precompute=True)
    total_qty = fields.Float(string='Total QTY')
    total_progeres = fields.Float(string='Total Progeres %', compute='_compute_total_progeres', store=True,
                                  precompute=True)

    @api.ondelete(at_uninstall=False)
    def _prevent_automatic_line_deletion(self):
        if not self.env.context.get('dynamic_unlink'):
            pass
            # for line in self:
            #     if line.display_type == 'tax' and line.move_id.line_ids.tax_ids:
            #         raise ValidationError(_(
            #             "You cannot delete a tax line as it would impact the tax report"
            #         ))
            #     if line.display_type == 'payment_term':
            #         raise ValidationError(_(
            #             "You cannot delete a payable/receivable line as it would not be consistent "
            #             "with the payment terms"
            #         ))
