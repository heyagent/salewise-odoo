/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { session } from "@web/session";

export function saasMenuToggleItem(env) {
    return {
        type: "item",
        id: "saas_menu_toggle",
        description: _t("Toggle Salewise"),
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