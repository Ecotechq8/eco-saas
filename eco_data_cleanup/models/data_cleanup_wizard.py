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

    def _get_existing_tables(self):
        """Get list of all existing tables in the database"""
        self.env.cr.execute("""
            SELECT tablename FROM pg_tables 
            WHERE schemaname = 'public'
        """)
        return [row[0] for row in self.env.cr.fetchall()]

    def _delete_table_data_safe(self, table_name, existing_tables, savepoint_name='sp'):
        """Delete data from a table using savepoints to prevent transaction abortion"""
        if table_name not in existing_tables:
            return 0
        
        try:
            # Create a savepoint before each DELETE
            self.env.cr.execute(f"SAVEPOINT {savepoint_name}")
            
            # Try the delete
            self.env.cr.execute(f"DELETE FROM {table_name}")
            count = self.env.cr.rowcount
            
            # Release the savepoint if successful
            self.env.cr.execute(f"RELEASE SAVEPOINT {savepoint_name}")
            
            if count > 0:
                _logger.info('Deleted %d records from %s', count, table_name)
            return count
            
        except Exception as e:
            # Rollback to savepoint on error
            try:
                self.env.cr.execute(f"ROLLBACK TO SAVEPOINT {savepoint_name}")
            except:
                pass
            _logger.warning('Could not delete from %s: %s', table_name, str(e))
            return 0

    def _delete_analytic_lines_sql(self):
        """Delete analytic lines using direct SQL"""
        _logger.info('Deleting analytic lines...')
        existing_tables = self._get_existing_tables()
        self._delete_table_data_safe('account_analytic_line', existing_tables, 'sp_analytic')

    def _delete_accounting_sql(self):
        """Delete accounting transactions using direct SQL"""
        _logger.info('Deleting accounting transactions...')
        existing_tables = self._get_existing_tables()
        sp_counter = [0]
        
        def next_sp():
            sp_counter[0] += 1
            return f'sp_acct_{sp_counter[0]}'
        
        # Delete in order to avoid FK constraints
        self._delete_table_data_safe('account_payment_register', existing_tables, next_sp())
        self._delete_table_data_safe('account_payment', existing_tables, next_sp())
        self._delete_table_data_safe('account_partial_reconcile', existing_tables, next_sp())
        self._delete_table_data_safe('account_full_reconcile', existing_tables, next_sp())
        self._delete_table_data_safe('account_bank_statement_line', existing_tables, next_sp())
        self._delete_table_data_safe('account_bank_statement', existing_tables, next_sp())
        self._delete_table_data_safe('account_tax_report_data', existing_tables, next_sp())
        self._delete_table_data_safe('account_reconcile_model', existing_tables, next_sp())
        self._delete_table_data_safe('account_reconcile_model_line', existing_tables, next_sp())
        self._delete_table_data_safe('account_move_line', existing_tables, next_sp())
        self._delete_table_data_safe('account_move_line_account_tax_rel', existing_tables, next_sp())
        self._delete_table_data_safe('account_move_line__tax__account_move_line_rel', existing_tables, next_sp())
        self._delete_table_data_safe('account_analytic_tag_account_move_line_rel', existing_tables, next_sp())
        self._delete_table_data_safe('account_move', existing_tables, next_sp())
        self._delete_table_data_safe('account_analytic_distribution_mixin', existing_tables, next_sp())
        
        _logger.info('Accounting transactions deleted')

    def _delete_inventory_sql(self):
        """Delete inventory transactions using direct SQL"""
        _logger.info('Deleting inventory transactions...')
        existing_tables = self._get_existing_tables()
        sp_counter = [0]
        
        def next_sp():
            sp_counter[0] += 1
            return f'sp_inv_{sp_counter[0]}'
        
        # Delete in order to avoid FK constraints
        self._delete_table_data_safe('stock_move_line', existing_tables, next_sp())
        self._delete_table_data_safe('stock_package_level', existing_tables, next_sp())
        self._delete_table_data_safe('stock_move', existing_tables, next_sp())
        self._delete_table_data_safe('stock_move_rule_repair_rel', existing_tables, next_sp())
        self._delete_table_data_safe('mrp_production_workcenter_move_rel', existing_tables, next_sp())
        self._delete_table_data_safe('stock_move_project_tag_rel', existing_tables, next_sp())
        self._delete_table_data_safe('stock_scrap', existing_tables, next_sp())
        self._delete_table_data_safe('stock_picking', existing_tables, next_sp())
        self._delete_table_data_safe('stock_inventory', existing_tables, next_sp())
        self._delete_table_data_safe('stock_quant', existing_tables, next_sp())
        
        _logger.info('Inventory transactions deleted')

    def _delete_sales_sql(self):
        """Delete sales orders using direct SQL"""
        _logger.info('Deleting sales orders...')
        existing_tables = self._get_existing_tables()
        sp_counter = [0]
        
        def next_sp():
            sp_counter[0] += 1
            return f'sp_sale_{sp_counter[0]}'
        
        self._delete_table_data_safe('sale_order_line', existing_tables, next_sp())
        self._delete_table_data_safe('sale_order_team_member_rel', existing_tables, next_sp())
        self._delete_table_data_safe('sale_order_crm_tracking_sale_order_rel', existing_tables, next_sp())
        self._delete_table_data_safe('sale_order_project_project_rel', existing_tables, next_sp())
        self._delete_table_data_safe('sale_order_tag_rel', existing_tables, next_sp())
        self._delete_table_data_safe('sale_order', existing_tables, next_sp())
        
        _logger.info('Sales orders deleted')

    def _delete_purchase_sql(self):
        """Delete purchase orders using direct SQL"""
        _logger.info('Deleting purchase orders...')
        existing_tables = self._get_existing_tables()
        sp_counter = [0]
        
        def next_sp():
            sp_counter[0] += 1
            return f'sp_po_{sp_counter[0]}'
        
        self._delete_table_data_safe('purchase_order_line', existing_tables, next_sp())
        self._delete_table_data_safe('purchase_order_invoice_plan_rel', existing_tables, next_sp())
        self._delete_table_data_safe('purchase_order_blanket_order_rel', existing_tables, next_sp())
        self._delete_table_data_safe('purchase_order_tag_rel', existing_tables, next_sp())
        self._delete_table_data_safe('purchase_order', existing_tables, next_sp())
        
        _logger.info('Purchase orders deleted')

    def _delete_projects_sql(self):
        """Delete projects and tasks using direct SQL"""
        _logger.info('Deleting projects and tasks...')
        existing_tables = self._get_existing_tables()
        sp_counter = [0]
        
        def next_sp():
            sp_counter[0] += 1
            return f'sp_proj_{sp_counter[0]}'
        
        self._delete_table_data_safe('project_task_project_tag_rel', existing_tables, next_sp())
        self._delete_table_data_safe('project_task_user_rel', existing_tables, next_sp())
        self._delete_table_data_safe('project_task_mail_message_rel', existing_tables, next_sp())
        self._delete_table_data_safe('project_task_stage_project_tag_rel', existing_tables, next_sp())
        self._delete_table_data_safe('project_task', existing_tables, next_sp())
        self._delete_table_data_safe('project_task_recurrence', existing_tables, next_sp())
        self._delete_table_data_safe('project_task_description', existing_tables, next_sp())
        
        # Delete project-related analytic accounts
        if 'project_project' in existing_tables and 'account_analytic_account' in existing_tables:
            try:
                self.env.cr.execute("SAVEPOINT sp_proj_analytic")
                self.env.cr.execute("""
                    DELETE FROM account_analytic_account
                    WHERE id IN (
                        SELECT account_id FROM project_project WHERE account_id IS NOT NULL
                    )
                """)
                self.env.cr.execute("RELEASE SAVEPOINT sp_proj_analytic")
                _logger.info('Deleted project-related analytic accounts')
            except Exception as e:
                try:
                    self.env.cr.execute("ROLLBACK TO SAVEPOINT sp_proj_analytic")
                except:
                    pass
                _logger.warning('Could not delete project analytic accounts: %s', str(e))
        
        self._delete_table_data_safe('project_project_project_tag_rel', existing_tables, next_sp())
        self._delete_table_data_safe('project_project_user_rel', existing_tables, next_sp())
        self._delete_table_data_safe('project_project_partner_rel', existing_tables, next_sp())
        self._delete_table_data_safe('project_project', existing_tables, next_sp())
        self._delete_table_data_safe('project_update', existing_tables, next_sp())
        
        _logger.info('Projects and tasks deleted')
