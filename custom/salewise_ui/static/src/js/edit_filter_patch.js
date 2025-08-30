/** @odoo-module **/

import { SearchBar } from "@web/search/search_bar/search_bar";
import { patch } from "@web/core/utils/patch";
import { session } from "@web/session";

// Patch SearchBar to disable filter editing in Salewise mode
patch(SearchBar.prototype, {
    // Add getter to check if filter editing should be hidden
    get hideFilterEdit() {
        return session.show_saas_menus || false;
    },
    
    onFacetLabelClick(target, facet) {
        // If in Salewise mode and facet has domain (editable filter), prevent editing
        if (session.show_saas_menus && facet.domain) {
            return; // Don't open the dialog
        }
        
        // Otherwise, call parent implementation
        return super.onFacetLabelClick(...arguments);
    }
});