from odoo import models, fields

class AirLine(models.Model):
    _name = 'air.line'
    _description = 'Air Line'

    name = fields.Char(string="Name", required=True)
    code = fields.Char(string='Code', required=True)

    def name_get(self):
        result = []
        for record in self:
            display_name = record.name or ''
            if record.code:
                display_name = "[" + record.code + "]" + record.name
            result.append((record.id, display_name))
        return result


