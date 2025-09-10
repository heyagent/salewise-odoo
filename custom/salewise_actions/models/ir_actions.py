# -*- coding: utf-8 -*-
from odoo import models, fields


class IrActionsActWindow(models.Model):
    _inherit = 'ir.actions.act_window'
    
    original_action = fields.Many2one(
        'ir.actions.act_window',
        string='Original Action',
        help='Reference to the original action this was cloned from'
    )
    
    original_view_mode = fields.Char(
        string='Original View Mode',
        help='The view_mode string from the original action'
    )
    
    is_saas = fields.Boolean(
        string='Is SaaS Action',
        default=False,
        help='Indicates if this action is part of the SaaS system'
    )
    
    is_system = fields.Boolean(
        string='Is System Action',
        default=False,
        help='Indicates if this is a system action (available to all plans)'
    )
    
    plan_id = fields.Many2one(
        'salewise.plan',
        string='Plan',
        help='The minimum plan required to access this action'
    )


class IrActionsServer(models.Model):
    _inherit = 'ir.actions.server'
    
    original_action = fields.Many2one(
        'ir.actions.server', 
        string='Original Action',
        help='Reference to the original action this was cloned from'
    )
    
    is_saas = fields.Boolean(
        string='Is SaaS Action',
        default=False,
        help='Indicates if this action is part of the SaaS system'
    )
    
    is_system = fields.Boolean(
        string='Is System Action',
        default=False,
        help='Indicates if this is a system action (available to all plans)'
    )
    
    plan_id = fields.Many2one(
        'salewise.plan',
        string='Plan',
        help='The minimum plan required to access this action'
    )
