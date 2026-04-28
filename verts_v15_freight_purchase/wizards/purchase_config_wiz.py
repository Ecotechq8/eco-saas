# -*- coding: utf-8 -*-
# Copyright 2020 Verts Services India Pvt. Ltd.
# http://www.verts.co.in

from odoo import api, fields, models

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

level_number_pa = [
    ('0', '0 level of Approval (Self Approval)'),
    ('1', '1 level of Approval (Deptt. Head)'),
    ('2', '2 levels of Approvals (Deptt. Head +1)'),
    ('3', '3 levels of Approvals (Deptt. Head +2)'),
    ('4', '4 levels of Approvals (Deptt. Head +3)'),
    ('5', '5 levels of Approvals (Deptt. Head +4)')
]

level_number_so = [
    ('0', '0 level of Approval (Self Approval)'),
    ('1', '1 level of Approval (Deptt. Head)'),
    ('2', '2 levels of Approvals (Deptt Head +1)'),
    ('3', '3 levels of Approvals (Deptt. Head +2)'),
    ('4', '4 levels of Approvals (Deptt. Head +3)'),
    ('5', '5 levels of Approvals (Deptt. Head +4)')
]

level_number_npo = [
    ('0', '0 level of Approval (Self Approval)'),
    ('1', '1 level of Approval (Deptt. Head)'),
    ('2', '2 levels of Approvals (Deptt Head +1)'),
    ('3', '3 levels of Approvals (Deptt. Head +2)'),
    ('4', '4 levels of Approvals (Deptt. Head +3)'),
    ('5', '5 levels of Approvals (Deptt. Head +4)')
]

level_number_qc = [
    ('0', '0 level of Approval (Self Approval)'),
    ('1', '1 level of Approval (Deptt. Head)'),
    ('2', '2 levels of Approvals (Deptt Head +1)'),
    ('3', '3 levels of Approvals (Deptt. Head +2)'),
    ('4', '4 levels of Approvals (Deptt. Head +3)'),
    ('5', '5 levels of Approvals (Deptt. Head +4)')
]


