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
            try:
                self.env.cr.execute("""
                    SET session_replication_role = DEFAULT;
                """)
            except:
                pass
            self.env.cr.rollback()
            _logger.error('DATA CLEANUP FAILED: %s', str(e), exc_info=True)
            raise UserError(_('Data cleanup failed: %s') % str(e))

    def _safe_execute(self, query, params=None):
        """Execute SQL safely, handling missing tables"""
        try:
            self.env.cr.execute(query, params)
            return self.env.cr.rowcount
        except Exception as e:
            if 'does not exist' in str(e):
                _logger.debug('Table not found, skipping: %s', str(e))
                return 0
            raise

    def _delete_analytic_lines_sql(self):
        """Delete analytic lines using direct SQL"""
        _logger.info('Deleting analytic lines...')
        self._safe_execute("DELETE FROM account_analytic_line")
        _logger.info('Deleted %d analytic lines', self.env.cr.rowcount)

    def _delete_accounting_sql(self):
        """Delete accounting transactions using direct SQL"""
        _logger.info('Deleting accounting transactions...')
        
        # Delete in order to avoid FK constraints
        
        # 1. Delete payments (with their related records)
        self._safe_execute("DELETE FROM account_payment_register")
        count = self._safe_execute("DELETE FROM account_payment")
        _logger.info('Deleted %d payments', count)
        
        # 2. Delete partial reconciliations
        count = self._safe_execute("DELETE FROM account_partial_reconcile")
        _logger.info('Deleted %d partial reconciliations', count)
        
        # 3. Delete full reconciliations  
        count = self._safe_execute("DELETE FROM account_full_reconcile")
        _logger.info('Deleted %d full reconciliations', count)
        
        # 4. Delete bank statement lines
        count = self._safe_execute("DELETE FROM account_bank_statement_line")
        _logger.info('Deleted %d bank statement lines', count)
        
        # 5. Delete bank statements
        count = self._safe_execute("DELETE FROM account_bank_statement")
        _logger.info('Deleted %d bank statements', count)
        
        # 6. Delete tax adjustments and distributions
        self._safe_execute("DELETE FROM account_tax_report_data")
        self._safe_execute("DELETE FROM account_reconcile_model")
        self._safe_execute("DELETE FROM account_reconcile_model_line")
        
        # 7. Delete move lines (account_move_line)
        count = self._safe_execute("DELETE FROM account_move_line")
        _logger.info('Deleted %d move lines', count)
        
        # 8. Delete many2many relations for moves
        self._safe_execute("DELETE FROM account_move_line_account_tax_rel")
        self._safe_execute("DELETE FROM account_move_line__tax__account_move_line_rel")
        self._safe_execute("DELETE FROM account_analytic_tag_account_move_line_rel")
        
        # 9. Delete account moves
        count = self._safe_execute("DELETE FROM account_move")
        _logger.info('Deleted %d account moves', count)
        
        # 10. Delete analytic distributions
        self._safe_execute("DELETE FROM account_analytic_distribution_mixin")
        
        _logger.info('Accounting transactions deleted')

    def _delete_inventory_sql(self):
        """Delete inventory transactions using direct SQL"""
        _logger.info('Deleting inventory transactions...')
        
        # Delete in order to avoid FK constraints
        
        # 1. Delete stock move lines first
        count = self._safe_execute("DELETE FROM stock_move_line")
        _logger.info('Deleted %d stock move lines', count)
        
        # 2. Delete stock package levels
        count = self._safe_execute("DELETE FROM stock_package_level")
        _logger.info('Deleted %d package levels', count)
        
        # 3. Delete stock lots (optional - comment out if you want to keep lots)
        # count = self._safe_execute("DELETE FROM stock_lot")
        # _logger.info('Deleted %d stock lots', count)
        
        # 4. Delete stock moves
        count = self._safe_execute("DELETE FROM stock_move")
        _logger.info('Deleted %d stock moves', count)
        
        # 5. Delete many2many relations
        self._safe_execute("DELETE FROM stock_move_rule_repair_rel")
        self._safe_execute("DELETE FROM mrp_production_workcenter_move_rel")
        self._safe_execute("DELETE FROM stock_move_project_tag_rel")
        
        # 6. Delete stock scrap
        count = self._safe_execute("DELETE FROM stock_scrap")
        _logger.info('Deleted %d scraps', count)
        
        # 7. Delete stock lots (if needed - preserves serial numbers)
        # count = self._safe_execute("DELETE FROM stock_lot")
        
        # 8. Delete stock pickings
        count = self._safe_execute("DELETE FROM stock_picking")
        _logger.info('Deleted %d stock pickings', count)
        
        # 9. Delete stock inventory
        count = self._safe_execute("DELETE FROM stock_inventory")
        _logger.info('Deleted %d inventory adjustments', count)
        
        # 10. Delete stock quants (resets physical inventory count)
        count = self._safe_execute("DELETE FROM stock_quant")
        _logger.info('Deleted %d stock quants', count)
        
        # Note: We DO NOT delete stock_location, stock_warehouse, stock_quant_package
        # as these are master data that should be preserved
        
        _logger.info('Inventory transactions deleted')

    def _delete_sales_sql(self):
        """Delete sales orders using direct SQL"""
        _logger.info('Deleting sales orders...')
        
        # 1. Delete sale order lines
        count = self._safe_execute("DELETE FROM sale_order_line")
        _logger.info('Deleted %d sale order lines', count)
        
        # 2. Delete sale order many2many relations
        self._safe_execute("DELETE FROM sale_order_team_member_rel")
        self._safe_execute("DELETE FROM sale_order_crm_tracking_sale_order_rel")
        self._safe_execute("DELETE FROM sale_order_project_project_rel")
        self._safe_execute("DELETE FROM sale_order_tag_rel")
        
        # 3. Delete sale orders
        count = self._safe_execute("DELETE FROM sale_order")
        _logger.info('Deleted %d sale orders', count)
        
        _logger.info('Sales orders deleted')

    def _delete_purchase_sql(self):
        """Delete purchase orders using direct SQL"""
        _logger.info('Deleting purchase orders...')
        
        # 1. Delete purchase order lines
        count = self._safe_execute("DELETE FROM purchase_order_line")
        _logger.info('Deleted %d purchase order lines', count)
        
        # 2. Delete purchase order many2many relations
        self._safe_execute("DELETE FROM purchase_order_invoice_plan_rel")
        self._safe_execute("DELETE FROM purchase_order_blanket_order_rel")
        self._safe_execute("DELETE FROM purchase_order_tag_rel")
        
        # 3. Delete purchase orders
        count = self._safe_execute("DELETE FROM purchase_order")
        _logger.info('Deleted %d purchase orders', count)
        
        _logger.info('Purchase orders deleted')

    def _delete_projects_sql(self):
        """Delete projects and tasks using direct SQL"""
        _logger.info('Deleting projects and tasks...')
        
        # 1. Delete project task entries from many2many
        self._safe_execute("DELETE FROM project_task_project_tag_rel")
        self._safe_execute("DELETE FROM project_task_user_rel")
        self._safe_execute("DELETE FROM project_task_mail_message_rel")
        self._safe_execute("DELETE FROM project_task_stage_project_tag_rel")
        
        # 2. Delete project tasks
        count = self._safe_execute("DELETE FROM project_task")
        _logger.info('Deleted %d tasks', count)
        
        # 3. Delete task recurrence rules
        count = self._safe_execute("DELETE FROM project_task_recurrence")
        _logger.info('Deleted %d task recurrences', count)
        
        # 4. Delete task descriptions (rich text fields)
        self._safe_execute("DELETE FROM project_task_description")
        
        # 5. Get analytic accounts linked to projects before deleting
        count = self._safe_execute("""
            DELETE FROM account_analytic_account
            WHERE id IN (
                SELECT account_id FROM project_project WHERE account_id IS NOT NULL
            )
        """)
        _logger.info('Deleted project-related analytic accounts')
        
        # 6. Delete project many2many relations
        self._safe_execute("DELETE FROM project_project_project_tag_rel")
        self._safe_execute("DELETE FROM project_project_user_rel")
        self._safe_execute("DELETE FROM project_project_partner_rel")
        
        # 7. Delete projects
        count = self._safe_execute("DELETE FROM project_project")
        _logger.info('Deleted %d projects', count)
        
        # 8. Delete project updates
        count = self._safe_execute("DELETE FROM project_update")
        _logger.info('Deleted %d project updates', count)
        
        # Note: We DO NOT delete project_task_type (stages) as Odoo requires at least one per user
        
        _logger.info('Projects and tasks deleted')
