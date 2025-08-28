# -*- coding: utf-8 -*-
from odoo import models, api


class ResUsers(models.Model):
    _inherit = 'res.users'
    
    @api.model
    def action_toggle_saas_menus(self):
        """Toggle the SaaS menu display preference for the current user"""
        user = self.env.user
        settings = user.res_users_settings_id
        
        if not settings:
            # Create settings if they don't exist
            settings = self.env['res.users.settings']._find_or_create_for_user(user)
        
        # Toggle the setting
        settings.show_saas_menus = not settings.show_saas_menus
        
        # Clear the menu cache to ensure menus are reloaded
        self.env['ir.ui.menu'].clear_caches()
        
        # Return reload action to refresh the menu
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }