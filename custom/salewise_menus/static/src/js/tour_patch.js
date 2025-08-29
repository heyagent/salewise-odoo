/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { tourService } from "@web_tour/tour_service/tour_service";
import { registry } from "@web/core/registry";
import { session } from "@web/session";

// Patch the tourService to conditionally remove the Onboarding menu item in Salewise mode
patch(tourService, {
    async start(_env, deps) {
        // Call the original start function
        const result = await super.start(_env, deps);
        
        // Only remove the Onboarding menu item when in Salewise mode
        if (session.show_saas_menus) {
            const userMenuRegistry = registry.category("user_menuitems");
            
            if (userMenuRegistry.contains("web_tour.tour_enabled")) {
                userMenuRegistry.remove("web_tour.tour_enabled");
            }
        }
        
        return result;
    }
});