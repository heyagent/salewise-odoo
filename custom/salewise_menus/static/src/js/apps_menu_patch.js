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
        
        for (const app of apps) {
            if (app.is_saas) {
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
