# -*- coding: utf-8 -*-
{
    'name': 'HR Attendance Date Restriction',
    'version': '18.0.1.0.0',
    'category': 'Human Resources/Attendances',
    'summary': 'Prevent creating or importing attendance records older than 7 days',
    'description': """
HR Attendance Date Restriction
==============================
This module prevents employees from creating or importing Attendance records (Check In / Check Out) for dates older than 7 days from the current date.

Key Features:
-------------
* **Manual Entry Protection**: Employees cannot manually create or modify Check In / Check Out records for dates older than 7 days.
* **Import Protection**: System automatically rejects imported attendance records (CSV, XLSX, etc.) with Check In / Check Out dates older than 7 days and displays clear validation errors.
* **Configurable Settings**: Configure the allowed past days limit and toggle the restriction in Attendances > Configuration > Settings.
* **Bypass Option**: Configurable option and dedicated security group to allow Attendance Managers / Authorized users to bypass the restriction when required.
    """,
    'author': 'Ahmed Emara',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'hr_attendance',
    ],
    'data': [
        'security/security.xml',
        'views/res_config_settings_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
