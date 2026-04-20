import re
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class MakersInfo(models.Model):
    _name = "makers.info"
    _description = "Makers Info"


    @api.constrains('name')
    def _check_alphabet(self):
        if self.name:
            lc = re.compile('[a-z]+')
            lower_case = lc.findall(self.name)
            if lower_case:
                raise ValidationError("Error! Alphabets must be Capitalized!!!")
        # return True

    _sql_constraints = [
        ('number_uniq', 'unique(name)', 'Name must be unique!'),
    ]

    name = fields.Char(string='Short Name/Code')
    full_name = fields.Char(string="Full Name", help="Optional Field")

