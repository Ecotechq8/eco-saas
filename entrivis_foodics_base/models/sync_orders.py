from odoo import fields, models, api, _
from odoo.exceptions import ValidationError, UserError


class PosOrderLine(models.Model):
    _inherit = "pos.order.line"

    discount_type = fields.Selection([('percentage', 'Percentage'), ('fix', 'FIx')])
    discount_amount = fields.Float('Disc. Amount')
    modifier_of = fields.Char('Modifier Of')

    @api.onchange('qty', 'discount', 'price_unit', 'tax_ids')
    def _onchange_qty(self):
        if self.product_id:
            if not self.order_id.pricelist_id:
                raise UserError(_('You have to select a pricelist in the sale form.'))
            price = self.price_unit * (1 - (self.discount or self.discount_amount or 0.0) / 100.0)
            self.price_subtotal = self.price_subtotal_incl = price * self.qty
            if (self.tax_ids):
                taxes = self.tax_ids.compute_all(price, self.order_id.pricelist_id.currency_id, self.qty,
                                                 product=self.product_id, partner=False)
                self.price_subtotal = taxes['total_excluded']
                self.price_subtotal_incl = taxes['total_included']


class PosOrder(models.Model):
    _inherit = "pos.order"

    foodics_id = fields.Char("Foodics User Id")
    discount_amount = fields.Float("Total Discount", compute='compute_total_discount')
    global_discount = fields.Float("Global Discount")

    @api.depends("global_discount", "lines")
    def compute_total_discount(self):
        """
        compute total discount
        :return:
        """
        for rec in self:
            rec.discount_amount = sum(rec.lines.mapped('discount_amount')) + rec.global_discount

    def sync_single_orders(self):
        """
        - Sync Order from foodics
        :return:
        """
        connector = self.env['foodic.connector'].search([('state', '=', 'authenticated')], limit=1)
        if not connector:
            raise ValidationError(_("Please check Foodics Configuration Detail."))
        if self.foodics_id:
            post_url = '/orders/' + self.foodics_id
            response = connector.call_foodics_api('GET', post_url, {})
            data = self.prepare_data_foodics_to_odoo(response.get('data'))
            self.update(data)
        else:
            data = self.prepare_data_odoo_to_foodics()
            response = connector.call_foodics_api('POST', '/orders', data)
            data = self.prepare_data_foodics_to_odoo(response.get('data'))
            self.update(data)

    def prepare_data_foodics_to_odoo(self, data):
        """
        Prepare The Data
        :param data:
        :return:
        """
        """ dummy data"""
        connector = self.env['foodic.connector'].search([('state', '=', 'authenticated')], limit=1)
        partner = False
        creator = False
        branch = False
        foodics_partner_id = False
        # foodics_session_id = data.get('session') and data.get('session').get('id', False)
        if data.get('customer'):
            foodics_partner_id = data.get('customer') and data.get('customer').get('id', False)
        foodics_creator_id = data.get('creator') and data.get('creator').get('id', False)
        foodics_branch_id = data.get('branch') and data.get('branch').get('id', False)
        vals = []
        if foodics_branch_id:
            branch = self.env['pos.config'].search([('foodics_id', '=', foodics_branch_id)], limit=1)
            if not branch:
                # read_all_branch = connector.call_foodics_api('GET', '/branches/' + str(foodics_branch_id), {})
                # for each_branch in read_all_branch.get('data'):
                foodics_id = data.get('branch').get('id') or ''
                if foodics_id:
                    config_vals = self.env['pos.config'].prepare_branch_data(data.get('branch'))
                    self.env['pos.config'].create(config_vals)
                branch = self.env['pos.config'].search([('foodics_id', '=', foodics_branch_id)], limit=1)

        if foodics_creator_id:
            creator = self.env['res.users'].search([('foodics_id', '=', foodics_creator_id)], limit=1)
            if not creator:
                # read_all_users = connector.call_foodics_api('GET', '/users/' + str(foodics_creator_id), {})
                # for user_data in read_all_users.get('data'):
                foodics_id = data.get('creator').get('id') or ''
                if foodics_id:
                    user_vals = self.env['res.users'].prepare_user_data(data.get('creator'))
                    self.env['res.users'].create(user_vals)
                creator = self.env['res.users'].search([('foodics_id', '=', foodics_creator_id)], limit=1)

        if foodics_partner_id:
            partner = self.env['res.partner'].search([('foodics_id', '=', foodics_partner_id)], limit=1)
            if not partner:
                # read_all_customer = connector.call_foodics_api('GET', '/customers/' + str(foodics_partner_id), {})
                # for customer_data in read_all_customer.get('data'):
                foodics_id = data.get('customer').get('id') or ''
                if foodics_id:
                    partner_vals = self.env['res.partner'].prepare_data_foodics_to_odoo(data.get('customer'))
                    partner = self.env['res.partner'].create(partner_vals)

        order_id = False
        if data.get('status') == 5:
            order_id = self.env['pos.order'].search([('foodics_id', '=', data.get('original_order', {}).get('id'))]).id

        tax_amount_total = 0
        if data.get('products'):
            line_lst = []

            for product_line in data.get('products'):
                product_id = self.env['product.product'].search(
                    [('foodics_id', '=', product_line.get('product').get('id'))], limit=1)

                if not product_id:
                    # read_all_products = connector.call_foodics_api('GET', '/products/' + str(product_line.get('product').get('id')), {})
                    # for product_data in read_all_products.get('data'):
                    foodics_id = product_line.get('product').get('id') or ''
                    if foodics_id:
                        product_vals = self.env['product.product'].prepare_data_foodics_to_odoo(product_line.get('product'), is_order=True)
                        product_id = self.env['product.product'].create(product_vals)

                tax = []
                tax_id = False
                tax_amount = 1
                for each_tax in product_line.get('taxes'):
                    tax_id = self.env['account.tax'].search([('foodics_id', '=', each_tax.get('id'))], limit=1)
                    if each_tax.get('pivot'):
                        tax_amount_total += each_tax.get('pivot', {}).get('amount')
                    if tax_id:
                        tax.append((4, tax_id.id))
                        tax_amount = tax_id.amount

                if product_id.id in self.lines.mapped('product_id').ids:

                    for each_product in self.lines:
                        if each_product.product_id.id == product_id.id:
                            qty = product_line.get('quantity')
                            discount_amount = product_line.get('discount', {}).get('amount') if product_line.get(
                                'discount', {}) else 0.00
                            price_subtotal = (product_line.get('unit_price') * product_line.get(
                                'quantity')) - (product_line.get('discount', {}).get('amount') if product_line.get(
                                'discount', {}) else 0.00)

                            price_subtotal_incl = price_subtotal + (price_subtotal / 100 * tax_amount if tax_amount != 1 else 0)

                            order_line_id = False
                            if data.get('status') == 5:
                                qty = -qty
                                discount_amount = -discount_amount
                                price_subtotal = -price_subtotal
                                price_subtotal_incl = -price_subtotal_incl

                                order_line_id = self.env['pos.order.line'].search(
                                    [('order_id', '=', order_id), ('product_id', '=', each_product.product_id.id),
                                     ('qty', '!=', each_product.refunded_qty)], limit=1).id

                            each_product.write({
                                'qty': qty,
                                'price_unit': product_line.get('unit_price'),
                                'tax_ids': tax,
                                'discount_amount': discount_amount,
                                'price_subtotal': price_subtotal,
                                'price_subtotal_incl': price_subtotal_incl,
                                'refunded_orderline_id': order_line_id,
                            })
                else:

                    qty = product_line.get('quantity')
                    discount_amount = product_line.get('discount_amount', {})

                    price_subtotal = (product_line.get('unit_price') * product_line.get(
                            'quantity')) - product_line.get('discount_amount', {})

                    price_subtotal_incl = price_subtotal + (price_subtotal / 100 * tax_amount if tax_amount != 1 else 0)
                    order_line_id = False
                    if data.get('status') == 5:
                        qty = -qty
                        discount_amount = -discount_amount
                        price_subtotal = -price_subtotal
                        price_subtotal_incl = -price_subtotal_incl

                        order_line_id = self.env['pos.order.line'].search(
                            [('order_id', '=', order_id), ('product_id', '=', product_id.id)])
                        for rec_product in order_line_id:
                            if rec_product.qty != rec_product.refunded_qty or rec_product.refunded_qty == 0.00:
                                if rec_product.id not in line_lst:
                                    order_line_id = rec_product
                                    line_lst.append(rec_product.id)
                        # order_line_id.filtered(lambda l: l.qty != l.refunded_qty)
                        if order_line_id:
                            order_line_id = order_line_id[0].id

                    vals.append((0, 0, {
                        'product_id': product_id.id,
                        'customer_note': product_line.get('kitchen_notes'),
                        'full_product_name': product_id.name,
                        'qty': qty,
                        'price_unit': product_line.get('unit_price'),
                        'tax_ids': tax,
                        'discount_amount': discount_amount,
                        'price_subtotal': price_subtotal,
                        'price_subtotal_incl': price_subtotal_incl,
                        'refunded_orderline_id': order_line_id

                    }))

                for modifiers_line in product_line.get('options'):
                    modifiers_id = self.env['product.product'].search(
                        [('foodics_id', '=', modifiers_line.get('modifier_option').get('id'))], limit=1)
                    if not modifiers_id:
                        modifiers_vals = self.env['product.product'].prepare_modifier_data_foodics_to_odoo(modifiers_line.get('modifier_option'),
                                                                                                is_order=True, is_modifiers=True)
                        modifiers_id = self.env['product.product'].create(modifiers_vals)

                    qty = modifiers_line.get('quantity')
                    price_subtotal = float(modifiers_line.get('modifier_option').get('price')) * modifiers_line.get('quantity')
                    price_subtotal_incl = float(modifiers_line.get('modifier_option').get('price')) * modifiers_line.get('quantity')

                    order_line_id = False
                    if data.get('status') == 5:
                        qty = -qty
                        price_subtotal = -price_subtotal
                        price_subtotal_incl = -price_subtotal_incl

                        order_line_id = self.env['pos.order.line'].search(
                            [('order_id', '=', order_id), ('product_id', '=', modifiers_id.id), ('modifier_of', '=', product_id.name)])
                        for rec in order_line_id:
                            if rec.qty != rec.refunded_qty or rec.refunded_qty == 0.00:
                                if rec.id not in line_lst:
                                    order_line_id = rec
                                    line_lst.append(rec.id)
                                # order_line_id = rec
                        # order_line_id.filtered(lambda l: l.qty != l.refunded_qty or l.refunded_qty == 0.00)
                        if order_line_id:
                            order_line_id = order_line_id[0].id

                    vals.append((0, 0, {
                        'product_id': modifiers_id.id,
                        'modifier_of': product_id.name,
                        'full_product_name': modifiers_id.name,
                        'qty': qty,
                        'price_unit': modifiers_line.get('modifier_option').get('price'),
                        'price_subtotal': price_subtotal,
                        'price_subtotal_incl': price_subtotal_incl,
                        'refunded_orderline_id': order_line_id

                    }))

        if data.get('combos'):
            combos_line_lst = []
            for rec in data.get('combos'):
                for combos_product_line in rec.get('products'):
                    combos_product_id = self.env['product.product'].search(
                        [('foodics_id', '=', combos_product_line.get('product').get('id'))], limit=1)

                    if not combos_product_id:
                        # read_all_products = connector.call_foodics_api('GET', '/products/' + str(product_line.get('product').get('id')), {})
                        # for product_data in read_all_products.get('data'):
                        foodics_id = combos_product_line.get('product').get('id') or ''
                        if foodics_id:
                            product_vals = self.env['product.product'].prepare_data_foodics_to_odoo(combos_product_line.get('product'), is_order=True)
                            product_id = self.env['product.product'].create(product_vals)

                    tax = []
                    tax_id = False
                    tax_amount = 1

                    for combos_each_tax in combos_product_line.get('taxes'):
                        tax_id = self.env['account.tax'].search([('foodics_id', '=', combos_each_tax.get('id'))], limit=1)
                        if combos_each_tax.get('pivot', {}):
                            tax_amount_total += combos_each_tax.get('pivot', {}).get('amount')
                        if tax_id:
                            tax.append((4, tax_id.id))
                            tax_amount = tax_id.amount

                    if combos_product_id.id in self.lines.mapped('product_id').ids:
                        for combos_each_product in self.lines:
                            if combos_each_product.product_id.id == combos_product_id.id:

                                qty = combos_product_line.get('quantity')
                                discount_amount = combos_product_line.get('discount', {}).get(
                                    'amount') if combos_product_line.get(
                                    'discount', {}) else 0.00
                                price_subtotal = (combos_product_line.get('unit_price') * combos_product_line.get(
                                    'quantity')) - (combos_product_line.get('discount', {}).get(
                                    'amount') if combos_product_line.get(
                                    'discount', {}) else 0.00)
                                price_subtotal_incl = price_subtotal + (price_subtotal / 100 * tax_amount if tax_amount != 1 else 0)

                                order_line_id = False
                                if data.get('status') == 5:
                                    qty = -qty
                                    discount_amount = -discount_amount
                                    price_subtotal = -price_subtotal
                                    price_subtotal_incl = -price_subtotal_incl

                                    order_line_id = self.env['pos.order.line'].search(
                                        [('order_id', '=', order_id), ('product_id', '=', combos_each_product.product_id.id),
                                         ('qty', '!=', combos_each_product.refunded_qty)], limit=1).id

                                combos_each_product.write({
                                    'qty': qty,
                                    'price_unit': combos_product_line.get('unit_price'),
                                    'tax_ids': tax,
                                    'discount_amount': discount_amount,
                                    'price_subtotal': price_subtotal,
                                    'price_subtotal_incl': price_subtotal_incl,
                                    'refunded_orderline_id': order_line_id
                                })
                    else:
                        qty = combos_product_line.get('quantity')
                        discount_amount = combos_product_line.get('discount_amount', {})
                        price_subtotal = (combos_product_line.get('unit_price') * combos_product_line.get(
                            'quantity')) - combos_product_line.get('discount_amount', {})
                        price_subtotal_incl = price_subtotal + (price_subtotal / 100 * tax_amount if tax_amount != 1 else 0)

                        order_line_id = False
                        if data.get('status') == 5:
                            qty = -qty
                            discount_amount = -discount_amount
                            price_subtotal = -price_subtotal
                            price_subtotal_incl = -price_subtotal_incl

                            order_line_id = self.env['pos.order.line'].search(
                                [('order_id', '=', order_id), ('product_id', '=', combos_product_id.id)])

                            for rec_combo in order_line_id:
                                if rec_combo.qty != rec_combo.refunded_qty or rec_combo.refunded_qty == 0.00:
                                    if rec_combo.id not in combos_line_lst:
                                        order_line_id = rec_combo
                                        combos_line_lst.append(rec_combo.id)
                                    # order_line_id = rec_combo
                            # order_line_id.filtered(lambda l: l.qty != l.refunded_qty)
                            if order_line_id:
                                order_line_id = order_line_id[0].id
                        vals.append((0, 0, {
                            'product_id': combos_product_id.id,
                            'customer_note': combos_product_line.get('kitchen_notes'),
                            'full_product_name': combos_product_id.name,
                            'qty': qty,
                            'price_unit': combos_product_line.get('unit_price'),
                            'tax_ids': tax,
                            'discount_amount': discount_amount,
                            'price_subtotal': price_subtotal,
                            'price_subtotal_incl': price_subtotal_incl,
                            'refunded_orderline_id': order_line_id,
                        }))

                    for combos_modifiers_line in combos_product_line.get('options'):
                        modifiers_id = self.env['product.product'].search(
                            [('foodics_id', '=', combos_modifiers_line.get('modifier_option').get('id'))], limit=1)
                        if not modifiers_id:
                            modifiers_vals = self.env['product.product'].prepare_modifier_data_foodics_to_odoo(
                                combos_modifiers_line.get('modifier_option'),
                                is_order=True, is_modifiers=True)
                            modifiers_id = self.env['product.product'].create(modifiers_vals)

                        qty = combos_modifiers_line.get('quantity')
                        price_subtotal = float(
                            combos_modifiers_line.get('modifier_option').get('price')) * combos_modifiers_line.get(
                            'quantity')
                        price_subtotal_incl = float(
                            combos_modifiers_line.get('modifier_option').get('price')) * combos_modifiers_line.get(
                            'quantity')

                        order_line_id = False
                        if data.get('status') == 5:
                            qty = -qty
                            price_subtotal = -price_subtotal
                            price_subtotal_incl = -price_subtotal_incl

                            order_line_id = self.env['pos.order.line'].search(
                                [('order_id', '=', order_id), ('product_id', '=', modifiers_id.id), ('modifier_of', '=', combos_product_id.name)])

                            for rec_combo_modifiers in order_line_id:
                                if rec_combo_modifiers.qty != rec_combo_modifiers.refunded_qty or rec_combo_modifiers.refunded_qty == 0.00:
                                    if rec_combo_modifiers.id not in combos_line_lst:
                                        order_line_id = rec_combo_modifiers
                                        combos_line_lst.append(rec_combo_modifiers.id)
                                    # order_line_id = rec_combo_modifiers
                            # order_line_id.filtered(lambda l: l.qty != l.refunded_qty)
                            if order_line_id:
                                order_line_id = order_line_id[0].id

                        vals.append((0, 0, {
                            'product_id': modifiers_id.id,
                            'modifier_of': combos_product_id.name,
                            'full_product_name': modifiers_id.name,
                            'qty': qty,
                            'price_unit': combos_modifiers_line.get('modifier_option').get('price'),
                            'price_subtotal': price_subtotal,
                            'price_subtotal_incl': price_subtotal_incl,
                            'refunded_orderline_id': order_line_id,
                        }))

        name = data.get('reference')
        global_discount = data.get('discount_amount')
        amount_total = data.get('total_price')
        amount_paid = data.get('rounding_amount')

        if data.get('status') == 5:
            name = str(data.get('original_order', {}).get('reference')) + " REFUND"
            global_discount = -global_discount
            amount_total = -amount_total
            amount_paid = -amount_paid
        response = {
            'name': branch.name + '/' + str(name),
            'date_order': data.get('opened_at'),
            'session_id': branch.open_session_cb_backend(creator).id,
            'foodics_id': data.get('id'),
            'partner_id': partner.id if partner else False,
            'user_id': creator.id,
            'lines': vals,
            'amount_tax': tax_amount_total,
            'global_discount': global_discount,
            'amount_total': amount_total,
            'amount_paid': amount_paid,
            'amount_return': 0,
            'pricelist_id': self.env.ref('product.list0').id,
            'company_id': self.env.user.company_id.id or creator.company_id.id,
            'currency_id': self.env.user.company_id.currency_id and self.env.user.company_id.currency_id.id,
        }
        return response

    def create_payment(self, data):
        connector = self.env['foodic.connector'].search([('state', '=', 'authenticated')], limit=1)
        for payment_line in data:
            payment_method_id = self.env['pos.payment.method'].search(
                [('foodics_id', '=', payment_line.get('payment_method').get('id'))], limit=1)
            if not payment_method_id:
                read_all_payment_methods = connector.call_foodics_api('GET', '/payment_methods/' + payment_line.get(
                    'payment_method').get('id'), {})
                for payment_method in read_all_payment_methods.get('data'):
                    foodics_id = payment_method.get('id') or ''
                    if foodics_id:
                        vals = self.env['pos.payment.method'].prepare_payment_method_data(payment_method)
                        self.env['pos.payment.method'].create(vals)
                payment_method_id = self.env['pos.payment.method'].search(
                    [('foodics_id', '=', payment_line.get('payment_method').get('id'))], limit=1)

            ctx = {"active_ids": self.ids, "active_id": self.id}
            order_payment = self.env['pos.make.payment'].with_context(**ctx).create({
                'payment_method_id': payment_method_id.id,
                'amount': payment_line.get('amount'),
                'config_id': self.config_id.id
            })
            order_payment.with_context(**ctx).check()

    def prepare_data_odoo_to_foodics(self):
        """
        Prepare The Data for odoo to foodics
        :param data:
        :return:
        """
        pos_line = []
        for line in self.lines:
            tax = []
            for each_tax in line.tax_ids_after_fiscal_position:
                tax.append(
                    {
                        "id": each_tax.foodics_id,
                    }
                )
            pos_line.append({
                'product_id': line.product_id.foodics_id,
                'quantity': line.qty,
                'unit_price': line.price_unit,
                'taxes': tax
            })

        response = {
            'date_order': self.date_order,
            'session_id': self.session_id,
            'partner_id': self.partner_id,
            'products': pos_line,
        }

        return response


