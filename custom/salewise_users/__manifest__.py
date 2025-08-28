{
    'name': 'SaleWise Demo Users',
    'version': '1.0',
    'category': 'SaleWise/Configuration',
    'summary': 'Demo users and roles for SaleWise platform',
    'description': """
        SaleWise Demo Users and Roles
        ==============================
        
        This module creates demo users and roles for testing the SaleWise platform.
        
        Features:
        ---------
        * Creates 12 predefined roles with appropriate permissions
        * Creates test users for each role
        * All users have simple login/password combinations for testing
        
        Roles Created:
        --------------
        - Super Administrator
        - System Administrator
        - Sales Manager
        - Sales User
        - Accountant
        - HR Manager
        - HR Officer
        - Project Manager
        - Project User
        - Marketing User
        - Employee
        - Team Lead
    """,
    'author': 'SaleWise',
    'depends': [
        'base',
        'base_user_role',
        'sales_team',
        'account',
        'project',
        'hr',
        'hr_expense',
        'hr_holidays',
        'hr_recruitment',
        'payroll',
        'documents',
        'hr_contract',
        'appointment',
        'mass_mailing',
        'marketing_automation',
        'social',
    ],
    'data': [
        'data/res_users_role.xml',
        'data/res_users.xml',
    ],
    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}