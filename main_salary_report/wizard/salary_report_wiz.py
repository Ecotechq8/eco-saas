from dateutil.relativedelta import relativedelta
from odoo import fields, models, api, _
from datetime import datetime, date

from odoo.exceptions import ValidationError


class EmployeeSalaryData(models.TransientModel):
    _name = 'employee.salary.data'

    employee_name = fields.Char()
    department_id = fields.Char()
    related_employee_salary = fields.Many2one(comodel_name='main.salary.wiz')


class MonthlySalaryWizard(models.TransientModel):
    _name = 'main.salary.wiz'

    month = fields.Char(compute='get_month_from_date')

    @api.depends('date_from')
    def get_month_from_date(self):
        for item in self:
            if item.date_from:
                item.month = datetime.strptime(str(item.date_from), "%Y-%m-%d").strftime('%B')

    date_from = fields.Date(string='Date From', readonly=False, required=True,
                            default=lambda self: fields.Date.to_string(date.today().replace(day=1)), )
    date_to = fields.Date(string='Date To', readonly=False, required=True,
                          default=lambda self: fields.Date.to_string((datetime.now() + relativedelta(months=+1, day=1,
                                                                                                     days=-1)).date()))
    employees_ids = fields.Many2many(comodel_name='hr.employee')
    departments_ids = fields.Many2many(comodel_name='hr.department')
    job_positions_ids = fields.Many2many(comodel_name='hr.job')

    salary_data_ids = fields.One2many(comodel_name='employee.salary.data', inverse_name='related_employee_salary')

    def get_data(self):
        domain = [('date_from', '>=', self.date_from), ('date_to', '<=', self.date_to)]
        if self.employees_ids:
            domain += [('employee_id', 'in', self.employees_ids.mapped('id'))]
        if self.departments_ids:
            domain += [('department_id', 'in', self.departments_ids.mapped('id'))]
        if self.job_positions_ids:
            domain += [('employee_id.job_id', 'in', self.job_positions_ids.mapped('id'))]

        payrolls = self.env['hr.payslip'].search(domain)
        if payrolls:
            for pay in payrolls:
                self.salary_data_ids = [(0, 0, {
                    'employee_name': pay.employee_id.name,
                    'department_id': pay.employee_id.department_id.name})]
        else:
            raise ValidationError(_('No record to print!!!'))

    def print_excel_report(self):
        data = {'ids': self.ids, 'model': self._name}
        report_action = self.env.ref('main_salary_report.main_salary_report_xlsx').report_action(self, data=data)
        report_action['close_on_report_download'] = True
        return report_action


