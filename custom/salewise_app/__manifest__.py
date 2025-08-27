# -*- coding: utf-8 -*-
{
    'name': 'Salewise App',
    'version': '18.0.1.0.0',
    'category': 'Tools',
    'summary': 'Salewise complete application with menu system and flattening',
    'description': """
        Complete Salewise application that provides:
        - SaaS menu system with user type filtering
        - Flattened menu hierarchy in apps dropdown
        - Group-based menu access control
        - Separate user types (SaaS vs Standard)
    """,
    'author': 'Salewise',
    'website': 'https://salewise.com',
    'depends': [
        'base',
        'web',
        'contacts',
        'crm',
        'sale',
        'sale_management',
        'sales_team',
        'contract',
        'account',
        'mail',
        'product',
        'hr',
        'hr_recruitment',
        'hr_holidays',
        'hr_expense',
        'hr_contract',
        'calendar',
        'project',
        'documents',
    ],
    'data': [
        'data/saas_menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            # Override navbar after the original
            (
                'after',
                'web/static/src/webclient/navbar/navbar.js',
                'salewise_app/static/src/webclient/navbar/navbar.js',
            ),
            (
                'after',
                'web/static/src/webclient/navbar/navbar.xml',
                'salewise_app/static/src/webclient/navbar/navbar.xml',
            ),
        ],
    },
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}