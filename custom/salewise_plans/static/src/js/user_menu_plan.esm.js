/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";

export function changePlanMenuItem(env) {
    return {
        type: "item",
        id: "salewise_change_plan",
        description: _t("Change Plan"),
        sequence: 58,
        // Only show to users who can write on res.company
        async show() {
            return await env.services.user.checkAccessRight("res.company", "write");
        },
        callback: async function () {
            await env.services.action.doAction("salewise_plans.action_salewise_plan_switch");
        },
    };
}

registry.category("user_menuitems").add("salewise_change_plan", changePlanMenuItem);

