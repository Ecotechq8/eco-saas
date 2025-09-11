# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import AccessDenied


class HrPortalOperation(models.Model):
    _inherit = 'hr.operation'

    @api.model
    def cancel_operation(self, values):
        operation = self.env['hr.operation'].browse(int(values['op_id']))
        operation.write({
            'cancellation_reason': values['name'],
            'state': 'cancelled'
        })
        return {"id": operation.id}

    @api.model
    def create_opFrom_portal(self, values):
        if not self.env.user.employee_id:
            raise AccessDenied()

        op_type = self.env['hr.operation.type'].browse(int(values['type_id']))

        if not (values['date'] and values['type_id']):
            return {
                'errors': _('All fields are required !')
            }
        create_values = {
            'employee_id': int(values.get('employee_id', self.env.user.employee_id.id)),
            'date': values['date'],
            'type_id': int(values['type_id']),
        }

        if op_type.show_fields == "final_release":
            if not (values.get('last_work_date')):
                return {
                    'errors': _('All fields are required !')
                }
            create_values['last_work_date'] = values['last_work_date']

        if op_type.show_fields == "passport_withdrawal":
            if not (values.get('passport_delivery_date') and values.get('passport_receive_date') and values.get(
                    'purpose_of_passport_withdrawal')):
                return {
                    'errors': _('All fields are required !')
                }
            create_values['passport_delivery_date'] = values['passport_delivery_date']
            create_values['passport_receive_date'] = values['passport_receive_date']
            create_values['purpose_of_passport_withdrawal'] = values['purpose_of_passport_withdrawal']

        if op_type.show_fields == "investigation_call":
            if not (values.get('calling_date') and values.get('calling_time')):
                return {
                    'errors': _('All fields are required !')
                }
            create_values['calling_date'] = values['calling_date']
            create_values['calling_time'] = values['calling_time']

        if op_type.show_fields == "proceed_work_leave":
            if not (values.get('date_resumes_duty') and values.get('reason_change_resume_date')):
                return {
                    'errors': _('All fields are required !')
                }
            create_values['date_resumes_duty'] = values['date_resumes_duty']
            create_values['reason_change_resume_date'] = values['reason_change_resume_date']

        if op_type.show_fields == "proceed_work":
            if not values.get('to_mr_miss'):
                return {
                    'errors': _('All fields are required !')
                }
            create_values['to_mr_miss'] = values['to_mr_miss']

        myoperation = self.env['hr.operation'].sudo().create(create_values)
        return {'id': myoperation.id}
