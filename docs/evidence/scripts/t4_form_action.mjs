#!/usr/bin/env node
import { spawn } from "node:child_process";
import { mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

const chromePath =
  process.env.CHROME_PATH ||
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const diagramId = process.env.T4_DIAGRAM_ID || "a9cb6660-0a0c-423a-9830-ec80067f459f";
const token = process.env.T4_BEARER_TOKEN;
const action = process.env.T4_FORM_ACTION;
const port = Number(process.env.T4_CHROME_PORT || 9241);
const resultPath = process.env.T4_FORM_RESULT_PATH || `docs/evidence/t4_form_${action}.json`;
const screenshotPath = process.env.T4_FORM_SCREENSHOT_PATH || "";

if (!token) throw new Error("T4_BEARER_TOKEN is required");
if (!action) throw new Error("T4_FORM_ACTION is required");

const diagramUrl = `http://ai4mde.localhost/diagram/${diagramId}`;
const profileDir = await mkdtemp(join(tmpdir(), "t4-form-chrome-"));
const chrome = spawn(
  chromePath,
  [
    "--headless=new",
    `--remote-debugging-port=${port}`,
    `--user-data-dir=${profileDir}`,
    "--no-first-run",
    "--no-default-browser-check",
    "--disable-gpu",
    "--window-size=1440,1100",
    "about:blank",
  ],
  { stdio: ["ignore", "pipe", "pipe"] },
);

async function sleep(ms) {
  await new Promise((resolve) => setTimeout(resolve, ms));
}

async function fetchJson(url, options) {
  const response = await fetch(url, options);
  if (!response.ok) throw new Error(`${url} -> ${response.status} ${await response.text()}`);
  return response.json();
}

async function waitForChrome() {
  let lastError;
  for (let i = 0; i < 80; i += 1) {
    try {
      return await fetchJson(`http://127.0.0.1:${port}/json/version`);
    } catch (error) {
      lastError = error;
      await sleep(250);
    }
  }
  throw lastError;
}

function connect(wsUrl) {
  const ws = new WebSocket(wsUrl);
  const pending = new Map();
  const events = [];
  let nextId = 1;

  ws.addEventListener("message", (event) => {
    const text =
      typeof event.data === "string"
        ? event.data
        : Buffer.from(event.data).toString("utf8");
    const message = JSON.parse(text);
    if (message.id && pending.has(message.id)) {
      const { resolve, reject } = pending.get(message.id);
      pending.delete(message.id);
      if (message.error) reject(new Error(JSON.stringify(message.error)));
      else resolve(message.result);
      return;
    }
    if (message.method) events.push(message);
  });

  return {
    events,
    open: () =>
      new Promise((resolve, reject) => {
        ws.addEventListener("open", resolve, { once: true });
        ws.addEventListener("error", reject, { once: true });
      }),
    send: (method, params = {}) =>
      new Promise((resolve, reject) => {
        const id = nextId;
        nextId += 1;
        pending.set(id, { resolve, reject });
        ws.send(JSON.stringify({ id, method, params }));
      }),
    close: () => ws.close(),
  };
}

function authStorageValue() {
  return JSON.stringify({
    state: {
      isAuthenticated: true,
      bearerToken: token,
      expires: Date.now() + 60 * 60 * 1000,
      user: { id: "1", email: "t4@example.local", username: "t4" },
      tokenData: {},
    },
    version: 0,
  });
}

async function evaluate(client, expression, awaitPromise = false) {
  const response = await client.send("Runtime.evaluate", {
    expression,
    awaitPromise,
    returnByValue: true,
  });
  if (response.exceptionDetails) {
    throw new Error(
      response.exceptionDetails.exception?.description ||
        response.exceptionDetails.text ||
        "Runtime.evaluate failed",
    );
  }
  return response.result?.value;
}

async function waitForExpression(client, expression, timeoutMs, label) {
  const start = Date.now();
  let lastError = null;
  while (Date.now() - start < timeoutMs) {
    try {
      const value = await evaluate(client, expression);
      if (value) return value;
    } catch (error) {
      lastError = error;
    }
    await sleep(250);
  }
  throw new Error(`timed out waiting for ${label}${lastError ? `: ${lastError.message}` : ""}`);
}

async function screenshot(client, path) {
  if (!path) return;
  const shot = await client.send("Page.captureScreenshot", {
    format: "png",
    captureBeyondViewport: false,
  });
  await writeFile(path, Buffer.from(shot.data, "base64"));
}

async function openNodeModal(client, className) {
  await client.send("Page.navigate", { url: diagramUrl });
  await waitForExpression(
    client,
    `document.body && document.body.innerText.includes(${JSON.stringify(className)})
      && document.querySelector(".react-flow__node") !== null`,
    45000,
    `${className} node`,
  );
  await sleep(1000);
  const rect = await evaluate(
    client,
    `(() => {
      const node = [...document.querySelectorAll(".react-flow__node")]
        .find((candidate) => candidate.innerText.includes(${JSON.stringify(className)}));
      if (!node) return null;
      const rect = node.getBoundingClientRect();
      return { x: rect.left + rect.width / 2, y: rect.top + rect.height / 2 };
    })()`,
  );
  if (!rect) throw new Error(`node not found: ${className}`);
  await client.send("Input.dispatchMouseEvent", {
    type: "mouseMoved",
    x: rect.x,
    y: rect.y,
  });
  for (const clickCount of [1, 2]) {
    await client.send("Input.dispatchMouseEvent", {
      type: "mousePressed",
      x: rect.x,
      y: rect.y,
      button: "left",
      clickCount,
    });
    await client.send("Input.dispatchMouseEvent", {
      type: "mouseReleased",
      x: rect.x,
      y: rect.y,
      button: "left",
      clickCount,
    });
    await sleep(100);
  }
  await waitForExpression(
    client,
    `document.body && document.body.innerText.includes("Edit Node")
      && document.body.innerText.includes(${JSON.stringify(className)})`,
    15000,
    `${className} edit modal`,
  );
}

async function setEnabled(client, attrName, enabled) {
  await waitForExpression(
    client,
    `document.querySelector('[data-t4-ai-config-section="${attrName}"]') !== null`,
    10000,
    `${attrName} AI section`,
  );
  const changed = await evaluate(
    client,
    `(() => {
      const section = document.querySelector('[data-t4-ai-config-section="${attrName}"]');
      const input = section && section.querySelector('input[type="checkbox"]');
      if (!input) return { ok: false, reason: "toggle input not found" };
      if (input.checked === ${enabled}) return { ok: true, changed: false, checked: input.checked };
      input.click();
      return { ok: true, changed: true, checked: input.checked };
    })()`,
  );
  if (!changed.ok) throw new Error(`toggle failed: ${JSON.stringify(changed)}`);
  await waitForExpression(
    client,
    `(() => {
      const section = document.querySelector('[data-t4-ai-config-section="${attrName}"]');
      const input = section && section.querySelector('input[type="checkbox"]');
      return !!input && input.checked === ${enabled};
    })()`,
    10000,
    `${attrName} toggle ${enabled}`,
  );
}

async function setSelect(client, selector, value) {
  await waitForExpression(
    client,
    `document.querySelector(${JSON.stringify(selector)}) !== null`,
    10000,
    `${selector}`,
  );
  await evaluate(
    client,
    `(() => {
      const select = document.querySelector(${JSON.stringify(selector)});
      const oldValue = select.value;
      const setter = Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype, "value").set;
      setter.call(select, ${JSON.stringify(value)});
      if (select._valueTracker) select._valueTracker.setValue(oldValue);
      select.dispatchEvent(new InputEvent("input", {
        bubbles: true,
        cancelable: true,
        inputType: "insertReplacementText",
        data: ${JSON.stringify(value)}
      }));
      select.dispatchEvent(new Event("input", { bubbles: true }));
      select.dispatchEvent(new Event("change", { bubbles: true }));
      const reactPropsKey = Object.keys(select).find((key) => key.startsWith("__reactProps$"));
      const reactProps = reactPropsKey ? select[reactPropsKey] : null;
      reactProps?.onInput?.({ currentTarget: select, target: select });
      reactProps?.onChange?.({ currentTarget: select, target: select });
      window.__t4_last_select_debug = {
        selector: ${JSON.stringify(selector)},
        requested: ${JSON.stringify(value)},
        oldValue,
        value: select.value,
        reactPropsKey,
        reactPropNames: reactProps ? Object.keys(reactProps) : [],
        hasOnInput: !!reactProps?.onInput,
        hasOnChange: !!reactProps?.onChange,
      };
      return select.value;
    })()`,
  );
  await waitForExpression(
    client,
    `document.querySelector(${JSON.stringify(selector)})?.value === ${JSON.stringify(value)}`,
    10000,
    `${selector}=${value}`,
  );
}

async function setAllowedValues(client, attrName, value) {
  const selector = `[data-t4-allowed-values="${attrName}"]`;
  await waitForExpression(
    client,
    `document.querySelector(${JSON.stringify(selector)}) !== null`,
    10000,
    `${attrName} allowed values input`,
  );
  await evaluate(
    client,
    `(() => {
      const input = document.querySelector(${JSON.stringify(selector)});
      const oldValue = input.value;
      const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, "value").set;
      setter.call(input, ${JSON.stringify(value)});
      if (input._valueTracker) input._valueTracker.setValue(oldValue);
      input.dispatchEvent(new InputEvent("input", {
        bubbles: true,
        cancelable: true,
        inputType: "insertReplacementText",
        data: ${JSON.stringify(value)}
      }));
      input.dispatchEvent(new Event("change", { bubbles: true }));
      const reactPropsKey = Object.keys(input).find((key) => key.startsWith("__reactProps$"));
      const reactProps = reactPropsKey ? input[reactPropsKey] : null;
      reactProps?.onInput?.({ currentTarget: input, target: input });
      reactProps?.onChange?.({ currentTarget: input, target: input });
      return input.value;
    })()`,
  );
  await waitForExpression(
    client,
    `document.querySelector(${JSON.stringify(selector)})?.value === ${JSON.stringify(value)}`,
    10000,
    `${attrName} allowed values=${value}`,
  );
}

async function waitForAttributesSaveEnabled(client) {
  const start = Date.now();
  while (Date.now() - start < 10000) {
    const enabled = await evaluate(
      client,
      `(() => {
        const buttons = [...document.querySelectorAll("button")]
          .filter((button) => button.innerText.trim() === "Save");
        return buttons.some((button) => !button.disabled);
      })()`,
    );
    if (enabled) return;
    await sleep(250);
  }
  const debug = await evaluate(
    client,
    `(() => ({
      selectDebug: window.__t4_last_select_debug ?? null,
      saveButtons: [...document.querySelectorAll("button")]
        .filter((button) => button.innerText.trim() === "Save")
        .map((button, index) => ({ index, disabled: button.disabled, text: button.innerText })),
      bodyText: document.body.innerText.slice(0, 2000),
    }))()`,
  );
  throw new Error(`timed out waiting for Attributes Save enabled: ${JSON.stringify(debug)}`);
}

async function saveAttributes(client, expectDirty = false) {
  if (expectDirty) await waitForAttributesSaveEnabled(client);
  const clicked = await evaluate(
    client,
    `(() => {
      const buttons = [...document.querySelectorAll("button")]
        .filter((button) => button.innerText.trim() === "Save");
      const button = buttons.find((candidate) => !candidate.disabled) ?? buttons[0];
      if (!button) return { ok: false, reason: "Attributes Save button not found" };
      if (button.disabled) return { ok: true, clicked: false, disabled: true };
      button.click();
      return { ok: true, clicked: true, disabled: false };
    })()`,
  );
  if (!clicked.ok) throw new Error(`save failed: ${JSON.stringify(clicked)}`);
  await sleep(1500);
  return clicked;
}

async function sectionState(client, attrName) {
  return evaluate(
    client,
    `(() => {
      const section = document.querySelector('[data-t4-ai-config-section="${attrName}"]');
      if (!section) return null;
      return {
        text: section.innerText,
        enabled: section.querySelector('input[type="checkbox"]')?.checked ?? false,
        preset: section.querySelector('[data-t4-ai-preset="${attrName}"]')?.value ?? null,
        modelProfile: section.querySelector('[data-t4-model-profile="${attrName}"]')?.value ?? null,
        allowedValues: section.querySelector('[data-t4-allowed-values="${attrName}"]')?.value ?? null,
      };
    })()`,
  );
}

async function performAction(client) {
  if (action === "bookloan_canonical") {
    await openNodeModal(client, "BookLoan");
    await setEnabled(client, "late_risk", false);
    await setEnabled(client, "late_risk", true);
    await setSelect(client, '[data-t4-ai-preset="late_risk"]', "late_return_risk");
    await setSelect(client, '[data-t4-model-profile="late_risk"]', "cheap");
    await setAllowedValues(client, "late_risk", "LOW, MEDIUM, HIGH");
    await screenshot(client, screenshotPath);
    const save = await saveAttributes(client);
    return { className: "BookLoan", attrName: "late_risk", save, section: await sectionState(client, "late_risk") };
  }
  if (action === "bookloan_values_safe_risky") {
    await openNodeModal(client, "BookLoan");
    await setEnabled(client, "late_risk", true);
    await setAllowedValues(client, "late_risk", "SAFE, RISKY");
    await screenshot(client, screenshotPath);
    const save = await saveAttributes(client, true);
    return { className: "BookLoan", attrName: "late_risk", save, section: await sectionState(client, "late_risk") };
  }
  if (action === "bookloan_model_strong") {
    await openNodeModal(client, "BookLoan");
    await setEnabled(client, "late_risk", true);
    await setSelect(client, '[data-t4-model-profile="late_risk"]', "strong");
    const save = await saveAttributes(client, true);
    return { className: "BookLoan", attrName: "late_risk", save, section: await sectionState(client, "late_risk") };
  }
  if (action === "bookloan_restore_canonical") {
    await openNodeModal(client, "BookLoan");
    await setEnabled(client, "late_risk", true);
    await setSelect(client, '[data-t4-ai-preset="late_risk"]', "late_return_risk");
    await setSelect(client, '[data-t4-model-profile="late_risk"]', "cheap");
    await setAllowedValues(client, "late_risk", "LOW, MEDIUM, HIGH");
    await screenshot(client, screenshotPath);
    const save = await saveAttributes(client, true);
    return { className: "BookLoan", attrName: "late_risk", save, section: await sectionState(client, "late_risk") };
  }
  if (action === "bookloan_toggle_off") {
    await openNodeModal(client, "BookLoan");
    await setEnabled(client, "late_risk", false);
    await screenshot(client, screenshotPath);
    const save = await saveAttributes(client, true);
    return { className: "BookLoan", attrName: "late_risk", save, section: await sectionState(client, "late_risk") };
  }
  if (action === "bookloan_enable_after_reset") {
    await openNodeModal(client, "BookLoan");
    await screenshot(client, screenshotPath);
    await setEnabled(client, "late_risk", true);
    await setSelect(client, '[data-t4-ai-preset="late_risk"]', "late_return_risk");
    await setSelect(client, '[data-t4-model-profile="late_risk"]', "cheap");
    await setAllowedValues(client, "late_risk", "LOW, MEDIUM, HIGH");
    const save = await saveAttributes(client, true);
    return { className: "BookLoan", attrName: "late_risk", save, section: await sectionState(client, "late_risk") };
  }
  if (action === "customer_enable_reading_plan") {
    await openNodeModal(client, "Customer");
    await setEnabled(client, "reading_plan", true);
    await setSelect(client, '[data-t4-ai-preset="reading_plan"]', "reading_plan");
    await setSelect(client, '[data-t4-model-profile="reading_plan"]', "strong");
    await screenshot(client, screenshotPath);
    const save = await saveAttributes(client, true);
    return { className: "Customer", attrName: "reading_plan", save, section: await sectionState(client, "reading_plan") };
  }
  throw new Error(`unknown T4_FORM_ACTION: ${action}`);
}

let client;
try {
  await waitForChrome();
  const page = await fetchJson(
    `http://127.0.0.1:${port}/json/new?${encodeURIComponent("about:blank")}`,
    { method: "PUT" },
  );
  client = connect(page.webSocketDebuggerUrl);
  await client.open();
  await client.send("Runtime.enable");
  await client.send("Page.enable");
  await client.send("Network.enable");
  await client.send("Network.setCookie", {
    name: "key",
    value: token,
    url: "http://api.ai4mde.localhost/",
    path: "/",
  });
  await client.send("Page.addScriptToEvaluateOnNewDocument", {
    source: `localStorage.setItem("auth-storage", ${JSON.stringify(authStorageValue())});`,
  });

  const actionResult = await performAction(client);
  const result = {
    action,
    diagramUrl,
    screenshotPath: screenshotPath || null,
    ...actionResult,
  };
  await writeFile(resultPath, JSON.stringify(result, null, 2) + "\n");
  console.log(JSON.stringify(result, null, 2));
} finally {
  if (client) client.close();
  chrome.kill("SIGTERM");
  await Promise.race([
    new Promise((resolve) => chrome.once("exit", resolve)),
    sleep(2000),
  ]);
  await rm(profileDir, { recursive: true, force: true, maxRetries: 3 }).catch(() => {});
}
