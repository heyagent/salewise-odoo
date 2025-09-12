#!/usr/bin/env python3
"""
Test web menus via JSON-RPC like the webclient does.

Features
- Switch company plan (Admin/no plan, Starter, Professional, Enterprise)
- Iterate over Salewise test users and enable SaaS mode for each
- Fetch web menus via ir.ui.menu.load_web_menus(False)
- Validate:
  - System/admin menus are hidden in SaaS mode
  - No "System" subtree leaked
  - For non-admin plans, all menus are within allowed plan tiers
  - Explicitly ensure Contracts/Payroll menus are not visible

Usage
  python3 custom/salewise_menus/scripts/test_web_menus.py \
    --url http://localhost:8069 --db salewise --plans Admin Starter Professional Enterprise \
    --users admin super_admin sys_admin hr_officer hr_manager

Exits non-zero on failures and prints a concise summary.
"""

import argparse
import importlib.util
import json
import sys
import time
from typing import Dict, Any, List, Tuple
import xmlrpc.client

import requests


def rpc(session: requests.Session, url: str, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    resp = session.post(f"{url}{endpoint}", json=payload)
    resp.raise_for_status()
    data = resp.json()
    if 'error' in data:
        raise RuntimeError(f"RPC error: {data['error']}")
    return data['result']


def rpc_auth(session: requests.Session, url: str, db: str, login: str, password: str) -> int:
    payload = {
        "jsonrpc": "2.0",
        "method": "call",
        "params": {"db": db, "login": login, "password": password},
        "id": 1,
    }
    res = rpc(session, f"{url}", "/web/session/authenticate", payload)
    return res.get("uid") or 0


def rpc_call_kw(session: requests.Session, url: str, model: str, method: str,
                args: List[Any] = None, kwargs: Dict[str, Any] = None) -> Any:
    payload = {
        "jsonrpc": "2.0",
        "method": "call",
        "params": {
            "model": model,
            "method": method,
            "args": args or [],
            "kwargs": kwargs or {},
        },
        "id": 2,
    }
    return rpc(session, f"{url}", "/web/dataset/call_kw", payload)


def get_session_info(session: requests.Session, url: str) -> Dict[str, Any]:
    payload = {"jsonrpc": "2.0", "method": "call", "params": {}, "id": 3}
    return rpc(session, f"{url}", "/web/session/get_session_info", payload)


def ensure_saas_enabled(session: requests.Session, url: str) -> None:
    info = get_session_info(session, url)
    if not info.get("show_saas_menus"):
        # Toggle via server method that creates settings if needed
        rpc_call_kw(session, url, 'res.users', 'action_toggle_saas_menus')
        # give server a moment and recheck
        time.sleep(0.1)
        info2 = get_session_info(session, url)
        if not info2.get("show_saas_menus"):
            raise RuntimeError("Failed to enable SaaS menus for user")


def set_company_plan(admin_sess: requests.Session, url: str, plan_name: str) -> Tuple[int, str]:
    # plan_name 'Admin' means no plan
    if plan_name == 'Admin':
        rpc_call_kw(admin_sess, url, 'res.company', 'write', args=[[1], {"plan_id": False}])
        return (0, 'Admin')
    # find plan by name
    plan_ids = rpc_call_kw(admin_sess, url, 'salewise.plan', 'search', args=[[['name', '=', plan_name]]])
    if not plan_ids:
        raise RuntimeError(f"Plan not found: {plan_name}")
    plan = rpc_call_kw(admin_sess, url, 'salewise.plan', 'read', args=[plan_ids, ['name']])[0]
    rpc_call_kw(admin_sess, url, 'res.company', 'write', args=[[1], {"plan_id": plan_ids[0]}])
    return (plan_ids[0], plan['name'])


def get_company_allowed_plans(session: requests.Session, url: str) -> List[int]:
    # call record method on company(1)
    try:
        return rpc_call_kw(session, url, 'res.company', 'get_available_plan_ids', args=[[1]])
    except Exception:
        return []


def load_web_menus(session: requests.Session, url: str) -> Dict[Any, Dict[str, Any]]:
    """Fetch web menus via the webclient GET route."""
    unique = str(int(time.time() * 1000))
    r = session.get(f"{url}/web/webclient/load_menus/{unique}")
    r.raise_for_status()
    return r.json()


def extract_menu_list(web_menus: Dict[Any, Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [m for mid, m in web_menus.items() if mid != 'root']


def validate_web_menus(plan_name: str, username: str, menu_map: Dict[Any, Dict[str, Any]],
                       allowed_plan_ids: List[int]) -> List[str]:
    errors: List[str] = []
    menus = extract_menu_list(menu_map)

    # rule: no system menus in SaaS mode
    sys_menus = [m for m in menus if m.get('is_system')]
    if sys_menus:
        ids = [m.get('xmlid') or m.get('id') for m in sys_menus[:5]]
        errors.append(f"system menus visible: {ids} ...")

    # rule: System subtree must not exist
    system_root = next((mid for mid, m in menu_map.items()
                        if isinstance(mid, int) and m.get('xmlid') == 'salewise_menus.menu_saas_system'), None)
    if system_root is not None:
        errors.append("System root is present in web menus")

    # rule: Contracts/Payroll must not be visible
    forbidden_xmlids = {
        'salewise_menus.menu_saas_core_contracts',
        'salewise_menus.menu_saas_hr_payroll',
    }
    viol = [m for m in menus if m.get('xmlid') in forbidden_xmlids]
    if viol:
        ids = [m.get('xmlid') for m in viol]
        errors.append(f"forbidden menus visible: {ids}")

    # rule: non-admin plans must only show allowed tiers
    if plan_name != 'Admin' and allowed_plan_ids:
        bad = []
        for m in menus:
            plan = m.get('plan_id')
            if plan:
                # plan may be [id, name] or id
                plan_id = plan[0] if isinstance(plan, list) else plan
                if plan_id not in allowed_plan_ids:
                    bad.append((m.get('xmlid') or m.get('name'), plan_id))
        if bad:
            sample = bad[:5]
            errors.append(f"menus outside allowed plans: {sample} ...")

    return errors


def _load_baseline_module(path: str, var: str):
    spec = importlib.util.spec_from_file_location('baseline_mod', path)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)  # type: ignore
    return getattr(mod, var)


def get_visible_menu_xmlids(sess: requests.Session, url: str, admin_sess: requests.Session) -> List[str]:
    """Return XMLIDs of visible SaaS menus for current user using JSON-RPC.

    We lookup menu ids via search(), then use admin to resolve xmlids from ir.model.data.
    """
    menu_ids = rpc_call_kw(sess, url, 'ir.ui.menu', 'search', args=[[['is_saas', '=', True]]]) or []
    xmlid_records = rpc_call_kw(
        admin_sess, url, 'ir.model.data', 'search_read',
        args=[[['model', '=', 'ir.ui.menu'], ['res_id', 'in', menu_ids]]],
        kwargs={'fields': ['module', 'name']}
    ) or []
    xmlids = [f"{rec['module']}.{rec['name']}" for rec in xmlid_records if rec.get('module') and rec.get('name')]
    return sorted(xmlids)


def main():
    ap = argparse.ArgumentParser(description="Test Salewise web menus across users/plans")
    ap.add_argument('--url', default='http://localhost:8069', help='Odoo base URL')
    ap.add_argument('--db', default='salewise', help='Database name')
    ap.add_argument('--plans', nargs='+', default=['Admin', 'Starter', 'Professional', 'Enterprise'])
    ap.add_argument('--check-baselines', action='store_true', help='Also validate counts and XMLIDs against baselines')
    ap.add_argument('--users', nargs='+', default=[
        'admin', 'super_admin', 'sys_admin', 'sales_user', 'sales_manager',
        'hr_officer', 'hr_manager', 'marketing_user', 'accountant',
        'project_manager', 'project_user', 'employee', 'team_lead',
    ])
    args = ap.parse_args()

    results = {plan: {} for plan in args.plans}
    failures = []

    # Load baselines if requested
    MENU_COUNT_BASELINE = {}
    MENU_BASELINE = {}
    if args.check_baselines:
        try:
            MENU_COUNT_BASELINE = _load_baseline_module('custom/salewise_menus/tests/menu_count_baseline.py', 'MENU_COUNT_BASELINE')
            MENU_BASELINE = _load_baseline_module('custom/salewise_menus/tests/menu_baseline.py', 'MENU_BASELINE')
        except Exception as e:
            print(f"ERROR: failed to load baselines: {e}", file=sys.stderr)
            return 2

    # Admin session to switch plans
    admin = requests.Session()
    uid = rpc_auth(admin, args.url, args.db, 'admin', 'admin')
    if not uid:
        print("ERROR: failed to login as admin", file=sys.stderr)
        return 2

    for plan in args.plans:
        set_company_plan(admin, args.url, plan)
        # small pause to let caches clear
        time.sleep(0.2)

        for user in args.users:
            sess = requests.Session()
            if not rpc_auth(sess, args.url, args.db, user, user):
                failures.append((plan, user, "login failed"))
                continue

            # ensure SaaS menus are enabled in session
            try:
                ensure_saas_enabled(sess, args.url)
            except Exception as e:
                failures.append((plan, user, f"saas toggle failed: {e}"))
                continue

            # fetch menus and validate
            try:
                wm = load_web_menus(sess, args.url)
                allowed_ids = get_company_allowed_plans(sess, args.url)
                errs = validate_web_menus(plan, user, wm, allowed_ids)
                results[plan][user] = {
                    'count': len([mid for mid in wm.keys() if mid != 'root']),
                    'errors': errs,
                }
                for e in errs:
                    failures.append((plan, user, e))
                # Optional baseline checks (counts + xmlids)
                if args.check_baselines:
                    # Count baseline
                    try:
                        cnt = rpc_call_kw(sess, args.url, 'ir.ui.menu', 'search_count', args=[[['is_saas', '=', True]]])
                        expected_cnt = MENU_COUNT_BASELINE.get(plan, {}).get(user)
                        if expected_cnt is not None and cnt != expected_cnt:
                            failures.append((plan, user, f"baseline count mismatch: expected {expected_cnt}, got {cnt}"))
                    except Exception as e:
                        failures.append((plan, user, f"count rpc error: {e}"))
                    # XMLIDs baseline
                    try:
                        xmlids = get_visible_menu_xmlids(sess, args.url, admin)
                        expected_xmlids = MENU_BASELINE.get(plan, {}).get(user)
                        if expected_xmlids is not None:
                            a, b = set(xmlids), set(expected_xmlids)
                            if a != b:
                                missing = sorted(list(b - a))[:5]
                                extra = sorted(list(a - b))[:5]
                                failures.append((plan, user, f"baseline xmlids mismatch: missing={len(b-a)} sample={missing} extra={len(a-b)} sample={extra}"))
                    except Exception as e:
                        failures.append((plan, user, f"xmlid rpc error: {e}"))
            except Exception as e:
                failures.append((plan, user, f"rpc error: {e}"))

    # Summary
    ok = not failures
    print("== SUMMARY ==")
    for plan, users in results.items():
        line = [f"{plan}:"]
        for u, info in users.items():
            tag = "OK" if not info['errors'] else f"FAIL({len(info['errors'])})"
            line.append(f"{u}={info['count']}/{tag}")
        print(" ".join(line))

    if not ok:
        print("\nFailures:")
        for plan, user, msg in failures[:50]:
            print(f" - [{plan}] {user}: {msg}")
        # also write JSON artifact
        try:
            with open('/tmp/salewise_web_menu_results.json', 'w') as f:
                json.dump(results, f, indent=2)
            print("\nDetails written to /tmp/salewise_web_menu_results.json")
        except Exception:
            pass
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
