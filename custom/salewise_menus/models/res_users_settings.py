# -*- coding: utf-8 -*-
from odoo import models, fields


class ResUsersSettings(models.Model):
    _inherit = 'res.users.settings'
    
    show_saas_menus = fields.Boolean('Show SaaS Menus', default=False)