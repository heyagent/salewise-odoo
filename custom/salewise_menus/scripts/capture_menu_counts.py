#!/usr/bin/env python3
"""
Capture menu counts for each user under each plan.
This generates a baseline of exact menu counts for testing.
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

def get_user_menu_count(username, password):
    """Get count of SaaS menus visible to a user"""
    uid = authenticate(username, password)
    if not uid:
        return 0
    
    models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
    
    # Count all SaaS menus the user can see
    menu_count = models.execute_kw(
        db, uid, password,
        'ir.ui.menu', 'search_count',
        [[('is_saas', '=', True)]]
    )
    
    return menu_count

print("=" * 80)
print("CAPTURING MENU COUNT BASELINE")
print("=" * 80)

# Test configurations
plans = ['Starter', 'Professional', 'Enterprise']
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

count_baseline = {}

for plan in plans:
    print(f"\nPlan: {plan}")
    print("-" * 40)
    
    # Set the plan
    if not set_company_plan(plan):
        print(f"  ❌ Failed to set plan")
        continue
    
    count_baseline[plan] = {}
    
    for username, password in users:
        print(f"  Counting for {username}...", end=' ')
        
        menu_count = get_user_menu_count(username, password)
        count_baseline[plan][username] = menu_count
        print(f"✅ {menu_count} menus")

# Print summary table
print("\n" + "=" * 80)
print("MENU COUNT SUMMARY")
print("=" * 80)
print(f"{'User':<20} {'Starter':<12} {'Professional':<12} {'Enterprise':<12}")
print("-" * 56)

for username, _ in users:
    starter_count = count_baseline.get('Starter', {}).get(username, 0)
    professional_count = count_baseline.get('Professional', {}).get(username, 0)
    enterprise_count = count_baseline.get('Enterprise', {}).get(username, 0)
    
    print(f"{username:<20} {starter_count:<12} {professional_count:<12} {enterprise_count:<12}")

# Save count baseline to JSON file
output_file = f'/home/tishmen/salewise-odoo/custom/salewise_menus/tests/menu_count_baseline_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
with open(output_file, 'w') as f:
    json.dump(count_baseline, f, indent=2, sort_keys=True)

print("\n" + "=" * 80)
print(f"✅ Count baseline saved to: {output_file}")

# Generate Python dict for test file
print("\n" + "=" * 80)
print("GENERATING PYTHON DICT FOR COUNT TEST")
print("=" * 80)

# Output Python code
python_file = '/home/tishmen/salewise-odoo/custom/salewise_menus/tests/menu_count_baseline.py'
with open(python_file, 'w') as f:
    f.write('"""Auto-generated menu count baseline - DO NOT EDIT MANUALLY"""\n')
    f.write(f'# Generated: {datetime.now().isoformat()}\n\n')
    f.write('MENU_COUNT_BASELINE = ')
    f.write(repr(count_baseline))
    f.write('\n')

print(f"✅ Python count baseline saved to: {python_file}")
print("\nYou can now use MENU_COUNT_BASELINE in your tests!")
print("=" * 80)