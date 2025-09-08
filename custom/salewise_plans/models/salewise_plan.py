# -*- coding: utf-8 -*-
from odoo import models, fields, api


class SalewisePlan(models.Model):
    _name = 'salewise.plan'
    _description = 'Salewise Subscription Plan'
    _order = 'sequence, id'
    
    name = fields.Char(string='Plan Name', required=True)
    description = fields.Text(string='Description')
    price = fields.Float(string='Price', required=True)
    currency_id = fields.Many2one('res.currency', string='Currency', required=True, default=lambda self: self.env.company.currency_id)
    sequence = fields.Integer(string='Sequence', default=10)
    is_active = fields.Boolean(string='Active', default=True)
    company_ids = fields.One2many('res.company', 'plan_id', string='Companies')
    
    @api.depends('name', 'price', 'currency_id')
    def _compute_display_name(self):
        for plan in self:
            if plan.currency_id:
                plan.display_name = f"{plan.name} - {plan.currency_id.symbol}{plan.price}"
            else:
                plan.display_name = plan.name