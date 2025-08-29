/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { tourService } from "@web_tour/tour_service/tour_service";
import { registry } from "@web/core/registry";

// Patch the tourService to prevent it from adding the Onboarding menu item
patch(tourService, {
    async start(_env, deps) {
        // Call the original start function
        const result = await super.start(_env, deps);
        
        // After the original function runs, remove the menu item it just added
        const userMenuRegistry = registry.category("user_menuitems");
        
        if (userMenuRegistry.contains("web_tour.tour_enabled")) {
            userMenuRegistry.remove("web_tour.tour_enabled");
        }
        
        return result;
    }
});