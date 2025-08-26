# -*- coding: utf-8 -*-


def post_init_hook(env):
    """
    Post-init hook to create SaaS menu and user programmatically
    """

    # Create SaaS Administrator group for full menu access
    saas_admin_group = env["res.groups"].search([("name", "=", "SaaS Administrator")], limit=1)
    if not saas_admin_group:
        saas_admin_group = env["res.groups"].create(
            {
                "name": "SaaS Administrator",
                # Use Extra Rights category instead of user types
                "category_id": env.ref("base.module_category_usability").id,
            }
        )
    # Create Salewise main menu
    salewise_menu = env["ir.ui.menu"].search([("name", "=", "Salewise")], limit=1)
    if not salewise_menu:
        salewise_menu = env["ir.ui.menu"].create(
            {
                "name": "Salewise",
                "is_saas_menu": True,
                "sequence": 1,
                "web_icon": "salewise_menu_system,static/description/icon.png",
            }
        )
    else:
        salewise_menu.write({
            "is_saas_menu": True,
            "web_icon": "salewise_menu_system,static/description/icon.png",
        })

    # Create submenu items for Salewise with dummy actions
    submenus = [
        {"name": "Dashboard", "sequence": 10, "restricted": False},
        {"name": "Customers", "sequence": 20, "restricted": False},
        {"name": "Analytics", "sequence": 30, "restricted": True},  # Only for admin
        {"name": "Settings", "sequence": 40, "restricted": True},   # Only for admin
    ]

    for submenu_data in submenus:
        existing = env["ir.ui.menu"].search(
            [("name", "=", submenu_data["name"]), ("parent_id", "=", salewise_menu.id)],
            limit=1,
        )

        # Create a dummy window action for each menu
        action_name = f"action_salewise_{submenu_data['name'].lower()}"
        action = env["ir.actions.act_window"].search([("name", "=", action_name)], limit=1)
        if not action:
            # Use appropriate model for each menu
            if "customer" in action_name:
                res_model = "res.partner"
            else:
                res_model = "res.users"
            
            action = env["ir.actions.act_window"].create({
                "name": action_name,
                "res_model": res_model,
                "view_mode": "list,form",  # Odoo 18 uses 'list' not 'tree'
                "target": "current",
            })

        menu_vals = {
            "name": submenu_data["name"],
            "parent_id": salewise_menu.id,
            "is_saas_menu": True,
            "sequence": submenu_data["sequence"],
            "action": f"ir.actions.act_window,{action.id}",
        }
        
        # Add group restriction for admin-only menus
        if submenu_data.get("restricted"):
            menu_vals["groups_id"] = [(6, 0, [saas_admin_group.id])]

        if not existing:
            env["ir.ui.menu"].create(menu_vals)
        else:
            existing.write(menu_vals)

    # Create SaaS admin user with full access
    saas_admin = env["res.users"].search([("login", "=", "saas_admin")], limit=1)
    if not saas_admin:
        saas_admin = env["res.users"].create(
            {
                "name": "SaaS Administrator",
                "login": "saas_admin",
                "password": "saas_admin",
                "is_saas_user": True,
                "groups_id": [(6, 0, [env.ref("base.group_user").id, saas_admin_group.id])],
            }
        )
    else:
        saas_admin.write({
            "is_saas_user": True,
            "groups_id": [(4, saas_admin_group.id)]  # Add the group if missing
        })

    # Create SaaS restricted user with limited access
    saas_restricted = env["res.users"].search([("login", "=", "saas_restricted")], limit=1)
    if not saas_restricted:
        saas_restricted = env["res.users"].create(
            {
                "name": "SaaS Restricted User",
                "login": "saas_restricted",
                "password": "saas_restricted",
                "is_saas_user": True,
                "groups_id": [(6, 0, [env.ref("base.group_user").id])],
            }
        )
    else:
        saas_restricted.write({"is_saas_user": True})

    # Ensure admin user is marked as standard user
    admin_user = env["res.users"].search([("login", "=", "admin")], limit=1)
    if admin_user:
        admin_user.write({"is_saas_user": False})