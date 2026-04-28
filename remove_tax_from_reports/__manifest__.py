{
    'name': 'Remove Tax Column From Reports',
    'version': '1.0',
    'summary': 'Removes Taxes column from Sale Order and Invoice reports',
    'author': 'Custom',
    'depends': ['sale', 'account'],
    'data': [
        'views/report_remove_tax.xml',
    ],
    'installable': True,
    'application': False,
}
