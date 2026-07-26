# -*- coding: utf-8 -*-
# Copyright 2021 Verts Services India Pvt Ltd.
# http://www.verts.co.in

from odoo import models, fields, api
from datetime import datetime, timedelta
import xlwt
from odoo import api, fields, models, _
import base64
from io import StringIO, BytesIO
from odoo.exceptions import UserError, RedirectWarning, ValidationError


class ExportScheduleAttachment(models.TransientModel):
    _name = "export.schedule.attachment"
    _description = 'Export Schedule Attachment'

    export_attachment_lines = fields.One2many('schedule.attachment.line', 'export_attachment_id', string='Attachment Lines')
    
    def attach_button(self):
        print(self,self.export_attachment_lines)
        context = (self._context or {})
        active_id = self._context.get('active_ids')
        print(".....active_id....",active_id)
        record = self.env['sale.schedule.line'].browse(active_id)
        for id in record:
            id.sale_export_attachment_lines.create({'sale_export_attachment_id': self.export_attachment_lines.export_attachment_id})
            print("...record........",record)
        return True

    
class ScheduleAttachmentLine(models.TransientModel):
    """ Attachment Details """
    _name = "schedule.attachment.line"
    _description = 'Schedule Attachment Line'
  
    export_attachment_id = fields.Many2one('export.schedule.attachment')
    remark = fields.Char(string='Remark')
    attachment_value = fields.Binary(string='Attachment')
    

