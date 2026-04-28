from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import base64
import io
import csv


class BoxDetailsLine(models.TransientModel):
    _name = "box.details.line"
    _description = "Box Details Line"

    wizard_id = fields.Many2one('box.details.wizard', string="Wizard")
    box_count = fields.Integer(string="Box Count")
    hs_code = fields.Char(string="HS Code")
    length = fields.Float(string="Length")
    width = fields.Float(string="Width")
    height = fields.Float(string="Height")
    weight = fields.Float(string="Weight")
    commodity_type = fields.Many2one('export.product.category', string="Commodity Type")

    @api.onchange('commodity_type')
    def _onchange_commodity_type(self):
        for rec in self:
            rec.hs_code = rec.commodity_type.hs_code


class BoxDetailsWizard(models.TransientModel):
    _name = "box.details.wizard"
    _description = "Box Details Wizard"

    total_boxes = fields.Integer(string="Total Boxes", required=True)
    box_line_ids = fields.One2many('box.details.line', 'wizard_id', string="Box Lines")
    lead_id = fields.Many2one('crm.lead', string="Lead")

    file = fields.Binary(string="Upload CSV File")
    filename = fields.Char(string="File Name")

    @api.onchange('file')
    def _onchange_file(self):
        print('_onchange_file=============')
        if not self.file:
            return

        # Decode the file
        data = base64.b64decode(self.file)
        file_input = io.StringIO(data.decode("utf-8"))
        csv_reader = csv.DictReader(file_input)

        lines = []
        for row in csv_reader:
            lines.append((0, 0, {
                'box_count': int(row.get('box_count', 0)),
                'hs_code': row.get('hs_code', ''),
                'length': float(row.get('length', 0)),
                'width': float(row.get('width', 0)),
                'height': float(row.get('height', 0)),
                'weight': float(row.get('weight', 0)),
                'commodity_type': self.env['export.product.category'].search(
                    [('name', '=', row.get('commodity_type', ''))], limit=1).id
            }))

        self.box_line_ids = [(5, 0, 0)] + lines  # Clear existing and add new lines
        self.total_boxes = len(lines)

    def action_submit(self):
        line_box = sum(line.box_count for line in self.box_line_ids)
        if line_box != self.total_boxes:
            raise ValidationError(_("Line boxes should equal to total boxes."))

        prod = False
        uom_id = False
        if self.lead_id.order_line:
            self.lead_id.order_line.unlink()
        if self.lead_id and self.lead_id.service_type and self.lead_id.service_type.service:
            product = self.lead_id.service_type.service
            prod = product.id
            uom_id = product.uom_id.id

        lines = []
        for line in self.box_line_ids:
            lines.append((0, 0, {
                'lead_id': self.lead_id.id,
                'product_id': prod,
                'product_uom': uom_id,
                'product_uom_quantity': line.box_count,
                'weight_input': line.weight,
                'height_per_package': line.height,
                'width_per_package': line.width,
                'length_per_package': line.length,
                'hs_code': line.hs_code,
                'commodity_type': line.commodity_type.id if line.commodity_type else False,
                'type':False,
            }))

        self.lead_id.order_line = lines
        self.lead_id.update_lead_line_Calculation()
        self.lead_id.order_line._compute_volume_cbcm()
        self.lead_id.order_line._compute_volume_cbm()

        return {'type': 'ir.actions.act_window_close'}
