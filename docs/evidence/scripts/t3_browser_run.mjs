#!/usr/bin/env node
import { spawn } from "node:child_process";
import { mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

const chromePath =
  process.env.CHROME_PATH ||
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const systemId = process.env.T3_SYSTEM_ID;
const prototypeName = process.env.T3_PROTOTYPE_NAME || "LibraryT3A";
const prototypeId = process.env.T3_PROTOTYPE_ID;
const token = process.env.T3_BEARER_TOKEN;
const port = Number(process.env.T3_CHROME_PORT || 9234);
const resultPath = process.env.T3_RUN_RESULT_PATH || "docs/evidence/t3_run_check.json";
const screenshotPath =
  process.env.T3_RUN_SCREENSHOT_PATH || "docs/evidence/t3_browser_run_login.png";

if (!systemId) throw new Error("T3_SYSTEM_ID is required");
if (!prototypeId) throw new Error("T3_PROTOTYPE_ID is required");
if (!token) throw new Error("T3_BEARER_TOKEN is required");

const studioUrl = `http://ai4mde.localhost/systems/${systemId}/prototypes`;
const prototypeUrl = "http://prototype.ai4mde.localhost";
const profileDir = await mkdtemp(join(tmpdir(), "t3-run-chrome-"));
const chrome = spawn(
  chromePath,
  [
    "--headless=new",
    `--remote-debugging-port=${port}`,
    `--user-data-dir=${profileDir}`,
    "--no-first-run",
    "--no-default-browser-check",
    "--disable-gpu",
    "--window-size=1440,1000",
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
      user: { id: "1", email: "t3@example.local", username: "t3" },
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
  while (Date.now() - start < timeoutMs) {
    if (await evaluate(client, expression).catch(() => false)) return true;
    await sleep(250);
  }
  throw new Error(`timed out waiting for ${label}`);
}

async function screenshot(client, path) {
  const shot = await client.send("Page.captureScreenshot", {
    format: "png",
    captureBeyondViewport: false,
  });
  await writeFile(path, Buffer.from(shot.data, "base64"));
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

  await client.send("Page.navigate", { url: studioUrl });
  await waitForExpression(
    client,
    `document.body && document.body.innerText.includes(${JSON.stringify(prototypeName)})`,
    30000,
    "Studio prototypes page",
  );
  await waitForExpression(
    client,
    `(() => {
      const row = [...document.querySelectorAll("tr")]
        .find((candidate) => candidate.innerText.includes(${JSON.stringify(prototypeName)}));
      return !!row && [...row.querySelectorAll("button")]
        .some((button) => ["Run", "Kill"].includes(button.innerText.trim()));
    })()`,
    30000,
    "Run/Kill button",
  );

  const preRunState = await evaluate(
    client,
    `(() => {
      const row = [...document.querySelectorAll("tr")]
        .find((candidate) => candidate.innerText.includes(${JSON.stringify(prototypeName)}));
      return row ? row.innerText : "";
    })()`,
  );
  const killClicked = await evaluate(
    client,
    `(() => {
      const row = [...document.querySelectorAll("tr")]
        .find((candidate) => candidate.innerText.includes(${JSON.stringify(prototypeName)}));
      const button = row && [...row.querySelectorAll("button")]
        .find((candidate) => candidate.innerText.trim() === "Kill");
      if (!button) return false;
      button.click();
      return true;
    })()`,
  );
  if (killClicked) await sleep(7000);
  const runClicked = await evaluate(
    client,
    `(() => {
      const row = [...document.querySelectorAll("tr")]
        .find((candidate) => candidate.innerText.includes(${JSON.stringify(prototypeName)}));
      const button = row && [...row.querySelectorAll("button")]
        .find((candidate) => candidate.innerText.trim() === "Run");
      if (!button) return false;
      button.click();
      return true;
    })()`,
  );
  if (!runClicked) throw new Error(`Run button not clicked for ${prototypeName}`);
  await sleep(8000);

  const active = await evaluate(
    client,
    `fetch("http://api.ai4mde.localhost:80/api/v1/generator/prototypes/active_prototype/", {
      headers: { Authorization: "Bearer ${token}" },
      credentials: "include",
    }).then(async (response) => {
      if (!response.ok) throw new Error(response.status + " " + await response.text());
      return response.json();
    })`,
    true,
  );
  if (!active.running || active.prototype_id !== prototypeId) {
    throw new Error(`active prototype mismatch: ${JSON.stringify(active)}`);
  }

  await client.send("Page.navigate", { url: prototypeUrl });
  await waitForExpression(
    client,
    `document.body && document.body.innerText.includes(${JSON.stringify(`${prototypeName} prototype`)})
      && document.querySelector('input#is_member') !== null`,
    45000,
    "LibraryT3A login page with member radio",
  );
  const loginPage = await evaluate(
    client,
    `({
      href: location.href,
      title: document.title,
      hasLibraryT3A: document.body.innerText.includes(${JSON.stringify(`${prototypeName} prototype`)}),
      hasMemberRadio: document.querySelector('input#is_member') !== null,
      bodyText: document.body.innerText.slice(0, 800),
    })`,
  );
  await screenshot(client, screenshotPath);

  const result = {
    studioUrl,
    prototypeUrl,
    prototypeName,
    prototypeId,
    preRunState,
    killClicked,
    runClicked,
    active,
    loginPage,
    screenshotPath,
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
