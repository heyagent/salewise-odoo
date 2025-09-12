# -*- coding: utf-8 -*-
from odoo import models, fields
from odoo.exceptions import AccessError


class IrActionsActWindow(models.Model):
    _inherit = 'ir.actions.act_window'
    
    original_action = fields.Many2one(
        'ir.actions.act_window',
        string='Original Action',
        help='Reference to the original action this was cloned from'
    )
    
    original_view_mode = fields.Char(
        string='Original View Mode',
        help='The view_mode string from the original action'
    )
    
    is_saas = fields.Boolean(
        string='Is SaaS Action',
        default=False,
        help='Indicates if this action is part of the SaaS system'
    )
    
    is_system = fields.Boolean(
        string='Is System Action',
        default=False,
        help='Indicates if this is a system action (available to all plans)'
    )
    
    plan_id = fields.Many2one(
        'salewise.plan',
        string='Plan',
        help='The minimum plan required to access this action'
    )

    # Enforce SaaS restrictions for window actions when loaded by the webclient
    def _is_saas_allowed_for_user(self):
        self.ensure_one()
        # Only enforce for SaaS-tagged actions
        if not self.is_saas:
            return True

        user = self.env.user

        # Group-based restriction (same semantics as menus: OR over groups)
        if self.groups_id:
            if not (user.groups_id & self.groups_id):
                return False

        # Plan-based restriction mirrors menu logic:
        # - Admin (no company plan) can access everything
        # - Non-admin (has company plan):
        #   * block is_system actions
        #   * require action.plan_id to be within allowed plan hierarchy
        company = self.env.company
        if company and company.plan_id:
            # Block system actions for non-admin plans
            if getattr(self, 'is_system', False):
                return False

            # If action is tied to a plan, ensure it is within allowed tiers
            if self.plan_id:
                try:
                    allowed = set(company.get_available_plan_ids() or [])
                except Exception:
                    allowed = set()
                if self.plan_id.id not in allowed:
                    return False

        return True

    def _get_action_dict(self):
        # The controller calls this method as sudo(); enforce SaaS restrictions explicitly.
        self.ensure_one()
        if not self._is_saas_allowed_for_user():
            # Raise AccessError to clearly signal forbidden access similar to menu filtering intent
            raise AccessError("You do not have access to this action.")
        return super()._get_action_dict()


class IrActionsServer(models.Model):
    _inherit = 'ir.actions.server'
    
    original_action = fields.Many2one(
        'ir.actions.server', 
        string='Original Action',
        help='Reference to the original action this was cloned from'
    )
    
    is_saas = fields.Boolean(
        string='Is SaaS Action',
        default=False,
        help='Indicates if this action is part of the SaaS system'
    )
    
    is_system = fields.Boolean(
        string='Is System Action',
        default=False,
        help='Indicates if this is a system action (available to all plans)'
    )
    
    plan_id = fields.Many2one(
        'salewise.plan',
        string='Plan',
        help='The minimum plan required to access this action'
    )
