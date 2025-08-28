/** @odoo-module **/

import { NavBar } from "@web/webclient/navbar/navbar";
import { patch } from "@web/core/utils/patch";
import { session } from "@web/session";

patch(NavBar.prototype, {
    setup() {
        super.setup(...arguments);
        this.showSaasMenus = session.show_saas_menus || false;
        
        // Override currentAppSectionsExtra directly since it's not a getter
        const originalSectionsExtra = this.currentAppSectionsExtra;
        if (this.showSaasMenus) {
            this.currentAppSectionsExtra = [];
        }
    }
});

// Override currentAppSections getter after patch
const proto = NavBar.prototype;
const sectionsDescriptor = Object.getOwnPropertyDescriptor(proto, 'currentAppSections');

// Only override if it's actually a getter (which it is)
if (sectionsDescriptor && sectionsDescriptor.get) {
    const originalSectionsGetter = sectionsDescriptor.get;
    
    Object.defineProperty(NavBar.prototype, 'currentAppSections', {
        get() {
            // Hide navbar menu sections when in Salewise mode
            if (this.showSaasMenus) {
                return [];
            }
            // Otherwise call original getter
            return originalSectionsGetter.call(this);
        },
        configurable: true
    });
}