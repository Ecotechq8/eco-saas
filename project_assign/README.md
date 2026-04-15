# Project Assignment to Employees

## Overview
This Odoo module adds a Many-to-Many relationship between Employees and Projects, allowing you to:
- Assign multiple projects to an employee
- View all projects an employee is working on
- Display employee's projects in Attendance records

## Features
✅ **Employee Form**: New "Projects" tab showing all assigned projects  
✅ **Project Form**: New "Assigned Employees" tab showing team members  
✅ **Attendance View**: Shows all projects the employee is working on  
✅ **Many-to-Many**: One employee can work on multiple projects, one project can have multiple employees  

## Installation
1. Place this module in your Odoo addons directory
2. Update your Odoo apps list
3. Install the module from the Odoo Apps menu

## Usage

### Assign Projects to Employee
1. Go to **Employees** → **Employees**
2. Open an employee record
3. Navigate to the **Projects** tab
4. Select all projects the employee is working on
5. Save

### View Employee Projects in Attendance
1. Go to **Attendances** → **Attendances**
2. Open or view any attendance record
3. The **Employee Projects** field will automatically display all projects assigned to that employee
4. This field is read-only and updates automatically when employee's projects change

### Assign Employees to Project (Alternative)
1. Go to **Project** → **Projects**
2. Open a project
3. Navigate to the **Assigned Employees** tab
4. Select all employees working on this project
5. Save

## Technical Details

### Models Extended
- `hr.employee` → Added `project_ids` field
- `project.project` → Added `employee_ids` field  
- `hr.attendance` → Added `project_ids` related field

### Database Tables
- `employee_project_rel` → Many2many relation table (automatically created by Odoo)

### Field Types
- **Employee.project_ids**: Many2many (stored)
- **Project.employee_ids**: Many2many (stored, same relation table)
- **Attendance.project_ids**: Many2many related field (readonly)

## Permissions
All users with Employee/Project access rights can view and edit project assignments.

## Support
For issues or questions, please contact your system administrator.

## License
LGPL-3
