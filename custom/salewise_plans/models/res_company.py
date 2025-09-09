# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ResCompany(models.Model):
    _inherit = 'res.company'
    
    plan_id = fields.Many2one('salewise.plan', string='Subscription Plan')
    
    def write(self, vals):
        """Override write to clear caches and reload when plan changes.
        
        Following Odoo's pattern from base res.company:
        - Check if critical fields changed before clearing cache
        - Use registry.clear_cache() as done in core
        - Return action only after successful write
        """
        # Check if plan is being changed
        plan_changing = 'plan_id' in vals
        
        if plan_changing:
            # Store old plan_id values before write
            old_plans = {company.id: company.plan_id.id for company in self}
        
        # Perform the write
        res = super().write(vals)
        
        if plan_changing:
            # Check if any plan actually changed
            plan_changed = False
            for company in self:
                if old_plans.get(company.id) != company.plan_id.id:
                    plan_changed = True
                    break
            
            if plan_changed:
                # Clear cache following Odoo's pattern
                # Using clear_cache() like in base res_company.write()
                self.env.registry.clear_cache()
                
                # If current company's plan changed, trigger page reload
                if self.env.company.id in self.ids:
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'salewise_reload_page',
                    }
        
        return res