#!/usr/bin/env python3
"""
Test Salewise SaaS window actions against baselines via JSON-RPC.

Loads ACTIONS_BASELINE and ACTIONS_COUNT_BASELINE from tests/, switches plans,
logs in as each test user, and checks which actions are loadable via /web/action/load.

Usage
  python3 custom/salewise_actions/scripts/test_actions_against_baseline.py \
    --url http://localhost:8069 --db salewise \
    --plans Admin Starter Professional Enterprise \
    --users admin super_admin sys_admin sales_user sales_manager \
            hr_officer hr_manager marketing_user accountant \
            project_manager project_user employee team_lead
"""

import argparse
import importlib.util
import json
import time
from typing import Any, Dict, List, Tuple
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
    res = rpc(session, url, "/web/session/authenticate", payload)
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
    return rpc(session, url, "/web/dataset/call_kw", payload)


def set_company_plan(admin_sess: requests.Session, url: str, plan_name: str) -> Tuple[int, str]:
    if plan_name == 'Admin':
        rpc_call_kw(admin_sess, url, 'res.company', 'write', args=[[1], {"plan_id": False}])
        return (0, 'Admin')
    plan_ids = rpc_call_kw(admin_sess, url, 'salewise.plan', 'search', args=[[['name', '=', plan_name]]])
    if not plan_ids:
        raise RuntimeError(f"Plan not found: {plan_name}")
    plan = rpc_call_kw(admin_sess, url, 'salewise.plan', 'read', args=[plan_ids, ['name']])[0]
    rpc_call_kw(admin_sess, url, 'res.company', 'write', args=[[1], {"plan_id": plan_ids[0]}])
    return (plan_ids[0], plan['name'])


def _load_baseline_module(path: str, var: str):
    spec = importlib.util.spec_from_file_location('actions_baseline_mod', path)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)  # type: ignore
    return getattr(mod, var)


def discover_saas_action_xmlids(sess: requests.Session, url: str) -> List[str]:
    imd = rpc_call_kw(
        sess, url, 'ir.model.data', 'search_read',
        args=[[['module', '=', 'salewise_actions'], ['model', '=', 'ir.actions.act_window']]],
        kwargs={'fields': ['module', 'name', 'res_id']}
    ) or []
    items: List[str] = []
    for rec in imd:
        rid = rec.get('res_id')
        if not rid:
            continue
        info = rpc_call_kw(sess, url, 'ir.actions.act_window', 'read', args=[[rid], ['is_saas']])
        if info and info[0].get('is_saas'):
            items.append(f"{rec['module']}.{rec['name']}")
    return sorted(items)


def can_load_action(sess: requests.Session, url: str, xmlid: str) -> bool:
    payload = {"jsonrpc": "2.0", "method": "call", "params": {"action_id": xmlid}, "id": 5}
    try:
        rpc(sess, url, "/web/action/load", payload)
        return True
    except Exception:
        return False


def main():
    ap = argparse.ArgumentParser(description="Test Salewise actions against baselines")
    ap.add_argument('--url', default='http://localhost:8069', help='Odoo base URL')
    ap.add_argument('--db', default='salewise', help='Database name')
    ap.add_argument('--plans', nargs='+', default=['Admin', 'Starter', 'Professional', 'Enterprise'])
    ap.add_argument('--users', nargs='+', default=[
        'admin', 'super_admin', 'sys_admin', 'sales_user', 'sales_manager',
        'hr_officer', 'hr_manager', 'marketing_user', 'accountant',
        'project_manager', 'project_user', 'employee', 'team_lead',
    ])
    args = ap.parse_args()

    # Load baselines
    try:
        ACTIONS_BASELINE = _load_baseline_module('custom/salewise_actions/tests/actions_baseline.py', 'ACTIONS_BASELINE')
        ACTIONS_COUNT_BASELINE = _load_baseline_module('custom/salewise_actions/tests/actions_count_baseline.py', 'ACTIONS_COUNT_BASELINE')
    except Exception as e:
        print(f"ERROR: failed to load baselines: {e}")
        return 2

    admin = requests.Session()
    if not rpc_auth(admin, args.url, args.db, 'admin', 'admin'):
        print("ERROR: failed to login as admin")
        return 2

    # Discover candidate SaaS actions once (from current DB)
    candidate_xmlids = discover_saas_action_xmlids(admin, args.url)
    if not candidate_xmlids:
        print("No SaaS actions found in salewise_actions.")
        return 2

    failures: List[Tuple[str, str, str]] = []

    for plan in args.plans:
        set_company_plan(admin, args.url, plan)
        time.sleep(0.2)
        for user in args.users:
            sess = requests.Session()
            if not rpc_auth(sess, args.url, args.db, user, user):
                failures.append((plan, user, "login failed"))
                continue
            allowed = []
            for xid in candidate_xmlids:
                if can_load_action(sess, args.url, xid):
                    allowed.append(xid)
            allowed = sorted(allowed)

            expected_list = sorted(ACTIONS_BASELINE.get(plan, {}).get(user, []))
            expected_cnt = ACTIONS_COUNT_BASELINE.get(plan, {}).get(user)

            if expected_cnt is not None and len(allowed) != expected_cnt:
                failures.append((plan, user, f"count mismatch: expected {expected_cnt}, got {len(allowed)}"))

            if expected_list:
                a, b = set(allowed), set(expected_list)
                if a != b:
                    missing = sorted(list(b - a))[:5]
                    extra = sorted(list(a - b))[:5]
                    failures.append((plan, user, f"xmlids mismatch: missing={len(b-a)} sample={missing} extra={len(a-b)} sample={extra}"))

    # Summary
    ok = not failures
    print("== ACTIONS TEST SUMMARY ==")
    if ok:
        print("All plan/user combinations match baselines.")
        return 0
    print("Failures (first 50):")
    for plan, user, msg in failures[:50]:
        print(f" - [{plan}] {user}: {msg}")
    return 1


if __name__ == '__main__':
    raise SystemExit(main())

