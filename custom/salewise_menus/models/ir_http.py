# -*- coding: utf-8 -*-
from odoo import models
from odoo.http import request


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'
    
    def session_info(self):
        """Add show_saas_menus to session info"""
        session_info = super().session_info()
        
        if request.env.user:
            user_settings = request.env.user.res_users_settings_id
            session_info.update({
                'show_saas_menus': user_settings.show_saas_menus if user_settings else False
            })
        
        return session_info