from odoo import models, fields, api

class SaleReport(models.Model):
    _inherit = "sale.report"

    next_pickup_date = fields.Datetime(string="Next Pickup", store=True)
    qty_returned = fields.Float(string="Qty Returned", readonly=True)
    is_rental_order = fields.Boolean(string="Rental Orders", readonly=True)

    def _query(self, with_clause='', fields=None, groupby='', from_clause=''):
        # Safeguard for fields if it's not passed correctly
        if fields is None:
            fields = {}

        # Adding custom fields for the inherited model
        fields['next_pickup_date'] = ", s.next_pickup_date AS next_pickup_date"
        fields['is_rental_order'] = ", s.is_rental_order AS is_rental_order"
        fields['qty_returned'] = (", CASE WHEN l.product_id IS NOT NULL THEN "
                                  "SUM(l.qty_returned / u.factor * u2.factor) ELSE 0 END AS qty_returned")

        # Adding custom fields to the group by clause
        groupby += ', s.next_pickup_date, s.is_rental_order'

        # Fetch additional fields from the parent method
        sale_report_fields = self._select_additional_fields()

        # Constructing the 'WITH' clause if applicable
        with_ = ("WITH %s" % with_clause) if with_clause else ""

        # Return the final query string, ensuring that fields and groupby are properly handled
        return '%s (SELECT %s %s FROM %s WHERE l.display_type IS NULL GROUP BY %s)' % (
            with_,
            self._select_sale(),  # Base select fields
            ''.join(fields.values()),  # Adding the custom fields to the SELECT clause
            self._from_sale(),    # Base FROM clause
            self._group_by_sale() + groupby  # Concatenate custom groupby fields here
        )
