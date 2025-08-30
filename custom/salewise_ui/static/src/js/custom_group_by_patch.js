/** @odoo-module **/

import { SearchBarMenu } from "@web/search/search_bar_menu/search_bar_menu";
import { patch } from "@web/core/utils/patch";
import { session } from "@web/session";

// Patch SearchBarMenu to hide Custom Group By in Salewise mode
patch(SearchBarMenu.prototype, {
    // Override the hideCustomGroupBy getter
    get hideCustomGroupBy() {
        // If in Salewise mode, always hide custom group by
        if (session.show_saas_menus) {
            return true;
        }
        
        // Otherwise use the original logic
        return this.env.searchModel.hideCustomGroupBy || false;
    }
});