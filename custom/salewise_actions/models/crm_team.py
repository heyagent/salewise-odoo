# -*- coding: utf-8 -*-
from odoo import models, api

class CrmTeam(models.Model):
    _inherit = 'crm.team'
    
    @api.model
    def salewise_action_your_pipeline(self):
        """Return Salewise pipeline action with view restrictions"""
        # Get the original action to preserve any dynamic context
        original_action = super().action_your_pipeline()
        
        # Get our Salewise action with view restrictions
        salewise_action = self.env.ref('salewise_actions.salewise_crm_lead_action_pipeline').read()[0]
        
        # Preserve dynamic context from original (like team_id filters)
        if original_action.get('context'):
            salewise_action['context'] = original_action['context']
            
        return salewise_action
    
    @api.model
    def salewise_action_opportunity_forecast(self):
        """Return Salewise forecast action with view restrictions"""
        # Get the original action to preserve any dynamic context
        original_action = super().action_opportunity_forecast()
        
        # Get our Salewise action with view restrictions
        salewise_action = self.env.ref('salewise_actions.salewise_crm_lead_action_forecast').read()[0]
        
        # Preserve dynamic context from original (like team_id filters)
        if original_action.get('context'):
            salewise_action['context'] = original_action['context']
            
        return salewise_action