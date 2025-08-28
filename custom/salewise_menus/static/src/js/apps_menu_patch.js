/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { NavBar } from "@web/webclient/navbar/navbar";
import { session } from "@web/session";
import { Component, xml } from "@odoo/owl";

// Override the Apps dropdown content when in Salewise mode
patch(NavBar.prototype, {
    setup() {
        super.setup(...arguments);
        this.showSaasMenus = session.show_saas_menus || false;
        
        // Get all Salewise menus from menuService
        if (this.showSaasMenus && this.menuService) {
            this.salewiseMenus = this._getSalewiseMenuTree();
        }
    },
    
    _getSalewiseMenuTree() {
        // Get all apps and filter for Salewise ones
        const apps = this.menuService.getApps();
        const salewiseApps = [];
        
        // Get the 5 Salewise root apps (IDs from your data)
        const salewiseAppIds = [522, 552, 573, 591, 626]; // Core, Marketing, Operations, HR, System
        
        for (const app of apps) {
            if (salewiseAppIds.includes(app.id)) {
                // Get full menu tree for this app
                const appTree = this.menuService.getMenuAsTree(app.id);
                salewiseApps.push(appTree);
            }
        }
        
        return salewiseApps;
    },
    
    onNavBarDropdownItemSelection(menu) {
        // Handle menu item selection
        this.menuService.selectMenu(menu);
    }
});