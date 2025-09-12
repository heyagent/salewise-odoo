#!/usr/bin/env node
/**
 * Playwright UI test for plan switching via the user menu wizard.
 * - Log in as admin
 * - Ensure SaaS mode enabled (via user menu item 'Switch App' if present; fallback to RPC toggle)
 * - Open user menu, click 'Change Plan'
 * - In the modal, select destination plan and Apply
 * - Wait for reload and verify menus changed (count and a known menu XMLID)
 */

const { chromium } = require('playwright');

function args() {
  const out = { url: 'http://localhost:8069', db: 'salewise', from: 'Starter', to: 'Professional' };
  for (const a of process.argv.slice(2)) {
    const [k, v] = a.startsWith('--') ? a.slice(2).split('=') : [null, null];
    if (!k) continue;
    out[k] = v;
  }
  return out;
}

async function login(page, baseURL, db, login, password) {
  await page.goto(`${baseURL}/web`);
  if (await page.locator('input[name="login"]').count()) {
    await page.fill('input[name="login"]', login);
    await page.fill('input[placeholder="Password"]', password);
    await page.getByRole('button', { name: 'Log in' }).click();
  }
  // Ensure session (reduces surprises)
  await page.evaluate(async (baseURL, db, login, password) => {
    const payload = { jsonrpc: '2.0', method: 'call', params: { db, login, password }, id: 1 };
    await fetch(`${baseURL}/web/session/authenticate`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
  }, baseURL, db, login, password);
}

async function ensureSaas(page) {
  // Try UI toggle first (user menu item 'Switch App'). If not found, fallback to RPC toggle.
  try {
    await page.getByRole('button', { name: /user|preferences|menu/i }).first().click({ timeout: 1000 });
  } catch {}
  const hasSwitch = await page.getByRole('menuitem', { name: /Switch App/i }).count().catch(() => 0);
  if (hasSwitch) {
    await page.getByRole('menuitem', { name: /Switch App/i }).click();
    return;
  }
  // Fallback RPC
  await page.evaluate(async () => {
    await fetch('/web/dataset/call_kw', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ jsonrpc: '2.0', method: 'call', params: { model: 'res.users', method: 'action_toggle_saas_menus', args: [], kwargs: {} }, id: 2 }) });
  });
}

async function fetchMenus(page, baseURL) {
  const hash = Date.now().toString();
  return await page.evaluate(async (url) => (await fetch(url)).json(), `${baseURL}/web/webclient/load_menus/${hash}`);
}

function summarize(menus) {
  const ids = Object.keys(menus).filter((k) => k !== 'root');
  const xmlids = new Set(ids.map((id) => menus[id]?.xmlid).filter(Boolean));
  const root = menus.root || { children: [] };
  const appCount = Array.isArray(root.children) ? root.children.length : 0;
  return { count: ids.length, appCount, xmlids };
}

async function openChangePlan(page) {
  // Open user menu and click Change Plan
  // Try to click the user menu button (varies by DOM), then the menu item.
  // Attempt a few strategies for robustness.
  const userButtons = [
    () => page.getByRole('button', { name: /User|Preferences|Menu|Log out/i }).first().click({ timeout: 1000 }),
    () => page.locator('button,o-dropdown,div[role="button"]').filter({ hasText: /Preferences|Log out|Shortcuts/i }).first().click({ timeout: 1000 }),
  ];
  for (const fn of userButtons) { try { await fn(); break; } catch {} }
  await page.getByRole('menuitem', { name: /Change Plan/i }).click();
  await page.getByRole('dialog', { name: /Change Plan/i }).waitFor({ state: 'visible' });
}

async function pickPlanAndApply(page, planName) {
  const dialog = page.getByRole('dialog', { name: /Change Plan/i });
  // Click the Plan many2one and type the desired plan; press Enter to select the first match
  await dialog.locator('div[name="plan_id"] input').click();
  await dialog.locator('div[name="plan_id"] input').fill('');
  await dialog.locator('div[name="plan_id"] input').type(planName);
  await page.keyboard.press('Enter');
  // Apply
  await dialog.getByRole('button', { name: /Apply/i }).click();
  // Wait for reload to complete by checking that the web menus endpoint returns JSON
  await page.waitForLoadState('load');
}

(async () => {
  const { url, db, from, to } = args();
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  try {
    await login(page, url, db, 'admin', 'admin');
    await ensureSaas(page);

    // Set starting plan via UI if needed
    await openChangePlan(page);
    await pickPlanAndApply(page, from);
    const before = summarize(await fetchMenus(page, url));

    // Switch to destination plan via UI
    await openChangePlan(page);
    await pickPlanAndApply(page, to);
    const after = summarize(await fetchMenus(page, url));

    if (to !== 'Admin' && from !== 'Admin' && after.count < before.count) {
      throw new Error(`Menu count did not increase: ${from}=${before.count} -> ${to}=${after.count}`);
    }
    const projectXmlId = 'salewise_menus.menu_saas_operations_project';
    if (from === 'Starter' && to === 'Professional' && !(after.xmlids.has(projectXmlId) && !before.xmlids.has(projectXmlId))) {
      throw new Error(`Expected ${projectXmlId} to appear when switching ${from} -> ${to}`);
    }
    console.log(`OK (UI): switched ${from} -> ${to} apps ${before.appCount}->${after.appCount}, items ${before.count}->${after.count}`);
    process.exit(0);
  } catch (e) {
    console.error('FAIL (UI):', e && e.message || e);
    process.exit(1);
  } finally {
    await browser.close();
  }
})();

