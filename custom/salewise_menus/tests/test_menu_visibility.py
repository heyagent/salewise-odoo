# -*- coding: utf-8 -*-
"""
Test menu visibility against captured baseline.
Ensures exact menu XML IDs match for each user/plan combination.
"""

from odoo.tests import TransactionCase, tagged
from .menu_baseline import MENU_BASELINE


@tagged('post_install', '-at_install', 'menu_visibility')
class TestMenuVisibility(TransactionCase):
    """Test menu visibility matches exact baseline"""
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        
        # Get models
        cls.User = cls.env['res.users']
        cls.Company = cls.env['res.company']
        cls.Plan = cls.env['salewise.plan']
        cls.Menu = cls.env['ir.ui.menu']
        cls.ModelData = cls.env['ir.model.data']
        cls.UserSettings = cls.env['res.users.settings']
        
        # Get plans
        cls.starter_plan = cls.Plan.search([('name', '=', 'Starter')], limit=1)
        cls.professional_plan = cls.Plan.search([('name', '=', 'Professional')], limit=1)
        cls.enterprise_plan = cls.Plan.search([('name', '=', 'Enterprise')], limit=1)
        
        # Get company
        cls.company = cls.Company.browse(1)
        
        # Users to test
        cls.test_users = [
            'admin', 'super_admin', 'sys_admin',
            'sales_user', 'sales_manager', 
            'hr_officer', 'hr_manager',
            'marketing_user', 'accountant',
            'project_manager', 'project_user',
            'employee', 'team_lead'
        ]

    def _set_company_plan(self, plan):
        """Set the company's plan"""
        self.company.sudo().write({'plan_id': plan.id if plan else False})
        self.env.invalidate_all()  # Invalidate cache after plan change

    def _get_user_menu_xmlids(self, username):
        """Get XML IDs of SaaS menus visible to a user"""
        user = self.User.search([('login', '=', username)], limit=1)
        if not user:
            return []
        
        # Ensure user has SaaS mode enabled
        if user.res_users_settings_id:
            user.res_users_settings_id.sudo().write({'show_saas_menus': True})
        
        # Invalidate cache for the user's environment to ensure fresh menu filtering
        user_env = self.Menu.with_user(user)
        user_env.env.invalidate_all()
        
        # Get menus visible to user
        menus = user_env.search([
            ('is_saas', '=', True)
        ])
        
        if not menus:
            return []
        
        # Get XML IDs for these menus
        xmlids = []
        for menu in menus:
            # Try to get XML ID
            model_data = self.ModelData.sudo().search([
                ('model', '=', 'ir.ui.menu'),
                ('res_id', '=', menu.id)
            ], limit=1)
            
            if model_data:
                xmlid = f"{model_data.module}.{model_data.name}"
                xmlids.append(xmlid)
            else:
                # Fallback if no XML ID
                xmlids.append(f"__id_{menu.id}")
        
        return sorted(xmlids)  # Sort for consistent comparison

    def _test_plan_menus(self, plan_name, plan_obj):
        """Test menus for a specific plan"""
        self._set_company_plan(plan_obj)
        
        # Get expected menus from baseline
        expected = MENU_BASELINE.get(plan_name, {})
        
        errors = []
        
        for username in self.test_users:
            if username not in expected:
                continue
            
            # Get actual menus
            actual = self._get_user_menu_xmlids(username)
            expected_xmlids = expected[username]
            
            # Convert to sets for comparison
            actual_set = set(actual)
            expected_set = set(expected_xmlids)
            
            # Find differences
            missing = expected_set - actual_set
            extra = actual_set - expected_set
            
            if missing or extra:
                errors.append(f"\n{username} in {plan_name}:")
                if missing:
                    errors.append(f"  Missing {len(missing)} menus:")
                    for xmlid in sorted(list(missing))[:5]:  # Show first 5
                        errors.append(f"    - {xmlid}")
                    if len(missing) > 5:
                        errors.append(f"    ... and {len(missing) - 5} more")
                
                if extra:
                    errors.append(f"  Extra {len(extra)} menus:")
                    for xmlid in sorted(list(extra))[:5]:  # Show first 5
                        errors.append(f"    + {xmlid}")
                    if len(extra) > 5:
                        errors.append(f"    ... and {len(extra) - 5} more")
        
        if errors:
            self.fail("Menu mismatches found:" + "\n".join(errors))

    def test_01_starter_plan_exact_match(self):
        """Test Starter plan menus match baseline exactly"""
        self._test_plan_menus('Starter', self.starter_plan)

    def test_02_professional_plan_exact_match(self):
        """Test Professional plan menus match baseline exactly"""
        self._test_plan_menus('Professional', self.professional_plan)

    def test_03_enterprise_plan_exact_match(self):
        """Test Enterprise plan menus match baseline exactly"""
        self._test_plan_menus('Enterprise', self.enterprise_plan)

    def test_04_baseline_consistency(self):
        """Verify baseline makes sense (progression, differentiation)"""
        
        # Check that menu counts increase with plan tier
        for username in ['sales_user', 'hr_officer', 'marketing_user']:
            if username in MENU_BASELINE.get('Starter', {}):
                starter = len(MENU_BASELINE['Starter'][username])
                professional = len(MENU_BASELINE['Professional'][username])
                enterprise = len(MENU_BASELINE['Enterprise'][username])
                
                self.assertLessEqual(
                    starter, professional,
                    f"{username}: Professional should have >= menus than Starter"
                )
                self.assertLessEqual(
                    professional, enterprise,
                    f"{username}: Enterprise should have >= menus than Professional"
                )
        
        # Check that different users see different menus in Enterprise
        if 'Enterprise' in MENU_BASELINE:
            sales_menus = set(MENU_BASELINE['Enterprise'].get('sales_user', []))
            hr_menus = set(MENU_BASELINE['Enterprise'].get('hr_officer', []))
            marketing_menus = set(MENU_BASELINE['Enterprise'].get('marketing_user', []))
            
            # They should have some unique menus
            self.assertTrue(
                hr_menus != sales_menus,
                "HR and Sales should see different menus"
            )
            self.assertTrue(
                marketing_menus != sales_menus,
                "Marketing and Sales should see different menus"
            )

