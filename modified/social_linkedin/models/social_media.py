# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import requests
from werkzeug.urls import url_encode, url_join

from odoo import _, models, fields
from odoo.exceptions import UserError


class SocialMediaLinkedin(models.Model):
    _inherit = 'social.media'

    _LINKEDIN_ENDPOINT = 'https://api.linkedin.com/rest/'
    _LINKEDIN_SCOPE = 'r_basicprofile r_organization_followers w_member_social w_member_social_feed rw_organization_admin w_organization_social w_organization_social_feed r_organization_social r_organization_social_feed'

    media_type = fields.Selection(selection_add=[('linkedin', 'LinkedIn')])

    def _action_add_account(self):
        self.ensure_one()

        if self.media_type != 'linkedin':
            return super(SocialMediaLinkedin, self)._action_add_account()

        linkedin_app_id = self.env['ir.config_parameter'].sudo().get_param('social.linkedin_app_id')
        linkedin_client_secret = self.env['ir.config_parameter'].sudo().get_param('social.linkedin_client_secret')

        if not linkedin_app_id or not linkedin_client_secret:
            raise UserError(_("Please configure your LinkedIn App ID and Client Secret in Settings > Social Marketing."))
        
        return self._add_linkedin_accounts_from_configuration(linkedin_app_id)

    def _add_linkedin_accounts_from_configuration(self, linkedin_app_id):
        params = {
            'response_type': 'code',
            'client_id': linkedin_app_id,
            'redirect_uri': self._get_linkedin_redirect_uri(),
            'state': self.csrf_token,
            'scope': self._LINKEDIN_SCOPE,
        }

        return {
            'type': 'ir.actions.act_url',
            'url': 'https://www.linkedin.com/oauth/v2/authorization?%s' % url_encode(params),
            'target': 'self'
        }

    def _get_linkedin_redirect_uri(self):
        return url_join(self.get_base_url(), 'social_linkedin/callback')
