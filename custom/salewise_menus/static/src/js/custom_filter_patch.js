/** @odoo-module **/

import { SearchBarMenu } from "@web/search/search_bar_menu/search_bar_menu";
import { patch } from "@web/core/utils/patch";
import { session } from "@web/session";

// Patch SearchBarMenu to hide Add Custom Filter in Salewise mode
patch(SearchBarMenu.prototype, {
    // Add a getter to check if we should hide Add Custom Filter
    get hideAddCustomFilter() {
        // If in Salewise mode, always hide Add Custom Filter
        if (session.show_saas_menus) {
            return true;
        }
        
        // Otherwise show it
        return false;
    }
});