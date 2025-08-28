{
    'name': 'SaleWise Plans Management',
    'version': '1.0',
    'category': 'SaleWise/Configuration',
    'summary': 'Plan-based feature management for SaleWise',
    'description': """
        SaleWise Plans Management
        ==========================
        
        This module implements plan-based feature control for SaleWise platform.
        
        Features:
        ---------
        * Three subscription plans (Starter, Professional, Enterprise)
        * Company-level plan configuration
        * Dynamic view filtering based on plan
        * Menu visibility control
        * Feature flags system
        
        Plans:
        ------
        - Starter: Basic sales and invoicing
        - Professional: + Inventory, HR, Projects, Advanced features
        - Enterprise: Everything including manufacturing, automation, analytics
    """,
    'author': 'SaleWise',
    'depends': [
        'base',
        'sale_management',
        'account',
        'stock',
        'hr',
        'project',
        'mrp',
        'marketing_automation',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/res_company_views.xml',
        'views/menu_visibility.xml',
        'data/default_plans.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}