class PurchaseConfig(models.TransientModel):
    _name = 'purchase.config.wiz'
    _description = "Purchase Config Wiz"

    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id.id)
    create_multiple_rfq = fields.Boolean(string='Create Multiple RFQ by Quote Comparison')
    # quote_comparision = fields.Boolean(string='Quote Comparison')

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

    #     pr_mail_template_1st = fields.Many2one('mail.template', string="Email template for first approver", domain=[('model_id.model', '=', 'purchase.requisition')])
    #     pr_mail_template_2nd = fields.Many2one('mail.template', string="Email template for second approver", domain=[('model_id.model', '=', 'purchase.requisition')])
    #     pr_mail_template_3rd = fields.Many2one('mail.template', string="Email template for third approver", domain=[('model_id.model', '=', 'purchase.requisition')])
    #     pr_mail_template_4th = fields.Many2one('mail.template', string="Email template for fourth approver", domain=[('model_id.model', '=', 'purchase.requisition')])
    #     pr_mail_template_5th = fields.Many2one('mail.template', string="Email template for fifth approver", domain=[('model_id.model', '=', 'purchase.requisition')])

    users_approval_line_pr = fields.One2many('users.approval.wiz', 'pr_id', 'PR Users Approval Line')
    users_approval_line_po = fields.One2many('users.approval.po.wiz', 'po_id', 'PO Users Approval Line')
    tc_lines = fields.One2many('purchase.tc.line.wiz', 'res_config_id', string="T&C")

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

    all_pa_disable = fields.Boolean(string='Disable Create button in All Advance Requests')
    allow_inv_from_pr = fields.Boolean(string='Allow Vendor Bills from PR',
                                       help="If this option is selected then you will see Create Vendor Bill button in the PR form.")
    mandatory_forecast = fields.Boolean(string='Forecast Mandatory?',
                                        help="If this option is selected then Forecast field will be mandatory on PR/PO.")
    mandatory_estimated_price = fields.Boolean(string='Estimated price Mandatory?',
                                               help="If this option is selected then Estimated price field will be mandatory on PR.")

    users_approval_line_pa = fields.One2many('users.approval.pa.wiz', 'pa_id', 'Advance Requests Users Approval Line')
    pa_validation = fields.Selection(level_number_pa, string="Levels of Approvals", default=0, \
                                     help="Provide a Four validation mechanism for Purchase Advance")

    so_label_button_name_1st = fields.Char("SO 1st Label Button")
    so_label_button_name_2nd = fields.Char("SO 2nd Label SO Button")
    so_label_button_name_3rd = fields.Char("SO 3rd Label SButton")
    so_label_button_name_4th = fields.Char("SO 4th Label Button")
    so_label_button_name_5th = fields.Char("SO 5th Label Button")

    so_label_state_name_1st = fields.Char("SO 1st Label State")
    so_label_state_name_2nd = fields.Char("SO 2nd Label State")
    so_label_state_name_3rd = fields.Char("SO 3rd Label State")
    so_label_state_name_4th = fields.Char("SO 4th Label State")
    so_label_state_name_5th = fields.Char("SO 5th Label State")

    all_so_disable = fields.Boolean(string='Disable Create button in All Service Order')
    users_approval_line_so = fields.One2many('users.approval.so.wiz', 'so_id', 'Service Order Users Approval Line')
    so_validation = fields.Selection(level_number_so, string="SO Levels of Approvals", default=0, \
                                     help="Provide a Four validation mechanism for Service Order")

    so_double_validation_amt = fields.Float("SO Double validation amount")
    so_triple_validation_amount = fields.Float("SO Triple validation amount")
    so_fourth_validation_amount = fields.Float("SO Fourth validation amount")
    so_fifth_validation_amount = fields.Float("SO Fifth validation amount")
    so_sixth_validation_amount = fields.Float("SO Sixth validation amount")

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
    users_approval_line_npo = fields.One2many('users.approval.npo.wiz', 'npo_id', 'Non PO Item Users Approval Line')
    npo_validation = fields.Selection(level_number_npo, string="NPO Levels of Approvals", default=0, \
                                      help="Provide a Four validation mechanism for Non PO Item")

    users_approval_line_qc = fields.One2many('users.approval.qc.wiz', 'qc_id', 'Non PO Item Users Approval Line')
    quote_validation = fields.Selection(level_number_qc, string="QC Levels of Approvals", default=0, \
                                        help="Provide a Four validation mechanism for Non QC Item")

    npo_double_validation_amt = fields.Float("NPO Double validation amount")
    npo_triple_validation_amount = fields.Float("NPO Triple validation amount")
    npo_fourth_validation_amount = fields.Float("NPO Fourth validation amount")
    npo_fifth_validation_amount = fields.Float("NPO Fifth validation amount")
    npo_sixth_validation_amount = fields.Float("NPO Sixth validation amount")

    pr_date_readonly = fields.Boolean("PR Date Readonly")
    make_hsn_code_mandatory = fields.Boolean(string='Make HSN Code Mandatory',
                                             help="If this is True then HSN Code field in the Purchase form will become Mandatory.")
    make_taxes_mandatory = fields.Boolean(string='Make Taxes Mandatory',
                                          help="If this is True then Customer Taxes & Vendor Taxes fields in the Purchase form will become Mandatory.")

    make_hsn_code_readonly = fields.Boolean(string='Make HSN Code Readonly',
                                            help="If this is True then HSN Code Readonly in the Purchase Lines.")

    make_tnc_mandatory = fields.Boolean(string='Make T&C Mandatory',
                                        help="If this is True then Terms and Conditions Readonly in the Purchase Order.")

    is_doc = fields.Boolean(string='Is Doc ID')
    hide_vendor_in_pr = fields.Boolean(string='Hide Vendor Name in PR')
    show_customer_in_pr = fields.Boolean(string='show customer field in PR')
    show_sale_order_in_pr = fields.Boolean(string='Show Sale Order field in PR ')
    invisible_estimated_price_value = fields.Boolean(string='Invisible Estimated Price and Estimated Value in PR Lines')
    last_purchase_price = fields.Boolean(string='Last Purchase Price')

    @api.onchange('po_date_readonly')
    def onchange_po_date_readonly(self):
        if self.po_date_readonly == 0:
            self.po_date_visible_bool = True
        if self.po_date_readonly == 1:
            self.po_date_visible_bool = False

    def _get_vals(self, poconf_id):
        res = {}
        tc_lines = []
        users_approval_line_pr = []
        users_approval_line_po = []
        users_approval_line_pa = []
        users_approval_line_so = []
        users_approval_line_npo = []
        users_approval_line_qc = []
        res['supplier_rating_formula_val2'] = poconf_id.supplier_rating_formula_val2
        res['supplier_rating_formula_val3'] = poconf_id.supplier_rating_formula_val3

        res['make_hsn_code_mandatory'] = poconf_id.make_hsn_code_mandatory
        res['create_multiple_rfq'] = poconf_id.create_multiple_rfq
        res['make_taxes_mandatory'] = poconf_id.make_taxes_mandatory
        res['make_hsn_code_readonly'] = poconf_id.make_hsn_code_readonly
        res['make_tnc_mandatory'] = poconf_id.make_tnc_mandatory

        res['po_label_button_name_1st'] = poconf_id.po_label_button_name_1st
        res['po_label_button_name_2nd'] = poconf_id.po_label_button_name_2nd
        res['po_label_button_name_3rd'] = poconf_id.po_label_button_name_3rd
        res['po_label_button_name_4th'] = poconf_id.po_label_button_name_4th
        res['po_label_button_name_5th'] = poconf_id.po_label_button_name_5th

        res['po_double_validation_amt'] = poconf_id.po_double_validation_amt
        res['po_triple_validation_amount'] = poconf_id.po_triple_validation_amount
        res['po_fourth_validation_amount'] = poconf_id.po_fourth_validation_amount
        res['po_fifth_validation_amount'] = poconf_id.po_fifth_validation_amount
        res['po_sixth_validation_amount'] = poconf_id.po_sixth_validation_amount

        res['pr_label_button_name_1st'] = poconf_id.pr_label_button_name_1st
        res['pr_label_button_name_2nd'] = poconf_id.pr_label_button_name_2nd
        res['pr_label_button_name_3rd'] = poconf_id.pr_label_button_name_3rd
        res['pr_label_button_name_4th'] = poconf_id.pr_label_button_name_4th
        res['pr_label_button_name_5th'] = poconf_id.pr_label_button_name_5th

        res['pr_double_validation_amt'] = poconf_id.pr_double_validation_amt
        res['pr_triple_validation_amount'] = poconf_id.pr_triple_validation_amount
        res['pr_fourth_validation_amount'] = poconf_id.pr_fourth_validation_amount
        res['pr_fifth_validation_amount'] = poconf_id.pr_fifth_validation_amount
        res['pr_sixth_validation_amount'] = poconf_id.pr_sixth_validation_amount

        res['po_label_state_name_1st'] = poconf_id.po_label_state_name_1st
        res['po_label_state_name_2nd'] = poconf_id.po_label_state_name_2nd
        res['po_label_state_name_3rd'] = poconf_id.po_label_state_name_3rd
        res['po_label_state_name_4th'] = poconf_id.po_label_state_name_4th
        res['po_label_state_name_5th'] = poconf_id.po_label_state_name_5th

        res['pr_label_state_name_1st'] = poconf_id.pr_label_state_name_1st
        res['pr_label_state_name_2nd'] = poconf_id.pr_label_state_name_2nd
        res['pr_label_state_name_3rd'] = poconf_id.pr_label_state_name_3rd
        res['pr_label_state_name_4th'] = poconf_id.pr_label_state_name_4th
        res['pr_label_state_name_5th'] = poconf_id.pr_label_state_name_5th

        res['pr_sequence_number'] = poconf_id.pr_sequence_number
        res['po_sequence_number'] = poconf_id.po_sequence_number
        res['po_date_readonly'] = poconf_id.po_date_readonly
        res['pr_date_readonly'] = poconf_id.pr_date_readonly
        res['po_date_as'] = poconf_id.po_date_as

        res['unit_price_in_po'] = poconf_id.unit_price_in_po
        res['unit_price_non_zero_only'] = poconf_id.unit_price_non_zero_only

        res['pr_common_prefix'] = poconf_id.pr_common_prefix
        res['po_common_prefix'] = poconf_id.po_common_prefix

        res['pr_raw_prefix'] = poconf_id.pr_raw_prefix
        res['pr_gi_prefix'] = poconf_id.pr_gi_prefix
        res['pr_consu_prefix'] = poconf_id.pr_consu_prefix
        res['pr_fa_prefix'] = poconf_id.pr_fa_prefix
        res['pr_service_prefix'] = poconf_id.pr_service_prefix
        res['pr_fg_prefix'] = poconf_id.pr_fg_prefix
        res['pr_mix_prefix'] = poconf_id.pr_mix_prefix
        res['pr_semi_fg_wip_prefix'] = poconf_id.pr_semi_fg_wip_prefix

        res['po_raw_prefix'] = poconf_id.po_raw_prefix
        res['po_gi_prefix'] = poconf_id.po_gi_prefix
        res['po_consu_prefix'] = poconf_id.po_consu_prefix
        res['po_fa_prefix'] = poconf_id.po_fa_prefix
        res['supplier_taxes_in_po'] = poconf_id.supplier_taxes_in_po
        res['hsn_sac_code_in_po'] = poconf_id.hsn_sac_code_in_po

        res['pr_validation'] = poconf_id.pr_validation
        res['po_validation'] = poconf_id.po_validation
        res['product_on_off'] = poconf_id.product_on_off
        res['description_on_off'] = poconf_id.description_on_off
        res['po_description'] = poconf_id.po_description
        res['so_description'] = poconf_id.so_description
        res['grn_mandatory'] = poconf_id.grn_mandatory
        # res['all_pr_disable'] = poconf_id.all_pr_disable
        # res['all_po_disable'] = poconf_id.all_po_disable

        res['all_pa_disable'] = poconf_id.all_pa_disable
        res['allow_inv_from_pr'] = poconf_id.allow_inv_from_pr
        res['mandatory_forecast'] = poconf_id.mandatory_forecast
        res['mandatory_estimated_price'] = poconf_id.mandatory_estimated_price

        res['pa_label_button_name_1st'] = poconf_id.pa_label_button_name_1st
        res['pa_label_button_name_2nd'] = poconf_id.pa_label_button_name_2nd
        res['pa_label_button_name_3rd'] = poconf_id.pa_label_button_name_3rd
        res['pa_label_button_name_4th'] = poconf_id.pa_label_button_name_4th
        res['pa_label_button_name_5th'] = poconf_id.pa_label_button_name_5th

        res['pa_label_state_name_1st'] = poconf_id.pa_label_state_name_1st
        res['pa_label_state_name_2nd'] = poconf_id.pa_label_state_name_2nd
        res['pa_label_state_name_3rd'] = poconf_id.pa_label_state_name_3rd
        res['pa_label_state_name_4th'] = poconf_id.pa_label_state_name_4th
        res['pa_label_state_name_5th'] = poconf_id.pa_label_state_name_5th
        res['pa_validation'] = poconf_id.pa_validation

        res['all_so_disable'] = poconf_id.all_so_disable
        res['so_label_button_name_1st'] = poconf_id.so_label_button_name_1st
        res['so_label_button_name_2nd'] = poconf_id.so_label_button_name_2nd
        res['so_label_button_name_3rd'] = poconf_id.so_label_button_name_3rd
        res['so_label_button_name_4th'] = poconf_id.so_label_button_name_4th
        res['so_label_button_name_5th'] = poconf_id.so_label_button_name_5th

        res['so_label_state_name_1st'] = poconf_id.so_label_state_name_1st
        res['so_label_state_name_2nd'] = poconf_id.so_label_state_name_2nd
        res['so_label_state_name_3rd'] = poconf_id.so_label_state_name_3rd
        res['so_label_state_name_4th'] = poconf_id.so_label_state_name_4th
        res['so_label_state_name_5th'] = poconf_id.so_label_state_name_5th
        res['so_validation'] = poconf_id.so_validation

        res['so_double_validation_amt'] = poconf_id.so_double_validation_amt
        res['so_triple_validation_amount'] = poconf_id.so_triple_validation_amount
        res['so_fourth_validation_amount'] = poconf_id.so_fourth_validation_amount
        res['so_fifth_validation_amount'] = poconf_id.so_fifth_validation_amount
        res['so_sixth_validation_amount'] = poconf_id.so_sixth_validation_amount

        res['all_npo_disable'] = poconf_id.all_npo_disable
        res['npo_label_button_name_1st'] = poconf_id.npo_label_button_name_1st
        res['npo_label_button_name_2nd'] = poconf_id.npo_label_button_name_2nd
        res['npo_label_button_name_3rd'] = poconf_id.npo_label_button_name_3rd
        res['npo_label_button_name_4th'] = poconf_id.npo_label_button_name_4th
        res['npo_label_button_name_5th'] = poconf_id.npo_label_button_name_5th

        res['npo_label_state_name_1st'] = poconf_id.npo_label_state_name_1st
        res['npo_label_state_name_2nd'] = poconf_id.npo_label_state_name_2nd
        res['npo_label_state_name_3rd'] = poconf_id.npo_label_state_name_3rd
        res['npo_label_state_name_4th'] = poconf_id.npo_label_state_name_4th
        res['npo_label_state_name_5th'] = poconf_id.npo_label_state_name_5th
        res['npo_validation'] = poconf_id.npo_validation
        res['quote_validation'] = poconf_id.quote_validation

        res['npo_double_validation_amt'] = poconf_id.npo_double_validation_amt
        res['npo_triple_validation_amount'] = poconf_id.npo_triple_validation_amount
        res['npo_fourth_validation_amount'] = poconf_id.npo_fourth_validation_amount
        res['npo_fifth_validation_amount'] = poconf_id.npo_fifth_validation_amount
        res['npo_sixth_validation_amount'] = poconf_id.npo_sixth_validation_amount

        res['is_doc'] = poconf_id.is_doc
        res['hide_vendor_in_pr'] = poconf_id.hide_vendor_in_pr
        res['show_customer_in_pr'] = poconf_id.show_customer_in_pr
        res['show_sale_order_in_pr'] = poconf_id.show_sale_order_in_pr
        res['invisible_estimated_price_value'] = poconf_id.invisible_estimated_price_value
        res['last_purchase_price'] = poconf_id.last_purchase_price

        for i in poconf_id.tc_lines:
            tc_lines.append((0, 0, {'item': i.item, 'tc': i.tc}))
        res['tc_lines'] = tc_lines

        for i in poconf_id.users_approval_line_pr:
            print('verts....................')
            print('verts....................', i.sequence)
            users_approval_line_pr.append(
                (0, 0, {'sequence': i.sequence, 'user_id': i.user_id.id, 'pr_mail_template': i.pr_mail_template.id}))
        res['users_approval_line_pr'] = users_approval_line_pr

        for i in poconf_id.users_approval_line_po:
            users_approval_line_po.append((0, 0, {'sequence': i.sequence, 'user_id': i.user_id.id,
                                                  'po_mail_template': i.po_mail_template.id, 'sla_days': i.sla_days}))
            # users_approval_line_po.append(('0', 0, {'sequence':i.sequence, 'user_id':i.user_id.id,'po_mail_template':i.po_mail_template.id}))
        res['users_approval_line_po'] = users_approval_line_po

        for i in poconf_id.users_approval_line_pa:
            users_approval_line_pa.append(
                (0, 0, {'sequence': i.sequence, 'user_id': i.user_id.id, 'pa_mail_template': i.pa_mail_template.id}))
        res['users_approval_line_pa'] = users_approval_line_pa

        for i in poconf_id.users_approval_line_so:
            users_approval_line_so.append(
                (0, 0, {'sequence': i.sequence, 'user_id': i.user_id.id, 'so_mail_template': i.so_mail_template.id}))
        res['users_approval_line_so'] = users_approval_line_so

        for i in poconf_id.users_approval_line_npo:
            users_approval_line_npo.append(
                (0, 0, {'sequence': i.sequence, 'user_id': i.user_id.id, 'npo_mail_template': i.npo_mail_template.id}))
        res['users_approval_line_npo'] = users_approval_line_npo

        for i in poconf_id.users_approval_line_qc:
            users_approval_line_qc.append(
                (0, 0, {'sequence': i.sequence, 'user_id': i.user_id.id, 'qc_mail_template': i.qc_mail_template.id}))
        res['users_approval_line_qc'] = users_approval_line_qc

        return res

    def save(self):
        print('save')
        ir_model_data = self.env['ir.model.data']
        vals = self._get_vals(self)
        company_po_config = self.sudo().company_id.po_config
        print('company_po_config', company_po_config)
        if company_po_config:
            company_po_config.users_approval_line_pr.unlink()
            company_po_config.users_approval_line_po.unlink()
            company_po_config.tc_lines.unlink()
            company_po_config.users_approval_line_pa.unlink()
            company_po_config.users_approval_line_so.unlink()
            company_po_config.users_approval_line_npo.unlink()
            company_po_config.users_approval_line_qc.unlink()
            company_po_config.write(vals)
        else:
            po_config = self.env['purchase.config'].sudo().create(vals)
            self.company_id.po_config = po_config.id

        pr_group_xml_id_1 = ir_model_data._xmlid_lookup('verts_v15_freight_purchase.group_pr_first_level')[2]
        pr_group_xml_id_2 = ir_model_data._xmlid_lookup('verts_v15_freight_purchase.group_pr_second_level')[2]
        pr_group_xml_id_3 = ir_model_data._xmlid_lookup('verts_v15_freight_purchase.group_pr_third_level')[2]
        pr_group_xml_id_4 = ir_model_data._xmlid_lookup('verts_v15_freight_purchase.group_pr_fourth_level')[2]
        pr_group_xml_id_5 = ir_model_data._xmlid_lookup('verts_v15_freight_purchase.group_pr_fifth_level')[2]

        po_group_xml_id_1 = ir_model_data._xmlid_lookup('verts_v15_freight_purchase.group_po_first_level')[2]
        print('1', po_group_xml_id_1)
        po_group_xml_id_2 = ir_model_data._xmlid_lookup('verts_v15_freight_purchase.group_po_second_level')[2]
        po_group_xml_id_3 = ir_model_data._xmlid_lookup('verts_v15_freight_purchase.group_po_third_level')[2]
        po_group_xml_id_4 = ir_model_data._xmlid_lookup('verts_v15_freight_purchase.group_po_fourth_level')[2]
        po_group_xml_id_5 = ir_model_data._xmlid_lookup('verts_v15_freight_purchase.group_po_fifth_level')[2]

        pa_group_xml_id_1 = ir_model_data._xmlid_lookup('verts_v15_freight_purchase.group_pa_first_level')[2]
        pa_group_xml_id_2 = ir_model_data._xmlid_lookup('verts_v15_freight_purchase.group_pa_second_level')[2]
        pa_group_xml_id_3 = ir_model_data._xmlid_lookup('verts_v15_freight_purchase.group_pa_third_level')[2]
        pa_group_xml_id_4 = ir_model_data._xmlid_lookup('verts_v15_freight_purchase.group_pa_fourth_level')[2]
        pa_group_xml_id_5 = ir_model_data._xmlid_lookup('verts_v15_freight_purchase.group_pa_fifth_level')[2]

        so_group_xml_id_1 = ir_model_data._xmlid_lookup('verts_v15_freight_purchase.group_menu_service_order_1st_approval')[
            2]
        so_group_xml_id_2 = ir_model_data._xmlid_lookup('verts_v15_freight_purchase.group_menu_service_order_2nd_approval')[
            2]
        so_group_xml_id_3 = ir_model_data._xmlid_lookup('verts_v15_freight_purchase.group_menu_service_order_3rd_approval')[
            2]
        so_group_xml_id_4 = \
        ir_model_data._xmlid_lookup('verts_v15_freight_purchase.group_menu_service_order_fourth_approval')[2]
        so_group_xml_id_5 = \
        ir_model_data._xmlid_lookup('verts_v15_freight_purchase.group_menu_service_order_fifth_approval')[2]

        npo_group_xml_id_1 = ir_model_data._xmlid_lookup('verts_v15_freight_purchase.group_menu_work_order_1st_approval')[2]
        npo_group_xml_id_2 = ir_model_data._xmlid_lookup('verts_v15_freight_purchase.group_menu_work_order_2nd_approval')[2]
        npo_group_xml_id_3 = ir_model_data._xmlid_lookup('verts_v15_freight_purchase.group_menu_work_order_3rd_approval')[2]
        npo_group_xml_id_4 = \
        ir_model_data._xmlid_lookup('verts_v15_freight_purchase.group_menu_work_order_fourth_approval')[2]
        npo_group_xml_id_5 = ir_model_data._xmlid_lookup('verts_v15_freight_purchase.group_menu_work_order_fifth_approval')[
            2]

        for i in self.users_approval_line_pa:
            if i.sequence == '1st_lavels':
                compose_form_id = pa_group_xml_id_1
                print('+++++++++++=compose_form_id', compose_form_id)
            if i.sequence == '2st_lavels':
                compose_form_id = pa_group_xml_id_2
            if i.sequence == '3st_lavels':
                compose_form_id = pa_group_xml_id_3
            if i.sequence == '4st_lavels':
                compose_form_id = pa_group_xml_id_4
            if i.sequence == '5st_lavels':
                compose_form_id = pa_group_xml_id_5
            #             self._cr.execute('delete from res_groups_users_rel WHERE gid in (%s,%s,%s,%s) and uid=%s', (pr_group_xml_id_1, pr_group_xml_id_2, pr_group_xml_id_3, pr_group_xml_id_4, i.user_id.id))
            self._cr.execute("SELECT * FROM res_groups_users_rel WHERE gid=%s and uid=%s",
                             (compose_form_id, i.user_id.id))
            res_groups_users_rel_id = self._cr.fetchone()
            if not (res_groups_users_rel_id and res_groups_users_rel_id[1]):
                self._cr.execute(""" INSERT INTO res_groups_users_rel (gid, uid)
                                   VALUES (%s, %s) """, (compose_form_id, i.user_id.id))

        for i in self.users_approval_line_so:
            if i.sequence == '1st_lavels':
                compose_form_id = so_group_xml_id_1
            if i.sequence == '2st_lavels':
                compose_form_id = so_group_xml_id_2
            if i.sequence == '3st_lavels':
                compose_form_id = so_group_xml_id_3
            if i.sequence == '4st_lavels':
                compose_form_id = so_group_xml_id_4
            if i.sequence == '5st_lavels':
                compose_form_id = so_group_xml_id_5
            #             self._cr.execute('delete from res_groups_users_rel WHERE gid in (%s,%s,%s,%s) and uid=%s', (pr_group_xml_id_1, pr_group_xml_id_2, pr_group_xml_id_3, pr_group_xml_id_4, i.user_id.id))
            self._cr.execute("SELECT * FROM res_groups_users_rel WHERE gid=%s and uid=%s",
                             (compose_form_id, i.user_id.id))
            res_groups_users_rel_id = self._cr.fetchone()
            if not (res_groups_users_rel_id and res_groups_users_rel_id[1]):
                self._cr.execute(""" INSERT INTO res_groups_users_rel (gid, uid)
                                   VALUES (%s, %s) """, (compose_form_id, i.user_id.id))

        for i in self.users_approval_line_npo:
            if i.sequence == '1st_lavels':
                compose_form_id = npo_group_xml_id_1
            if i.sequence == '2st_lavels':
                compose_form_id = npo_group_xml_id_2
            if i.sequence == '3st_lavels':
                compose_form_id = npo_group_xml_id_3
            if i.sequence == '4st_lavels':
                compose_form_id = npo_group_xml_id_4
            if i.sequence == '5st_lavels':
                compose_form_id = npo_group_xml_id_5
            #             self._cr.execute('delete from res_groups_users_rel WHERE gid in (%s,%s,%s,%s) and uid=%s', (pr_group_xml_id_1, pr_group_xml_id_2, pr_group_xml_id_3, pr_group_xml_id_4, i.user_id.id))
            self._cr.execute("SELECT * FROM res_groups_users_rel WHERE gid=%s and uid=%s",
                             (compose_form_id, i.user_id.id))
            res_groups_users_rel_id = self._cr.fetchone()
            if not (res_groups_users_rel_id and res_groups_users_rel_id[1]):
                self._cr.execute(""" INSERT INTO res_groups_users_rel (gid, uid)
                                   VALUES (%s, %s) """, (compose_form_id, i.user_id.id))

        # for i in self.users_approval_line_qc:
        #     if i.sequence == '1st_lavels':
        #         compose_form_id = npo_group_xml_id_1
        #     if i.sequence == '2st_lavels':
        #         compose_form_id = npo_group_xml_id_2
        #     if i.sequence == '3st_lavels':
        #         compose_form_id = npo_group_xml_id_3
        #     if i.sequence == '4st_lavels':
        #         compose_form_id = npo_group_xml_id_4
        #     if i.sequence == '5st_lavels':
        #         compose_form_id = npo_group_xml_id_5
        #     #             self._cr.execute('delete from res_groups_users_rel WHERE gid in (%s,%s,%s,%s) and uid=%s', (pr_group_xml_id_1, pr_group_xml_id_2, pr_group_xml_id_3, pr_group_xml_id_4, i.user_id.id))
        #     self._cr.execute("SELECT * FROM res_groups_users_rel WHERE gid=%s and uid=%s",
        #                      (compose_form_id, i.user_id.id))
        #     res_groups_users_rel_id = self._cr.fetchone()
        #     if not (res_groups_users_rel_id and res_groups_users_rel_id[1]):
        #         self._cr.execute(""" INSERT INTO res_groups_users_rel (gid, uid)
        #                                    VALUES (%s, %s) """, (compose_form_id, i.user_id.id))

        for i in self.users_approval_line_pr:
            print('hello..............')
            print('hello..............', i)
            if i.sequence == '1st_lavels':
                compose_form_id = pr_group_xml_id_1
            if i.sequence == '2st_lavels':
                compose_form_id = pr_group_xml_id_2
            if i.sequence == '3st_lavels':
                compose_form_id = pr_group_xml_id_3
            if i.sequence == '4st_lavels':
                compose_form_id = pr_group_xml_id_4
            if i.sequence == '5st_lavels':
                compose_form_id = pr_group_xml_id_5
            # self._cr.execute('delete from res_groups_users_rel WHERE gid in (%s,%s,%s,%s) and uid=%s', (pr_group_xml_id_1, pr_group_xml_id_2, pr_group_xml_id_3, pr_group_xml_id_4, i.user_id.id))
            self._cr.execute("SELECT * FROM res_groups_users_rel WHERE gid=%s and uid=%s",
                             (compose_form_id, i.user_id.id))
            res_groups_users_rel_id = self._cr.fetchone()
            if not (res_groups_users_rel_id and res_groups_users_rel_id[1]):
                self._cr.execute(""" INSERT INTO res_groups_users_rel (gid, uid)
                                   VALUES (%s, %s) """, (compose_form_id, i.user_id.id))

        for i in self.users_approval_line_po:
            print('i', i)
            if i.sequence == '1st_lavels':
                compose_form_id = po_group_xml_id_1
                print('c', compose_form_id)
            if i.sequence == '2nd_lavels':
                compose_form_id = po_group_xml_id_2
            if i.sequence == '3rd_lavels':
                compose_form_id = po_group_xml_id_3
            if i.sequence == '4th_lavels':
                compose_form_id = po_group_xml_id_4
            if i.sequence == '5th_lavels':
                compose_form_id = po_group_xml_id_5
            #             self._cr.execute('delete from res_groups_users_rel WHERE gid in (%s,%s,%s,%s) and uid=%s', (po_group_xml_id_1, po_group_xml_id_2, po_group_xml_id_3, po_group_xml_id_4, i.user_id.id))
            self._cr.execute("SELECT * FROM res_groups_users_rel WHERE gid=%s and uid=%s",
                             (compose_form_id, i.user_id.id))
            res_groups_users_rel_id = self._cr.fetchone()
            if not (res_groups_users_rel_id and res_groups_users_rel_id[1]):
                self._cr.execute(""" INSERT INTO res_groups_users_rel (gid, uid)
                                   VALUES (%s, %s) """, (compose_form_id, i.user_id.id))
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    @api.model
    def default_get(self, fields):
        res = super(PurchaseConfig, self).default_get(fields)
        poconf_id = self.env.user.company_id.po_config
        if poconf_id:
            res.update(self._get_vals(poconf_id))
        return res


