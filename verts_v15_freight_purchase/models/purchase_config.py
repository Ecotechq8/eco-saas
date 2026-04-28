# -*- coding: utf-8 -*-
# Copyright 2020 Verts Services India Pvt. Ltd.
# http://www.verts.co.in

from odoo import api, fields, models, _

level_number_pa = [
    ('0', '0 level of Approval (Self Approval)'),
    ('1', '1 level of Approval (Deptt. Head)'),
    ('2', '2 levels of Approvals (Deptt. Head +1)'),
    ('3', '3 levels of Approvals (Deptt. Head +2)'),
    ('4', '4 levels of Approvals (Deptt. Head +3)'),
    ('5', '5 levels of Approvals (Deptt. Head +4)')
]

level_number_pr = [
    ('0', '0 level of Approval (Self Approval)'),
    ('1', '1 level of Approval (Deptt. Head)'),
    ('2', '2 levels of Approvals (Deptt. Head +1)'),
    ('3', '3 levels of Approvals (Deptt. Head +2)'),
    ('4', '4 levels of Approvals (Deptt. Head +3)'),
    ('5', '5 levels of Approvals (Deptt. Head +4)')
]

level_number_po = [
    ('0', '0 level of Approval (Self Approval)'),
    ('1', '1 level of Approval (Deptt. Head)'),
    ('2', '2 levels of Approvals (Deptt Head +1)'),
    ('3', '3 levels of Approvals (Deptt. Head +2)'),
    ('4', '4 levels of Approvals (Deptt. Head +3)'),
    ('5', '5 levels of Approvals (Deptt. Head +4)')
]

level_number_so = [
    ('0', '0 level of Approval (Self Approval)'),
    ('1', '1 level of Approval (Deptt. Head)'),
    ('2', '2 levels of Approvals (Deptt. Head +1)'),
    ('3', '3 levels of Approvals (Deptt. Head +2)'),
    ('4', '4 levels of Approvals (Deptt. Head +3)'),
    ('5', '5 levels of Approvals (Deptt. Head +4)')
]

level_number_npo = [
    ('0', '0 level of Approval (Self Approval)'),
    ('1', '1 level of Approval (Deptt. Head)'),
    ('2', '2 levels of Approvals (Deptt. Head +1)'),
    ('3', '3 levels of Approvals (Deptt. Head +2)'),
    ('4', '4 levels of Approvals (Deptt. Head +3)'),
    ('5', '5 levels of Approvals (Deptt. Head +4)')
]


