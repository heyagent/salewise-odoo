/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { session } from "@web/session";
// Import user_menu_items to ensure menu items are registered before we try to remove them
import { user_menu_items } from "@web/webclient/user_menu/user_menu_items"; // eslint-disable-line no-unused-vars

export function saasMenuToggleItem(env) {
    return {
        type: "item",
        id: "saas_menu_toggle",
        description: _t("Switch App"),
        callback: async function () {
            const result = await env.services.orm.call(
                "res.users",
                "action_toggle_saas_menus"
            );
            env.services.action.doAction(result);
        },
        sequence: 60,
        hide: false,
        // Add checkmark if SaaS menus are enabled
        classNames: session.show_saas_menus ? "o-dropdown-item_selected" : "",
    };
}

registry
    .category("user_menuitems")
    .add("saas_menu_toggle", saasMenuToggleItem, { force: true });

// Only remove unwanted menu items when in Salewise mode
if (session.show_saas_menus) {
    registry.category("user_menuitems").remove("shortcuts");
    registry.category("user_menuitems").remove("install_pwa");
    registry.category("user_menuitems").remove("separator");
}