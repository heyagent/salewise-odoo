/** @odoo-module **/

import { NavBar } from "@web/webclient/navbar/navbar";
import { patch } from "@web/core/utils/patch";

patch(NavBar.prototype, {
    /**
     * Override to return empty array so no sections appear in navbar
     */
    get currentAppSections() {
        // Return empty array to hide sections from navbar
        // All menus are now in the dropdown
        return [];
    },

    /**
     * Get inline style for menu item based on level
     * @param {Number} level - The menu level (0 for apps, 1+ for submenus)
     * @returns {String} - Inline style string
     */
    getMenuItemStyle(level) {
        const safeLevel = parseInt(level, 10) || 0;
        
        if (safeLevel === 0) {
            // Top level apps
            return 'font-weight: bold; background-color: #f8f9fa; border-bottom: 1px solid #dee2e6; padding-left: 0.5rem';
        } else {
            // Submenu items
            const paddingLeft = 0.5 + (safeLevel * 1.5);
            const fontWeight = safeLevel === 1 ? 'font-weight: 500; ' : '';
            return `${fontWeight}padding-left: ${paddingLeft}rem`;
        }
    },

    /**
     * Get prefix symbol for menu item based on level
     * @param {Number} level - The menu level
     * @returns {String} - Prefix symbol
     */
    getMenuPrefix(level) {
        switch (level) {
            case 1:
                return '▸';
            case 2:
                return '◦';
            case 3:
                return '—';
            default:
                return '·';
        }
    },

    /**
     * Handle selection of a flattened menu item
     * @param {Object} menuItem - The menu item selected
     * @param {Object} parentApp - The parent app of this menu item
     */
    async selectFlattenedMenu(menuItem, parentApp) {
        // First set the current app context
        if (parentApp) {
            this.menuService.setCurrentMenu(parentApp);
        }
        
        // Then navigate to the selected menu
        if (menuItem.actionID) {
            await this.env.services.action.doAction(menuItem.actionID, {
                clearBreadcrumbs: true,
                onActionReady: () => {
                    // Update current menu to the actual selected item
                    this.menuService.setCurrentMenu(menuItem);
                },
            });
        } else if (menuItem.childrenTree && menuItem.childrenTree.length) {
            // If it has children but no action, select the first child with an action
            const firstActionChild = this.findFirstActionChild(menuItem);
            if (firstActionChild) {
                await this.selectFlattenedMenu(firstActionChild, parentApp);
            }
        }
    },

    /**
     * Find the first child menu with an action
     * @param {Object} menu - The menu to search in
     * @returns {Object|null} - First child with action or null
     */
    findFirstActionChild(menu) {
        if (menu.actionID) {
            return menu;
        }
        
        if (menu.childrenTree && menu.childrenTree.length) {
            for (const child of menu.childrenTree) {
                const result = this.findFirstActionChild(child);
                if (result) {
                    return result;
                }
            }
        }
        
        return null;
    },

    /**
     * Override the original dropdown item selection to handle our flattened structure
     */
    onNavBarDropdownItemSelection(menu) {
        // If it's a top-level app, use the original behavior
        if (this.menuService.getApps().includes(menu)) {
            return super.onNavBarDropdownItemSelection(menu);
        }
        
        // For sub-menus, find the parent app and use our custom handler
        const parentApp = this.findParentApp(menu);
        if (parentApp) {
            return this.selectFlattenedMenu(menu, parentApp);
        }
        
        // Fallback to original behavior
        return super.onNavBarDropdownItemSelection(menu);
    },

    /**
     * Find the parent app for a given menu
     * @param {Object} menu - The menu to find parent for
     * @returns {Object|null} - Parent app or null
     */
    findParentApp(menu) {
        const apps = this.menuService.getApps();
        
        for (const app of apps) {
            if (this.isMenuDescendantOf(menu, app)) {
                return app;
            }
        }
        
        return null;
    },

    /**
     * Check if a menu is a descendant of another menu
     * @param {Object} menu - The potential descendant
     * @param {Object} ancestor - The potential ancestor
     * @returns {Boolean} - True if menu is descendant of ancestor
     */
    isMenuDescendantOf(menu, ancestor) {
        const tree = this.menuService.getMenuAsTree(ancestor.id);
        
        if (tree.id === menu.id) {
            return true;
        }
        
        if (tree.childrenTree) {
            for (const child of tree.childrenTree) {
                if (this.isMenuDescendantOf(menu, child)) {
                    return true;
                }
            }
        }
        
        return false;
    },
});