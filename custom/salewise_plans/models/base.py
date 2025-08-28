# -*- coding: utf-8 -*-
from odoo import models, api
from lxml import etree
import json


class Base(models.AbstractModel):
    _inherit = 'base'
    
    @api.model
    def get_view(self, view_id=None, view_type='form', **options):
        """Override to filter fields based on company plan"""
        result = super().get_view(view_id, view_type, **options)
        
        # Parse the view
        doc = etree.XML(result['arch'])
        company = self.env.company
        
        # Check for salewise-feature attributes
        for node in doc.xpath("//*[@salewise-feature]"):
            feature = node.get('salewise-feature')
            
            # Check if company has this feature
            if not company.has_feature(feature):
                # Hide the element
                node.set('invisible', '1')
                
                # Update modifiers
                modifiers = json.loads(node.get('modifiers', '{}'))
                modifiers['invisible'] = True
                node.set('modifiers', json.dumps(modifiers))
        
        # Handle plan-specific visibility
        for node in doc.xpath("//*[@salewise-plan]"):
            required_plans = node.get('salewise-plan').split(',')
            
            if company.plan_type not in required_plans:
                node.set('invisible', '1')
                
                modifiers = json.loads(node.get('modifiers', '{}'))
                modifiers['invisible'] = True
                node.set('modifiers', json.dumps(modifiers))
        
        # Convert back to string
        result['arch'] = etree.tostring(doc, encoding='unicode')
        
        return result