# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ResCompany(models.Model):
    _inherit = 'res.company'
    
    plan_id = fields.Many2one('salewise.plan', string='Subscription Plan')
    
    def get_available_plan_ids(self):
        """Get available plan IDs based on company's current plan.
        Returns plan IDs that should be visible (current plan and lower tiers).
        
        This is used for filtering menus, actions, views, etc. based on the plan hierarchy.
        Admin users (no plan) get an empty list which means they see everything.
        """
        self.ensure_one()
        
        if not self.plan_id:
            return []  # No plan = admin mode, they see everything
        
        # Get current plan and all lower tier plans
        available_plans = self.env['salewise.plan'].search([
            ('sequence', '<=', self.plan_id.sequence)
        ])
        return available_plans.ids
    
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
                # Clear all caches when plan changes to ensure menu filtering is updated
                # First clear registry cache (for ormcache decorated methods)
                self.env.registry.clear_cache()
                
                # Then invalidate all environment caches (for computed fields, etc.)
                # This ensures menu visibility is recalculated with new plan
                self.env.invalidate_all()
                
                # If current company's plan changed, trigger page reload
                if self.env.company.id in self.ids:
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'salewise_reload_page',
                    }
        
        return res