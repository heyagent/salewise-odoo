# -*- coding: utf-8 -*-
from odoo import models, api


class IrUiMenu(models.Model):
    _inherit = 'ir.ui.menu'
    
    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        """Filter menus based on company plan"""
        menus = super().search(args, offset, limit, order, count)
        
        if count:
            return menus
            
        company = self.env.company
        
        # Define menu restrictions per plan
        if company.plan_type == 'starter':
            # Hide advanced modules for starter plan
            hidden_keywords = ['inventory', 'manufacturing', 'mrp', 'employee', 'project', 
                              'marketing', 'automation', 'quality', 'maintenance']
            menus = menus.filtered(
                lambda m: not any(keyword in m.complete_name.lower() for keyword in hidden_keywords)
            )
            
        elif company.plan_type == 'professional':
            # Hide enterprise-only features
            hidden_keywords = ['manufacturing', 'mrp', 'marketing automation', 'quality']
            menus = menus.filtered(
                lambda m: not any(keyword in m.complete_name.lower() for keyword in hidden_keywords)
            )
        
        # Enterprise sees everything (no filtering needed)
        
        return menus