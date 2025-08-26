# -*- coding: utf-8 -*-
from odoo import models, fields

class ResUsers(models.Model):
    _inherit = 'res.users'
    
    is_saas_user = fields.Boolean(
        string='SaaS User',
        default=False,
        help='If checked, user will only see SaaS menus'
    )