# -*- coding: utf-8 -*-
from odoo import models, api


class ResUsers(models.Model):
    _inherit = 'res.users'
    
    @api.model_create_multi
    def create(self, vals_list):
        """Override to ensure new users have SaaS menus enabled by default"""
        users = super().create(vals_list)
        
        # For each new user, ensure they have settings with SaaS menus enabled
        for user in users:
            if not user.res_users_settings_id:
                # Create settings with SaaS menus enabled by default
                self.env['res.users.settings'].create({
                    'user_id': user.id,
                    'show_saas_menus': True,
                })
            elif not user.res_users_settings_id.show_saas_menus:
                # Enable SaaS menus if settings exist but it's disabled
                user.res_users_settings_id.show_saas_menus = True
        
        return users