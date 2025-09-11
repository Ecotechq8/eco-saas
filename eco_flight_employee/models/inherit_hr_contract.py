from odoo import models, fields, api, _
from datetime import date
from odoo.exceptions import ValidationError


class HrContract(models.Model):
    _inherit = 'hr.contract'

    has_air_ticket = fields.Boolean(
        string='Has Air Ticket'
    )
    air_ticket_type = fields.Selection(
        selection=[
            ('private', 'Private'),
            ('with_family', 'Yes with Family'),
        ], string='Air Ticket Type'
    )
    ticket_count = fields.Integer(
        string='Number of Tickets'
    )
    total_amount = fields.Monetary(
        string="Total Amount",
        currency_field='currency_id'
    )
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id
    )
    ticket_duration_date = fields.Date(
        string="Duration"
    )

    def generate_air_ticket_lines(self):
        today = date.today()
        for contract in self:
            if (
                    contract.has_air_ticket
                    and contract.date_start
                    and contract.ticket_duration_date
                    and contract.state == 'open'
                    and today > contract.ticket_duration_date
            ):
                already_exists = self.env['air.ticket.line'].search([
                    ('contract_id', '=', contract.id),
                    ('date', '=', today)
                ])
                if already_exists:
                    continue

                # Create air ticket line
                self.env['air.ticket.line'].create({
                    'employee_id': contract.employee_id.id,
                    'contract_id': contract.id,
                    'date': today,
                    'air_ticket_type': contract.air_ticket_type,
                    'ticket_count': contract.ticket_count,
                    'total_amount': contract.total_amount,
                })

                # Fetch config
                params = self.env['ir.config_parameter'].sudo()
                debit_account_id = int(params.get_param('eco_flight_employee.air_ticket_debit_account_id') or 0)
                credit_account_id = int(params.get_param('eco_flight_employee.air_ticket_credit_account_id') or 0)
                journal_id = int(params.get_param('eco_flight_employee.air_ticket_journal_id') or 0)
                analytic_distribution = {}

                if not (debit_account_id and credit_account_id and journal_id):
                    raise ValidationError(_("Please configure debit, credit accounts and journal in Settings."))

                # Get related partner
                partner = contract.employee_id.user_id.partner_id or self.env['res.partner'].search([
                    ('name', '=', contract.employee_id.name)
                ], limit=1)

                if not partner:
                    raise ValidationError(_("No related partner found for employee '%s'.") % contract.employee_id.name)

                # Create journal entry
                move = self.env['account.move'].create({
                    'ref': contract.employee_id.name + ' Air Ticket',
                    'move_type': 'entry',
                    'date': fields.Date.today(),
                    'journal_id': journal_id,
                    'line_ids': [
                        (0, 0, {
                            'name': 'Air Ticket Debit',
                            'debit': contract.total_amount,
                            'credit': 0,
                            'account_id': debit_account_id,
                            'partner_id': partner.id,
                            'analytic_distribution': analytic_distribution,

                        }),
                        (0, 0, {
                            'name': 'Air Ticket Credit',
                            'debit': 0,
                            'credit': contract.total_amount,
                            'account_id': credit_account_id,
                            'partner_id': partner.id,
                            'analytic_distribution': analytic_distribution,

                        }),
                    ]
                })
                move.action_post()