class UsersApprovalWiz(models.TransientModel):
    _name = "users.approval.wiz"
    _description = "Users Approval Wiz"

    pr_id = fields.Many2one('purchase.config.wiz', 'PO Config')
    user_id = fields.Many2one('res.users', "User")
    pr_mail_template = fields.Many2one('mail.template', string="Email template",
                                       help="This email will be sent to the Approver",
                                       domain=[('model_id.model', '=', 'purchase.requisition')])
    sequence = fields.Selection(string="Sequence", selection=[
        ('1st_lavels', '1st Levels Approval'),
        ('2st_lavels', '2nd Levels Approval'),
        ('3st_lavels', '3rd Levels Approval'),
        ('4st_lavels', '4th Levels Approval'),
        ('5st_lavels', '5th Levels Approval'), ], )


class UsersApprovalPO(models.TransientModel):
    _name = "users.approval.po.wiz"
    _description = "Users Approval PO Wiz"

    po_id = fields.Many2one('purchase.config.wiz', 'PO Config')
    user_id = fields.Many2one('res.users', "User")
    po_mail_template = fields.Many2one('mail.template', string="Email template",
                                       help="This email will be sent to the Approver",
                                       domain=[('model_id.model', '=', 'purchase.order')])
    sequence = fields.Selection(string="Sequence", selection=[
        ('1st_lavels', '1st Levels Approval'),
        ('2nd_lavels', '2nd Levels Approval'),
        ('3rd_lavels', '3rd Levels Approval'),
        ('4th_lavels', '4th Levels Approval'),
        ('5th_lavels', '5th Levels Approval'), ])
    #####Next Approval################
    sla_days = fields.Integer('SLA(Days)')


class PurchaseTcLineWiz(models.TransientModel):
    _name = "purchase.tc.line.wiz"
    _description = "Purchase Tc Line Wiz"

    res_config_id = fields.Many2one('purchase.config.wiz', 'Company')
    item = fields.Char("T&C")
    tc = fields.Char("Details")


class UsersApprovalWizPA(models.TransientModel):
    _name = "users.approval.pa.wiz"
    _description = "Users Approval PA Wiz"

    pa_id = fields.Many2one('purchase.config.wiz', 'PO Config')
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


class UsersApprovalWizSO(models.TransientModel):
    _name = "users.approval.so.wiz"
    _description = "Users Approval SO Wiz"

    so_id = fields.Many2one('purchase.config.wiz', 'Service Order Config')
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


class UsersApprovalWizNPO(models.TransientModel):
    _name = "users.approval.npo.wiz"
    _description = "Users Approval NPO Wiz"

    npo_id = fields.Many2one('purchase.config.wiz', 'Non PO Item Config')
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


class UsersApprovalWizQC(models.TransientModel):
    _name = "users.approval.qc.wiz"
    _description = "Users Approval QC Wiz"

    qc_id = fields.Many2one('purchase.config.wiz', 'Non PO Item Config')
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
