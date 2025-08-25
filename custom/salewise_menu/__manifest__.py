# -*- coding: utf-8 -*-
{
    'name': 'Salewise Menu',
    'version': '1.0.0',
    'category': 'Tools',
    'summary': 'Manage Salewise menu configuration',
    'author': 'Salewise',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'views/salewise_menu_views.xml',
        'data/menu_data.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}