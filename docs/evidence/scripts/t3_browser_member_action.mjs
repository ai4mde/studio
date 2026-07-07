#!/usr/bin/env node
import { spawn } from "node:child_process";
import { mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

const chromePath =
  process.env.CHROME_PATH ||
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const prototypeName = process.env.T3_PROTOTYPE_NAME || "LibraryT3A";
const port = Number(process.env.T3_CHROME_PORT || 9235);
const resultPath =
  process.env.T3_ACTION_RESULT_PATH || "docs/evidence/t3_browser_member_action_result.json";
const loginScreenshotPath =
  process.env.T3_ACTION_LOGIN_SCREENSHOT || "docs/evidence/t3_browser_member_login.png";
const buttonScreenshotPath =
  process.env.T3_ACTION_BUTTON_SCREENSHOT || "docs/evidence/t3_browser_member_button.png";
const resultScreenshotPath =
  process.env.T3_ACTION_RESULT_SCREENSHOT || "docs/evidence/t3_browser_member_result.png";
const refreshedScreenshotPath =
  process.env.T3_ACTION_REFRESHED_SCREENSHOT ||
  "docs/evidence/t3_browser_member_refreshed_result.png";
const prototypeUrl = "http://prototype.ai4mde.localhost";

const profileDir = await mkdtemp(join(tmpdir(), "t3-action-chrome-"));
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
    }
  });
  return {
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

async function aliceState(client) {
  return evaluate(
    client,
    `(() => {
      const rows = [...document.querySelectorAll("table tr")].slice(1);
      const row = rows.find((candidate) => candidate.cells[0]?.innerText.trim() === "alice");
      if (!row) return { hasAlice: false };
      const submit = [...row.querySelectorAll('input[type="submit"]')]
        .find((input) => input.value === "generate_reading_plan");
      return {
        hasAlice: true,
        name: row.cells[0]?.innerText.trim() || "",
        email: row.cells[1]?.innerText.trim() || "",
        readingPlan: row.cells[2]?.innerText.trim() || "",
        hasGenerateButton: !!submit,
        rowText: row.innerText,
      };
    })()`,
  );
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

  await client.send("Page.navigate", { url: prototypeUrl });
  await waitForExpression(
    client,
    `document.body && document.body.innerText.includes(${JSON.stringify(`${prototypeName} prototype`)})`,
    30000,
    "prototype login page",
  );
  await screenshot(client, loginScreenshotPath);

  await evaluate(
    client,
    `(() => {
      const setInput = (selector, value) => {
        const input = document.querySelector(selector);
        const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, "value").set;
        setter.call(input, value);
        input.dispatchEvent(new Event("input", { bubbles: true }));
        input.dispatchEvent(new Event("change", { bubbles: true }));
      };
      setInput('input[name="username"]', "demo_member");
      setInput('input[name="password"]', "ai4mde-demo");
      const submit = [...document.querySelectorAll('input[type="submit"]')]
        .find((input) => input.value === "Login");
      submit.click();
      return true;
    })()`,
  );
  await waitForExpression(
    client,
    `location.pathname.startsWith("/member") && document.body.innerText.includes("Member")`,
    20000,
    "member home after login",
  );

  await evaluate(
    client,
    `([...document.querySelectorAll("a")]
      .find((link) => link.innerText.trim() === "customers")).click()`,
  );
  await waitForExpression(
    client,
    `location.pathname.includes("render_member_customers")
      && document.body.innerText.includes("reading_plan")
      && document.querySelector('input[value="generate_reading_plan"]') !== null`,
    20000,
    "member customers page",
  );
  const beforeClick = await aliceState(client);
  if (!beforeClick.hasAlice || !beforeClick.hasGenerateButton) {
    throw new Error(`alice row/button missing before click: ${JSON.stringify(beforeClick)}`);
  }
  await screenshot(client, buttonScreenshotPath);

  await evaluate(
    client,
    `(() => {
      const row = [...document.querySelectorAll("table tr")]
        .slice(1)
        .find((candidate) => candidate.cells[0]?.innerText.trim() === "alice");
      const submit = [...row.querySelectorAll('input[type="submit"]')]
        .find((input) => input.value === "generate_reading_plan");
      submit.click();
      return true;
    })()`,
  );
  await waitForExpression(
    client,
    `location.pathname.includes("render_member_customers")
      && document.body.innerText.includes("reading_plan")`,
    30000,
    "member customers response page",
  );
  const responsePage = await aliceState(client);
  await screenshot(client, resultScreenshotPath);

  let refreshedPage = null;
  if (!responsePage.readingPlan) {
    await client.send("Page.navigate", { url: `${prototypeUrl}/member/render_member_customers` });
    await waitForExpression(
      client,
      `location.pathname.includes("render_member_customers")
        && document.body.innerText.includes("reading_plan")`,
      20000,
      "member customers refreshed page",
    );
    refreshedPage = await aliceState(client);
    await screenshot(client, refreshedScreenshotPath);
  }

  const result = {
    prototypeUrl,
    prototypeName,
    beforeClick,
    responsePage,
    responsePageHasSummary: !!responsePage.readingPlan,
    refreshedPage,
    screenshots: {
      login: loginScreenshotPath,
      button: buttonScreenshotPath,
      response: resultScreenshotPath,
      refreshed: refreshedPage ? refreshedScreenshotPath : null,
    },
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
