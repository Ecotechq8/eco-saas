# ECO Data Cleanup - Delete All Transactions

## Overview
This Odoo module provides a centralized action to delete all transactions from multiple modules:
- **Purchase Orders**
- **Sales Orders**
- **Inventory Transactions** (Stock Moves, Pickings, etc.)
- **Projects & Tasks**
- **Accounting Entries** (Journal Entries, Invoices, Payments, etc.)

## Features
- ✅ One-click deletion of all transactions across modules
- ✅ Selective deletion (choose which modules to clean)
- ✅ Proper order of deletion to respect database constraints
- ✅ Preserves master data (products, partners, employees, etc.)
- ✅ Comprehensive logging of all deletion actions
- ✅ Warning notifications before deletion

## Installation
1. Place this module in your Odoo addons directory
2. Update your Odoo apps list
3. Install the module from the Odoo Apps menu

## Usage

### Access the Cleanup Wizard
The cleanup feature is available in two locations:

1. **Inventory Menu** → `Delete All Transactions`
   - Path: Inventory > Operations > Delete All Transactions
   - Accessible to: Inventory Managers

2. **Settings Menu** → `Data Cleanup`
   - Path: Settings > Technical > Data Cleanup
   - Accessible to: Administrators

### Steps to Delete Transactions
1. Navigate to the cleanup wizard using one of the menu paths above
2. Choose your deletion options:
   - ☑️ **Delete All Transactions** - Deletes everything (default)
   - Or selectively choose which modules to clean:
     - Delete Purchase Orders
     - Delete Sales Orders
     - Delete Inventory Transactions
     - Delete Projects & Tasks
     - Delete Accounting Entries

3. Click **"Delete Transactions"** button
4. Confirm the warning dialog
5. Wait for the process to complete

## What Gets Deleted

### Purchase Module
- Purchase Orders (all states)
- Purchase Order Lines

### Sales Module
- Sales Orders (all states)
- Quotations
- Sales Order Lines

### Inventory Module
- Stock Moves
- Stock Move Lines
- Stock Pickings
- Inventory Adjustments
- Scrap Orders

### Projects Module
- Projects
- Tasks
- Custom Project Stages

### Accounting Module
- Journal Entries (posted and draft)
- Invoices
- Payments
- Bank Statements
- Reconciliations
- Move Lines

## What is NOT Deleted (Master Data)
The following master data is preserved:
- Products
- Partners (Customers/Vendors)
- Employees
- Warehouses
- Locations
- Journals
- Accounts
- Payment Methods
- Default Project Stages
- Users

## Important Warnings

⚠️ **CRITICAL**: This is a DESTRUCTIVE operation
- All deleted data is **PERMANENTLY** removed
- This operation **CANNOT BE UNDONE**
- Always create a **database backup** before using this feature

⚠️ **Best Practices**:
1. Create a database backup before running cleanup
2. Test in a staging environment first
3. Review the logs after deletion
4. Verify the results in each module

## Technical Details

### Deletion Order
The module deletes data in a specific order to respect foreign key constraints:
1. Accounting (depends on sales/purchase invoices)
2. Projects & Tasks
3. Sales Orders
4. Purchase Orders
5. Inventory (last, as it may link to other modules)

### Logging
All deletion actions are logged in the Odoo server logs with the format:
```
WARNING: DATA CLEANUP INITIATED BY USER: [username]
INFO: Deleting [module] transactions...
INFO: Deleted [count] [type]
WARNING: DATA CLEANUP COMPLETED SUCCESSFULLY
```

### Database Transaction
- The entire cleanup runs in a single database transaction
- If any error occurs, the entire operation is rolled back
- No partial deletions will occur on failure

## Permissions
- **Inventory Managers** can access the cleanup from the Inventory menu
- **Administrators** can access from both Inventory and Settings menus

## Troubleshooting

### Issue: Permission Error
**Solution**: Ensure you have Inventory Manager or Administrator rights

### Issue: Deletion Failed
**Solution**: 
1. Check the Odoo logs for specific error messages
2. Ensure no other processes are locking the database
3. Try running in smaller selections (not "Delete All")

### Issue: Orphaned Records
**Solution**: The module handles cascading deletes properly. If you find orphaned records, they are likely from manual deletions outside this tool.

## Support
For issues or questions, please contact your system administrator.

## License
LGPL-3
