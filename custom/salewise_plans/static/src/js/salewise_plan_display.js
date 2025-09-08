/** @odoo-module **/

import { Component, useState, onWillStart, useEffect } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class SalewisePlanDisplay extends Component {
    static template = "salewise_plans.PlanDisplay";
    static props = {};

    setup() {
        this.companyService = useService("company");
        this.orm = useService("orm");
        this.state = useState({
            planName: "",
            loading: true,
        });
        
        onWillStart(async () => {
            await this.loadPlanName();
        });
        
        // Listen for company changes
        useEffect(
            async () => {
                await this.loadPlanName();
            },
            () => [this.companyService.currentCompany.id]
        );
    }

    async loadPlanName() {
        try {
            this.state.loading = true;
            const companyId = this.companyService.currentCompany.id;
            
            // Fetch the company with its plan
            const companies = await this.orm.read(
                "res.company",
                [companyId],
                ["plan_id"]
            );
            
            if (companies && companies.length > 0 && companies[0].plan_id) {
                const planId = companies[0].plan_id[0];
                const plans = await this.orm.read(
                    "salewise.plan",
                    [planId],
                    ["name"]
                );
                
                if (plans && plans.length > 0) {
                    this.state.planName = plans[0].name;
                } else {
                    this.state.planName = "No Plan";
                }
            } else {
                this.state.planName = "No Plan";
            }
        } catch (error) {
            console.error("Error loading plan name:", error);
            this.state.planName = "Error";
        } finally {
            this.state.loading = false;
        }
    }
}

export const systrayItem = {
    Component: SalewisePlanDisplay,
};

// Register with sequence 1.5 to appear right after company switcher (which has sequence 1)
registry.category("systray").add("SalewisePlanDisplay", systrayItem, { sequence: 1.5 });