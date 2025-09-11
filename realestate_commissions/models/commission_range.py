# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class CommissionRange(models.Model):
    _name = 'commission.range'

    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']

    _description = 'Sales Commission Range'

    name = fields.Char(
        string='Name',
        required=True)
    state = fields.Selection(
        string='State',
        selection=[('draft', 'Draft'),
                   ('confirm', 'Confirm'), ],
        default='draft', )

    date_from = fields.Date(string='Date From', required=True)
    date_to = fields.Date(string='Date To', required=True)
    type = fields.Selection(
        string='Type',
        selection=[
            ("direct", "Direct"),
            ("indirect", "Indirect"),
        ],
        required=True, default='direct')
    range_from = fields.Integer(string='Range From', required=True)
    range_to = fields.Integer(string='Range To', required=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)

    sales_team_commission_ids = fields.One2many('commission.range.sales.team','range_id',string='Sales Team')
    sales_agent_commission_ids = fields.One2many('commission.range.sales.agent','range_id',string='Sales Agent')

    def action_confirm(self):
        self.write({"state": "confirm"})

    def action_set_draft(self):
        self.write({"state": "draft"})

class CommissionRangeSalesTeam(models.Model):
    _name = 'commission.range.sales.team'
    
    range_id = fields.Many2one('commission.range',string='Range_id')
    range_from = fields.Integer(string='Range From', required=True)
    range_to = fields.Integer(string='Range To', required=True)
    sales_person_percent = fields.Float(string='Sales Person %', required=True)
    sales_manager_percent = fields.Float(string='Sales Manager %', required=True)

    group_id = fields.Many2one(
        comodel_name='res.groups',string='Group')
    group_percent = fields.Float(string='Group  %',)
class CommissionRangeSalesAgent(models.Model):
    _name = 'commission.range.sales.agent'

    range_id = fields.Many2one('commission.range', string='Range_id')

    type = fields.Selection([
        ("freelancer", "Freelancer"),
        ("referral", "Referral"),
        ("exclusive", "Broker [Exclusive]"),
        ("no_exclusive", "Broker [None Exclusive]"),
    ], "Type")
    sales_agent_percent = fields.Float(string='Sales Agent %', required=True)