class PurchaseConfig(models.Model):
    _name = 'purchase.config'
    _description = "Purchase Config"

    create_multiple_rfq = fields.Boolean(string='Create Multiple RFQ by Quote Comparison')

    po_label_button_name_1st = fields.Char("1st Label PO Button")
    po_label_button_name_2nd = fields.Char("2nd Label PO Button")
    po_label_button_name_3rd = fields.Char("3rd Label PO Button")
    po_label_button_name_4th = fields.Char("4th Label PO Button")
    po_label_button_name_5th = fields.Char("5th Label PO Button")

    po_double_validation_amt = fields.Float("PO Double validation amount")
    po_triple_validation_amount = fields.Float("PO Triple validation amount")
    po_fourth_validation_amount = fields.Float("PO Fourth validation amount")
    po_fifth_validation_amount = fields.Float("PO Fifth validation amount")
    po_sixth_validation_amount = fields.Float("PO Sixth validation amount")

    pr_label_button_name_1st = fields.Char("1st Label PR Button")
    pr_label_button_name_2nd = fields.Char("2nd Label PR Button")
    pr_label_button_name_3rd = fields.Char("3rd Label PR Button")
    pr_label_button_name_4th = fields.Char("4th Label PR Button")
    pr_label_button_name_5th = fields.Char("5th Label PR Button")

    pr_double_validation_amt = fields.Float("PR Double validation amount")
    pr_triple_validation_amount = fields.Float("PR Triple validation amount")
    pr_fourth_validation_amount = fields.Float("PR Fourth validation amount")
    pr_fifth_validation_amount = fields.Float("PR Fifth validation amount")
    pr_sixth_validation_amount = fields.Float("PR Sixth validation amount")

    po_label_state_name_1st = fields.Char("PO 1st Label State")
    po_label_state_name_2nd = fields.Char("PO 2nd Label State")
    po_label_state_name_3rd = fields.Char("PO 3rd Label State")
    po_label_state_name_4th = fields.Char("PO 4th Label State")
    po_label_state_name_5th = fields.Char("PO 5th Label State")

    pr_label_state_name_1st = fields.Char("PR 1st Label State")
    pr_label_state_name_2nd = fields.Char("PR 2nd Label State")
    pr_label_state_name_3rd = fields.Char("PR 3rd Label State")
    pr_label_state_name_4th = fields.Char("PR 4th Label State")
    pr_label_state_name_5th = fields.Char("PR 5th Label State")
    users_approval_line_pr = fields.One2many('users.approval.pr', 'pr_id', 'PR Users Approval Line')
    users_approval_line_po = fields.One2many('users.approval.po', 'po_id', 'PO Users Approval Line')
    tc_lines = fields.One2many('purchase.tc.line', 'res_config_id', string="T&C")

    product_on_off = fields.Selection(
        [
            ('0', 'OFF'),
            ('1', 'ON'),
        ], string='Product/Item',
        help="""""")

    description_on_off = fields.Selection(
        [
            ('0', 'OFF'),
            ('1', 'ON'),
        ], string='Description',
        help="""""")

    po_description = fields.Selection(
        [
            ('0', 'OFF'),
            ('1', 'ON'),
        ], string='PO Description',
        help="""""")

    so_description = fields.Selection(
        [
            ('0', 'OFF'),
            ('1', 'ON'),
        ], string='SO Description',
        help="""""")

    pr_sequence_number = fields.Selection(
        [
            ('0', 'Common'),
            ('1', 'Separate'),
        ], string='PR Seq. Numbers',
        help="""You can decide how you want the PR Sequence numbers to be generated""")
    pr_raw_prefix = fields.Char("PR-Raw Material Prefix")
    pr_gi_prefix = fields.Char("PR-General Items Prefix")
    pr_consu_prefix = fields.Char("PR-Consumable Prefix")
    pr_fa_prefix = fields.Char("PR-Fixed Assets Prefix")
    pr_service_prefix = fields.Char("PR-Service Prefix")

    pr_fg_prefix = fields.Char("PR-Finished Goods Prefix")
    pr_mix_prefix = fields.Char("PR-Mix Prefix")
    pr_semi_fg_wip_prefix = fields.Char("PR-Semi FG/WIP Prefix")

    pr_common_prefix = fields.Char("PR-Common Prefix")
    po_common_prefix = fields.Char("PO-Common Prefix")

    po_sequence_number = fields.Selection(
        [
            ('0', 'Common'),
            ('1', 'Separate'),
        ], string='PO Seq. Numbers',
        help="""You can decide how you want the PO Sequence numbers to be generated""")
    po_raw_prefix = fields.Char("PO-Raw Material Prefix")
    po_gi_prefix = fields.Char("PO-General Items Prefix")
    po_consu_prefix = fields.Char("PO-Consumable Prefix")
    po_fa_prefix = fields.Char("PO-Fixed Assets Prefix")

    po_date_readonly = fields.Selection(
        [
            ('0', 'Yes'),
            ('1', 'No'),
        ], string='PO Date Read Only',
        help="""You can decide if PO date should be manually selected or selected same send for first approval or same as last Approval Date""")
    po_date_as = fields.Selection(
        [
            ('0', 'Send for approval'),
            ('1', 'Final approval'),
        ], string='PO Date As',
        help="""whatever date is selected here will be marked as PO date.""")
    unit_price_in_po = fields.Selection(
        [
            ('0', 'Readonly'),
            ('1', 'Editable'),
        ], string='Unit Price in PO',
        help="""In PO Order line you can decide if the Unit price should be read only or editable. If Readonly then it will pick up Unit Price mentioned in the Item Master.""")
    unit_price_non_zero_only = fields.Selection(
        [
            ('0', 'Not Applicable'),
            ('1', 'Applicable'),
        ], string='Unit Price Non Zero Only',
        help="""In PO Order line you can decide if the Unit price should be zero or greater than zero. If Non Zero value then You can put value of Unit Price greater than zero.""")
    supplier_taxes_in_po = fields.Selection(
        [
            ('0', 'Readonly'),
            ('1', 'Editable'),
        ], string='Supplier Taxes in PO',
        help="""In PO Order line you can decide if the Supplier Taxes should be read only or editable. If Readonly then it will pick up taxes mentioned in the Item Master.""")
    hsn_sac_code_in_po = fields.Selection(
        [
            ('0', 'Readonly'),
            ('1', 'Editable'),
        ], string='HSN/SAC in PO',
        help="""In PO Order line you can decide if the HSN/SAC should be read only or editable. If Readonly then it will pick up HSN/SAC mentioned in the Item Master.""")

    pr_validation = fields.Selection(level_number_pr, string="PR Levels of Approvals", default=0, \
                                     help="Provide a Four validation mechanism for Purchase Requisition")

    po_validation = fields.Selection(level_number_po, string="PO Levels of Approvals", default=0, \
                                     help="Provide a Four validation mechanism for Purchase Order")

    po_date_visible_bool = fields.Boolean()
    grn_mandatory = fields.Selection(
        [
            ('0', 'Yes'),
            ('1', 'No'),
        ], string='GRN Mandatory for PO')
    # all_pr_disable = fields.Boolean(string='Disable Create button in All PR')
    # all_po_disable = fields.Boolean(string='Disable Create button in All PO')
    supplier_rating_formula_div = fields.Char(string="Supplier Rating formula",
                                              default="{(Supplies Accepted Without Deviation(n) / Total supplies in month (N)) * ",
                                              readonly=True)
    supplier_rating_formula_val1 = fields.Float()
    supplier_rating_formula_add = fields.Char(
        default="+  Total deliveries in time (A) / Total supplies in month (N)) * ", readonly=True)
    supplier_rating_formula_val2 = fields.Float()
    supplier_rating_formula_mul = fields.Char(default="}        *", readonly=True)
    supplier_rating_formula_val3 = fields.Float()
    all_pa_disable = fields.Boolean(string='Disable Create button in All Advance Requests')
    pa_validation = fields.Selection(level_number_pa, string="Levels of Approvals", default=0, \
                                     help="Provide a Four validation mechanism for Advance Requests")
    pa_label_button_name_1st = fields.Char("1st Label Button")
    pa_label_button_name_2nd = fields.Char("2nd Label Button")
    pa_label_button_name_3rd = fields.Char("3rd Label Button")
    pa_label_button_name_4th = fields.Char("4th Label Button")
    pa_label_button_name_5th = fields.Char("5th Label Button")

    pa_label_state_name_1st = fields.Char("1st Label State")
    pa_label_state_name_2nd = fields.Char("2nd Label State")
    pa_label_state_name_3rd = fields.Char("3rd Label State")
    pa_label_state_name_4th = fields.Char("4th Label State")
    pa_label_state_name_5th = fields.Char("5th Label State")

    allow_inv_from_pr = fields.Boolean(string='Allow Vendor Bills from PR',
                                       help="If this option is selected then you will see Create Vendor Bill button in the PR form.")
    users_approval_line_pa = fields.One2many('users.approval.pa', 'pa_id', 'Advance Requests Users Approval Line')

    mandatory_forecast = fields.Boolean(string='Forecast Mandatory?',
                                        help="If this option is selected then Forecast field will be mandatory on PR/PO.")
    mandatory_estimated_price = fields.Boolean(string='Estimated price Mandatory?',
                                               help="If this option is selected then Estimated price field will be mandatory on PR.")

    all_so_disable = fields.Boolean(string='Disable Create button in All Service Order')
    so_validation = fields.Selection(level_number_so, string="SO Levels of Approvals", default=0, \
                                     help="Provide a Four validation mechanism for Service Order")
    so_label_button_name_1st = fields.Char("SO 1st Label Button")
    so_label_button_name_2nd = fields.Char("SO 2nd Label Button")
    so_label_button_name_3rd = fields.Char("SO 3rd Label Button")
    so_label_button_name_4th = fields.Char("SO 4th Label Button")
    so_label_button_name_5th = fields.Char("SO 5th Label Button")

    so_label_state_name_1st = fields.Char("SO 1st Label State")
    so_label_state_name_2nd = fields.Char("SO 2nd Label State")
    so_label_state_name_3rd = fields.Char("SO 3rd Label State")
    so_label_state_name_4th = fields.Char("SO 4th Label State")
    so_label_state_name_5th = fields.Char("SO 5th Label State")

    so_double_validation_amt = fields.Float("SO Double validation amount")
    so_triple_validation_amount = fields.Float("SO Triple validation amount")
    so_fourth_validation_amount = fields.Float("SO Fourth validation amount")
    so_fifth_validation_amount = fields.Float("SO Fifth validation amount")
    so_sixth_validation_amount = fields.Float("SO Sixth validation amount")

    users_approval_line_so = fields.One2many('users.approval.so', 'so_id', 'Service Order Users Approval Line')

    npo_label_button_name_1st = fields.Char("NPO 1st Label Button")
    npo_label_button_name_2nd = fields.Char("NPO 2nd Label Button")
    npo_label_button_name_3rd = fields.Char("NPO 3rd Label Button")
    npo_label_button_name_4th = fields.Char("NPO 4th Label Button")
    npo_label_button_name_5th = fields.Char("NPO 5th Label Button")

    npo_label_state_name_1st = fields.Char("NPO 1st Label State")
    npo_label_state_name_2nd = fields.Char("NPO 2nd Label State")
    npo_label_state_name_3rd = fields.Char("NPO 3rd Label State")
    npo_label_state_name_4th = fields.Char("NPO 4th Label State")
    npo_label_state_name_5th = fields.Char("NPO 5th Label State")

    all_npo_disable = fields.Boolean(string='Disable Create button in All Non PO Item')
    users_approval_line_npo = fields.One2many('users.approval.npo', 'npo_id', 'Non PO Item Users Approval Line')
    npo_validation = fields.Selection(level_number_npo, string="NPO Levels of Approvals", default=0, \
                                      help="Provide a Four validation mechanism for Non PO Item")
    users_approval_line_qc = fields.One2many('users.approval.qc', 'qc_id', 'Non QC Item Users Approval Line')
    quote_validation = fields.Selection(level_number_npo, string="NPO Levels of Approvals", default=0, \
                                        help="Provide a Four validation mechanism for Non PO Item")

    npo_double_validation_amt = fields.Float("NPO Double validation amount")
    npo_triple_validation_amount = fields.Float("NPO Triple validation amount")
    npo_fourth_validation_amount = fields.Float("NPO Fourth validation amount")
    npo_fifth_validation_amount = fields.Float("NPO Fifth validation amount")
    npo_sixth_validation_amount = fields.Float("NPO Sixth validation amount")

    make_hsn_code_mandatory = fields.Boolean(string='Make HSN Code Mandatory',
                                             help="If this is True then HSN Code field in the Purchase form will become Mandatory.")
    make_taxes_mandatory = fields.Boolean(string='Make Taxes Mandatory',
                                          help="If this is True then Customer Taxes & Vendor Taxes fields in the Purchase form will become Mandatory.")
    make_hsn_code_readonly = fields.Boolean(string='Make HSN Code Readonly',
                                            help="If this is True then HSN Code Readonly in the Purchase Lines.")
    make_tnc_mandatory = fields.Boolean(string='Make T&C Mandatory',
                                        help="If this is True then Terms and Conditions Readonly in the Purchase Order.")

    pr_date_readonly = fields.Boolean("PR Date Readonly")
    is_doc = fields.Boolean("Doc ID")
    hide_vendor_in_pr = fields.Boolean(string='Hide Vendor Name in PR')
    show_customer_in_pr = fields.Boolean(string='show customer field in PR')
    show_sale_order_in_pr = fields.Boolean(string='Show Sale Order field in PR ')
    invisible_estimated_price_value = fields.Boolean(string='Invisible Estimated Price and Estimated Value in PR Lines')
    last_purchase_price = fields.Boolean(string='Last Purchase Price')


