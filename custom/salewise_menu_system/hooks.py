# -*- coding: utf-8 -*-
import logging

_logger = logging.getLogger(__name__)

def post_init_hook(env):
    """
    Post-init hook to create SaaS menu and user programmatically
    """
    _logger.info("Salewise Menu System: Setting up menus and users...")
    
    # Create Salewise main menu
    salewise_menu = env['ir.ui.menu'].search([('name', '=', 'Salewise')], limit=1)
    if not salewise_menu:
        salewise_menu = env['ir.ui.menu'].create({
            'name': 'Salewise',
            'is_saas_menu': True,
            'sequence': 1,
        })
        _logger.info(f"Created Salewise main menu: {salewise_menu.id}")
    else:
        salewise_menu.write({'is_saas_menu': True})
        _logger.info(f"Updated existing Salewise menu: {salewise_menu.id}")
    
    # Create submenu items for Salewise
    submenus = [
        {'name': 'Dashboard', 'sequence': 10},
        {'name': 'Customers', 'sequence': 20},
        {'name': 'Analytics', 'sequence': 30},
        {'name': 'Settings', 'sequence': 40},
    ]
    
    for submenu_data in submenus:
        existing = env['ir.ui.menu'].search([
            ('name', '=', submenu_data['name']),
            ('parent_id', '=', salewise_menu.id)
        ], limit=1)
        
        if not existing:
            env['ir.ui.menu'].create({
                'name': submenu_data['name'],
                'parent_id': salewise_menu.id,
                'is_saas_menu': True,
                'sequence': submenu_data['sequence'],
            })
            _logger.info(f"Created submenu: {submenu_data['name']}")
    
    # Create SaaS admin user
    saas_user = env['res.users'].search([('login', '=', 'saas_admin')], limit=1)
    if not saas_user:
        saas_user = env['res.users'].create({
            'name': 'SaaS Administrator',
            'login': 'saas_admin',
            'password': 'saas_admin',
            'is_saas_user': True,
            'groups_id': [(6, 0, [env.ref('base.group_user').id])],
        })
        _logger.info(f"Created SaaS admin user: {saas_user.login}")
    else:
        saas_user.write({'is_saas_user': True})
        _logger.info(f"Updated existing SaaS user: {saas_user.login}")
    
    # Ensure admin user is marked as standard user
    admin_user = env['res.users'].search([('login', '=', 'admin')], limit=1)
    if admin_user:
        admin_user.write({'is_saas_user': False})
        _logger.info("Ensured admin user is marked as standard user")
    
    _logger.info("Salewise Menu System: Setup completed successfully")