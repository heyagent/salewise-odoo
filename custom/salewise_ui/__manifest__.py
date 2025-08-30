{
    'name': 'Salewise UI Customizations',
    'version': '1.0',
    'summary': 'UI element customizations for Salewise mode',
    'description': """
        This module provides UI customizations that are applied when Salewise mode is enabled.
        It hides various Odoo UI elements and features that are not needed in the simplified Salewise interface.
    """,
    'depends': [
        'base',
        'web',
        'web_tour',
        'salewise_menus',  # For session.show_saas_menus
    ],
    'assets': {
        'web.assets_backend': [
            'salewise_ui/static/src/js/tour_patch.js',
            'salewise_ui/static/src/js/user_menu.esm.js',
            'salewise_ui/static/src/js/favorites_menu_patch.js',
            'salewise_ui/static/src/js/custom_group_by_patch.js',
            'salewise_ui/static/src/js/custom_filter_patch.js',
            'salewise_ui/static/src/js/search_autocomplete_patch.js',
            'salewise_ui/static/src/js/edit_filter_patch.js',
            'salewise_ui/static/src/js/add_properties_patch.js',
            'salewise_ui/static/src/xml/search_bar_menu.xml',
            'salewise_ui/static/src/xml/search_bar.xml',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}