class UsersApproval(models.Model):
    _name = "users.approval.pr"
    _description = "Users Approval PR"

    pr_id = fields.Many2one('purchase.config', 'PO Config')
    user_id = fields.Many2one('res.users', "Approver")
    pr_mail_template = fields.Many2one('mail.template', string="Email template",
                                       help="This email will be sent to the Approver",
                                       domain=[('model_id.model', '=', 'purchase.requisition')])
    sequence = fields.Selection(string="Sequence", selection=[
        ('1st_lavels', '1st Levels Approval'),
        ('2st_lavels', '2nd Levels Approval'),
        ('3st_lavels', '3rd Levels Approval'),
        ('4st_lavels', '4th Levels Approval'),
        ('5st_lavels', '5th Levels Approval'), ], )
    sla_days = fields.Integer('SLA (Days)')


class UsersApprovalPO(models.Model):
    _name = "users.approval.po"
    _description = "Users Approval PO"

    po_id = fields.Many2one('purchase.config', 'PO Config')
    user_id = fields.Many2one('res.users', "Approver")
    po_mail_template = fields.Many2one('mail.template', string="Email template",
                                       help="This email will be sent to the Approver",
                                       domain=[('model_id.model', '=', 'purchase.order')])
    sequence = fields.Selection(string="Sequence", selection=[
        ('1st_lavels', '1st Levels Approval'),
        ('2nd_lavels', '2nd Levels Approval'),
        ('3rd_lavels', '3rd Levels Approval'),
        ('4th_lavels', '4th Levels Approval'),
        ('5th_lavels', '5th Levels Approval'), ], )
    sla_days = fields.Integer('SLA (Days)')


