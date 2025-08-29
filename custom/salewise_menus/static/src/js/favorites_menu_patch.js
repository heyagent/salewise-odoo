/** @odoo-module **/

import { SearchBarMenu } from "@web/search/search_bar_menu/search_bar_menu";
import { patch } from "@web/core/utils/patch";
import { session } from "@web/session";

// Patch SearchBarMenu to hide Favorites menu in Salewise mode
patch(SearchBarMenu.prototype, {
    setup() {
        // Call the original setup first
        super.setup(...arguments);
        
        // Check if we're in Salewise mode
        if (session.show_saas_menus) {
            // Remove 'favorite' from searchMenuTypes
            if (this.env.searchModel && this.env.searchModel.searchMenuTypes) {
                const originalMenuTypes = this.env.searchModel.searchMenuTypes;
                
                if (originalMenuTypes.has('favorite')) {
                    // Delete favorite from the set
                    originalMenuTypes.delete('favorite');
                }
            }
        }
    }
});