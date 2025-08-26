# -*- coding: utf-8 -*-
{
    "name": "Salewise Menu System",
    "version": "1.0",
    "category": "Hidden",
    "summary": "Menu access control for SaaS users",
    "description": """
        This module provides menu filtering based on user type:
        - Standard users see only standard Odoo menus
        - SaaS users see only Salewise menus
    """,
    "depends": ["base"],
    "data": [],
    "installable": True,
    "auto_install": False,
    "application": False,
    "post_init_hook": "post_init_hook",
}
