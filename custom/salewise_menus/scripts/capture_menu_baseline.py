#!/usr/bin/env python3
"""
Capture the current menu state as baseline for tests.
This will generate the exact menu XML IDs visible to each user under each plan.
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

def get_user_menu_xmlids(username, password):
    """Get all SaaS menu XML IDs visible to a user"""
    uid = authenticate(username, password)
    if not uid:
        return []
    
    models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
    
    # Get all SaaS menus the user can see
    menus = models.execute_kw(
        db, uid, password,
        'ir.ui.menu', 'search_read',
        [[('is_saas', '=', True)]],
        {'fields': ['id', 'name']}
    )
    
    if not menus:
        return []
    
    menu_ids = [m['id'] for m in menus]
    
    # Get XML IDs for these menus - use admin for ir.model.data access
    admin_uid = authenticate('admin', 'admin')
    xml_ids = models.execute_kw(
        db, admin_uid, 'admin',
        'ir.model.data', 'search_read',
        [[
            ('model', '=', 'ir.ui.menu'),
            ('res_id', 'in', menu_ids)
        ]],
        {'fields': ['res_id', 'module', 'name']}
    )
    
    # Build XML ID map
    xmlid_map = {}
    for data in xml_ids:
        xmlid = f"{data['module']}.{data['name']}"
        xmlid_map[data['res_id']] = xmlid
    
    # Return list of XML IDs with menu names
    result = []
    for menu in menus:
        xmlid = xmlid_map.get(menu['id'], f"__id_{menu['id']}")  # Fallback to ID if no XML ID
        result.append({
            'xmlid': xmlid,
            'name': menu['name'],
            'id': menu['id']
        })
    
    return result

print("=" * 80)
print("CAPTURING MENU BASELINE")
print("=" * 80)

# Test configurations
plans = ['Starter', 'Professional', 'Enterprise', None]  # None = no plan
users = [
    ('admin', 'admin'),
    ('sales_user', 'sales_user'),
    ('sales_manager', 'sales_manager'),
    ('hr_officer', 'hr_officer'),
    ('hr_manager', 'hr_manager'),
    ('marketing_user', 'marketing_user'),
    ('accountant', 'accountant'),
    ('project_manager', 'project_manager'),
    ('project_user', 'project_user'),
]

baseline = {}

for plan in plans:
    plan_key = plan if plan else 'no_plan'
    print(f"\nPlan: {plan_key}")
    print("-" * 40)
    
    # Set the plan
    if not set_company_plan(plan):
        print(f"  ❌ Failed to set plan")
        continue
    
    baseline[plan_key] = {}
    
    for username, password in users:
        print(f"  Capturing {username}...", end=' ')
        
        menu_data = get_user_menu_xmlids(username, password)
        
        if menu_data:
            # Store just the XML IDs for easy comparison
            xmlids = [m['xmlid'] for m in menu_data]
            baseline[plan_key][username] = sorted(xmlids)  # Sort for consistent comparison
            print(f"✅ {len(xmlids)} menus")
            
            # Also store detailed version for reference
            baseline[f"{plan_key}_detailed"] = baseline.get(f"{plan_key}_detailed", {})
            baseline[f"{plan_key}_detailed"][username] = menu_data
        else:
            print(f"❌ Failed")
            baseline[plan_key][username] = []

# Save baseline to file
output_file = f'/home/tishmen/salewise-odoo/custom/salewise_menus/tests/menu_baseline_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
with open(output_file, 'w') as f:
    json.dump(baseline, f, indent=2, sort_keys=True)

print("\n" + "=" * 80)
print(f"✅ Baseline saved to: {output_file}")

# Generate Python dict for test file
print("\n" + "=" * 80)
print("GENERATING PYTHON DICT FOR TEST")
print("=" * 80)

# Create a simpler structure for the test
test_baseline = {}
for plan in ['Starter', 'Professional', 'Enterprise']:
    test_baseline[plan] = {}
    for username, _ in users:
        if username in baseline[plan]:
            test_baseline[plan][username] = baseline[plan][username]

# Output Python code
python_file = '/home/tishmen/salewise-odoo/custom/salewise_menus/tests/menu_baseline.py'
with open(python_file, 'w') as f:
    f.write('"""Auto-generated menu baseline - DO NOT EDIT MANUALLY"""\n')
    f.write(f'# Generated: {datetime.now().isoformat()}\n\n')
    f.write('MENU_BASELINE = ')
    f.write(repr(test_baseline))

print(f"✅ Python baseline saved to: {python_file}")
print("\nYou can now use MENU_BASELINE in your tests!")
print("=" * 80)