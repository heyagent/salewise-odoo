/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { user } from "@web/core/user";

export function changePlanMenuItem(env) {
    return {
        type: "item",
        id: "salewise_change_plan",
        description: _t("Change Plan"),
        sequence: 58,
        // Only show to users who can write on res.company
        async show() {
            try {
                return await user.checkAccessRight("res.company", "write");
            } catch (e) {
                return false;
            }
        },
        callback: async function () {
            const company = env.services.company && env.services.company.currentCompany;
            const resId = company && company.id;
            if (resId) {
                await env.services.action.doAction({
                    type: "ir.actions.act_window",
                    name: _t("Company"),
                    res_model: "res.company",
                    res_id: resId,
                    views: [[false, "form"]],
                    target: "current",
                });
            } else {
                await env.services.action.doAction("base.action_res_company_form");
            }
        },
    };
}

registry.category("user_menuitems").add("salewise_change_plan", changePlanMenuItem);
