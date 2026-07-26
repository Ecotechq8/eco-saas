from odoo import models, fields
from odoo import api, models, fields, _


class InboundFlight(models.Model):
    _name = 'inbound.flight'
    _description = 'Inbound Flight'

    loaded = fields.Boolean(string='Loaded', default=False, copy=False)
    location = fields.Char(string='Location')
    route = fields.Many2one('ports', string="Route")
    route2 = fields.Many2one('ports', string="")
    date = fields.Date(string='Date')
    flt_date = fields.Date(string='Flt Date')
    arr_date = fields.Date(string='Arr Date')
    trx_type = fields.Selection([
        ('cargo_flights', 'Cargo Flights'),
        ('commercial_flights', 'Commercial Flights'),
        ('private_jets', 'Private Jets'),
    ], string='Trx Type')
    doc_no = fields.Char(string='Document No.')
    airline_id = fields.Many2one('res.partner', string='Airline')
    flt = fields.Char(string='Flt#')
    manifest = fields.Char(string='Manifest#')
    type = fields.Selection([
        ('normal', 'Normal'),
    ], string='Type', default='normal')
    gross_wt = fields.Float(string='Gross Weight(KG)')
    chrg_wt = fields.Float(string='Chargeable Weight (KG)')
    name = fields.Char(string='Document Number', readonly=True, copy=False, default='New')

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('inbound.flight') or 'New'
        return super(InboundFlight, self).create(vals)


    def action_create_invoice(self):
        invoice_obj = self.env['account.move']

        invoice_vals = {
            'move_type': 'out_invoice',
            'invoice_line_ids': [],
        }
        invoice = invoice_obj.create(invoice_vals)

        return {
            'name': 'Customer Invoice',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': invoice.id,
            'target': 'current',
        }
