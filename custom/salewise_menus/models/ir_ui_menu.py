# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.http import request


class IrUiMenu(models.Model):
    _inherit = 'ir.ui.menu'
    
    is_saas = fields.Boolean('Is SaaS', default=False)
    lucide_icon = fields.Char('Lucide Icon')
    original_menu_id = fields.Many2one('ir.ui.menu', string='Original Menu')
    plan_id = fields.Many2one('salewise.plan', string='Required Plan', 
                              help='Plan required to see this menu. Empty means admin/no plan required.')
    
    @api.model
    def _get_available_plan_ids(self, company=None):
        """Get available plan IDs based on company's current plan.
        Returns plan IDs that should be visible (current plan and lower tiers).
        Centralized to avoid duplicate lookups."""
        if not company:
            company = request.env.company if request else self.env.company
        
        current_plan_id = company.plan_id.id if company.plan_id else False
        
        if not current_plan_id:
            return []  # No plan = admin mode, they see everything
        
        # Get current plan and all lower tier plans
        current_plan = self.env['salewise.plan'].browse(current_plan_id)
        if current_plan:
            available_plans = self.env['salewise.plan'].search([
                ('sequence', '<=', current_plan.sequence)
            ])
            return available_plans.ids
        
        return [current_plan_id]
    
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to ensure proper parent_path"""
        # Create the menus first
        menus = super().create(vals_list)
        
        # Force parent_path recomputation for ALL menus being created
        # This is needed because XML data loading doesn't trigger it properly
        if menus:
            # Get all menus including their ancestors
            all_menus = menus
            for menu in menus:
                if menu.parent_id:
                    all_menus |= menu.parent_id
            
            # Force recomputation of parent_path
            all_menus._parent_store_compute()
        
        return menus
    
    def write(self, vals):
        """Override write to maintain parent_path integrity"""
        res = super().write(vals)
        
        # If parent_id changed, parent_path is automatically updated by Odoo
        # We just need to ensure it's flushed to DB
        if 'parent_id' in vals:
            self.flush_model(['parent_path'])
        
        return res
    
    @api.model
    def load_menus(self, debug):
        """Override to filter menus based on is_saas flag when in SaaS mode"""
        import logging
        import time
        _logger = logging.getLogger(__name__)
        start_time = time.time()
        _logger.error(f"=== SALEWISE load_menus CALLED at {start_time} ===")
        
        # Check if we're in SaaS mode
        if request and request.env.user:
            user_settings = request.env.user.res_users_settings_id
            if user_settings and user_settings.show_saas_menus:
                # _logger.error("=== SAAS MODE - FILTERING MENUS ===")
                
                # Get company plan
                company = request.env.company
                current_plan_id = company.plan_id.id if company.plan_id else False
                
                # Call parent method to get base structure
                fields = ['name', 'sequence', 'parent_id', 'action', 'web_icon', 'is_saas', 'plan_id']
                menu_roots = self.get_user_roots()
                menu_roots_data = menu_roots.read(fields) if menu_roots else []
                menu_root = {
                    'id': False,
                    'name': 'root',
                    'parent_id': [-1, ''],
                    'children': [menu['id'] for menu in menu_roots_data],
                }
                
                all_menus = {'root': menu_root}
                
                if not menu_roots_data:
                    return all_menus
                
                # CRITICAL: Only load menus with is_saas=True
                menus_domain = [
                    ('id', 'child_of', menu_roots.ids),
                    ('is_saas', '=', True)  # ONLY SaaS menus!
                ]
                
                # Add plan filtering if not admin
                if current_plan_id:
                    plan_ids = self._get_available_plan_ids(company)
                    if plan_ids:
                        menus_domain.append(('plan_id', 'in', plan_ids))
                        # _logger.error(f"=== Filtering for plans: {plan_ids} ===")
                
                blacklisted_menu_ids = self._load_menus_blacklist()
                if blacklisted_menu_ids:
                    from odoo.osv import expression
                    menus_domain = expression.AND([menus_domain, [('id', 'not in', blacklisted_menu_ids)]])
                
                menus = self.search(menus_domain)
                _logger.error(f"=== Found {len(menus)} SaaS child menus ===")
                _logger.error(f"=== Domain was: {menus_domain} ===")
                
                # Check if Automation menu is in the result
                automation = menus.filtered(lambda m: m.id == 607)
                if automation:
                    _logger.error(f"=== Automation menu 607 IS in search result ===")
                else:
                    _logger.error(f"=== Automation menu 607 NOT in search result ===")
                    # Check System menu children
                    system_children = menus.filtered(lambda m: m.parent_id.id == 544)
                    _logger.error(f"=== System menu children found: {[(m.id, m.name) for m in system_children]} ===")
                
                menu_items = menus.read(fields)
                xmlids = (menu_roots + menus)._get_menuitems_xmlids()
                
                # add roots at the end
                menu_items.extend(menu_roots_data)
                
                # Load attachments for web icons
                mi_attachments = self.env['ir.attachment'].sudo().search_read(
                    domain=[('res_model', '=', 'ir.ui.menu'),
                            ('res_id', 'in', [menu_item['id'] for menu_item in menu_items if menu_item['id']]),
                            ('res_field', '=', 'web_icon_data')],
                    fields=['res_id', 'datas', 'mimetype'])
                
                mi_attachment_by_res_id = {attachment['res_id']: attachment for attachment in mi_attachments}
                
                # set children ids and xmlids
                menu_items_map = {menu_item["id"]: menu_item for menu_item in menu_items}
                for menu_item in menu_items:
                    menu_item.setdefault('children', [])
                    parent = menu_item['parent_id'] and menu_item['parent_id'][0]
                    menu_item['xmlid'] = xmlids.get(menu_item['id'], "")
                    if parent in menu_items_map:
                        menu_items_map[parent].setdefault(
                            'children', []).append(menu_item['id'])
                    attachment = mi_attachment_by_res_id.get(menu_item['id'])
                    if attachment:
                        menu_item['web_icon_data'] = attachment['datas'].decode()
                        menu_item['web_icon_data_mimetype'] = attachment['mimetype']
                    else:
                        menu_item['web_icon_data'] = False
                        menu_item['web_icon_data_mimetype'] = False
                all_menus.update(menu_items_map)
                
                # sort by sequence
                for menu_id in all_menus:
                    all_menus[menu_id]['children'].sort(key=lambda id: all_menus[id]['sequence'])
                
                # recursively set app ids to related children
                def _set_app_id(app_id, menu):
                    menu['app_id'] = app_id
                    for child_id in menu['children']:
                        _set_app_id(app_id, all_menus[child_id])
                
                for app in menu_roots_data:
                    app_id = app['id']
                    _set_app_id(app_id, all_menus[app_id])
                
                # filter out menus not related to an app (+ keep root menu)
                all_menus = {menu['id']: menu for menu in all_menus.values() if menu.get('app_id')}
                all_menus['root'] = menu_root
                
                end_time = time.time()
                _logger.error(f"=== Returning {len(all_menus)} total menus (SaaS mode) in {end_time - start_time:.3f}s ===")
                return all_menus
        
        # Not in SaaS mode - call parent
        end_time = time.time()
        _logger.error(f"=== NOT IN SAAS MODE - calling parent (took {end_time - start_time:.3f}s so far) ===")
        return super().load_menus(debug)
    
    @api.model
    def get_user_roots(self):
        """Override to return SaaS root menus when user has SaaS preference"""
        import logging
        import time
        _logger = logging.getLogger(__name__)
        start_time = time.time()
        _logger.error(f"=== GET_USER_ROOTS CALLED at {start_time} ===")
        
        if request and request.env.user:
            user_settings = request.env.user.res_users_settings_id
            _logger.error(f"User settings: {user_settings}")
            _logger.error(f"User settings ID: {user_settings.id if user_settings else 'NONE'}")
            
            if user_settings and user_settings.show_saas_menus:
                _logger.error("=== SAAS MODE ACTIVE ===")
                # Get current company's plan
                company = request.env.company
                current_plan_id = company.plan_id.id if company.plan_id else False
                _logger.error(f"Company: {company.name}, Plan ID: {current_plan_id}")
                
                # Return only SaaS root menus for the current plan WITH SUDO
                domain = [
                    ('parent_id', '=', False),
                    ('is_saas', '=', True),
                ]
                
                if current_plan_id:
                    # If company has a plan, show menus for that plan AND all lower tier plans
                    plan_ids = self._get_available_plan_ids(company)
                    if plan_ids:
                        _logger.error(f"Current plan ID: {current_plan_id}")
                        _logger.error(f"Available plan IDs: {plan_ids}")
                        # ONLY show menus that match available plans - NO menus with null plan_id!
                        domain.append(('plan_id', 'in', plan_ids))
                    else:
                        domain.append(('plan_id', '=', current_plan_id))
                    _logger.error(f"Looking for menus with plan_id in {plan_ids if plan_ids else [current_plan_id]}")
                else:
                    # If no plan (admin mode), show ALL SaaS menus
                    # Don't add any plan_id filter - admin sees everything
                    _logger.error("Admin mode - showing ALL SaaS menus")
                
                _logger.error(f"Domain: {domain}")
                saas_roots = self.sudo().search(domain)
                _logger.error(f"Found {len(saas_roots)} SaaS root menus in {time.time() - start_time:.3f}s: {saas_roots.mapped('name')}")
                return saas_roots
            else:
                _logger.error("=== NORMAL MODE (NOT SAAS) ===")
                # Return normal root menus excluding SaaS ones
                normal_roots = self.search([
                    ('parent_id', '=', False),
                    ('is_saas', '=', False)
                ])
                _logger.error(f"Found {len(normal_roots)} normal root menus")
                return normal_roots
        
        # Default behavior when no user context
        _logger.error("=== NO USER CONTEXT - CALLING SUPER ===")
        return super().get_user_roots()
    
    @api.model
    def search_fetch(self, domain, field_names, offset=0, limit=None, order=None):
        """Override to apply plan-based filtering for SaaS menus"""
        # First get the records using parent method
        menus = super().search_fetch(domain, field_names, offset=offset, limit=limit, order=order)
        
        # Check if we're searching for SaaS menus
        if any(term for term in domain if len(term) == 3 and term[0] == 'is_saas' and term[2] == True):
            # Apply plan-based filtering
            company = self.env.company
            if company.plan_id:
                # Get available plan IDs (current plan and lower tiers)
                available_plan_ids = self._get_available_plan_ids(company)
                
                # Filter menus to only those matching available plans or no plan
                menus = menus.filtered(lambda m: not m.plan_id or m.plan_id.id in available_plan_ids)
        
        return menus
    
    @api.model
    def search_count(self, domain, limit=None):
        """Override to apply plan-based filtering for count consistency"""
        # Check if we're counting SaaS menus
        if any(term for term in domain if len(term) == 3 and term[0] == 'is_saas' and term[2] == True):
            # Use search_fetch to get filtered menus and count them
            menus = self.search_fetch(domain, ['id'], limit=limit)
            return len(menus)
        
        # For non-SaaS menus, use parent method
        return super().search_count(domain, limit=limit)
    
    def load_web_menus(self, debug):
        """Override to add is_saas field and filter by plan"""
        import logging
        import traceback
        import time
        _logger = logging.getLogger(__name__)
        start_time = time.time()
        _logger.error(f"=== SALEWISE_MENUS LOAD_WEB_MENUS CALLED at {start_time} ===")
        _logger.error(f"=== DEBUG: {debug} ===")
        _logger.error(f"=== STACK TRACE: {traceback.format_stack()[-3]} ===")
        
        # Call parent method
        parent_start = time.time()
        _logger.error("=== CALLING SUPER().LOAD_WEB_MENUS ===")
        web_menus = super().load_web_menus(debug)
        _logger.error(f"=== GOT {len(web_menus)} MENUS FROM PARENT in {time.time() - parent_start:.3f}s ===")
        
        # Log root menu details
        if 'root' in web_menus:
            _logger.error(f"Root menu: {web_menus['root']}")
            _logger.error(f"Root children: {web_menus['root'].get('children', [])}")
        
        # ADD MISSING PROFESSIONAL/ENTERPRISE MENUS
        if request and request.env.user:
            user_settings = request.env.user.res_users_settings_id
            if user_settings and user_settings.show_saas_menus:
                company = request.env.company
                current_plan_id = company.plan_id.id if company.plan_id else False
                
                if current_plan_id:
                    # Get all plans up to current tier using helper method
                    available_plan_ids = self._get_available_plan_ids(company)
                    
                    # Find menus that should be visible but aren't loaded
                    all_plan_menus = self.sudo().search([
                        ('is_saas', '=', True),
                        ('plan_id', 'in', available_plan_ids)
                    ])
                    
                    search_start = time.time()
                    _logger.error(f"Found {len(all_plan_menus)} total menus for plans {available_plan_ids} in {time.time() - search_start:.3f}s")
                    
                    # Add missing menus
                    for menu in all_plan_menus:
                        if menu.id not in web_menus:
                            _logger.error(f"Adding missing menu: {menu.name} (id: {menu.id}, parent: {menu.parent_id.id if menu.parent_id else None})")
                            
                            # Build menu dict like the base method does
                            menu_dict = {
                                'id': menu.id,
                                'name': menu.name,
                                'appID': menu.parent_id.id if menu.parent_id else False,
                                'actionID': menu.action.id if menu.action else False,
                                'xmlid': menu.get_external_id()[menu.id] or '',
                                'sequence': menu.sequence,
                                'children': [],
                                'is_saas': menu.is_saas,
                                'plan_id': menu.plan_id.id if menu.plan_id else False
                            }
                            
                            # Add webIcon for root menus
                            if not menu.parent_id and menu.web_icon:
                                menu_dict['webIcon'] = menu.web_icon
                                menu_dict['webIconData'] = menu.web_icon_data
                            
                            web_menus[menu.id] = menu_dict
                            
                            # Add to parent's children list
                            if menu.parent_id and menu.parent_id.id in web_menus:
                                parent = web_menus[menu.parent_id.id]
                                if 'children' not in parent:
                                    parent['children'] = []
                                if menu.id not in parent['children']:
                                    parent['children'].append(menu.id)
                                    parent['children'].sort()  # Keep them sorted by sequence
                                    _logger.error(f"  -> Added to parent {menu.parent_id.name}'s children")
        
        # NO FILTERING NEEDED - we already added only the right menus above
        
        # Get the actual menu records from database to add is_saas field
        menu_ids = [menu_id for menu_id in web_menus.keys() if menu_id != 'root']
        
        if menu_ids:
            menus = self.browse(menu_ids).read(['id', 'is_saas', 'plan_id'])
            menu_dict = {menu['id']: {'is_saas': menu['is_saas'], 'plan_id': menu['plan_id']} for menu in menus}
            
            for menu_id, menu_data in web_menus.items():
                if menu_id != 'root' and menu_id in menu_dict:
                    menu_data['is_saas'] = menu_dict[menu_id]['is_saas']
                    menu_data['plan_id'] = menu_dict[menu_id]['plan_id']
        
        _logger.error(f"=== TOTAL load_web_menus took {time.time() - start_time:.3f}s ===")
        return web_menus