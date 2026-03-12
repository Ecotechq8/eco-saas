{
    'name': 'HR Attendance Custom',
    'version': '18.0.1.0',
    'category': 'Human Resources',
    'depends': ['base', 'hr_attendance'],
    'author': "Eco-Tech, Zaynab Ibrahim",
    'assets': {
        'web.assets_backend': [
            'eco_hr_attendance_custom/static/src/js/geolocation_patch.js',
        ],
        'hr_attendance.assets_public_kiosk': [
            'eco_hr_attendance_custom/static/src/js/geolocation_patch.js',
        ],
    },
    'data': [
        'data/ir_action_data.xml',
        'views/hr_attendance.xml',
    ],
    'installable': True,
}