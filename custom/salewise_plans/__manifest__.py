{
    'name': 'Salewise Plans',
    'version': '1.0',
    'summary': 'Subscription plans management for Salewise',
    'depends': [
        'base',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/plans_data.xml',
        'data/plan_features.xml',
        'views/salewise_plan_views.xml',
        'views/res_company_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}