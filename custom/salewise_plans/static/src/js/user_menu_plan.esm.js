/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { session } from "@web/session";

console.debug('[SALEWISE_SWITCH_PLAN] user_menu_plan.esm.js loaded', {
    is_switch_plan_user: session.is_switch_plan_user,
    impersonate_from_uid: session.impersonate_from_uid,
});

export function changePlanMenuItem(env) {
    const hidden = session.impersonate_from_uid || !session.is_switch_plan_user;
    console.debug('[SALEWISE_SWITCH_PLAN] building menu item', {
        is_switch_plan_user: session.is_switch_plan_user,
        impersonate_from_uid: session.impersonate_from_uid,
        hidden,
    });
    return {
        type: "item",
        id: "salewise_change_plan",
        description: _t("Switch Plan"),
        sequence: 58,
        // Visibility mirrors OCA switch_login: hidden when impersonating or not allowed
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
    const cat = registry.category("user_menuitems");
    console.debug('[SALEWISE_SWITCH_PLAN] before add, user_menuitems keys:', cat.getEntries().map(([k]) => k));
    cat.add("salewise_change_plan", changePlanMenuItem, { force: true });
    console.debug('[SALEWISE_SWITCH_PLAN] after add, user_menuitems keys:', cat.getEntries().map(([k]) => k));
} catch (e) {
    console.error('[SALEWISE_SWITCH_PLAN] registry add failed', e);
}