class MainSalaryReportXlsx(models.AbstractModel):
    _name = 'report.main_salary_report.main_salary_report_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    @api.model
    def generate_xlsx_report(self, workbook, data, objs):
        record = self.env['main.salary.wiz'].browse(self.env.context.get('active_id'))
        record.get_data()
        domain = [('date_from', '>=', record.date_from), ('date_to', '<=', record.date_to)]
        if record.employees_ids:
            domain += [('employee_id', 'in', record.employees_ids.mapped('id'))]
        if record.departments_ids:
            domain += [('department_id', 'in', record.departments_ids.mapped('id'))]
        if record.job_positions_ids:
            domain += [('employee_id.job_id', 'in', record.job_positions_ids.mapped('id'))]

        payrolls = self.env['hr.payslip'].search(domain)

        sheet = workbook.add_worksheet('كشف رواتب الموظفين')
        sheet.right_to_left()
        format1 = workbook.add_format(
            {'font_size': 15, 'bottom': True, 'right': True, 'left': True, 'top': True, 'align': 'center',
             'bold': False})
        format2 = workbook.add_format(
            {'font_size': 15, 'bottom': True, 'right': True, 'left': True, 'top': True, 'align': 'center',
             'bold': True})
        format3 = workbook.add_format(
            {'font_size': 15, 'bottom': True, 'right': True, 'left': True, 'top': True, 'align': 'center',
             'bold': True})
        format4 = workbook.add_format(
            {'font_size': 15, 'bottom': False, 'right': False, 'left': False, 'top': False, 'align': 'left',
             'bold': True})

        format2.set_align('center')
        format2.set_align('vcenter')
        format1.set_font_color('black')
        format2.set_font_color('black')
        format3.set_font_color('black')
        format4.set_font_color('black')
        format2.set_fg_color('#d3d3d3')
        format3.set_fg_color('#b1dd9e')

        sheet.set_column('A:A', 10)
        sheet.set_column('B:B', 25)
        sheet.set_column('C:C', 45)
        sheet.set_column('D:D', 25)
        sheet.set_column('E:E', 25)
        sheet.set_column('F:F', 25)
        sheet.set_column('G:G', 25)
        sheet.set_column('H:H', 25)
        sheet.set_column('I:I', 25)
        sheet.set_column('J:J', 25)
        sheet.set_column('K:K', 25)
        sheet.set_column('L:L', 25)
        sheet.set_column('M:M', 25)
        sheet.set_column('N:N', 25)
        sheet.set_column('O:O', 25)
        sheet.set_column('P:P', 25)
        sheet.set_column('Q:Q', 25)
        sheet.set_column('R:R', 25)
        sheet.set_column('S:S', 25)
        sheet.set_column('T:T', 40)
        sheet.set_column('U:U', 40)
        sheet.set_column('V:V', 25)
        sheet.set_column('W:W', 25)
        sheet.set_column('X:X', 25)
        sheet.set_column('Y:Y', 25)
        sheet.set_column('Z:Z', 25)

        sheet.merge_range('A2:Z2', 'كـشـف رواتـب عن شـهـر ' + record.month + ' سنة ' + str(record.date_from.year),
                          format2)
        row, col = 3, 0

        salary_rules = self.env['hr.payroll.structure'].search([('use_in_report', '=', True)])

        # Headers
        headers = ['م', 'رقم الموظف', 'اسم الموظف', 'الوظيفة', 'أيام العمل']
        rules = salary_rules.rule_ids.sorted('sequence')
        # allowances_headers = [rec.name for rec in salary_rules.rule_ids.filtered(
        #     lambda x: x.category_id.name == 'Allowance')]
        # total_allowances_headers = ['اجمالى اضافى', 'اجمالى الراتب']

        # deductions_headers = [rec.name for rec in salary_rules.rule_ids.filtered(
        #     lambda x: x.category_id.name == 'Deduction')]
        # total_deductions_headers = ['اجمالى الخصومات', 'صافى الراتب']

        bank_details_headers = ['البنك', 'رقم الحساب']
        headers += [rec.name for rec in rules]
        for col, header in enumerate(headers):
            sheet.write(3, col, header, format2)
            col += 1

        # for allowance_col, header in enumerate(allowances_headers):
        #     sheet.write(3, col, header, format2)
        #     col += 1

        # for total_allowance_col, header in enumerate(total_allowances_headers):
        #     sheet.write(3, col, header, format2)
        #     col += 1

        # for deduction_col, header in enumerate(deductions_headers):
        #     sheet.write(3, col, header, format2)
        #     col += 1

        # for total_deduction_col, header in enumerate(total_deductions_headers):
        #     sheet.write(3, col, header, format2)
        #     col += 1

        for bank_details_col, header in enumerate(bank_details_headers):
            sheet.write(3, col, header, format2)
            col += 1

        row += 1
        col = 0
        departments = []
        for line in record.salary_data_ids:
            departments.append(line.department_id)

        for dep in set(departments):
            total1, total2, total3, i = 0.0, 0.0, 0.0, 1
            total_of_total_allowance, total_of_total_deductions = 0.0, 0.0

            sheet.merge_range(row, col, row, col + 2, dep, format2)
            row += 2

            for line in payrolls:

                if line.employee_id.department_id.name == dep:

                    sheet.write(row, col, i, format1)
                    sheet.write(row, col + 1, line.employee_id.pin or '-', format1)
                    sheet.write(row, col + 2, line.employee_id.name, format1)
                    sheet.write(row, col + 3, line.employee_id.job_id.name or '-', format1)
                    worked_days_list = line.worked_days_line_ids.filtered(
                        lambda w: w.work_entry_type_id.code == 'WORK100').mapped('number_of_days')
                    sheet.write(row, col + 4, worked_days_list[0] if worked_days_list else 0, format1)
                    col, total_allowance, basic_salary, total_deduction = 5, 0, 0, 0
                    for rule in rules:
                        rule_amount = line.line_ids.filtered(lambda x: x.salary_rule_id.id == rule.id).mapped('amount')

                        sheet.write(row, col, rule_amount[0] if rule_amount else 0, format1)
                        # basic_salary = item.amount
                        col += 1

                    # for item in line.line_ids.filtered(lambda x: x.category_id.name == 'Allowance'):
                    #     if item.name in allowances_headers:
                    #         sheet.write(row, col, item.amount, format1)
                    #         col += 1
                    #         displayed_allowance.append(item.name)
                    #         total_allowance += item.amount
                    #
                    # for rec in allowances_headers:
                    #     if rec not in displayed_allowance:
                    #         sheet.write(row, col, 0.0, format1)
                    #         col += 1
                    # print(col, col + 1)
                    # sheet.write(row, col, total_allowance, format1)
                    # col += 1
                    # sheet.write(row, col, basic_salary + total_allowance, format1)
                    #
                    # col += 1
                    # for item in line.line_ids.filtered(lambda x: x.category_id.name == 'Deduction'):
                    #     if item.name in deductions_headers:
                    #         sheet.write(row, col, item.amount, format1)
                    #         col += 1
                    #         displayed_deduction.append(item.name)
                    #         total_deduction += item.amount
                    #
                    # for rec in deductions_headers:
                    #     if rec not in displayed_deduction:
                    #         sheet.write(row, col, 0.0, format1)
                    #         col += 1
                    #
                    # sheet.write(row, col, total_deduction, format1)
                    # col += 1
                    # sheet.write(row, col, basic_salary + total_allowance - total_deduction, format1)
                    # col += 1
                    sheet.write(row, col, line.employee_id.bank_account_id.acc_number or '-', format1)
                    col += 1
                    sheet.write(row, col, line.employee_id.bank_account_id.bank_id.name or '-', format1)

                    # total1 += float(basic_salary)
                    # total_of_total_allowance += float(line.total_all_allowances)
                    # total2 += float(basic_salary + total_allowance)
                    # total_of_total_deductions += float(line.total_deductions)
                    # total3 += float(basic_salary + total_allowance - total_deduction)
                    row += 1
                    col = 0
                    i += 1

            row += 2
            # sheet.merge_range(row, 0, row, 4, 'الاجمالى', format2)
            # sheet.write(row, 5, total1, format2)
            # sheet.merge_range(row, 6, row, 10, '', format2)
            # sheet.write(row, 11, total2, format2)
            # sheet.merge_range(row, 12, row, 17, '', format2)
            # sheet.write(row, 18, total_of_total_allowance, format2)
            # sheet.merge_range(row, 19, row, 25, '', format2)
            # sheet.write(row, 26, total_of_total_deductions, format2)
            # sheet.write(row, 27, total3, format2)
            # sheet.merge_range(row, 28, row, 29, '', format2)
            # row += 2
