# -*- coding: utf-8 -*-
from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'
    
    plan_id = fields.Many2one('salewise.plan', string='Subscription Plan')