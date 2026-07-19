# -*- coding: utf-8 -*-

import io
import math
import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)

class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    pdf_batch_size = fields.Integer(
        string='PDF Batch Size',
        default=0,
        help="If greater than 0, rendering multiple PDF pages will be split into batches of this size, "
             "then merged using Python's PDF library. This reduces memory footprint and avoids "
             "wkhtmltopdf crash/timeout issues on low-resource servers. Default 0 means no batching."
    )

    def _render_qweb_pdf(self, report_ref, res_ids=None, data=None):
        # Resolve docids if passed as a string (common when called from controllers)
        if isinstance(res_ids, str):
            res_ids = [int(x) for x in res_ids.split(',') if x.strip()]

        # Resolve the actual report record first
        report = self
        if not isinstance(report_ref, int):
            # Resolve XML ID or name
            report = self.env.ref(report_ref, raise_if_not_found=False) or self.search([('report_name', '=', report_ref)], limit=1)
        else:
            report = self.browse(report_ref)
            
        report = report[:1]

        # Determine the batch size to use from the resolved report
        batch_size = report.pdf_batch_size if report else 0
        
        # Check report model dynamically to apply a default optimization
        # Payslips are notoriously huge and prone to wkhtmltopdf errors, so we default to a batch size of 10
        # unless an explicit batch size is configured.
        if not batch_size and report and report.model == 'hr.payslip':
            batch_size = 10
            
        if batch_size > 0 and res_ids and isinstance(res_ids, (list, tuple)) and len(res_ids) > batch_size:
            _logger.info(
                "Splitting PDF rendering of %s for %d records into batches of size %d",
                report.report_name or report_ref, len(res_ids), batch_size
            )
            
            pdf_contents = []
            report_type = 'pdf'
            
            # Split res_ids into batches
            num_batches = math.ceil(len(res_ids) / batch_size)
            for i in range(num_batches):
                batch_res_ids = res_ids[i * batch_size : (i + 1) * batch_size]
                _logger.info("Rendering PDF batch %d/%d (%d records)...", i + 1, num_batches, len(batch_res_ids))
                
                content, r_type = super(IrActionsReport, self)._render_qweb_pdf(
                    report_ref, res_ids=batch_res_ids, data=data
                )
                if content:
                    pdf_contents.append(content)
                    report_type = r_type
            
            if pdf_contents:
                # Merge the PDFs in memory
                merged_pdf = self._merge_pdf_contents(pdf_contents)
                return merged_pdf, report_type
        
        return super(IrActionsReport, self)._render_qweb_pdf(report_ref, res_ids=res_ids, data=data)

    def _merge_pdf_contents(self, pdf_list):
        """Merge multiple PDF bytes into a single PDF bytes."""
        try:
            from pypdf import PdfReader, PdfWriter
        except ImportError:
            try:
                from PyPDF2 import PdfReader, PdfWriter
            except ImportError:
                from PyPDF2 import PdfFileReader as PdfReader, PdfFileWriter as PdfWriter

        writer = PdfWriter()
        for pdf_data in pdf_list:
            reader = PdfReader(io.BytesIO(pdf_data))
            # Handle pages API difference between old PyPDF2 and new pypdf
            pages = reader.pages if hasattr(reader, 'pages') else [reader.getPage(i) for i in range(reader.getNumPages())]
            for page in pages:
                if hasattr(writer, 'add_page'):
                    writer.add_page(page)
                else:
                    writer.addPage(page)
        
        output = io.BytesIO()
        writer.write(output)
        return output.getvalue()
