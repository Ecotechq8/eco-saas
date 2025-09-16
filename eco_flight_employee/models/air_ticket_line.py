from odoo import fields, models, api


class AirTicketLine(models.Model):
    _name = 'air.ticket.line'
    _description = 'Air Ticket Line'
    _order = 'create_date desc'

    employee_id = fields.Many2one(
        comodel_name='hr.employee',
        string="Employee",
        required=True
    )
    contract_id = fields.Many2one(
        comodel_name='hr.contract',
        string="Contract",
        required=True,
        ondelete='cascade'
    )
    date = fields.Date(
        string="Request Date",
        default=fields.Date.today
    )
    air_ticket_type = fields.Selection(
        string="Ticket Type",
        selection=[
            ('private', 'Private'),
            ('with_family', 'With Family')
        ]
    )
    ticket_count = fields.Integer(
        string="Number of Tickets"
    )
    total_amount = fields.Monetary(
        string="Total Amount"
    )
    max_ticket_amount = fields.Monetary(
        string="Max Ticket Amount"
    )
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        related='contract_id.currency_id',
        store=True,
        readonly=True
    )
