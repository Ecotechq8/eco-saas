from odoo import models, fields, api


class AWBMaster(models.Model):
    _name = 'awb.master'
    _description = 'AWB Master'
    _rec_name = 'airline_id'

    airline_id = fields.Many2one(
        'res.partner',
        string='Airline',
        domain=[('is_airline', '=', True)]
    )
    date = fields.Date(string='Date')
    remarks = fields.Text(string='Remarks')
    start_number = fields.Char(string='Start Number')
    end_number = fields.Char(string='End Number')
    check_digit_start = fields.Selection([(str(i), str(i)) for i in range(7)], string='Check Digit', default='0')
    awb_line_ids = fields.One2many('awb.master.line', 'master_id', string='AWB Lines')
    quantity = fields.Integer(string='Quantity', compute='_compute_quantity', store=True)

    from odoo.exceptions import ValidationError

    @api.depends('start_number', 'end_number')
    def _compute_quantity(self):
        for rec in self:
            try:
                start = int(rec.start_number)
                end = int(rec.end_number)
                if end >= start:
                    rec.quantity = end - start + 1
                else:
                    rec.quantity = 0
            except (ValueError, TypeError):
                rec.quantity = 0

    def action_generate_awb_lines(self):
        for rec in self:
            if rec.awb_line_ids:
                rec.awb_line_ids.unlink()
            if rec.start_number and rec.end_number:
                start = int(rec.start_number)
                end = int(rec.end_number)
                if end >= start:
                    lines = []
                    check_digit = int(rec.check_digit_start)
                    length = max(len(rec.start_number), len(rec.end_number))  # Get the length for zero padding
                    for serial in range(start, end + 1):
                        serial_str = str(serial).zfill(length)  # Pad with leading zeros
                        awb_number = f"{serial_str}{check_digit}"
                        lines.append((0, 0, {
                            'awb_no': awb_number,
                            'check_digit': check_digit,
                            'state': 'open',
                            'airline_id': rec.airline_id.id,
                        }))
                        check_digit = (check_digit + 1) % 7
                    rec.awb_line_ids = lines


class AWBMasterLine(models.Model):
    _name = 'awb.master.line'
    _description = 'AWB Master Line'
    _rec_name = 'awb_no'

    master_id = fields.Many2one('awb.master', string='AWB Master')
    airline_id = fields.Many2one('res.partner', string='Airline')
    awb_no = fields.Char(string='AWB No.')
    check_digit = fields.Integer(string='Check Digit')
    state = fields.Selection([
        ('open', 'Open'),
        ('used', 'Used'),
    ], string='State', default='open')

