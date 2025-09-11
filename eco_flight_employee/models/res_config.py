from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    air_ticket_debit_account_id = fields.Many2one(
        comodel_name='account.account',
        string='Air Ticket Debit Account',
        config_parameter='eco_flight_employee.air_ticket_debit_account_id'
    )

    air_ticket_credit_account_id = fields.Many2one(
        comodel_name='account.account',
        string='Air Ticket Credit Account',
        config_parameter='eco_flight_employee.air_ticket_credit_account_id'
    )

    air_ticket_product_id = fields.Many2one(
        comodel_name='product.product',
        string='Air Ticket Product',
        domain="[('type','=','service')]",
        config_parameter='eco_flight_employee.air_ticket_product_id'
    )

    air_ticket_journal_id = fields.Many2one(
        comodel_name='account.journal',
        string='Air Ticket Journal',
        config_parameter='eco_flight_employee.air_ticket_journal_id'
    )



