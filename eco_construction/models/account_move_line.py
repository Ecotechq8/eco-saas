from odoo import fields, models, api, _
from odoo.exceptions import ValidationError, UserError
from contextlib import contextmanager
from odoo.tools import format_amount


class AccountMove(models.Model):
    _inherit = 'account.move'

    allow_construction = fields.Boolean(compute='_compute_allow_construction')

    def _compute_allow_construction(self):
        for rec in self:
            rec.allow_construction = False
            if rec.company_id.is_construction:
                rec.allow_construction = True
            elif rec.partner_id.is_construction:
                rec.allow_construction = True

    @api.onchange('partner_id')
    def _onchange_partner_id_construction_accounts(self):
        if self.partner_id:
            self.adv_customer = self.partner_id.adv_customer
            self.customer_retention = self.partner_id.customer_retention

    adv_customer = fields.Many2one('account.account', string='Advanced Customer',
                                   domain="[('account_type', '=', 'asset_receivable'), ('deprecated', '=', False)]")
    customer_retention = fields.Many2one('account.account', string='Customer Retention',
                                         domain="[('account_type', '=', 'asset_receivable'), ('deprecated', '=', False)]")

    is_subcontracting = fields.Boolean(string='Is Subcontracting', readonly=True)
    adv_percent = fields.Float(string='Advanced Percent %', )
    retention_percent = fields.Float(string='Retention Percent %')
    adv_amount = fields.Float(string='Adv_amount', compute='_compute_adv_amount', store=True)
    retention_amount = fields.Float(string='Adv_amount', compute='_compute_retention_amount', store=True)
    guarantee_letter_id = fields.Many2one('guarantee.letter', string='Guarantee letter', copy=False)
    from_date = fields.Date(string='From Date', required=False)
    to_date = fields.Date(string='To Date', required=False)
    project_id = fields.Many2one('project.project', string='Project ', readonly=True)

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
        for move in self:
            partner = move.partner_id

            if move.company_id.is_construction and move.move_type == 'out_invoice':
                if not move.adv_customer or not move.customer_retention:
                    raise UserError(_(
                        "Construction customer is missing required accounts on the invoice:\n"
                        "- Advance Customer Account\n"
                        "- Customer Retention Account\n\n"
                        "Please fill these fields in the 'Other Info' or relevant section before confirming the invoice."
                    ))

        for move in self.filtered(
                lambda m: m.state == 'draft' and m.is_invoice(
                    include_receipts=True) and m.is_subcontracting and m.company_id.is_construction):

            receivable_lines = move.line_ids.filtered(lambda l: l.account_type == 'asset_receivable')
            receivable_lines.unlink()

            currency = move.currency_id or move.company_currency_id
            total_debit = move.amount_total

            if total_debit > 0 and move.move_type == 'out_invoice':
                amount1 = currency.round(total_debit) - (move.adv_amount + move.retention_amount)
                adv_amount = currency.round(move.adv_amount)
                retention_amount = currency.round(move.retention_amount)

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
                    },
                    {
                        'move_id': move.id,
                        'account_id': move.adv_customer.id,
                        'partner_id': move.partner_id.id,
                        'name': _('Advanced Payment'),
                        'debit': adv_amount,
                        'credit': 0.0,
                        'currency_id': move.currency_id.id,
                        'amount_currency': adv_amount,
                    },
                    {
                        'move_id': move.id,
                        'account_id': move.customer_retention.id,
                        'partner_id': move.partner_id.id,
                        'name': _('Retention Amount'),
                        'debit': retention_amount,
                        'credit': 0.0,
                        'currency_id': move.currency_id.id,
                        'amount_currency': retention_amount,
                    }
                ])

        # Final: Post move
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
    progeres = fields.Float(string='Progress %', compute='_compute_progeres', store=True, precompute=True)
    last_qty = fields.Float(string='Last QTY')
    last_progeres = fields.Float(string='Last Progeres %', compute='_compute_last_progeres', store=True,
                                 precompute=True)
    total_qty = fields.Float(string='Total QTY')
    total_progeres = fields.Float(string='Total Progeres %', compute='_compute_total_progeres', store=True,
                                  precompute=True)

    task_id = fields.Many2one(
        comodel_name='project.task',
        string='Task',
        domain="[('project_id', 'in', available_project_ids)]",
    )

    available_project_ids = fields.Many2many(
        comodel_name='project.project',
        string='Available Projects',
        compute='_compute_available_projects',
        store=False
    )

    @api.depends('analytic_distribution')
    def _compute_available_projects(self):
        for move in self:
            projects = self.env['project.project']
            if move.analytic_distribution:
                for a in move.analytic_distribution.keys():
                    analytic_ids = str(a).split(',')
                    analytics = self.env['account.analytic.account'].browse([int(s) for s in analytic_ids])
                    projects = analytics.mapped('project_ids')
            move.available_project_ids = projects

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

    @api.constrains('debit', 'task_id')
    def _check_task_budget_journal(self):
        for line in self:
            if line.task_id and line.move_id.state == 'posted':
                budget_line = self.env['budget.line'].search([
                    ('task_id', '=', line.task_id.id)
                ], limit=1)

                if budget_line:
                    po_spent = sum(self.env['purchase.order.line'].search([
                        ('task_id', '=', line.task_id.id),
                        ('order_id.state', 'in', ['purchase', 'done'])
                    ]).mapped('price_unit'))

                    journal_spent = sum(self.env['account.move.line'].search([
                        ('task_id', '=', line.task_id.id),
                        ('move_id.state', '=', 'posted')
                    ]).mapped(lambda l: l.debit))

                    total_spent = po_spent + journal_spent

                    if total_spent > budget_line.budget_amount:
                        raise UserError(_(
                            "Budget exceeded for task %s.\n"
                            "Budget: %s\nSpent: %s"
                        ) % (line.task_id.name, budget_line.budget_amount, total_spent))


