# -*- coding: utf-8 -*-
from odoo import models, fields, api

class SalewiseMenu(models.Model):
    _name = 'salewise.menu'
    _description = 'Salewise Menu Configuration'
    _order = 'sequence, id'
    _parent_store = True
    _rec_name = 'name'
    
    name = fields.Char('Menu Name', required=True)
    parent_id = fields.Many2one('salewise.menu', 'Parent Menu', ondelete='cascade', index=True)
    parent_path = fields.Char(index=True)
    child_ids = fields.One2many('salewise.menu', 'parent_id', 'Child Menus')
    
    sequence = fields.Integer('Order', default=10)
    icon = fields.Char('Icon')
    
    # Action fields - stored as strings from YAML
    action_ref = fields.Char('Action Reference', help='e.g. contacts.action_contacts')
    model_name = fields.Char('Model', help='e.g. res.partner')
    views = fields.Char('Views', help='Comma-separated view types, e.g. card,list,form')
    
    # Optional fields from YAML
    domain = fields.Char('Domain')
    context = fields.Char('Context')
    search_view_ref = fields.Char('Search View Reference')
    technical = fields.Boolean('Technical', default=False)
    
    active = fields.Boolean('Active', default=True)
    
    # Computed field for display
    display_name = fields.Char('Display Name', compute='_compute_display_name', store=True, recursive=True)
    level = fields.Integer('Level', compute='_compute_level', store=True, recursive=True)
    complete_sequence = fields.Char('Complete Sequence', compute='_compute_complete_sequence', store=True, recursive=True)
    
    @api.depends('name', 'parent_id.display_name')
    def _compute_display_name(self):
        for record in self:
            if record.parent_id:
                record.display_name = f"{record.parent_id.display_name} / {record.name}"
            else:
                record.display_name = record.name
    
    @api.depends('parent_id', 'parent_id.level')
    def _compute_level(self):
        for record in self:
            if not record.parent_id:
                record.level = 1
            else:
                record.level = record.parent_id.level + 1
    
    @api.depends('sequence', 'parent_id', 'parent_id.complete_sequence')
    def _compute_complete_sequence(self):
        for record in self:
            if record.parent_id:
                record.complete_sequence = f"{record.parent_id.complete_sequence or ''}{str(record.sequence).zfill(6)}/"
            else:
                record.complete_sequence = f"{str(record.sequence).zfill(6)}/"
    
    def get_menu_tree(self, domain=None):
        """API method to get menu tree structure"""
        if domain is None:
            domain = [('parent_id', '=', False), ('active', '=', True)]
        
        menus = self.search(domain, order='sequence')
        result = []
        
        for menu in menus:
            menu_dict = {
                'id': menu.id,
                'name': menu.name,
                'icon': menu.icon,
                'sequence': menu.sequence,
                'action_ref': menu.action_ref,
                'model_name': menu.model_name,
                'views': menu.views,
                'domain': menu.domain,
                'context': menu.context,
                'search_view_ref': menu.search_view_ref,
                'technical': menu.technical,
                'children': menu._get_children_tree()
            }
            result.append(menu_dict)
        
        return result
    
    def _get_children_tree(self):
        """Recursive method to get children tree"""
        result = []
        for child in self.child_ids.filtered(lambda c: c.active).sorted('sequence'):
            child_dict = {
                'id': child.id,
                'name': child.name,
                'icon': child.icon,
                'sequence': child.sequence,
                'action_ref': child.action_ref,
                'model_name': child.model_name,
                'views': child.views,
                'domain': child.domain,
                'context': child.context,
                'search_view_ref': child.search_view_ref,
                'technical': child.technical,
                'children': child._get_children_tree()
            }
            result.append(child_dict)
        return result