class PurchaseTcLine(models.Model):
    _name = "purchase.tc.line"
    _description = "Purchase TC Line"

    res_config_id = fields.Many2one('purchase.config', 'PO Config')
    po_id = fields.Many2one('purchase.order', 'Purchase Order')
    item = fields.Char("T&C")
    tc = fields.Char("Details")


class UsersApprovalPA(models.Model):
    _name = "users.approval.pa"
    _description = "Users Approval PA"

    pa_id = fields.Many2one('purchase.config', 'Advance Requests Config')
    user_id = fields.Many2one('res.users', "User")
    pa_mail_template = fields.Many2one('mail.template', string="Email template",
                                       help="This email will be sent to the Approver",
                                       domain=[('model_id.model', '=', 'purchase.advance')])
    sequence = fields.Selection(string="Sequence", selection=[
        ('1st_lavels', '1st Levels Approval'),
        ('2st_lavels', '2nd Levels Approval'),
        ('3st_lavels', '3rd Levels Approval'),
        ('4st_lavels', '4th Levels Approval'),
        ('5st_lavels', '5th Levels Approval'), ], )


class UsersApprovalSO(models.Model):
    _name = "users.approval.so"
    _description = "Users Approval SO"

    so_id = fields.Many2one('purchase.config', 'Service Order Config')
    user_id = fields.Many2one('res.users', "User")
    so_mail_template = fields.Many2one('mail.template', string="Email template",
                                       help="This email will be sent to the Approver",
                                       domain=[('model_id.model', '=', 'purchase.order')])
    sequence = fields.Selection(string="Sequence", selection=[
        ('1st_lavels', '1st Levels Approval'),
        ('2st_lavels', '2nd Levels Approval'),
        ('3st_lavels', '3rd Levels Approval'),
        ('4st_lavels', '4th Levels Approval'),
        ('5st_lavels', '5th Levels Approval'), ], )

    sla_days = fields.Integer('SLA (Days)')


