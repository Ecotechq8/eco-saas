from odoo import fields, models, api, _


class HrContract(models.Model):
    _inherit = 'hr.contract'

    e_modify_contract_info = fields.Boolean(compute='_compute_modify_contract_info')

    @api.onchange('employee_id')
    def set_contract_reference(self):
        self.name = self.employee_id.pin

    def _compute_modify_contract_info(self):
        for contract in self.filtered('employee_id'):
            contract.e_modify_contract_info = True
            contract.department_id = contract.employee_id.department_id
            # contract.resource_calendar_id = contract.employee_id.resource_calendar_id
            contract.att_policy_id = contract.employee_id.department_id.e_att_policy_id

    # @api.onchange('department_id')
    # def set_department_info(self):
    #     self.resource_calendar_id = self.department_id.e_resource_calendar_id
    #     self.att_policy_id = self.department_id.e_att_policy_id
