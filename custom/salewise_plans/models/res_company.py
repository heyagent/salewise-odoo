# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ResCompany(models.Model):
    _inherit = 'res.company'
    
    plan_type = fields.Selection([
        ('starter', 'Starter'),
        ('professional', 'Professional'),
        ('enterprise', 'Enterprise')
    ], string='Subscription Plan', default='starter', required=True,
       help="Current subscription plan determining available features")
    
    # Computed feature flags based on plan
    has_sales = fields.Boolean(compute='_compute_features', string='Sales Features')
    has_invoicing = fields.Boolean(compute='_compute_features', string='Invoicing Features')
    has_inventory = fields.Boolean(compute='_compute_features', string='Inventory Management')
    has_manufacturing = fields.Boolean(compute='_compute_features', string='Manufacturing')
    has_hr = fields.Boolean(compute='_compute_features', string='HR Management')
    has_projects = fields.Boolean(compute='_compute_features', string='Project Management')
    has_marketing = fields.Boolean(compute='_compute_features', string='Marketing Automation')
    has_advanced_accounting = fields.Boolean(compute='_compute_features', string='Advanced Accounting')
    has_reporting = fields.Boolean(compute='_compute_features', string='Advanced Reporting')
    has_automation = fields.Boolean(compute='_compute_features', string='Business Automation')
    
    @api.depends('plan_type')
    def _compute_features(self):
        """Compute available features based on subscription plan"""
        
        # Define features per plan
        PLAN_FEATURES = {
            'starter': {
                'sales': True,
                'invoicing': True,
                'inventory': False,
                'manufacturing': False,
                'hr': False,
                'projects': False,
                'marketing': False,
                'advanced_accounting': False,
                'reporting': False,
                'automation': False,
            },
            'professional': {
                'sales': True,
                'invoicing': True,
                'inventory': True,
                'manufacturing': False,
                'hr': True,
                'projects': True,
                'marketing': False,
                'advanced_accounting': True,
                'reporting': True,
                'automation': False,
            },
            'enterprise': {
                'sales': True,
                'invoicing': True,
                'inventory': True,
                'manufacturing': True,
                'hr': True,
                'projects': True,
                'marketing': True,
                'advanced_accounting': True,
                'reporting': True,
                'automation': True,
            }
        }
        
        for company in self:
            features = PLAN_FEATURES.get(company.plan_type, PLAN_FEATURES['starter'])
            company.has_sales = features['sales']
            company.has_invoicing = features['invoicing']
            company.has_inventory = features['inventory']
            company.has_manufacturing = features['manufacturing']
            company.has_hr = features['hr']
            company.has_projects = features['projects']
            company.has_marketing = features['marketing']
            company.has_advanced_accounting = features['advanced_accounting']
            company.has_reporting = features['reporting']
            company.has_automation = features['automation']
    
    def has_feature(self, feature_name):
        """Check if company plan has a specific feature"""
        self.ensure_one()
        feature_field = f'has_{feature_name}'
        if hasattr(self, feature_field):
            return getattr(self, feature_field)
        return False
    
    def get_plan_display_name(self):
        """Get formatted plan name for display"""
        self.ensure_one()
        return dict(self._fields['plan_type'].selection).get(self.plan_type, 'Unknown')