# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.http import request


class IrUiMenu(models.Model):
    _inherit = 'ir.ui.menu'
    
    is_saas = fields.Boolean('Is SaaS', default=False)
    lucide_icon = fields.Char('Lucide Icon')
    original_menu_id = fields.Many2one('ir.ui.menu', string='Original Menu')
    
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to ensure proper parent_path"""
        # Create the menus first
        menus = super().create(vals_list)
        
        # Force parent_path recomputation for ALL menus being created
        # This is needed because XML data loading doesn't trigger it properly
        if menus:
            # Get all menus including their ancestors
            all_menus = menus
            for menu in menus:
                if menu.parent_id:
                    all_menus |= menu.parent_id
            
            # Force recomputation of parent_path
            all_menus._parent_store_compute()
        
        return menus
    
    def write(self, vals):
        """Override write to maintain parent_path integrity"""
        res = super().write(vals)
        
        # If parent_id changed, parent_path is automatically updated by Odoo
        # We just need to ensure it's flushed to DB
        if 'parent_id' in vals:
            self.flush_model(['parent_path'])
        
        return res
    
    @api.model
    def get_user_roots(self):
        """Override to return SaaS root menus when user has SaaS preference"""
        if request and request.env.user:
            user_settings = request.env.user.res_users_settings_id
            
            if user_settings and user_settings.show_saas_menus:
                # Return only SaaS root menus WITH SUDO to bypass permissions
                saas_roots = self.sudo().search([
                    ('parent_id', '=', False),
                    ('is_saas', '=', True)
                ])
                return saas_roots
            else:
                # Return normal root menus excluding SaaS ones
                normal_roots = self.search([
                    ('parent_id', '=', False),
                    ('is_saas', '=', False)
                ])
                return normal_roots
        
        # Default behavior when no user context
        return super().get_user_roots()
    
    def load_web_menus(self, debug):
        """Override to add is_saas field to menu data sent to frontend"""
        # Call parent method
        web_menus = super().load_web_menus(debug)
        
        # Get the actual menu records from database to add is_saas field
        menu_ids = [menu_id for menu_id in web_menus.keys() if menu_id != 'root']
        
        if menu_ids:
            menus = self.browse(menu_ids).read(['id', 'is_saas'])
            menu_dict = {menu['id']: menu['is_saas'] for menu in menus}
            
            for menu_id, menu_data in web_menus.items():
                if menu_id != 'root' and menu_id in menu_dict:
                    menu_data['is_saas'] = menu_dict[menu_id]
        
        return web_menus