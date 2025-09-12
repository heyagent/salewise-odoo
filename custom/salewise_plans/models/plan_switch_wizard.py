# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class SalewisePlanSwitchWizard(models.TransientModel):
    _name = 'salewise.plan.switch.wizard'
    _description = 'Switch Company Plan'

    plan_id = fields.Many2one('salewise.plan', string='Plan', required=True)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        company = self.env.company
        if 'plan_id' in fields_list and company.plan_id:
            res['plan_id'] = company.plan_id.id
        return res

    def action_apply(self):
        self.ensure_one()
        company = self.env.company
        # Respect access rights: only users with write access on res.company can change plan
        company.write({'plan_id': self.plan_id.id})
        # Trigger a reload of the UI
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

