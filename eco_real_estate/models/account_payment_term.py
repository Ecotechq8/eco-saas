from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class AccountPaymentTerm(models.Model):
    _inherit = 'account.payment.term'

    installment_lines = fields.One2many('installment.line', 'payment_term_id', string='Installments', )
    state = fields.Selection(
        string='State',
        selection=[('draft', 'Draft'),
                   ('approve', 'Approved'),
                   ('reject', 'Rejected'),
                   ],
        default='draft')

    @api.constrains('line_ids', 'early_discount')
    def _check_lines(self):
        round_precision = self.env['decimal.precision'].precision_get('Payment Terms')
        for terms in self:
            total_percent = sum(line.value_amount for line in terms.line_ids if line.value == 'percent')
            # if float_round(total_percent, precision_digits=round_precision) != 100:
            #     raise ValidationError(
            #         _('The Payment Term must have at least one percent line and the sum of the percent must be 100%.'))
            if len(terms.line_ids) > 1 and terms.early_discount:
                raise ValidationError(
                    _("The Early Payment Discount functionality can only be used with payment terms using a single 100% line. "))
            if terms.early_discount and terms.discount_percentage <= 0.0:
                raise ValidationError(_("The Early Payment Discount must be strictly positive."))
            if terms.early_discount and terms.discount_days <= 0:
                raise ValidationError(_("The Early Payment Discount days must be strictly positive."))

    def action_approve(self):
        self.state = 'approve'

    def action_reject(self):
        self.state = 'reject'

    def compute_payment_term_line(self):
        line_vals = []
        last_days_n = 0
        for rec in self.installment_lines:
            in_amount = rec.instalment_percent / rec.installment_no
            result = {'description': rec.name,
                      'value_amount': in_amount,
                      'value': rec.calculated_by,
                      'journal_id': rec.journal_id.id,
                      'type': rec.type,
                      'nb_days': 0
                      }
            if rec.type == 'deposit':
                line_vals.append((0, 0, result))
            elif rec.type in ('installment', 'maintenance'):
                for line in range(rec.installment_no):
                    nf_days = rec.calculate_number_of_days(last_days_n) or 0
                    result.update({'nb_days': nf_days})
                    line_vals.append((0, 0, result))
                    last_days_n = nf_days

        if line_vals:
            self.line_ids.unlink()
            self.line_ids = line_vals

    @api.constrains("installment_lines")
    def _check_installment_lines_total_percent(self):
        total_percent = self.installment_lines.filtered(lambda line: line.maintanance_exclude != True).mapped(
            'instalment_percent')
        print('total_percent', total_percent)
        if sum(total_percent) != 100:
            raise ValidationError(_("The sum of the percent must be 100%."))


class AccountPaymentTermLine(models.Model):
    _inherit = "account.payment.term.line"

    description = fields.Char(
        string='Description')
    journal_id = fields.Many2one('account.journal', string='Payment Method')
    type = fields.Selection(
        string='Type',
        selection=[('installment', 'Installment'),
                   ('deposit', 'Deposit'),
                   ('maintenance', 'Maintenance'),
                   ])
