# -*- coding: utf-8 -*-
{
    'name': 'Salewise Menu Flatten',
    'version': '18.0.1.0.0',
    'category': 'Tools/UI',
    'summary': 'Flatten menu hierarchy in apps dropdown',
    'description': """
        This module flattens the menu hierarchy so that all menu levels
        appear directly in the main apps dropdown (grid icon) instead of
        being spread across the navbar and nested dropdowns.
    """,
    'author': 'Salewise',
    'website': 'https://salewise.com',
    'depends': [
        'web',
        'salewise_menu_system',  # For SaaS menu filtering
    ],
    'data': [
    ],
    'assets': {
        'web.assets_backend': [
            # Override navbar after the original
            (
                'after',
                'web/static/src/webclient/navbar/navbar.js',
                'salewise_menu_flatten/static/src/webclient/navbar/navbar.js',
            ),
            (
                'after',
                'web/static/src/webclient/navbar/navbar.xml',
                'salewise_menu_flatten/static/src/webclient/navbar/navbar.xml',
            ),
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}