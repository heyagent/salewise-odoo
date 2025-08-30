/** @odoo-module **/

import { SearchBar } from "@web/search/search_bar/search_bar";
import { patch } from "@web/core/utils/patch";
import { session } from "@web/session";

// Patch SearchBar to hide Add Custom Filter in search autocomplete
patch(SearchBar.prototype, {
    async computeState(options = {}) {
        // Call the parent computeState
        await super.computeState(...arguments);
        
        // If in Salewise mode, filter out the Add Custom Filter button
        if (session.show_saas_menus && this.items) {
            this.items = this.items.filter(item => !item.isAddCustomFilterButton);
        }
    }
});