{
    'name': 'EcoTech-Advanced',
    'summary': 'Eco Advanced Modules',
    'description': '''
        Advanced modules bundle for eco tech saas
    ''',
    'version': '18.0.1.2.4',
    'category': 'Themes/Backend',
    'license': 'LGPL-3',
    'author': 'Ahmed Ismail (EcoTech.co)',

    'depends': [
        'eco_theme','mrp','hr','hr_holidays','hr_recruitment','employee_religion','hr_attendance',
        'hr_skills','hr_contract','eco_hr_custom','dev_hr_loan','check_management'
    ],
    'excludes': [
        'web_enterprise',
    ],
    'data': [
        'views/menu_overrides.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
