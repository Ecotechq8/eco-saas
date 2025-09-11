from odoo import models, fields, api, _
import io
import xlsxwriter
import base64
from datetime import datetime


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    binary_data = fields.Binary()

    def float_to_time(self, float_hour):
        hours = int(float_hour)
        minutes = int(round((float_hour - hours) * 60))
        return f"{hours:02d}:{minutes:02d}"

    def floats_to_times(self, float_list):
        return [self.float_to_time(f) for f in float_list]

    def action_print_attendance_report(self):
        self.ensure_one()

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Attendance Sheet')

        '''       /////                           Format         ///////          '''
        header_format = workbook.add_format({'bold': True, 'border': 1, 'align': 'center', 'font_size': 9})
        main_header_format = workbook.add_format(
            {'bold': True, 'border': 1, 'align': 'left', 'bg_color': '#A0A0A0', 'font_size': 9})
        normal_format = workbook.add_format({'bold': False, 'border': 1, 'align': 'center', 'font_size': 9})
        vertical_format = workbook.add_format({
            'rotation': 90,  # 0 degrees = horizontal
            'align': 'center',
            'valign': 'vcenter',
            'bold': True,
            'font_size': 13
        })
        worksheet.set_column('A:A', 3)
        worksheet.set_row(1, 12)

        '''       /////                           Header         ///////          '''
        attendance_sheet_lines = self.env['attendance.sheet.line'].sudo().search(
            [('employee_id', '=', self.employee_id.id), ('date', '>=', self.date_from),
             ('date', '<=', self.date_to)])
        dates = attendance_sheet_lines.mapped('date')
        dates = [dt.strftime('%Y-%m-%d') for dt in dates]

        days = attendance_sheet_lines.mapped('day')
        days = list(map(int, days))
        arabic_days = ['الاثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة', 'السبت', 'الأحد']
        day_names = [arabic_days[d] for d in days]

        row_num = 0
        worksheet.merge_range(row_num, 0, row_num, len(dates) + 1, 'حركة حضور وانصراف العاملين',
                              main_header_format)
        worksheet.set_column(2, len(dates) + 1, 6)  # columns are 0-indexed
        worksheet.fit_to_pages(1, 1)  # Fit to 1 page wide by 1 page tall
        worksheet.set_landscape()  # Optional: landscape orientation
        worksheet.center_horizontally()
        worksheet.set_margins(left=0.2, right=0.2, top=0.5, bottom=0.5)

        row_num += 1
        worksheet.write(row_num, 1, '', header_format)
        row_num += 1

        worksheet.merge_range(row_num, 0, 12, 0, self.employee_id.name, vertical_format)
        row_num += 1

        '''       /////                       Main Data             ///////          '''
        check_in = []
        check_out = []
        worked_hours = []
        late_in = []
        penalities = []
        overtime = []
        overtime_per = []
        permitted_timeoff = []
        unpermitted_time_off = []
        holidays = []

        for line in attendance_sheet_lines:
            check_in.append(line.ac_sign_in)
            check_out.append(line.ac_sign_out)
            worked_hours.append(line.worked_hours)
            late_in.append(line.late_in)
            penalities.append(0)
            overtime.append(line.overtime)
            overtime_per.append(0)
            permitted_timeoff.append(0)
            unpermitted_time_off.append(0)
            holidays.append(0)

        col_num = 2
        for day in day_names:
            worksheet.write(1, col_num, day, header_format)
            col_num += 1

        col_num = 2
        for date in dates:
            month = datetime.strptime(str(date), '%Y-%m-%d').month
            day = datetime.strptime(str(date), '%Y-%m-%d').day
            worksheet.write(2, col_num, str(month) + '-' + str(day), header_format)
            col_num += 1

        check_in = self.floats_to_times(check_in)
        worksheet.write(row_num, 1, 'حضور', header_format)
        col_num = 2
        for chi in check_in:
            worksheet.write(row_num, col_num, chi, normal_format)
            col_num += 1
        row_num += 1

        check_out = self.floats_to_times(check_out)
        worksheet.write(row_num, 1, 'انصراف', header_format)
        col_num = 2
        for cho in check_out:
            worksheet.write(row_num, col_num, cho, normal_format)
            col_num += 1
        row_num += 1

        worked_hours = self.floats_to_times(worked_hours)
        worksheet.write(row_num, 1, 'ساعات', header_format)
        col_num = 2
        for wh in worked_hours:
            worksheet.write(row_num, col_num, wh, normal_format)
            col_num += 1
        row_num += 1

        late_in = self.floats_to_times(late_in)
        worksheet.write(row_num, 1, 'تأخير', header_format)
        col_num = 2
        for li in late_in:
            worksheet.write(row_num, col_num, li, normal_format)
            col_num += 1
        row_num += 1

        penalities = self.floats_to_times(penalities)
        worksheet.write(row_num, 1, 'جزاءات', header_format)
        col_num = 2
        for ps in penalities:
            worksheet.write(row_num, col_num, ps, normal_format)
            col_num += 1
        row_num += 1

        overtime = self.floats_to_times(overtime)
        worksheet.write(row_num, 1, 'اضافى', header_format)
        col_num = 2
        for ot in overtime:
            worksheet.write(row_num, col_num, ot, normal_format)
            col_num += 1
        row_num += 1

        overtime_per = self.floats_to_times(overtime_per)
        worksheet.write(row_num, 1, 'اضافى-ج', header_format)
        col_num = 2
        for otp in overtime_per:
            worksheet.write(row_num, col_num, otp, normal_format)
            col_num += 1
        row_num += 1

        permitted_timeoff = self.floats_to_times(permitted_timeoff)
        worksheet.write(row_num, 1, 'غ.اذن', header_format)
        col_num = 2
        for pto in permitted_timeoff:
            worksheet.write(row_num, col_num, pto, normal_format)
            col_num += 1
        row_num += 1

        unpermitted_time_off = self.floats_to_times(unpermitted_time_off)
        worksheet.write(row_num, 1, 'غ.ب.اذن', header_format)
        col_num = 2
        for unpto in unpermitted_time_off:
            worksheet.write(row_num, col_num, unpto, normal_format)
            col_num += 1
        row_num += 1

        holidays = self.floats_to_times(holidays)
        worksheet.write(row_num, 1, 'اجازات', header_format)
        col_num = 2
        for hd in holidays:
            worksheet.write(row_num, col_num, hd, normal_format)
            col_num += 1
        row_num += 2

        salary_computation_line = self.line_ids
        basic_amount_line = salary_computation_line.filtered(lambda e: e.salary_rule_id.sequence == 1)
        extra_allowance_line = salary_computation_line.filtered(lambda e: e.salary_rule_id.sequence == 23)
        ovt_allowance_line = salary_computation_line.filtered(lambda e: e.salary_rule_id.sequence == 30)
        ded_allowance_line = salary_computation_line.filtered(lambda e: e.salary_rule_id.sequence == 60)
        loan_allowance_line = salary_computation_line.filtered(lambda e: e.salary_rule_id.sequence == 190)

        related_attendance_sheet = self.env['attendance.sheet'].sudo().search([('payslip_id', '=', self.id)])
        ph_overtime_days = len(related_attendance_sheet.line_ids.filtered(
            lambda sh: sh.status == 'ph' and sh.ac_sign_in > 0 and sh.ac_sign_out > 0))
        ph_overtime_hours = ph_overtime_days * related_attendance_sheet.contract_id.workdays_hour
        ph_overtime_amount = ph_overtime_hours * related_attendance_sheet.contract_id.hour_value
        ''''            ////                    Totals          ////            '''
        # ''''total first row'''' #
        worksheet.merge_range(row_num, 0, row_num, 1, 'الأساسي:', header_format)
        worksheet.write(row_num, 2, self.contract_id.wage, header_format)
        worksheet.write(row_num, 3, "أساسي المدة:", header_format)
        worksheet.write(row_num, 4, basic_amount_line.amount if basic_amount_line.amount else 0, header_format)
        worksheet.write(row_num, 5, "اضافى:", header_format)
        worksheet.write(row_num, 6, ovt_allowance_line.amount if ovt_allowance_line.amount else 0, header_format)
        worksheet.write(row_num, 7, 0, header_format)
        worksheet.write(row_num, 8, 0, header_format)
        worksheet.write(row_num, 9, "قسط التأمينات:", header_format)
        worksheet.write(row_num, 10, ded_allowance_line.amount if ded_allowance_line.amount else 0, header_format)
        worksheet.write(row_num, 11, " التأخير:", header_format)
        worksheet.write(row_num, 12, 0, header_format)
        worksheet.write(row_num, 13, 0, header_format)
        worksheet.write(row_num, 14, 0, header_format)
        worksheet.write(row_num, 15, "الإجمالى", header_format)
        row_num += 1

        # ''''               total second row                    '''' #
        worksheet.merge_range(row_num, 0, row_num, 1, 'أجر اليوم :', header_format)
        worksheet.write(row_num, 2, round(self.contract_id.wage / 30, 3), header_format)
        worksheet.write(row_num, 3, "بدلات :", header_format)
        worksheet.write(row_num, 4, extra_allowance_line.amount if extra_allowance_line.amount else 0, header_format)
        worksheet.write(row_num, 5, "سهرات9:", header_format)
        worksheet.write(row_num, 6, 0, header_format)
        worksheet.write(row_num, 7, 0, header_format)
        worksheet.write(row_num, 8, 0, header_format)
        worksheet.write(row_num, 9, "سلف :", header_format)
        worksheet.write(row_num, 10, loan_allowance_line.amount if loan_allowance_line else 0, header_format)
        worksheet.write(row_num, 11, " ج بدون أجر:", header_format)
        worksheet.write(row_num, 12, 0, header_format)
        worksheet.write(row_num, 13, 0, header_format)
        worksheet.write(row_num, 14, 0, header_format)
        worksheet.write(row_num, 15, "مجموع الصف", header_format)
        row_num += 1

        # ''''               total third row                    '''' #
        total_working_hours = self.contract_id.resource_calendar_id.total_worked_hours
        worksheet.merge_range(row_num, 0, row_num, 1, 'عدد الساعات  :', header_format)
        worksheet.write(row_num, 2, self.contract_id.workdays_hour, header_format)
        worksheet.write(row_num, 3, " حافز انتظام :", header_format)
        worksheet.write(row_num, 4, 0, header_format)
        worksheet.write(row_num, 5, "سهرات1:", header_format)
        worksheet.write(row_num, 6, 0, header_format)
        worksheet.write(row_num, 7, "أجمالى", header_format)
        worksheet.write(row_num, 8, 0, header_format)
        worksheet.write(row_num, 9, "جزاءات إدارية :", header_format)
        worksheet.write(row_num, 10, 0, header_format)
        worksheet.write(row_num, 11, "غياب:", header_format)
        worksheet.write(row_num, 12, 0, header_format)
        worksheet.write(row_num, 13, 0, header_format)
        worksheet.write(row_num, 14, 0, header_format)
        worksheet.write(row_num, 15, "مجموع الصف", header_format)
        row_num += 1

        # ''''               total forth row                    '''' #
        worksheet.merge_range(row_num, 0, row_num, 1, 'أجر الساعة   :', header_format)
        worksheet.write(row_num, 2, self.contract_id.hour_value, header_format)
        worksheet.merge_range(row_num, 2, row_num, 2, self.employee_id.contract_id.wage, header_format)
        worksheet.write(row_num, 3, "اضافى-ج ", header_format)
        worksheet.write(row_num, 4, "", header_format)
        worksheet.write(row_num, 5, "بدل راحات:", header_format)
        worksheet.write(row_num, 6, ph_overtime_amount, header_format)
        worksheet.write(row_num, 7, 0, header_format)
        worksheet.write(row_num, 8, 0, header_format)
        worksheet.write(row_num, 9, "", header_format)
        worksheet.write(row_num, 10, "", header_format)
        worksheet.write(row_num, 11, "", header_format)
        worksheet.write(row_num, 12, "", header_format)
        worksheet.write(row_num, 13, "", header_format)
        worksheet.write(row_num, 14, "", header_format)
        worksheet.write(row_num, 15, "", header_format)
        row_num += 1

        # ''''               total last row                    '''' #
        worksheet.merge_range(row_num, 0, row_num, 1, 'أيام العمل    :', header_format)
        worksheet.merge_range(row_num, 2, row_num, 2, self.contract_id.number_of_month_days, header_format)
        worksheet.write(row_num, 5, " أجمالى:", header_format)
        worksheet.write(row_num, 8, 0, header_format)
        worksheet.write(row_num, 14, "  == ", header_format)
        worksheet.write(row_num, 15, "total", header_format)
        worksheet.set_row(row_num, 30)

        workbook.close()
        output.seek(0)
        filename = 'Monthly Attendance.xlsx'

        output = base64.encodebytes(output.read())

        self.write({'binary_data': output})

        return {'type': 'ir.actions.act_url',
                'url': 'web/content/?model=hr.payslip&field=binary_data&download=true&id=%s&filename=%s' % (
                    self.id, filename), 'target': 'new', }
