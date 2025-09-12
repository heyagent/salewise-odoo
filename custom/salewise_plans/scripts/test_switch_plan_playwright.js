#!/usr/bin/env node
/**
 * Playwright-based external test for plan switching:
 * - logs in as admin
 * - enables SaaS menus
 * - switches plan (Starter -> Professional) via JSON-RPC
 * - verifies that the web menus payload changes accordingly
 *
 * Usage:
 *   node custom/salewise_plans/scripts/test_switch_plan_playwright.js \
 *     --url http://localhost:8069 --db salewise --from Starter --to Professional
 */

const { chromium } = require('playwright');

function parseArgs() {
  const args = process.argv.slice(2);
  const opts = { url: 'http://localhost:8069', db: 'salewise', from: 'Starter', to: 'Professional' };
  for (const a of args) {
    const [k, v] = a.startsWith('--') ? a.slice(2).split('=') : [null, null];
    if (!k) continue;
    if (k === 'url') opts.url = v;
    else if (k === 'db') opts.db = v;
    else if (k === 'from') opts.from = v;
    else if (k === 'to') opts.to = v;
  }
  return opts;
}

async function rpc(page, endpoint, payload) {
  const res = await page.evaluate(async ({ endpoint, payload }) => {
    const r = await fetch(endpoint, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
    const d = await r.json();
    if (d.error) throw new Error(JSON.stringify(d.error));
    return d.result;
  }, { endpoint, payload });
  return res;
}

async function login(page, baseURL, db, login, password) {
  await page.goto(`${baseURL}/web`);
  if (await page.locator('input[name="login"]').count()) {
    await page.fill('input[name="login"]', login);
    await page.fill('input[placeholder="Password"]', password);
    await page.getByRole('button', { name: 'Log in' }).click();
  }
  await rpc(page, `${baseURL}/web/session/authenticate`, { jsonrpc: '2.0', method: 'call', params: { db, login, password }, id: 1 });
}

async function ensureSaas(page, baseURL) {
  const info = await rpc(page, `${baseURL}/web/session/get_session_info`, { jsonrpc: '2.0', method: 'call', params: {}, id: 2 });
  if (!info.show_saas_menus) {
    await rpc(page, `${baseURL}/web/dataset/call_kw`, { jsonrpc: '2.0', method: 'call', params: { model: 'res.users', method: 'action_toggle_saas_menus', args: [], kwargs: {} }, id: 3 });
  }
}

async function setPlan(page, baseURL, db, planName) {
  if (planName === 'Admin') {
    await rpc(page, `${baseURL}/web/dataset/call_kw`, { jsonrpc: '2.0', method: 'call', params: { model: 'res.company', method: 'write', args: [[1], { plan_id: false }], kwargs: {} }, id: 4 });
    return;
  }
  const planIds = await rpc(page, `${baseURL}/web/dataset/call_kw`, { jsonrpc: '2.0', method: 'call', params: { model: 'salewise.plan', method: 'search', args: [[['name', '=', planName]]], kwargs: {} }, id: 5 });
  if (!planIds || !planIds.length) throw new Error(`Plan not found: ${planName}`);
  await rpc(page, `${baseURL}/web/dataset/call_kw`, { jsonrpc: '2.0', method: 'call', params: { model: 'res.company', method: 'write', args: [[1], { plan_id: planIds[0] }], kwargs: {} }, id: 6 });
}

async function fetchMenus(page, baseURL) {
  const hash = Date.now().toString();
  const menus = await page.evaluate(async ({ url }) => (await fetch(url)).json(), { url: `${baseURL}/web/webclient/load_menus/${hash}` });
  return menus;
}

function summarize(menus) {
  const ids = Object.keys(menus).filter((k) => k !== 'root');
  const root = menus.root || { children: [] };
  const appIds = Array.isArray(root.children) ? root.children.slice() : [];
  const apps = appIds.map((id) => menus[id]).filter(Boolean);
  const xmlids = new Set(ids.map((id) => menus[id]?.xmlid).filter(Boolean));
  return { count: ids.length, appCount: apps.length, xmlids };
}

async function run() {
  const { url, db, from, to } = parseArgs();
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  try {
    await login(page, url, db, 'admin', 'admin');
    await ensureSaas(page, url);

    await setPlan(page, url, db, from);
    const m1 = summarize(await fetchMenus(page, url));

    await setPlan(page, url, db, to);
    const m2 = summarize(await fetchMenus(page, url));

    // Basic expectations: Professional should have >= items than Starter
    if (to !== 'Admin' && from !== 'Admin' && m2.count < m1.count) {
      throw new Error(`Menu count did not increase: ${from}=${m1.count} -> ${to}=${m2.count}`);
    }

    // Check presence/absence of a known menu between plans (e.g., Project app subtree only in Professional or higher)
    const projectXmlId = 'salewise_menus.menu_saas_operations_project';
    const hadProject = m1.xmlids.has(projectXmlId);
    const hasProject = m2.xmlids.has(projectXmlId);
    if (from === 'Starter' && to === 'Professional' && !(hasProject && !hadProject)) {
      throw new Error(`Expected ${projectXmlId} to appear when switching ${from} -> ${to}`);
    }

    console.log(`OK: switched ${from} -> ${to} (apps ${m1.appCount}->${m2.appCount}, items ${m1.count}->${m2.count})`);
    process.exit(0);
  } catch (e) {
    console.error('FAIL:', e && e.message || e);
    process.exit(1);
  } finally {
    await browser.close();
  }
}

run();

