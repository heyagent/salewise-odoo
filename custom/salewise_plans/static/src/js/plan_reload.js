/** @odoo-module **/

import { registry } from "@web/core/registry";

// Simple client action that reloads the page
function reloadPage(env, action) {
    window.location.reload();
}

registry.category("actions").add("salewise_reload_page", reloadPage);