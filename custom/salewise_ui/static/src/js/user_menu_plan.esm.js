/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { session } from "@web/session";

// Add a "Switch Plan" entry to the user dropdown.
// Visibility: only for users in salewise_plans.group_switch_plan and not impersonating.
// Action: opens current company form to allow changing plan.

export function changePlanMenuItem(env) {
    const hidden = session.impersonate_from_uid || !session.is_switch_plan_user;
    return {
        type: "item",
        id: "salewise_change_plan",
        description: _t("Switch Plan"),
        sequence: 58,
        hide: hidden,
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

try {
    registry.category("user_menuitems").add("salewise_change_plan", changePlanMenuItem, { force: true });
} catch (_) {
    // ignore if registry not available yet
}

