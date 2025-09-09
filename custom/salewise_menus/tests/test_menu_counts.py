# -*- coding: utf-8 -*-
"""
Test menu counts against captured baseline.
Ensures exact menu counts match for each user/plan combination.
"""

from odoo.tests import TransactionCase, tagged
from .menu_count_baseline import MENU_COUNT_BASELINE


@tagged('post_install', '-at_install', 'menu_counts')
class TestMenuCounts(TransactionCase):
    """Test menu counts match exact baseline"""
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        
        # Get models
        cls.User = cls.env['res.users']
        cls.Company = cls.env['res.company']
        cls.Plan = cls.env['salewise.plan']
        cls.Menu = cls.env['ir.ui.menu']
        cls.UserSettings = cls.env['res.users.settings']
        
        # Get plans
        cls.starter_plan = cls.Plan.search([('name', '=', 'Starter')], limit=1)
        cls.professional_plan = cls.Plan.search([('name', '=', 'Professional')], limit=1)
        cls.enterprise_plan = cls.Plan.search([('name', '=', 'Enterprise')], limit=1)
        
        # Get company
        cls.company = cls.Company.browse(1)
        
        # Users to test
        cls.test_users = [
            'admin', 'sales_user', 'sales_manager', 'hr_officer', 
            'hr_manager', 'marketing_user', 'accountant',
            'project_manager', 'project_user'
        ]

    def _set_company_plan(self, plan):
        """Set the company's plan"""
        self.company.sudo().write({'plan_id': plan.id if plan else False})
        self.env.cache.clear()  # Clear cache after plan change

    def _get_user_menu_count(self, username):
        """Get count of SaaS menus visible to a user"""
        user = self.User.search([('login', '=', username)], limit=1)
        if not user:
            return 0
        
        # Ensure user has SaaS mode enabled
        if user.res_users_settings_id:
            user.res_users_settings_id.sudo().write({'show_saas_menus': True})
        
        # Count menus visible to user
        menu_count = self.Menu.with_user(user).search_count([
            ('is_saas', '=', True)
        ])
        
        return menu_count

    def _test_plan_counts(self, plan_name, plan_obj):
        """Test menu counts for a specific plan"""
        self._set_company_plan(plan_obj)
        
        # Get expected counts from baseline
        expected = MENU_COUNT_BASELINE.get(plan_name, {})
        
        errors = []
        
        for username in self.test_users:
            if username not in expected:
                continue
            
            # Get actual count
            actual_count = self._get_user_menu_count(username)
            expected_count = expected[username]
            
            # Compare counts
            if actual_count != expected_count:
                errors.append(
                    f"\n{username} in {plan_name}: "
                    f"Expected {expected_count} menus, got {actual_count} "
                    f"(diff: {actual_count - expected_count:+d})"
                )
        
        if errors:
            self.fail("Menu count mismatches found:" + "".join(errors))

    def test_01_starter_plan_counts(self):
        """Test Starter plan menu counts match baseline exactly"""
        self._test_plan_counts('Starter', self.starter_plan)

    def test_02_professional_plan_counts(self):
        """Test Professional plan menu counts match baseline exactly"""
        self._test_plan_counts('Professional', self.professional_plan)

    def test_03_enterprise_plan_counts(self):
        """Test Enterprise plan menu counts match baseline exactly"""
        self._test_plan_counts('Enterprise', self.enterprise_plan)

    def test_04_count_progression(self):
        """Verify menu counts follow expected progression across plans"""
        
        # For most users, counts should increase or stay same with plan tier
        for username in self.test_users:
            if username not in MENU_COUNT_BASELINE.get('Starter', {}):
                continue
            
            starter_count = MENU_COUNT_BASELINE['Starter'][username]
            professional_count = MENU_COUNT_BASELINE['Professional'][username]
            enterprise_count = MENU_COUNT_BASELINE['Enterprise'][username]
            
            self.assertLessEqual(
                starter_count, professional_count,
                f"{username}: Professional should have >= menus than Starter "
                f"(Starter: {starter_count}, Professional: {professional_count})"
            )
            self.assertLessEqual(
                professional_count, enterprise_count,
                f"{username}: Enterprise should have >= menus than Professional "
                f"(Professional: {professional_count}, Enterprise: {enterprise_count})"
            )

    def test_05_user_differentiation(self):
        """Verify different user types see different menu counts"""
        
        # Check Enterprise plan for maximum differentiation
        if 'Enterprise' not in MENU_COUNT_BASELINE:
            self.skipTest("No Enterprise baseline available")
        
        enterprise_counts = MENU_COUNT_BASELINE['Enterprise']
        
        # Different roles should have different counts
        sales_count = enterprise_counts.get('sales_user', 0)
        hr_count = enterprise_counts.get('hr_officer', 0)
        marketing_count = enterprise_counts.get('marketing_user', 0)
        accountant_count = enterprise_counts.get('accountant', 0)
        
        # Admin should see the most
        admin_count = enterprise_counts.get('admin', 0)
        self.assertGreaterEqual(
            admin_count, sales_count,
            "Admin should see at least as many menus as sales_user"
        )
        
        # Different departments should have different counts (not all the same)
        counts = [sales_count, hr_count, marketing_count, accountant_count]
        unique_counts = len(set(counts))
        
        self.assertGreater(
            unique_counts, 1,
            f"Different user types should see different menu counts. "
            f"All counts are: {counts}"
        )