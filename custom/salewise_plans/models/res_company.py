# -*- coding: utf-8 -*-
from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'
    
    plan_type = fields.Selection([
        ('starter', 'Starter'),
        ('professional', 'Professional'),
        ('enterprise', 'Enterprise')
    ], string='Subscription Plan', default='starter', required=True)