# -*- coding: utf-8 -*-
# Copyright 2020 Verts Services India Pvt. Ltd.
# http://www.verts.co.in

from odoo import fields, models,api

class ResCompany(models.Model):
    _inherit = 'res.company'

    po_config = fields.Many2one('purchase.config', "PO Config")
    doc_id_type = fields.Char("Document ID")
    is_doc = fields.Boolean("Is Doc", related="po_config.is_doc")
    po_double_validation = fields.Selection([
        ('one_step', 'Confirm purchase orders in one step'),
        ('two_step', 'Get 2 levels of approvals to confirm a purchase order'),
        ('three_step', 'Get 3 levels of approvals to confirm a purchase order'),
        ('four_step', 'Get 4 levels of approvals to confirm a purchase order'),
        ('five_step', 'Get 5 levels of approvals to confirm a purchase order'),
        ], string="Levels of Approvals", default='one_step', help="Provide a Four validation mechanism for purchases")
    po_fifth_validation_amount = fields.Monetary(string='Fifth validation amount', default=1000000,\
        help="Minimum amount for which a five validation is required")
    po_fourth_validation_amount = fields.Monetary(string='Fourth validation amount', default=500000,\
        help="Minimum amount for which a four validation is required")
    po_triple_validation_amount = fields.Monetary(string='Triple validation amount', default=200000,\
        help="Minimum amount for which a double validation is required")
    pi_submission = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No')], string="PI Submission")
    pi_submission_template_id = fields.Many2one(
        'mail.template', 'PI Submission template')
    pi_approve = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No'),], string="PI Approve")
    pi_approve_template_id = fields.Many2one(
        'mail.template', 'PI Approve template')
    po_submission = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No'),], string="PO Submission")
    po_submission_template_id = fields.Many2one(
        'mail.template', 'PO Submission template')
    po_approve = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No'),], string="PO Approve")
    po_approve_template_id = fields.Many2one(
        'mail.template', 'PO Approve template')
    cin_no = fields.Char('CIN No.', size=64)
