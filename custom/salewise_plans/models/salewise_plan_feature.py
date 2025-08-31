# -*- coding: utf-8 -*-
from odoo import models, fields


class SalewisePlanFeature(models.Model):
    _name = 'salewise.plan.feature'
    _description = 'Salewise Plan Feature'
    _order = 'sequence, id'
    
    name = fields.Char(string='Feature', required=True)
    plan_id = fields.Many2one('salewise.plan', string='Plan', required=True, ondelete='cascade')
    sequence = fields.Integer(string='Sequence', default=10)