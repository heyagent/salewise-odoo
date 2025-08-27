# -*- coding: utf-8 -*-
from odoo import models, fields, api, tools
from odoo.osv import expression


class IrUiMenu(models.Model):
    _inherit = "ir.ui.menu"

    is_saas_menu = fields.Boolean(
        string="SaaS Menu",
        default=False,
        help="If checked, this menu is only visible to SaaS users",
    )
    
    saas_action_ref = fields.Char(
        string="SaaS Action Reference",
        help="Action reference string (e.g., 'contacts.action_contacts')"
    )
    
    saas_views = fields.Char(
        string="SaaS Views",
        help="Comma-separated view types (e.g., 'card,list,form')"
    )
    
    @api.model
    def _resolve_saas_action(self):
        """Resolve saas_action_ref to actual action and set it"""
        for menu in self:
            if menu.saas_action_ref and not menu.action:
                try:
                    # Try to resolve the action reference
                    action = self.env.ref(menu.saas_action_ref, raise_if_not_found=False)
                    if action:
                        # Set the action field with proper format
                        menu.action = f"{action._name},{action.id}"
                except Exception:
                    # If resolution fails, skip this menu
                    pass

    @api.model
    def _get_saas_domain_filter(self):
        """Helper method to get domain filter based on user type.
        Returns empty list if no filtering needed."""
        user = self.env.user

        # Check if user has the SaaS field
        if not hasattr(user, "is_saas_user"):
            return []

        if user.is_saas_user:
            return [("is_saas_menu", "=", True)]
        else:
            return ["|", ("is_saas_menu", "=", False), ("is_saas_menu", "=", None)]

    @api.model
    def search(self, domain, offset=0, limit=None, order=None):
        """Override search to apply SaaS menu filtering"""
        # Skip filtering if context says so
        if self._context.get("ir.ui.menu.full_list"):
            return super().search(domain, offset=offset, limit=limit, order=order)

        # Apply SaaS filtering
        saas_filter = self._get_saas_domain_filter()
        if saas_filter:
            domain = expression.AND([domain, saas_filter])

        return super().search(domain, offset=offset, limit=limit, order=order)

    @api.model
    def search_fetch(self, domain, field_names, offset=0, limit=None, order=None):
        """Override search_fetch to apply SaaS menu filtering"""
        # Skip filtering if context says so
        if self._context.get("ir.ui.menu.full_list"):
            return super().search_fetch(
                domain, field_names, offset=offset, limit=limit, order=order
            )

        # Apply SaaS filtering
        saas_filter = self._get_saas_domain_filter()
        if saas_filter:
            domain = expression.AND([domain, saas_filter])

        return super().search_fetch(
            domain, field_names, offset=offset, limit=limit, order=order
        )

    @api.model
    @api.returns("self")
    def get_user_roots(self):
        """Override to filter root menus based on user type and groups"""
        user = self.env.user

        # Check if user has is_saas_user field
        if not hasattr(user, "is_saas_user"):
            return super().get_user_roots()

        # Build base domain for root menus
        domain = [("parent_id", "=", False)]

        # Add SaaS filtering
        if user.is_saas_user:
            domain.append(("is_saas_menu", "=", True))
        else:
            domain.extend(
                ["|", ("is_saas_menu", "=", False), ("is_saas_menu", "=", None)]
            )

        # Search with full list context to bypass additional filtering
        menus = self.with_context({"ir.ui.menu.full_list": True}).search(domain)

        # For SaaS users, we need to apply group filtering here
        # because load_menus doesn't call _filter_visible_menus on root menus
        if user.is_saas_user:
            # Get user's groups
            group_ids = set(user._get_group_ids())
            # Filter menus by group access
            menus = menus.filtered(
                lambda menu: not menu.groups_id
                or not group_ids.isdisjoint(menu.groups_id._ids)
            )

        return menus

    def read(self, fields=None, load="_classic_read"):
        """Override to filter menu records based on user type"""
        # Make sure we always read is_saas_menu field for filtering
        if fields and 'is_saas_menu' not in fields:
            fields = fields + ['is_saas_menu']
        
        result = super().read(fields, load)

        user = self.env.user
        if not hasattr(user, "is_saas_user"):
            return result

        # Filter results based on user type
        filtered_result = []
        for record_data in result:
            # Check if this menu should be visible to this user type
            is_saas_menu = record_data.get("is_saas_menu", False)

            if user.is_saas_user and is_saas_menu:
                filtered_result.append(record_data)
            elif not user.is_saas_user and not is_saas_menu:
                filtered_result.append(record_data)

        return filtered_result

    @api.model
    def search_read(
        self, domain=None, fields=None, offset=0, limit=None, order=None, **read_kwargs
    ):
        """Override to enforce menu isolation between user types"""
        user = self.env.user

        # Only apply filtering if user has is_saas_user field
        if hasattr(user, "is_saas_user"):
            # Build the filter domain based on user type
            if user.is_saas_user:
                filter_domain = [("is_saas_menu", "=", True)]
            else:
                filter_domain = [
                    "|",
                    ("is_saas_menu", "=", False),
                    ("is_saas_menu", "=", None),
                ]

            # Properly combine domains using expression.AND
            from odoo.osv import expression

            domain = expression.AND([domain or [], filter_domain])

        return super().search_read(domain, fields, offset, limit, order, **read_kwargs)

    @api.model
    def search_count(self, domain=None, limit=None):
        """Override to return correct counts with menu isolation"""
        user = self.env.user

        # Only apply filtering if user has is_saas_user field
        if hasattr(user, "is_saas_user"):
            # Build the filter domain based on user type
            if user.is_saas_user:
                filter_domain = [("is_saas_menu", "=", True)]
            else:
                filter_domain = [
                    "|",
                    ("is_saas_menu", "=", False),
                    ("is_saas_menu", "=", None),
                ]

            # Properly combine domains using expression.AND
            from odoo.osv import expression

            domain = expression.AND([domain or [], filter_domain])

        return super().search_count(domain, limit)

    @api.model
    @tools.ormcache(
        "frozenset(self.env.user.groups_id.ids)",
        'self.env.user.is_saas_user if hasattr(self.env.user, "is_saas_user") else False',
        "debug",
    )
    def _visible_menu_ids(self, debug=False):
        """Override to implement SaaS menu filtering with proper caching"""
        user = self.env.user

        # If user doesn't have is_saas_user field, use standard behavior
        if not hasattr(user, "is_saas_user"):
            return super()._visible_menu_ids(debug)

        # Get all menus efficiently
        context = {"ir.ui.menu.full_list": True}
        menus = self.with_context(context).search_fetch(
            [], ["action", "parent_id", "groups_id", "is_saas_menu"]
        )

        # Filter based on user type
        if user.is_saas_user:
            menus = menus.filtered(lambda m: m.is_saas_menu)
        else:
            menus = menus.filtered(lambda m: not m.is_saas_menu)

        # Apply group filtering
        group_ids = set(user._get_group_ids())
        if not debug:
            # Remove debug group
            debug_group = self.env["ir.model.data"]._xmlid_to_res_id(
                "base.group_no_one", raise_if_not_found=False
            )
            if debug_group:
                group_ids.discard(debug_group)

        # Keep menus that either have no groups OR user has at least one of the groups
        menus = menus.filtered(
            lambda menu: not menu.groups_id
            or not group_ids.isdisjoint(menu.groups_id._ids)
        )

        # Filter by action existence
        from collections import defaultdict

        actions_by_model = defaultdict(set)
        for action in menus.mapped("action"):
            if action:
                actions_by_model[action._name].add(action.id)

        existing_actions = {
            action
            for model_name, action_ids in actions_by_model.items()
            for action in self.env[model_name].browse(action_ids).exists()
        }

        menus = menus.filtered(
            lambda menu: not menu.action or menu.action in existing_actions
        )

        # Build visible menu hierarchy
        visible_ids = set(menus.ids)

        # Remove children of hidden menus
        for menu in menus:
            if menu.parent_id and menu.parent_id.id not in visible_ids:
                visible_ids.discard(menu.id)

        return frozenset(visible_ids)
