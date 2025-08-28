# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.http import request


class IrUiMenu(models.Model):
    _inherit = 'ir.ui.menu'
    
    is_saas = fields.Boolean('Is SaaS', default=False)
    lucide_icon = fields.Char('Lucide Icon')
    original_menu_id = fields.Many2one('ir.ui.menu', string='Original Menu')
    
    @api.model
    def load_menus(self, debug):
        """Override to filter menus based on SaaS preference"""
        menus = super().load_menus(debug)
        
        # Check if user has SaaS menus preference
        if request and request.env.user:
            user_settings = request.env.user.res_users_settings_id
            
            if user_settings and user_settings.show_saas_menus:
                # Filter to only show SaaS menus
                saas_menu_ids = request.env['ir.ui.menu'].search([
                    ('is_saas', '=', True)
                ]).ids
                
                # Also include parent menus of SaaS menus
                all_menu_ids = set(saas_menu_ids)
                for menu_id in saas_menu_ids:
                    menu = request.env['ir.ui.menu'].browse(menu_id)
                    parent = menu.parent_id
                    while parent:
                        all_menu_ids.add(parent.id)
                        parent = parent.parent_id
                
                # Find SaaS root menus (those without parents)
                saas_root_menu_ids = request.env['ir.ui.menu'].search([
                    ('is_saas', '=', True),
                    ('parent_id', '=', False)
                ]).ids
                
                # Filter the menus dictionary
                filtered_menus = {}
                for menu_id, menu_data in menus.items():
                    if menu_id == 'root':
                        filtered_menus[menu_id] = menu_data
                        # Update root children to only include SaaS root menus
                        menu_data['children'] = [
                            child_id for child_id in menu_data['children']
                            if child_id in saas_root_menu_ids
                        ]
                    elif menu_id in all_menu_ids:
                        filtered_menus[menu_id] = menu_data
                        # Ensure SaaS root menus have app_id set
                        if menu_id in saas_root_menu_ids:
                            menu_data['app_id'] = menu_id
                        # Update children to only include SaaS menus
                        if 'children' in menu_data:
                            menu_data['children'] = [
                                child_id for child_id in menu_data['children']
                                if child_id in all_menu_ids
                            ]
                
                # Recursively set app_id for all children of SaaS root menus
                def _set_app_id(app_id, menu_id):
                    if menu_id in filtered_menus:
                        filtered_menus[menu_id]['app_id'] = app_id
                        for child_id in filtered_menus[menu_id].get('children', []):
                            _set_app_id(app_id, child_id)
                
                for root_id in saas_root_menu_ids:
                    if root_id in filtered_menus:
                        _set_app_id(root_id, root_id)
                
                return filtered_menus
            else:
                # When SaaS mode is OFF, exclude SaaS menus from normal menus
                saas_menu_ids = request.env['ir.ui.menu'].search([
                    ('is_saas', '=', True)
                ]).ids
                
                # Include all children of SaaS menus to exclude them too
                all_saas_ids = set(saas_menu_ids)
                for menu_id in saas_menu_ids:
                    menu = request.env['ir.ui.menu'].browse(menu_id)
                    children = request.env['ir.ui.menu'].search([('id', 'child_of', menu_id)]).ids
                    all_saas_ids.update(children)
                
                # Filter out SaaS menus from the normal menus
                filtered_menus = {}
                for menu_id, menu_data in menus.items():
                    if menu_id == 'root' or menu_id not in all_saas_ids:
                        filtered_menus[menu_id] = menu_data
                        # Update children to exclude SaaS menus
                        if 'children' in menu_data:
                            menu_data['children'] = [
                                child_id for child_id in menu_data['children']
                                if child_id not in all_saas_ids
                            ]
                
                return filtered_menus
        
        # Return normal Odoo menus when no user settings
        return menus