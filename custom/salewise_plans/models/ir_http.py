# -*- coding: utf-8 -*-
import logging
from odoo import models
from odoo.http import request


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    def session_info(self):
        info = super().session_info()
        if request and request.env and request.env.user:
            # Mirror OCA impersonate pattern: expose group-based ability via session
            is_allowed = request.env.user.has_group('salewise_plans.group_switch_plan')
            info.update({'is_switch_plan_user': is_allowed})
            try:
                logger = logging.getLogger(__name__)
                logger.debug(
                    "[SALEWISE_PLANS] session_info uid=%s login=%s is_switch_plan_user=%s impersonate_from_uid=%s",
                    request.env.uid,
                    request.env.user.login,
                    is_allowed,
                    getattr(request.session, 'impersonate_from_uid', None),
                )
            except Exception:
                pass
        return info
