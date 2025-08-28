# -*- coding: utf-8 -*-
from odoo import models, fields


class IrUiMenu(models.Model):
    _inherit = 'ir.ui.menu'
    
    is_saas = fields.Boolean('Is SaaS', default=False)
    lucide_icon = fields.Char('Lucide Icon')
    original_menu_id = fields.Many2one('ir.ui.menu', string='Original Menu')