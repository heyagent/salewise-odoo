#!/usr/bin/env node
/*
Visual web menus validation using Playwright, mirroring the JSON‑RPC tester.

Checks per plan/user:
 - Logs in via UI
 - Ensures SaaS menus enabled (JSON-RPC)
 - Loads web menus payload (GET /web/webclient/load_menus/<hash>)
 - Asserts non-empty apps, forbidden menus absence, and prints a compact report
 - Captures browser console traces for menu building (from our JS instrumentation)

Usage examples
  node custom/salewise_menus/scripts/test_web_menus_playwright.js \
    --url http://localhost:8069 --db salewise \
    --plans Starter,Professional,Enterprise \
    --users hr_manager:hr_manager,sales_user:sales_user

Prereqs
  npm i -D playwright
  npx playwright install
*/

const { chromium, request } = require('playwright');

function parseArgs() {
  const args = process.argv.slice(2);
  const opts = { url: 'http://localhost:8069', db: 'salewise', plans: ['Starter'], users: ['hr_manager:hr_manager'] };
  for (const a of args) {
    const [k, v] = a.startsWith('--') ? a.slice(2).split('=') : [null, null];
    if (!k) continue;
    if (k === 'url') opts.url = v;
    else if (k === 'db') opts.db = v;
    else if (k === 'plans') opts.plans = v.split(',').map(s => s.trim()).filter(Boolean);
    else if (k === 'users') opts.users = v.split(',').map(s => s.trim()).filter(Boolean);
  }
  return opts;
}

async function rpc(page, endpoint, payload) {
  const res = await page.evaluate(async ({ endpoint, payload }) => {
    const resp = await fetch(endpoint, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
    const data = await resp.json();
    if (data.error) throw new Error(JSON.stringify(data.error));
    return data.result;
  }, { endpoint, payload });
  return res;
}

async function adminSetPlan(baseURL, db, planName) {
  const ctx = await chromium.launchPersistentContext('', { headless: true });
  const page = await ctx.newPage();
  await page.goto(`${baseURL}/web`);
  await page.fill('input[name="login"]', 'admin');
  await page.fill('input[placeholder="Password"]', 'admin');
  await page.getByRole('button', { name: 'Log in' }).click();
  // authenticate JSON-RPC session
  await rpc(page, `${baseURL}/web/session/authenticate`, { jsonrpc: '2.0', method: 'call', params: { db, login: 'admin', password: 'admin' }, id: 1 });
  if (planName === 'Admin') {
    await rpc(page, `${baseURL}/web/dataset/call_kw`, { jsonrpc: '2.0', method: 'call', params: { model: 'res.company', method: 'write', args: [[1], { plan_id: false }], kwargs: {} }, id: 2 });
  } else {
    const planIds = await rpc(page, `${baseURL}/web/dataset/call_kw`, { jsonrpc: '2.0', method: 'call', params: { model: 'salewise.plan', method: 'search', args: [[['name', '=', planName]]], kwargs: {} }, id: 3 });
    if (!planIds || !planIds.length) throw new Error(`Plan not found: ${planName}`);
    await rpc(page, `${baseURL}/web/dataset/call_kw`, { jsonrpc: '2.0', method: 'call', params: { model: 'res.company', method: 'write', args: [[1], { plan_id: planIds[0] }], kwargs: {} }, id: 4 });
  }
  await ctx.close();
}

async function loginAndEnsureSaas(page, baseURL, db, login, password) {
  await page.goto(`${baseURL}/web`);
  // If already logged, Odoo may redirect to /odoo; if on login, fill credentials
  if (await page.locator('input[name="login"]').count()) {
    await page.fill('input[name="login"]', login);
    await page.fill('input[placeholder="Password"]', password);
    await page.getByRole('button', { name: 'Log in' }).click();
  }
  // JSON-RPC session auth to be safe
  await rpc(page, `${baseURL}/web/session/authenticate`, { jsonrpc: '2.0', method: 'call', params: { db, login, password }, id: 5 });
  const info = await rpc(page, `${baseURL}/web/session/get_session_info`, { jsonrpc: '2.0', method: 'call', params: {}, id: 6 });
  if (!info.show_saas_menus) {
    await rpc(page, `${baseURL}/web/dataset/call_kw`, { jsonrpc: '2.0', method: 'call', params: { model: 'res.users', method: 'action_toggle_saas_menus', args: [], kwargs: {} }, id: 7 });
  }
}

async function fetchWebMenus(page, baseURL) {
  const hash = Date.now().toString();
  const menus = await page.evaluate(async ({ url }) => {
    const resp = await fetch(url);
    return resp.json();
  }, { url: `${baseURL}/web/webclient/load_menus/${hash}` });
  return menus;
}

function analyzeMenus(menus) {
  const ids = Object.keys(menus).filter((k) => k !== 'root');
  const root = menus.root || { children: [] };
  const appIds = Array.isArray(root.children) ? root.children.slice() : [];
  const apps = appIds.map((id) => menus[id]).filter(Boolean);
  const forbidden = new Set([
    'salewise_menus.menu_saas_core_contracts',
    'salewise_menus.menu_saas_hr_payroll',
  ]);
  const xmlids = new Map(ids.map((id) => [id, menus[id].xmlid]));
  const forbiddenHits = [...xmlids.values()].filter((x) => forbidden.has(x));
  return { count: ids.length, appCount: apps.length, forbiddenHits };
}

async function run() {
  const { url, db, plans, users } = parseArgs();
  const browser = await chromium.launch({ headless: true });
  const summary = [];

  for (const plan of plans) {
    await adminSetPlan(url, db, plan);
    for (const cred of users) {
      const [login, password] = cred.split(':');
      const context = await browser.newContext();
      const page = await context.newPage();
      const logs = [];
      page.on('console', (msg) => {
        const t = msg.type();
        const txt = msg.text();
        if (txt.includes('[SALEWISE_TRACE_JS]') || /menu_service|getApps|getMenu/.test(txt)) {
          logs.push(`${t.toUpperCase()} ${txt}`);
        }
      });

      let ok = true;
      let reason = '';
      try {
        await loginAndEnsureSaas(page, url, db, login, password);
        const menus = await fetchWebMenus(page, url);
        const { count, appCount, forbiddenHits } = analyzeMenus(menus);
        if (appCount === 0 || count === 0) {
          ok = false; reason = `No apps or items (apps=${appCount}, items=${count})`;
        }
        if (forbiddenHits.length) {
          ok = false; reason = `Forbidden menus present: ${forbiddenHits.join(',')}`;
        }
        summary.push({ plan, user: login, count, appCount, ok, reason });
      } catch (e) {
        ok = false; reason = `Error: ${e && e.message || e}`;
        summary.push({ plan, user: login, count: 0, appCount: 0, ok, reason });
      }
      // Persist logs for debugging
      if (!ok) {
        console.log(`--- Console trace [${plan}/${login}] ---`);
        for (const l of logs) console.log(l);
      }
      await context.close();
    }
  }

  // Print summary table
  console.log('\n== VISUAL MENU SUMMARY ==');
  for (const row of summary) {
    const tag = row.ok ? 'OK' : `FAIL(${row.reason})`;
    console.log(`${row.plan}/${row.user}: apps=${row.appCount} items=${row.count} => ${tag}`);
  }

  // Exit non-zero on any failure
  process.exit(summary.every((r) => r.ok) ? 0 : 1);
}

run().catch((e) => { console.error(e); process.exit(1); });

