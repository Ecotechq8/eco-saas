# guarantee_letter/models/guarantee_letter.py
from odoo import models, fields, api, _


class GuaranteeLetter(models.Model):
    _name = 'guarantee.letter'
    _description = 'Guarantee Letter'

    name = fields.Char(string='Reference', required=True, copy=False, default='New')
    type = fields.Many2one('guarantee.letter.type', string='Type', required=False)
    journal_bank_id = fields.Many2one('account.journal', string='Bank Journal', required=True)
    journal_payment_id = fields.Many2one('account.journal', string='Payment Journal', required=True)
    letter_account_id = fields.Many2one('account.account', string='Letter of Guarantee Account', required=True)
    ref = fields.Char(string='Reference No', required=False)
    issued_date = fields.Date(string='Issued Date', )
    expiry_date = fields.Date(string='Expiry Date', )
    project_id = fields.Many2one('project.project', string='Project', required=False)
    # analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account', required=False)
    amount = fields.Float(string='Amount', required=True)
    company_percent = fields.Float(string='Company %', required=True)
    date = fields.Date(string='Date', default=fields.Date.today())
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('expense', 'Expenses Submitted'),
        ('return', 'Returned'),
    ], string='Status', default='draft')
    total = fields.Float(string='Total', compute="_compute_total")
    transaction_ids = fields.One2many('guarantee.letter.transaction', 'letter_id', string='Transactions',
                                      required=False)
    extension_ids = fields.One2many('guarantee.letter.extension', 'letter_id', string='Extension', required=False)
    entries_count = fields.Integer(compute="_entries_count", string="Entries")
    purpose = fields.Text(string="Purpose", required=False)
    is_deducted = fields.Boolean(string='Is Deducted', required=False)
    expenses_loss_account_id = fields.Many2one('account.account', string='Expenses/loss Account')

    @api.depends('transaction_ids')
    def _compute_total(self):
        for rec in self:
            rec.total = 0
            rec.total = sum(self.transaction_ids.mapped('subtotal'))

    # @api.model
    # def create(self, vals):
    #     if vals.get("name", "New") == "New":
    #         vals["name"] = (
    #                 self.env["ir.sequence"].next_by_code(
    #                     "property.reservation") or "New"
    #         )
    #     result = super(PropertyReservation, self).create(vals)
    #     return result

    def action_confirm(self):
        if self.company_percent > 0 and self.amount > 0:
            amount = (self.company_percent / 100) * self.amount
            account_move_obj = self.env["account.move"]
            invoice = account_move_obj.create({
                "ref": self.ref,
                "journal_id": self.journal_bank_id.id,
                "move_type": 'entry',
                "guarantee_letter_id": self.id,
                "line_ids": [
                    (0, 0, {
                        # "name": rec.name,
                        # "partner_id": rec.partner_id.id,
                        "account_id": self.journal_bank_id.default_account_id.id,
                        "debit": 0.0,
                        "credit": amount,
                    }),
                    (0, 0, {
                        # "name": rec.name,
                        # "partner_id": rec.partner_id.id,
                        "account_id": self.letter_account_id.id,
                        "debit": amount,
                        "credit": 0.0,
                    }),
                ],
            })
        if invoice:
            invoice.action_post()
        self.state = 'confirmed'

    def action_expense(self):
        account_move_obj = self.env["account.move"]
        for line in self.transaction_ids:

            invoice = account_move_obj.create({
                "ref": self.ref,
                "journal_id": self.journal_payment_id.id,
                "move_type": 'entry',
                "guarantee_letter_id": self.id,
                "line_ids": [
                    (0, 0, {
                        "account_id": self.journal_payment_id.default_account_id.id,
                        "debit": 0.0,
                        "credit": line.subtotal,
                    }),
                    (0, 0, {
                        "account_id": line.account_id.id,
                        "debit": line.subtotal,
                        "credit": 0.0,
                    }),
                ],
            })

            if invoice:
                invoice.action_post()
        self.state = 'expense'

    def action_return(self):
        if self.company_percent > 0 and self.amount > 0:
            amount = (self.company_percent / 100) * self.amount
            account_move_obj = self.env["account.move"]
            data = {"ref": self.ref,
                    "journal_id": self.journal_bank_id.id,
                    "move_type": 'entry',
                    "guarantee_letter_id": self.id, }
            data.update( {

                "line_ids": [
                    (0, 0, {

                        "account_id": self.journal_bank_id.default_account_id.id,
                        "debit": amount,
                        "credit": 0.0,
                    }),
                    (0, 0, {

                        "account_id": self.letter_account_id.id,
                        "debit": 0.0,
                        "credit": amount,
                    }),
                ],
            })
            invoice = account_move_obj.create(data)
            if invoice:
                invoice.action_post()
            if self.is_deducted:
                data.update({

                    "line_ids": [
                        (0, 0, {

                            "account_id": self.expenses_loss_account_id.id,
                            "debit": amount,
                            "credit": 0.0,
                        }),
                        (0, 0, {

                            "account_id": self.letter_account_id.id,
                            "debit": 0.0,
                            "credit": amount,
                        }),
                    ],
                })
                deducted_entry = account_move_obj.create(data)
                if deducted_entry:
                    deducted_entry.action_post()
        self.state = 'return'

    def _entries_count(self):
        move = self.env["account.move"]
        for rec in self:
            rec.entries_count = move.search_count([("guarantee_letter_id", "=", rec.id)])

    def button_view_entries(self):
        entries = self.env["account.move"].search([("guarantee_letter_id", "=", self.id)])
        return {
            "name": _("Journal Entries"),
            "domain": [("id", "in", entries.ids)],
            "view_type": "list",
            "view_mode": "list,form",
            "res_model": "account.move",
            "type": "ir.actions.act_window",
            "nodestroy": True,
            "view_id": False,
            "target": "current",
        }


class GuaranteeLetterType(models.Model):
    _name = 'guarantee.letter.type'

    name = fields.Char(string='Name', required=True)


class GuaranteeLetterExtension(models.Model):
    _name = 'guarantee.letter.extension'

    name = fields.Char(string='Extension No', required=True)
    extension_date = fields.Date(string='Extension Date', required=True)
    letter_id = fields.Many2one('guarantee.letter', string='Letter_id', required=False)
