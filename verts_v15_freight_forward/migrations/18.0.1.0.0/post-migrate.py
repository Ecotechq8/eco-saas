# -*- coding: utf-8 -*-
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Post-migration operations for Odoo 18 upgrade."""
    if version and version < '18.0.1.0.0':
        _logger.info("Running post-migration for verts_v15_freight_forward 18.0...")
        
        # Migrate customer/supplier fields to customer_rank/supplier_rank on res.partner
        # Odoo 15: customer=True, supplier=True
        # Odoo 18: customer_rank=1, supplier_rank=1
        cr.execute("""
            UPDATE res_partner 
            SET customer_rank = 1 
            WHERE customer = true AND customer_rank = 0
        """)
        cr.execute("""
            UPDATE res_partner 
            SET supplier_rank = 1 
            WHERE supplier = true AND supplier_rank = 0
        """)
        
        # Update account.move line references if needed
        # account_accountant menu reference was changed to account.menu_finance
        # No data migration needed for this as it's just a menu modification
        
        _logger.info("Post-migration completed successfully")
