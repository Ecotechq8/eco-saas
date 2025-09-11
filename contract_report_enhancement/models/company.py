# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools


class Company(models.Model):
    _inherit = 'res.company'

    notes_ids = fields.One2many("res.company.notes", "company_id")


class CompanyNotes(models.Model):
    _name = 'res.company.notes'

    company_id = fields.Many2one("res.company")

    special_notes_ar = fields.Text()
    special_notes_en = fields.Text()
