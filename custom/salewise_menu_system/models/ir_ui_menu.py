# -*- coding: utf-8 -*-
from odoo import models, fields, api, tools
from odoo.osv import expression
import logging
import traceback

_logger = logging.getLogger(__name__)

class IrUiMenu(models.Model):
    _inherit = 'ir.ui.menu'
    
    is_saas_menu = fields.Boolean(
        string='SaaS Menu',
        default=False,
        help='If checked, this menu is only visible to SaaS users'
    )
    
    @api.model
    def search(self, domain, offset=0, limit=None, order=None):
        """Override search to apply SaaS menu filtering"""
        user = self.env.user
        
        # Don't filter if context says to show full list or if user doesn't have is_saas_user field
        if self._context.get('ir.ui.menu.full_list') or not hasattr(user, 'is_saas_user'):
            _logger.debug(f"Skipping menu filter: full_list={self._context.get('ir.ui.menu.full_list')}, has_is_saas_user={hasattr(user, 'is_saas_user')}")
            return super().search(domain, offset=offset, limit=limit, order=order)
        
        # Add filtering based on user type
        if user.is_saas_user:
            # SaaS users only see menus with is_saas_menu=True
            domain = expression.AND([domain, [('is_saas_menu', '=', True)]])
            _logger.info(f"SaaS user {user.login} searching menus with domain: {domain}")
        else:
            # Standard users only see menus with is_saas_menu=False or None
            domain = expression.AND([domain, ['|', ('is_saas_menu', '=', False), ('is_saas_menu', '=', None)]])
            _logger.info(f"Standard user {user.login} searching menus with domain: {domain}")
        
        result = super().search(domain, offset=offset, limit=limit, order=order)
        _logger.info(f"Search returned {len(result)} menus for {user.login}")
        return result
    
    @api.model
    def search_fetch(self, domain, field_names, offset=0, limit=None, order=None):
        """Override search_fetch to apply SaaS menu filtering"""
        user = self.env.user
        
        # Don't filter if context says to show full list or if user doesn't have is_saas_user field
        if self._context.get('ir.ui.menu.full_list') or not hasattr(user, 'is_saas_user'):
            return super().search_fetch(domain, field_names, offset=offset, limit=limit, order=order)
        
        # Add filtering based on user type
        if user.is_saas_user:
            # SaaS users only see menus with is_saas_menu=True
            domain = expression.AND([domain, [('is_saas_menu', '=', True)]])
            _logger.debug(f"SaaS user {user.login} search_fetch with added filter for is_saas_menu=True")
        else:
            # Standard users only see menus with is_saas_menu=False or None
            domain = expression.AND([domain, ['|', ('is_saas_menu', '=', False), ('is_saas_menu', '=', None)]])
            _logger.debug(f"Standard user {user.login} search_fetch with added filter for is_saas_menu!=True")
        
        return super().search_fetch(domain, field_names, offset=offset, limit=limit, order=order)
    
    @api.model
    @api.returns('self')
    def get_user_roots(self):
        """Override to filter root menus based on user type"""
        user = self.env.user
        
        # If user doesn't have the is_saas_user field, use default behavior
        if not hasattr(user, 'is_saas_user'):
            return super().get_user_roots()
        
        # Build domain based on user type
        if user.is_saas_user:
            # SaaS users only see root menus with is_saas_menu=True
            domain = [('parent_id', '=', False), ('is_saas_menu', '=', True)]
            _logger.info(f"SaaS user {user.login} getting root menus with domain: {domain}")
        else:
            # Standard users only see root menus with is_saas_menu=False or None
            domain = [('parent_id', '=', False), '|', ('is_saas_menu', '=', False), ('is_saas_menu', '=', None)]
            _logger.info(f"Standard user {user.login} getting root menus with domain: {domain}")
        
        # Use full list context to bypass filtering in search method
        result = self.with_context({'ir.ui.menu.full_list': True}).search(domain)
        
        # For SaaS users, also apply group filtering RIGHT HERE
        if user.is_saas_user:
            # Filter by groups - this is what was missing!
            result = result._filter_visible_menus()
            _logger.info(f"After group filtering, {user.login} has {len(result)} root menus")
        else:
            _logger.info(f"User {user.login} has {len(result)} root menus")
        
        return result
    
    @api.model
    @tools.ormcache('frozenset(self.env.user.groups_id.ids)', 'debug')
    def _visible_menu_ids(self, debug=False):
        """Override to implement SaaS menu filtering"""
        user = self.env.user
        
        _logger.error(f"!!!!! _visible_menu_ids called for user {user.login} !!!!!")
        
        # If user doesn't have is_saas_user field, use standard behavior
        if not hasattr(user, 'is_saas_user'):
            return super()._visible_menu_ids(debug)
        
        # Get all menus with full list context
        context = {'ir.ui.menu.full_list': True}
        menus = self.with_context(context).search_fetch([], ['action', 'parent_id', 'groups_id', 'is_saas_menu']).sudo()
        
        # Filter based on user type FIRST
        if user.is_saas_user:
            # SaaS users only see SaaS menus
            menus = menus.filtered(lambda m: m.is_saas_menu)
            _logger.info(f"SaaS user {user.login} filtered to {len(menus)} SaaS menus")
        else:
            # Standard users only see non-SaaS menus
            menus = menus.filtered(lambda m: not m.is_saas_menu)
            _logger.info(f"Standard user {user.login} filtered to {len(menus)} standard menus")
        
        # Now apply group filtering on the filtered menus
        group_ids = set(self.env.user._get_group_ids())
        if not debug:
            group_ids = group_ids - {self.env['ir.model.data']._xmlid_to_res_id('base.group_no_one', raise_if_not_found=False)}
        
        _logger.warning(f"DEBUG: User {user.login} has groups: {group_ids}")
        
        # Keep menus that either have no groups OR user has at least one of the groups
        menus_before_group_filter = menus
        menus = menus.filtered(
            lambda menu: not menu.groups_id or not group_ids.isdisjoint(menu.groups_id._ids)
        )
        
        # DEBUG: Show what was filtered out
        filtered_out = menus_before_group_filter - menus
        if filtered_out:
            _logger.warning(f"DEBUG: Filtered out {len(filtered_out)} menus due to group restrictions:")
            for m in filtered_out:
                _logger.warning(f"  - {m.name} requires groups {m.groups_id.ids}, user has {group_ids}")
        
        _logger.info(f"After group filtering, {user.login} has {len(menus)} visible menus")
        
        # Continue with standard action filtering...
        from collections import defaultdict
        actions_by_model = defaultdict(set)
        for action in menus.mapped('action'):
            if action:
                actions_by_model[action._name].add(action.id)
        
        existing_actions = {
            action
            for model_name, action_ids in actions_by_model.items()
            for action in self.env[model_name].browse(action_ids).exists()
        }
        
        menus = menus.filtered(lambda menu: not menu.action or menu.action in existing_actions)
        
        # Filter out children of hidden menus
        visible_ids = set(menus.ids)
        for menu in menus:
            if menu.parent_id and menu.parent_id.id not in visible_ids:
                visible_ids.discard(menu.id)
        
        return frozenset(visible_ids)