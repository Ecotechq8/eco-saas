# -*- coding: utf-8 -*-

import base64
import csv
import io

from odoo import _, fields, models
from odoo.exceptions import UserError


class BoxDetailsWizard(models.TransientModel):
    _name = "box.details.wizard"
    _description = "Box Details Wizard"

    total_boxes = fields.Integer(string="Total Boxes")
    lead_id = fields.Many2one("crm.lead", string="Lead", required=True)
    file = fields.Binary(string="File")
    filename = fields.Char(string="Filename")
    box_line_ids = fields.One2many("box.details.line", "wizard_id", string="Box Lines")

    def _load_csv_file(self):
        self.ensure_one()
        if not self.file:
            return

        try:
            content = base64.b64decode(self.file)
            text = content.decode("utf-8-sig")
        except Exception as exc:
            raise UserError(_("The uploaded file could not be decoded as UTF-8 CSV.")) from exc

        reader = csv.DictReader(io.StringIO(text))
        required_columns = {"box_count", "commodity_type", "hs_code", "length", "width", "height", "weight"}
        if not reader.fieldnames or not required_columns.issubset(set(reader.fieldnames)):
            raise UserError(
                _(
                    "The CSV file must contain these columns: box_count, commodity_type, hs_code, "
                    "length, width, height, weight."
                )
            )

        self.box_line_ids.unlink()
        product_category_model = self.env["export.product.category"]
        total_boxes = 0.0
        for row in reader:
            commodity = False
            commodity_name = (row.get("commodity_type") or "").strip()
            if commodity_name:
                commodity = product_category_model.search([("name", "=", commodity_name)], limit=1)

            box_count = float(row.get("box_count") or 0.0)
            total_boxes += box_count
            self.env["box.details.line"].create(
                {
                    "wizard_id": self.id,
                    "box_count": box_count,
                    "commodity_type": commodity.id,
                    "hs_code": row.get("hs_code"),
                    "length": float(row.get("length") or 0.0),
                    "width": float(row.get("width") or 0.0),
                    "height": float(row.get("height") or 0.0),
                    "weight": float(row.get("weight") or 0.0),
                }
            )
        self.total_boxes = int(total_boxes)

    def action_submit(self):
        self.ensure_one()
        self._load_csv_file()

        if not self.box_line_ids:
            raise UserError(_("Add at least one box line before submitting."))
        total_line_boxes = sum(self.box_line_ids.mapped("box_count"))
        if self.total_boxes and abs(total_line_boxes - self.total_boxes) > 1e-6:
            raise UserError(_("Line boxes should equal the total boxes."))

        lead_lines = self.lead_id.order_line.sorted("id")
        if not lead_lines:
            raise UserError(_("Create at least one freight line before using bulk entry."))

        for index, box_line in enumerate(self.box_line_ids):
            lead_line = box_line.lead_line_id
            if not lead_line and index < len(lead_lines):
                lead_line = lead_lines[index]
            if not lead_line:
                lead_line = self.env["lead.order.line"].create(
                    {
                        "lead_id": self.lead_id.id,
                        "product_id": lead_lines[0].product_id.id,
                        "product_uom": lead_lines[0].product_uom.id,
                        "service_type": lead_lines[0].service_type.id,
                        "packing_type": lead_lines[0].packing_type.id,
                        "type": lead_lines[0].type,
                    }
                )

            lead_line.write(
                {
                    "product_uom_quantity": box_line.box_count,
                    "commodity_type": box_line.commodity_type.id,
                    "hs_code": box_line.hs_code,
                    "length_per_package": box_line.length,
                    "width_per_package": box_line.width,
                    "height_per_package": box_line.height,
                    "weight_input": box_line.weight,
                }
            )
            lead_line.onchange_weight_input()
            lead_line.onchange_get_weight_factor()
            lead_line.onchange_get_uoms()

        self.lead_id.update_lead_line_Calculation()
        return {"type": "ir.actions.act_window_close"}


class BoxDetailsLine(models.TransientModel):
    _name = "box.details.line"
    _description = "Box Details Line"

    wizard_id = fields.Many2one("box.details.wizard", string="Wizard", required=True, ondelete="cascade")
    lead_line_id = fields.Many2one("lead.order.line", string="Lead Line")
    box_count = fields.Float(string="Box Count")
    commodity_type = fields.Many2one("export.product.category", string="Commodity Type")
    hs_code = fields.Char(string="HS Code")
    length = fields.Float(string="Length")
    width = fields.Float(string="Width")
    height = fields.Float(string="Height")
    weight = fields.Float(string="Weight")