class UsersApprovalNPO(models.Model):
    _name = "users.approval.npo"
    _description = "Users Approval NPO"

    npo_id = fields.Many2one('purchase.config', 'Non PO Item Config')
    user_id = fields.Many2one('res.users', "User")
    npo_mail_template = fields.Many2one('mail.template', string="Email template",
                                        help="This email will be sent to the Approver",
                                        domain=[('model_id.model', '=', 'purchase.order')])
    sequence = fields.Selection(string="Sequence", selection=[
        ('1st_lavels', '1st Levels Approval'),
        ('2st_lavels', '2nd Levels Approval'),
        ('3st_lavels', '3rd Levels Approval'),
        ('4st_lavels', '4th Levels Approval'),
        ('5st_lavels', '5th Levels Approval'), ], )


class UsersApprovalQC(models.Model):
    _name = "users.approval.qc"
    _description = "Users Approval QC"

    qc_id = fields.Many2one('purchase.config', 'Non PO Item Config')
    user_id = fields.Many2one('res.users', "User")
    qc_mail_template = fields.Many2one('mail.template', string="Email template",
                                       help="This email will be sent to the Approver",
                                       domain=[('model_id.model', '=', 'purchase.order')])
    sequence = fields.Selection(string="Sequence", selection=[
        ('1st_lavels', '1st Levels Approval'),
        ('2st_lavels', '2nd Levels Approval'),
        ('3st_lavels', '3rd Levels Approval'),
        ('4st_lavels', '4th Levels Approval'),
        ('5st_lavels', '5th Levels Approval'), ], )
