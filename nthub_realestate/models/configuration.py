# -*- coding: utf-8 -*-
from odoo import api, fields, models


class Configration(models.TransientModel):
    _inherit = 'res.config.settings'

    reservation_days = fields.Integer(string='Days to release units reservation',
                                      config_parameter='nthub_realestate.reservation_days')

    location_id = fields.Many2one(
        'stock.location', 'Source Location',
        domain="[('usage','=','internal'), '|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        check_company=True, config_parameter='nthub_realestate.location_id')

    location_dest_id = fields.Many2one(
        'stock.location', 'Destination Location',
        domain="[('usage','=','internal'), '|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        check_company=True, config_parameter='nthub_realestate.location_dest_id')

    ownership_settlement_account = fields.Many2one('account.account', 'OwnerShip Settlement Account',
                                                   config_parameter='nthub_realestate.ownership_settlement_account')
    ownership_maintenance_account = fields.Many2one('account.account', 'OwnerShip Maintain Account',
                                                 config_parameter='nthub_realestate.ownership_maintenance_account')
    ownership_delay_account = fields.Many2one('account.account', 'OwnerShip Delay Account',
                                              config_parameter='nthub_realestate.ownership_delay_account')
    ownership_extras_account = fields.Many2one('account.account', 'OwnerShip Extras Account',
                                               config_parameter='nthub_realestate.ownership_extras_account')
    rental_settlement_account = fields.Many2one('account.account', 'Rental Settlement Account',
                                                config_parameter='nthub_realestate.rental_settlement_account')



