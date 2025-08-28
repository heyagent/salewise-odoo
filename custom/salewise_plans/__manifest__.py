{
    'name': 'Salewise Plans',
    'version': '1.0',
    'summary': 'Adds plan selection to company',
    'depends': [
        'base',
    ],
    'data': [
        'views/res_company_views.xml',
        'data/default_plans.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}