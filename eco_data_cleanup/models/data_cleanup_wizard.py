# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class DataCleanupWizard(models.TransientModel):
    _name = 'data.cleanup.wizard'
    _description = 'Data Cleanup Wizard'

    delete_purchase = fields.Boolean(string='Delete Purchase Orders', default=True)
    delete_sales = fields.Boolean(string='Delete Sales Orders', default=True)
    delete_inventory = fields.Boolean(string='Delete Inventory Transactions', default=True)
    delete_projects = fields.Boolean(string='Delete Projects & Tasks', default=True)
    delete_accounting = fields.Boolean(string='Delete Accounting Entries', default=True)
    delete_all = fields.Boolean(string='Delete All Transactions', default=True)

    def action_delete_all_transactions(self):
        """Delete all transactions based on selected options"""
        self.ensure_one()
        
        # Log the cleanup action
        _logger.warning('=' * 80)
        _logger.warning('DATA CLEANUP INITIATED BY USER: %s', self.env.user.name)
        _logger.warning('=' * 80)

        try:
            # Delete in proper order to respect foreign key constraints
            
            # 1. Accounting (depends on sales/purchase)
            if self.delete_accounting or self.delete_all:
                self._delete_accounting()
            
            # 2. Projects & Tasks
            if self.delete_projects or self.delete_all:
                self._delete_projects()
            
            # 3. Sales Orders
            if self.delete_sales or self.delete_all:
                self._delete_sales()
            
            # 4. Purchase Orders
            if self.delete_purchase or self.delete_all:
                self._delete_purchase()
            
            # 5. Inventory (should be last as it may be linked to other modules)
            if self.delete_inventory or self.delete_all:
                self._delete_inventory()
            
            self.env.cr.commit()
            
            _logger.warning('DATA CLEANUP COMPLETED SUCCESSFULLY')
            _logger.warning('=' * 80)
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': _('All selected transactions have been deleted successfully.'),
                    'type': 'success',
                    'sticky': False,
                }
            }
            
        except Exception as e:
            self.env.cr.rollback()
            _logger.error('DATA CLEANUP FAILED: %s', str(e), exc_info=True)
            raise UserError(_('Data cleanup failed: %s') % str(e))

    def _delete_accounting(self):
        """Delete accounting transactions"""
        _logger.info('Deleting accounting transactions...')
        
        # Delete payments
        payment_obj = self.env['account.payment'].sudo()
        payments = payment_obj.search([])
        if payments:
            payments.action_draft()
            payments.unlink()
            _logger.info('Deleted %d payments', len(payments))
        
        # Delete partial reconciliations
        self.env['account.partial.reconcile'].sudo().search([]).unlink()
        
        # Delete full reconciliations
        self.env['account.full.reconcile'].sudo().search([]).unlink()
        
        # Delete bank statements
        bank_stmt_obj = self.env['account.bank.statement'].sudo()
        bank_stmts = bank_stmt_obj.search([])
        if bank_stmts:
            bank_stmts.button_draft()
            bank_stmts.unlink()
            _logger.info('Deleted %d bank statements', len(bank_stmts))
        
        # Delete moves (journal entries) - exclude locked entries
        move_obj = self.env['account.move'].sudo()
        moves = move_obj.search([
            ('state', '=', 'posted')
        ])
        if moves:
            moves.button_draft()
            moves.unlink()
            _logger.info('Deleted %d posted moves', len(moves))
        
        # Delete draft moves
        draft_moves = move_obj.search([
            ('state', '=', 'draft')
        ])
        if draft_moves:
            draft_moves.unlink()
            _logger.info('Deleted %d draft moves', len(draft_moves))
        
        # Delete move lines (should be empty now, but just in case)
        self.env['account.move.line'].sudo().search([]).unlink()
        
        # Delete payment registers
        self.env['account.payment.register'].sudo().search([]).unlink()
        
        _logger.info('Accounting transactions deleted')

    def _delete_projects(self):
        """Delete projects and tasks"""
        _logger.info('Deleting projects and tasks...')
        
        # Delete tasks first (they may have dependencies)
        task_obj = self.env['project.task'].sudo()
        tasks = task_obj.search([])
        if tasks:
            tasks.unlink()
            _logger.info('Deleted %d tasks', len(tasks))
        
        # Delete projects
        project_obj = self.env['project.project'].sudo()
        projects = project_obj.search([])
        if projects:
            projects.unlink()
            _logger.info('Deleted %d projects', len(projects))
        
        # Delete project stages (custom ones only)
        # Keep default stages from base data
        stage_obj = self.env['project.task.type'].sudo()
        custom_stages = stage_obj.search([('user_id', '!=', False)])
        if custom_stages:
            custom_stages.unlink()
            _logger.info('Deleted %d custom project stages', len(custom_stages))
        
        _logger.info('Projects and tasks deleted')

    def _delete_sales(self):
        """Delete sales orders"""
        _logger.info('Deleting sales orders...')
        
        sale_obj = self.env['sale.order'].sudo()
        sales = sale_obj.search([])
        
        if sales:
            # Cancel all sales first
            sales.action_cancel()
            # Then delete them
            sales.unlink()
            _logger.info('Deleted %d sales orders', len(sales))
        
        # Delete quotations (draft/cancelled sales)
        quotations = sale_obj.search([], order='id DESC')
        if quotations:
            quotations.unlink()
            _logger.info('Deleted %d remaining quotations', len(quotations))
        
        _logger.info('Sales orders deleted')

    def _delete_purchase(self):
        """Delete purchase orders"""
        _logger.info('Deleting purchase orders...')
        
        po_obj = self.env['purchase.order'].sudo()
        pos = po_obj.search([])
        
        if pos:
            # Cancel all purchase orders first
            pos.button_cancel()
            # Then delete them
            pos.unlink()
            _logger.info('Deleted %d purchase orders', len(pos))
        
        _logger.info('Purchase orders deleted')

    def _delete_inventory(self):
        """Delete inventory transactions"""
        _logger.info('Deleting inventory transactions...')
        
        # Delete stock moves first
        move_obj = self.env['stock.move'].sudo()
        moves = move_obj.search([
            ('state', 'in', ('done', 'cancel'))
        ])
        if moves:
            moves._action_cancel()
            moves.unlink()
            _logger.info('Deleted %d done/cancelled stock moves', len(moves))
        
        # Delete remaining stock moves
        remaining_moves = move_obj.search([])
        if remaining_moves:
            remaining_moves._action_cancel()
            remaining_moves.unlink()
            _logger.info('Deleted %d remaining stock moves', len(remaining_moves))
        
        # Delete stock move lines
        move_line_obj = self.env['stock.move.line'].sudo()
        move_lines = move_line_obj.search([])
        if move_lines:
            move_lines.unlink()
            _logger.info('Deleted %d stock move lines', len(move_lines))
        
        # Delete pickings
        picking_obj = self.env['stock.picking'].sudo()
        pickings = picking_obj.search([])
        if pickings:
            pickings.action_cancel()
            pickings.unlink()
            _logger.info('Deleted %d pickings', len(pickings))
        
        # Delete scrap orders
        scrap_obj = self.env['stock.scrap'].sudo()
        scraps = scrap_obj.search([])
        if scraps:
            scraps.unlink()
            _logger.info('Deleted %d scraps', len(scraps))
        
        # Delete inventory adjustments
        inventory_obj = self.env['stock.inventory'].sudo()
        inventories = inventory_obj.search([])
        if inventories:
            inventories.action_cancel()
            inventories.unlink()
            _logger.info('Deleted %d inventory adjustments', len(inventories))
        
        # Delete quant packages (optional - keep this if you want to preserve packaging)
        # self.env['stock.quant.package'].sudo().search([]).unlink()
        
        # DO NOT delete stock quants - they represent current physical inventory
        # If user wants to reset quantities, they should do inventory adjustments
        _logger.info('Inventory transactions deleted')
