# -*- coding: utf-8 -*-


def post_init_hook(env):
    """
    Post-init hook to create SaaS users and groups
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