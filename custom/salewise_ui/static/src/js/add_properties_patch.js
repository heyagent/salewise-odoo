/** @odoo-module **/

import { FormController } from "@web/views/form/form_controller";
import { patch } from "@web/core/utils/patch";
import { session } from "@web/session";

// Patch FormController to hide Add Properties action in Salewise mode
patch(FormController.prototype, {
    getStaticActionMenuItems() {
        const items = super.getStaticActionMenuItems(...arguments);
        
        // If in Salewise mode, modify the addPropertyFieldValue item
        if (session.show_saas_menus && items.addPropertyFieldValue) {
            const originalIsAvailable = items.addPropertyFieldValue.isAvailable;
            items.addPropertyFieldValue.isAvailable = () => {
                const originalResult = originalIsAvailable ? originalIsAvailable() : true;
                // Hide if in Salewise mode
                return !session.show_saas_menus && originalResult;
            };
        }
        
        return items;
    }
});