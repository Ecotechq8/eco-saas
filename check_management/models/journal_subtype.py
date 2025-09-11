from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class AccountJournal(models.Model):
    _inherit = 'account.journal'

    payment_subtype = fields.Selection([('issue_check', _('Issued Checks')),
                                        ('rece_check', _('Received Checks'))],
                                       string="Payment Subtype")

    deposit_check = fields.Boolean()

    # deposit check

    @api.constrains('bank_id')
    def _check_unique_bank_name(self):
        """
        Ensure that no two journals have the same bank_id.
        """
        for record in self:
            if record.bank_id:
                existing_journal = self.search([
                    ('bank_id', '=', record.bank_id.id),
                    ('id', '!=', record.id)
                ], limit=1)
                if existing_journal:
                    raise ValidationError((
                        "A journal with the bank '%s' already exists. "
                        "You cannot create another journal with the same bank."
                    ) % record.bank_id.name)