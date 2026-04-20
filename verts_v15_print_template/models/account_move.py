# -*- coding: utf-8 -*-

from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _get_tax_amount_by_group(self):
        """Return tax amounts grouped by tax group for report templates.
        Compatible with Odoo 15 enterprise report templates.
        """
        self.ensure_one()
        if not self.tax_totals:
            return []
        tax_groups = []
        for subtotal in self.tax_totals.get('subtotals', []):
            for tax_group in subtotal.get('tax_groups', []):
                tax_groups.append((
                    tax_group.get('group_name', ''),
                    tax_group.get('tax_group_amount', 0.0),
                    tax_group.get('base_amount', 0.0),
                ))
        return tax_groups
