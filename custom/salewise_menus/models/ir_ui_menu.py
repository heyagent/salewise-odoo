# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.http import request


class IrUiMenu(models.Model):
    _inherit = 'ir.ui.menu'
    
    is_saas = fields.Boolean('Is SaaS', default=False)
    is_system = fields.Boolean('Is System', default=False, help='System/Admin only menu')
    lucide_icon = fields.Char('Lucide Icon')
    original_menu_id = fields.Many2one('ir.ui.menu', string='Original Menu')
    plan_id = fields.Many2one('salewise.plan', string='Required Plan', 
                              help='Plan required to see this menu. Empty means admin/no plan required.')

    # no module-level logging in production

    # --------------------
    # Helpers
    # --------------------
    def _is_saas_mode(self):
        """Return True when the current user enabled SaaS menus.

        Works both with and without an HTTP request (e.g., in tests/cron).
        """
        if request and request.env and request.env.user:
            settings = request.env.user.res_users_settings_id
            return bool(settings and settings.show_saas_menus)
        # fallback: use env user (e.g., tests using with_user)
        user = self.env.user
        settings = getattr(user, 'res_users_settings_id', False)
        return bool(settings and settings.show_saas_menus)

    def _get_available_plan_ids(self):
        company = self.env.company
        return company.get_available_plan_ids() if company else []

    # --------------------
    # Core integration points
    # --------------------
    def _load_menus_blacklist(self):
        """Return ids to exclude from load_menus when in SaaS mode.

        We leverage core's blacklist hook to avoid re-implementing load_menus.
        """
        if not self._is_saas_mode():
            return []

        domain_parts = [[('is_saas', '=', False)]]  # always exclude non-SaaS in SaaS mode
        plan_ids = self._get_available_plan_ids()
        if plan_ids:
            # Non-admin: exclude system menus and menus outside allowed plans
            domain_parts.append([('is_system', '=', True)])
            domain_parts.append([('is_saas', '=', True), ('plan_id', 'not in', plan_ids)])

        from odoo.osv import expression
        blacklist_domain = expression.OR(domain_parts) if len(domain_parts) > 1 else domain_parts[0]
        ids = self.sudo().search(blacklist_domain).ids
        return ids
    
    @api.model
    def get_user_roots(self):
        """Override to return SaaS root menus when user has SaaS preference"""
        if request and request.env.user:
            settings = request.env.user.res_users_settings_id
            if settings and settings.show_saas_menus:
                company = request.env.company
                domain = [('parent_id', '=', False), ('is_saas', '=', True)]
                if company and company.plan_id:
                    # Non-admin: only roots within allowed plans and not system
                    plan_ids = company.get_available_plan_ids()
                    if plan_ids:
                        domain += [('is_system', '=', False), ('plan_id', 'in', plan_ids)]
                # Admin (no plan): all SaaS roots including system
                recs = self.search(domain)
                return recs
            # Normal mode: only non-SaaS roots
            return self.search([('parent_id', '=', False), ('is_saas', '=', False)])
        
        # Default behavior when no user context
        return super().get_user_roots()
    
    @api.model
    def search_fetch(self, domain, field_names, offset=0, limit=None, order=None):
        """Override to apply plan-based filtering for SaaS menus"""
        menus = super().search_fetch(domain, field_names, offset=offset, limit=limit, order=order)

        # When explicitly querying SaaS menus, apply plan filter for non-admins
        if any(
            term for term in domain if len(term) == 3 and term[0] == 'is_saas' and term[2] is True
        ):
            company = self.env.company
            if company and company.plan_id:
                allowed = set(company.get_available_plan_ids())
                menus = menus.filtered(lambda m: not m.is_system and m.plan_id and m.plan_id.id in allowed)
        
        return menus
    
    @api.model
    def search_count(self, domain, limit=None):
        """Override to apply plan-based filtering for count consistency"""
        if any(
            term for term in domain if len(term) == 3 and term[0] == 'is_saas' and term[2] is True
        ):
            # Ensure count aligns with search_fetch filtering
            return len(self.search_fetch(domain, ['id'], limit=limit))
        
        # For non-SaaS menus, use parent method
        return super().search_count(domain, limit=limit)
    
    def load_web_menus(self, debug):
        """Enrich web menus with SaaS metadata; rely on core filtering."""
        web_menus = super().load_web_menus(debug)

        # Add is_saas/plan_id/is_system flags used by client patches and filtering
        menu_ids = [mid for mid in web_menus.keys() if mid != 'root']
        if menu_ids:
            data = {
                rec['id']: rec
                for rec in self.browse(menu_ids).read(['id', 'is_saas', 'plan_id', 'is_system'])
            }
            for mid, m in web_menus.items():
                if mid == 'root':
                    continue
                info = data.get(mid)
                if info:
                    m['is_saas'] = info['is_saas']
                    m['plan_id'] = info['plan_id']
                    m['is_system'] = info['is_system']

        # In SaaS mode, hide admin/system area from the web UI for all users
        if self._is_saas_mode():
            system_root = self.env.ref('salewise_menus.menu_saas_system', raise_if_not_found=False)
            system_root_id = system_root.id if system_root else None

            # collect ids to remove: any is_system=True and the System root subtree
            to_remove = set(mid for mid, m in web_menus.items()
                            if mid != 'root' and m.get('is_system'))
            if system_root_id and system_root_id in web_menus:
                stack = [system_root_id]
                while stack:
                    current = stack.pop()
                    if current in to_remove:
                        # already marked, still expand its children
                        pass
                    to_remove.add(current)
                    for child in web_menus.get(current, {}).get('children', []) or []:
                        if child not in to_remove:
                            stack.append(child)

            if to_remove:
                # Remove references from parents first
                for mid, m in list(web_menus.items()):
                    if mid == 'root':
                        # root keeps children as list of ids
                        if 'children' in m and isinstance(m['children'], list):
                            m['children'] = [cid for cid in m['children'] if cid not in to_remove]
                        continue
                    children = m.get('children')
                    if isinstance(children, list):
                        m['children'] = [cid for cid in children if cid not in to_remove]

                # Finally drop the removed nodes
                for rid in to_remove:
                    web_menus.pop(rid, None)

            # Additionally enforce plan-based pruning on the client data for non-admin
            company = self.env.company
            if company and company.plan_id:
                allowed = set(company.get_available_plan_ids() or [])
                # collect all nodes with a plan outside allowed set
                def menu_plan_id(mid):
                    pid = web_menus.get(mid, {}).get('plan_id')
                    if not pid:
                        return None
                    # plan_id may be int id, [id, name] or (id, name)
                    if isinstance(pid, (list, tuple)):
                        return pid[0]
                    return pid

                bad = set(
                    mid for mid, m in web_menus.items()
                    if mid != 'root' and m.get('is_saas') and (menu_plan_id(mid) is not None) and (menu_plan_id(mid) not in allowed)
                )
                # expand to include full subtree under those nodes
                stack = list(bad)
                while stack:
                    current = stack.pop()
                    for child in web_menus.get(current, {}).get('children', []) or []:
                        if child not in bad:
                            bad.add(child)
                            stack.append(child)
                if bad:
                    # detach from parents
                    for mid, m in list(web_menus.items()):
                        if mid == 'root':
                            if 'children' in m and isinstance(m['children'], list):
                                m['children'] = [cid for cid in m['children'] if cid not in bad and cid not in to_remove]
                            continue
                        children = m.get('children')
                        if isinstance(children, list):
                            m['children'] = [cid for cid in children if cid not in bad and cid not in to_remove]
                    # drop nodes
                    for rid in bad:
                        web_menus.pop(rid, None)
                # end plan-based pruning

        return web_menus
