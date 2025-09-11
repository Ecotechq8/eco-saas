from odoo import fields, models, api, _


class InstallmentLine(models.Model):
    _name = 'installment.line'
    _description = "Installment Line"

    payment_term_id = fields.Many2one('account.payment.term')
    name = fields.Char("Name", size=64, required=True)
    seq = fields.Integer(
        string='Seq', 
        required=False)
    type = fields.Selection(
        string='Type',
        selection=[('installment', 'Installment'),
                   ('deposit', 'Deposit'),
                   ('maintenance', 'Maintenance'),
                   ],
        required=True, default='installment')
    calculated_by = fields.Selection(
        string='Calculated By',
        selection=[('percent', 'Percent'),
                   ('fixed', 'Fixed'), ],
        default='percent')

    instalment_percent = fields.Float(string='Instalment Percentage', required=False)
    installment_no = fields.Integer(string='Installment Count', required=True)
    journal_id = fields.Many2one('account.journal', string='Payment Method', required=True)
    maintanance_exclude = fields.Boolean(string='Maintanance Exclude', required=False)
    range = fields.Selection(
        string='Range',
        selection=[('days', 'By Days'),
                   ('period', 'By Period'), ],
        default='days')
    by_period = fields.Selection(
        string='By Period',
        selection=[('once', 'Once'),
                   ('month', 'Monthly'),
                   ('quarter', 'Quarterly'),
                   ('sami_annual', 'Sami Annual'),
                   ('annual', 'Annually'),
                   ],
        required=False, )
    by_days = fields.Integer('Period Days')
    shift_by = fields.Selection(
        string='Shift By',
        selection=[('days', 'Days'),
                   ('month', 'Months'), ],
        required=False, )
    shift_days = fields.Integer(string='Days', required=False)
    shift_months = fields.Integer(string='Months ', required=False)
    company_id = fields.Many2one("res.company", string="Company", default=lambda self: self.env.company)


    def calculate_number_of_days(self, last_no):
        no_days = last_no
        if self.shift_by :
            if self.shift_by == 'days' :
                no_days += self.shift_days
            else:
                no_days += (self.shift_months * 30)
        if self.range == 'days':
            no_days += self.by_days
            return no_days
        else:
            if self.by_period == 'once':
                return no_days
            if self.by_period == 'month':
                no_days += 30
                return no_days
            if self.by_period == 'quarter':
                no_days += (30 *3)
                return no_days
            if self.by_period == 'sami_annual':
                no_days += (30 *6)
                return no_days
            if self.by_period == 'annual':
                no_days += 365
                return no_days



