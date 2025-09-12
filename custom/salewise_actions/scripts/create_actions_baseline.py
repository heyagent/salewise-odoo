#!/usr/bin/env python3
"""
Create baseline of accessible Salewise SaaS window actions per plan and user.

Discovers all ir.actions.act_window with XMLIDs in module 'salewise_actions' and is_saas=True,
then for each plan and test user, attempts to load the action via /web/action/load.

Outputs two Python files under custom/salewise_actions/tests/:
- actions_baseline.py: ACTIONS_BASELINE mapping {plan: {user: [xmlids...]}}
- actions_count_baseline.py: ACTIONS_COUNT_BASELINE mapping {plan: {user: count}}

Usage
  python3 custom/salewise_actions/scripts/create_actions_baseline.py \
    --url http://localhost:8069 --db salewise \
    --plans Admin Starter Professional Enterprise \
    --users admin super_admin sales_user sales_manager hr_officer hr_manager \
            marketing_user accountant project_manager project_user employee team_lead
"""

import argparse
import json
import os
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


def discover_saas_action_xmlids(sess: requests.Session, url: str) -> List[str]:
    # Find all act_window in salewise_actions
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


def write_python_baseline(path: str, var_name: str, data: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        f.write("# -*- coding: utf-8 -*-\n")
        f.write(f"{var_name} = ")
        json.dump(data, f, indent=2, sort_keys=True)
        f.write("\n")


def main():
    ap = argparse.ArgumentParser(description="Create baseline of Salewise actions per plan/user")
    ap.add_argument('--url', default='http://localhost:8069', help='Odoo base URL')
    ap.add_argument('--db', default='salewise', help='Database name')
    ap.add_argument('--plans', nargs='+', default=['Admin', 'Starter', 'Professional', 'Enterprise'])
    ap.add_argument('--users', nargs='+', default=[
        'admin', 'super_admin', 'sys_admin', 'sales_user', 'sales_manager',
        'hr_officer', 'hr_manager', 'marketing_user', 'accountant',
        'project_manager', 'project_user', 'employee', 'team_lead',
    ])
    args = ap.parse_args()

    admin = requests.Session()
    if not rpc_auth(admin, args.url, args.db, 'admin', 'admin'):
        print("ERROR: failed to login as admin")
        return 2

    # Discover candidate SaaS actions once
    action_xmlids = discover_saas_action_xmlids(admin, args.url)
    if not action_xmlids:
        print("No SaaS actions found in salewise_actions.")
        return 2

    baseline: Dict[str, Dict[str, List[str]]] = {plan: {} for plan in args.plans}
    counts: Dict[str, Dict[str, int]] = {plan: {} for plan in args.plans}

    for plan in args.plans:
        set_company_plan(admin, args.url, plan)
        time.sleep(0.2)
        for user in args.users:
            sess = requests.Session()
            if not rpc_auth(sess, args.url, args.db, user, user):
                baseline[plan][user] = []
                counts[plan][user] = 0
                continue
            allowed = []
            for xid in action_xmlids:
                if can_load_action(sess, args.url, xid):
                    allowed.append(xid)
            allowed = sorted(allowed)
            baseline[plan][user] = allowed
            counts[plan][user] = len(allowed)

    # Write files
    write_python_baseline('custom/salewise_actions/tests/actions_baseline.py', 'ACTIONS_BASELINE', baseline)
    write_python_baseline('custom/salewise_actions/tests/actions_count_baseline.py', 'ACTIONS_COUNT_BASELINE', counts)

    print("Baselines written to:")
    print(" - custom/salewise_actions/tests/actions_baseline.py")
    print(" - custom/salewise_actions/tests/actions_count_baseline.py")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

