{
    'name': 'Salewise Plans',
    'version': '1.0',
    'summary': 'Subscription plans management for Salewise',
    'depends': [
        'base',
        'web',
    ],
    'data': [
        'security/group.xml',
        'security/ir.model.access.csv',
        'data/plans_data.xml',
        'views/salewise_plan_views.xml',
        'views/res_company_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'salewise_plans/static/src/js/salewise_plan_display.js',
            'salewise_plans/static/src/js/plan_reload.js',
            'salewise_plans/static/src/js/user_menu_plan.esm.js',
            'salewise_plans/static/src/xml/salewise_plan_display.xml',
            'salewise_plans/static/src/scss/salewise_plan_display.scss',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
