from odoo import fields, models, api, _


class HrContract(models.Model):
    _inherit = 'hr.contract'

    contract_join_date = fields.Date()
    contract_start_training = fields.Date()
    contract_end_training = fields.Date()

    # Allowances
    housing_allowance = fields.Monetary()
    transportation_allowance = fields.Monetary()
    other_allowances = fields.Monetary()
    refunded_salary = fields.Monetary()
    flat_bonus = fields.Monetary()
    total_amount = fields.Monetary(compute='get_total_amount', string='Total Salary ')

    # def _update_related_comp_requests(self):
    #     config = self.env['ir.config_parameter'].sudo()
    #
    #     for contract in self:
    #         requests = self.env['compensation.request'].search([
    #             ('employee_id', '=', contract.employee_id.id)
    #         ])
    #
    #         for req in requests:
    #             total = 0.0
    #             if config.get_param('eos_with_allow1') == 'True':
    #                 total += contract.housing_allowance or 0.0
    #             if config.get_param('eos_with_allow2') == 'True':
    #                 total += contract.transportation_allowance or 0.0
    #             if config.get_param('eos_with_allow3') == 'True':
    #                 total += contract.other_allowance or 0.0
    #             if config.get_param('eos_with_allow4') == 'True':
    #                 total += contract.food_allowance or 0.0
    #             if config.get_param('eos_with_allow5') == 'True':
    #                 total += contract.fuel_allowance or 0.0
    #
    #             req.allowances = total

    def write(self, vals):
        result = super().write(vals)
        tracked_fields = [
            'housing_allowance',
            'transportation_allowance',
            'other_allowance',
            'food_allowance',
            'fuel_allowance'
        ]

        if any(field in vals for field in tracked_fields):
            for contract in self:
                # contract._update_related_comp_requests()

        return result

    @api.model
    def create(self, vals):
        contract = super().create(vals)
        tracked_fields = [
            'housing_allowance',
            'transportation_allowance',
            'other_allowance',
            'food_allowance',
            'fuel_allowance'
        ]
        if any(field in vals for field in tracked_fields):
            # contract._update_related_comp_requests()
        return contract

    @api.depends('wage', 'housing_allowance', 'fuel_allowance', 'food_allowance', 'transportation_allowance',
                 'other_allowances', 'refunded_salary')
    def get_total_amount(self):
        for item in self:
            item.total_amount = (item.wage + item.housing_allowance + item.transportation_allowance
                                 + item.fuel_allowance + item.food_allowance + item.other_allowances + item.refunded_salary)

    workdays_hour = fields.Float(digits=(12, 3))
    number_of_month_days = fields.Float(string='No. Month Days', digits=(12, 3))
    hour_value = fields.Float(compute='compute_hour_value', digits=(12, 3))
    day_value = fields.Float(compute='compute_day_value', digits=(12, 3))

    def compute_day_value(self):
        for item in self:
            item.day_value = 0.0
            if item.wage and item.number_of_month_days:
                item.day_value = item.wage / item.number_of_month_days

    def compute_hour_value(self):
        for rec in self:
            rec.hour_value = 0.0
            if rec.day_value and rec.workdays_hour:
                rec.hour_value = rec.day_value / rec.workdays_hour

    medical_details = fields.Boolean()
    insurance_company = fields.Many2one(comodel_name='insurance.company')
    insurance_number = fields.Char()
    insurance_start_date = fields.Date()
    insurance_end_date = fields.Date()

    payment_type = fields.Selection(selection=[('bank', 'Bank'),
                                               ('cash', 'Cash')])

    fuel_allowance = fields.Monetary()
    food_allowance = fields.Monetary()
