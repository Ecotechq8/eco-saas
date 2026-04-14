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
        """Delete all transactions using direct SQL (aggressive cleanup)"""
        self.ensure_one()
        
        # Log the cleanup action
        _logger.warning('=' * 80)
        _logger.warning('DATA CLEANUP INITIATED BY USER: %s', self.env.user.name)
        _logger.warning('=' * 80)

        try:
            # Use direct SQL to bypass all ORM constraints
            self.env.cr.execute("""
                -- Disable triggers temporarily
                SET session_replication_role = replica;
            """)
            
            # 1. Analytic Lines (referenced by many modules)
            if self.delete_projects or self.delete_sales or self.delete_purchase or self.delete_all:
                self._delete_analytic_lines_sql()
            
            # 2. Accounting (depends on sales/purchase invoices)
            if self.delete_accounting or self.delete_all:
                self._delete_accounting_sql()
            
            # 3. Inventory (stock moves, pickings)
            if self.delete_inventory or self.delete_all:
                self._delete_inventory_sql()
            
            # 4. Sales Orders
            if self.delete_sales or self.delete_all:
                self._delete_sales_sql()
            
            # 5. Purchase Orders
            if self.delete_purchase or self.delete_all:
                self._delete_purchase_sql()
            
            # 6. Projects & Tasks
            if self.delete_projects or self.delete_all:
                self._delete_projects_sql()
            
            # Re-enable triggers
            self.env.cr.execute("""
                SET session_replication_role = DEFAULT;
            """)
            
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
            # Re-enable triggers even on error
            self.env.cr.execute("""
                SET session_replication_role = DEFAULT;
            """)
            self.env.cr.rollback()
            _logger.error('DATA CLEANUP FAILED: %s', str(e), exc_info=True)
            raise UserError(_('Data cleanup failed: %s') % str(e))

    def _delete_analytic_lines_sql(self):
        """Delete analytic lines using direct SQL"""
        _logger.info('Deleting analytic lines...')
        self.env.cr.execute("DELETE FROM account_analytic_line")
        _logger.info('Deleted %d analytic lines', self.env.cr.rowcount)

    def _delete_accounting_sql(self):
        """Delete accounting transactions using direct SQL"""
        _logger.info('Deleting accounting transactions...')
        
        # Delete in order to avoid FK constraints
        
        # 1. Delete payment lines
        self.env.cr.execute("DELETE FROM account_payment_line")
        _logger.info('Deleted %d payment lines', self.env.cr.rowcount)
        
        # 2. Delete payments
        self.env.cr.execute("DELETE FROM account_payment")
        _logger.info('Deleted %d payments', self.env.cr.rowcount)
        
        # 3. Delete partial reconciliations
        self.env.cr.execute("DELETE FROM account_partial_reconcile")
        _logger.info('Deleted %d partial reconciliations', self.env.cr.rowcount)
        
        # 4. Delete full reconciliations  
        self.env.cr.execute("DELETE FROM account_full_reconcile")
        _logger.info('Deleted %d full reconciliations', self.env.cr.rowcount)
        
        # 5. Delete bank statement lines
        self.env.cr.execute("DELETE FROM account_bank_statement_line")
        _logger.info('Deleted %d bank statement lines', self.env.cr.rowcount)
        
        # 6. Delete bank statements
        self.env.cr.execute("DELETE FROM account_bank_statement")
        _logger.info('Deleted %d bank statements', self.env.cr.rowcount)
        
        # 7. Delete move lines (account_move_line)
        self.env.cr.execute("DELETE FROM account_move_line")
        _logger.info('Deleted %d move lines', self.env.cr.rowcount)
        
        # 8. Delete move lines from account_move_rel (many2many)
        self.env.cr.execute("DELETE FROM account_move_line_account_tax_rel")
        self.env.cr.execute("DELETE FROM account_move_line__tax__account_move_line_rel")
        
        # 9. Delete account moves
        self.env.cr.execute("DELETE FROM account_move")
        _logger.info('Deleted %d account moves', self.env.cr.rowcount)
        
        # 10. Delete payment register transients (if any exist in DB)
        self.env.cr.execute("DELETE FROM account_payment_register")
        
        # 11. Delete analytic distributions
        self.env.cr.execute("DELETE FROM account_analytic_distribution_mixin")
        
        _logger.info('Accounting transactions deleted')

    def _delete_inventory_sql(self):
        """Delete inventory transactions using direct SQL"""
        _logger.info('Deleting inventory transactions...')
        
        # Delete in order to avoid FK constraints
        
        # 1. Delete stock move lines first
        self.env.cr.execute("DELETE FROM stock_move_line")
        _logger.info('Deleted %d stock move lines', self.env.cr.rowcount)
        
        # 2. Delete stock package lots
        self.env.cr.execute("DELETE FROM stock_package_level")
        _logger.info('Deleted %d package levels', self.env.cr.rowcount)
        
        # 3. Delete stock lots (optional - comment out if you want to keep lots)
        # self.env.cr.execute("DELETE FROM stock_lot")
        
        # 4. Delete stock moves
        self.env.cr.execute("DELETE FROM stock_move")
        _logger.info('Deleted %d stock moves', self.env.cr.rowcount)
        
        # 5. Delete stock move entries from many2many relations
        self.env.cr.execute("DELETE FROM stock_move_rule_repair_rel")
        self.env.cr.execute("DELETE FROM mrp_production_workcenter_move_rel")
        
        # 6. Delete stock scrap
        self.env.cr.execute("DELETE FROM stock_scrap")
        _logger.info('Deleted %d scraps', self.env.cr.rowcount)
        
        # 7. Delete stock inventory adjustments
        self.env.cr.execute("DELETE FROM stock_inventory_adjustment_name")
        self.env.cr.execute("DELETE FROM stock_quant")  # This will reset quants, but keeps locations
        
        # 8. Delete stock pickings
        self.env.cr.execute("DELETE FROM stock_picking")
        _logger.info('Deleted %d stock pickings', self.env.cr.rowcount)
        
        # 9. Delete stock inventory
        self.env.cr.execute("DELETE FROM stock_inventory")
        _logger.info('Deleted %d inventory adjustments', self.env.cr.rowcount)
        
        # 10. Delete procurement groups related to stock
        self.env.cr.execute("""
            DELETE FROM procurement_group 
            WHERE id IN (
                SELECT procurement_group_id 
                FROM stock_picking 
                WHERE procurement_group_id IS NOT NULL
            )
        """)
        
        # Note: We DO NOT delete stock_location, stock_warehouse, stock_quant_package
        # as these are master data that should be preserved
        
        _logger.info('Inventory transactions deleted')

    def _delete_sales_sql(self):
        """Delete sales orders using direct SQL"""
        _logger.info('Deleting sales orders...')
        
        # 1. Delete sale order lines
        self.env.cr.execute("DELETE FROM sale_order_line")
        _logger.info('Deleted %d sale order lines', self.env.cr.rowcount)
        
        # 2. Delete sale order many2many relations
        self.env.cr.execute("DELETE FROM sale_order_team_member_rel")
        self.env.cr.execute("DELETE FROM sale_order_crm_tracking_sale_order_rel")
        
        # 3. Delete sale orders
        self.env.cr.execute("DELETE FROM sale_order")
        _logger.info('Deleted %d sale orders', self.env.cr.rowcount)
        
        # 4. Delete sale-related analytic lines (already done above)
        
        _logger.info('Sales orders deleted')

    def _delete_purchase_sql(self):
        """Delete purchase orders using direct SQL"""
        _logger.info('Deleting purchase orders...')
        
        # 1. Delete purchase order lines
        self.env.cr.execute("DELETE FROM purchase_order_line")
        _logger.info('Deleted %d purchase order lines', self.env.cr.rowcount)
        
        # 2. Delete purchase order many2many relations
        self.env.cr.execute("DELETE FROM purchase_order_invoice_plan_rel")
        self.env.cr.execute("DELETE FROM purchase_order_blanket_order_rel")
        
        # 3. Delete purchase orders
        self.env.cr.execute("DELETE FROM purchase_order")
        _logger.info('Deleted %d purchase orders', self.env.cr.rowcount)
        
        # 4. Delete purchase-related analytic lines (already done above)
        
        _logger.info('Purchase orders deleted')

    def _delete_projects_sql(self):
        """Delete projects and tasks using direct SQL"""
        _logger.info('Deleting projects and tasks...')
        
        # 1. Delete project task entries from many2many
        self.env.cr.execute("DELETE FROM project_task_project_tag_rel")
        self.env.cr.execute("DELETE FROM project_task_user_rel")
        self.env.cr.execute("DELETE FROM project_task_mail_message_rel")
        
        # 2. Delete project tasks
        self.env.cr.execute("DELETE FROM project_task")
        _logger.info('Deleted %d tasks', self.env.cr.rowcount)
        
        # 3. Delete task recurrence rules
        self.env.cr.execute("DELETE FROM project_task_recurrence")
        _logger.info('Deleted %d task recurrences', self.env.cr.rowcount)
        
        # 4. Get analytic accounts linked to projects before deleting
        self.env.cr.execute("""
            DELETE FROM account_analytic_account
            WHERE id IN (
                SELECT account_id FROM project_project WHERE account_id IS NOT NULL
            )
        """)
        _logger.info('Deleted project-related analytic accounts')
        
        # 5. Delete project many2many relations
        self.env.cr.execute("DELETE FROM project_project_project_tag_rel")
        self.env.cr.execute("DELETE FROM project_project_user_rel")
        self.env.cr.execute("DELETE FROM project_project_partner_rel")
        
        # 6. Delete projects
        self.env.cr.execute("DELETE FROM project_project")
        _logger.info('Deleted %d projects', self.env.cr.rowcount)
        
        # 7. Delete project updates
        self.env.cr.execute("DELETE FROM project_update")
        _logger.info('Deleted %d project updates', self.env.cr.rowcount)
        
        # Note: We DO NOT delete project_task_type (stages) as Odoo requires at least one per user
        
        _logger.info('Projects and tasks deleted')
