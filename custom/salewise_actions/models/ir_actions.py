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


class IrActionsServer(models.Model):
    _inherit = 'ir.actions.server'
    
    original_action = fields.Many2one(
        'ir.actions.server', 
        string='Original Action',
        help='Reference to the original action this was cloned from'
    )
