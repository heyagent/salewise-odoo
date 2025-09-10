#!/usr/bin/env python3
"""
Unified script to capture both menu baselines in a single pass.
This generates menu_baseline.py (XML IDs) and menu_count_baseline.py (counts) simultaneously.
"""
import xmlrpc.client
import json
from datetime import datetime

url = 'http://localhost:8069'
db = 'salewise'

def authenticate(username, password):
    """Authenticate and return uid"""
    common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
    uid = common.authenticate(db, username, password, {})
    return uid

def set_company_plan(plan_name):
    """Set company plan as admin"""
    uid = authenticate('admin', 'admin')
    if not uid:
        return False
    
    models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
    
    if plan_name:
        # Find plan
        plan_ids = models.execute_kw(
            db, uid, 'admin',
            'salewise.plan', 'search',
            [[['name', '=', plan_name]]]
        )
        
        if not plan_ids:
            return False
        
        plan_id = plan_ids[0]
    else:
        plan_id = False  # No plan
    
    # Update company
    models.execute_kw(
        db, uid, 'admin',
        'res.company', 'write',
        [[1], {'plan_id': plan_id}]
    )
    return True

def get_user_menu_data(username, password):
    """Get both menu XML IDs and count for a user"""
    uid = authenticate(username, password)
    if not uid:
        print(f"Failed to authenticate as {username}")
        return [], 0
    
    models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
    
    # Ensure user has SaaS mode enabled
    user_settings = models.execute_kw(
        db, uid, password,
        'res.users', 'read',
        [[uid], ['res_users_settings_id']]
    )[0]
    
    if user_settings.get('res_users_settings_id'):
        settings_id = user_settings['res_users_settings_id'][0]
        models.execute_kw(
            db, uid, password,
            'res.users.settings', 'write',
            [[settings_id], {'show_saas_menus': True}]
        )
    
    # Get SaaS menus
    menu_ids = models.execute_kw(
        db, uid, password,
        'ir.ui.menu', 'search',
        [[['is_saas', '=', True]]]
    )
    
    if not menu_ids:
        return [], 0
    
    # Get XML IDs for menus using admin access
    admin_uid = authenticate('admin', 'admin')
    admin_models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
    
    xmlids = []
    for menu_id in menu_ids:
        # Find XML ID using admin access
        model_data = admin_models.execute_kw(
            db, admin_uid, 'admin',
            'ir.model.data', 'search_read',
            [[['model', '=', 'ir.ui.menu'], ['res_id', '=', menu_id]]],
            {'fields': ['module', 'name']}
        )
        
        if model_data:
            xmlid = f"{model_data[0]['module']}.{model_data[0]['name']}"
            xmlids.append(xmlid)
        else:
            # Fallback if no XML ID
            xmlids.append(f"salewise_menus.{menu_id}")
    
    return sorted(xmlids), len(menu_ids)

def capture_baselines():
    """Capture both baselines for all plans and users"""
    plans = ['Starter', 'Professional', 'Enterprise']
    
    # Updated user list to include ALL users from salewise_users
    users = [
        ('admin', 'admin'),
        ('super_admin', 'super_admin'),
        ('sys_admin', 'sys_admin'),
        ('sales_user', 'sales_user'),
        ('sales_manager', 'sales_manager'),
        ('hr_officer', 'hr_officer'),
        ('hr_manager', 'hr_manager'),
        ('marketing_user', 'marketing_user'),
        ('accountant', 'accountant'),
        ('project_manager', 'project_manager'),
        ('project_user', 'project_user'),
        ('employee', 'employee'),
        ('team_lead', 'team_lead'),
    ]
    
    # Initialize results
    menu_baseline = {}
    menu_count_baseline = {}
    
    print(f"Starting baseline capture at {datetime.now()}")
    print("=" * 60)
    
    for plan in plans:
        print(f"\nProcessing {plan} plan...")
        
        # Set plan
        if not set_company_plan(plan):
            print(f"Failed to set plan: {plan}")
            continue
        
        menu_baseline[plan] = {}
        menu_count_baseline[plan] = {}
        
        for username, password in users:
            # Get both XML IDs and count in one pass
            xmlids, count = get_user_menu_data(username, password)
            
            # Store results
            menu_baseline[plan][username] = xmlids
            menu_count_baseline[plan][username] = count
            
            print(f"  {username}: {count} menus")
    
    # Write menu_baseline.py
    with open('../tests/menu_baseline.py', 'w') as f:
        f.write('# -*- coding: utf-8 -*-\n')
        f.write('"""Menu baseline for SaleWise plans - auto-generated"""\n\n')
        f.write('MENU_BASELINE = ')
        # Pretty format with proper indentation
        import pprint
        pp = pprint.PrettyPrinter(indent=4, width=120, compact=False)
        f.write(pp.pformat(menu_baseline))
        f.write('\n')
    
    print(f"\n✅ Generated menu_baseline.py")
    
    # Write menu_count_baseline.py
    with open('../tests/menu_count_baseline.py', 'w') as f:
        f.write('# -*- coding: utf-8 -*-\n')
        f.write('"""Menu count baseline for SaleWise plans - auto-generated"""\n\n')
        f.write('MENU_COUNT_BASELINE = ')
        import pprint
        pp = pprint.PrettyPrinter(indent=4, width=120, compact=False)
        f.write(pp.pformat(menu_count_baseline))
        f.write('\n')
    
    print(f"✅ Generated menu_count_baseline.py")
    
    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"{'User':<20} {'Starter':>10} {'Professional':>15} {'Enterprise':>12}")
    print("-" * 60)
    
    for username, _ in users:
        starter = menu_count_baseline.get('Starter', {}).get(username, 0)
        prof = menu_count_baseline.get('Professional', {}).get(username, 0)
        ent = menu_count_baseline.get('Enterprise', {}).get(username, 0)
        print(f"{username:<20} {starter:>10} {prof:>15} {ent:>12}")
    
    print(f"\n✅ Capture completed at {datetime.now()}")

if __name__ == '__main__':
    capture_baselines()