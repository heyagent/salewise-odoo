# -*- coding: utf-8 -*-
from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    plan_type = fields.Selection(
        related='company_id.plan_type',
        string='Subscription Plan',
        readonly=False
    )