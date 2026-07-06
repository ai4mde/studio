#!/usr/bin/env node
import { spawn } from "node:child_process";
import { mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

const chromePath =
  process.env.CHROME_PATH ||
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const targetUrl = process.env.T0_TARGET_URL;
const token = process.env.T0_BEARER_TOKEN;
const screenshotPath = process.env.T0_SCREENSHOT_PATH;
const waitMs = Number(process.env.T0_WAIT_MS || 8000);
const port = Number(process.env.T0_CHROME_PORT || 9223);

if (!targetUrl) {
  throw new Error("T0_TARGET_URL is required");
}
if (!token) {
  throw new Error("T0_BEARER_TOKEN is required");
}

const profileDir = await mkdtemp(join(tmpdir(), "t0-chrome-"));
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

const chromeOutput = [];
chrome.stdout.on("data", (chunk) => chromeOutput.push(String(chunk)));
chrome.stderr.on("data", (chunk) => chromeOutput.push(String(chunk)));

async function sleep(ms) {
  await new Promise((resolve) => setTimeout(resolve, ms));
}

async function fetchJson(url, options) {
  const response = await fetch(url, options);
  if (!response.ok) {
    throw new Error(`${url} -> ${response.status} ${await response.text()}`);
  }
  return response.json();
}

async function waitForChrome() {
  const versionUrl = `http://127.0.0.1:${port}/json/version`;
  let lastError;
  for (let i = 0; i < 80; i += 1) {
    try {
      return await fetchJson(versionUrl);
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
      if (message.error) {
        reject(new Error(JSON.stringify(message.error)));
      } else {
        resolve(message.result);
      }
      return;
    }
    if (message.method) {
      events.push(message);
    }
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
      user: { id: "1", email: "t0@example.local", username: "t0" },
      tokenData: {},
    },
    version: 0,
  });
}

function collectProblems(events) {
  return events
    .map((event) => {
      if (event.method === "Runtime.consoleAPICalled") {
        const type = event.params.type;
        if (type !== "error") return null;
        return {
          source: "console",
          type,
          text: event.params.args
            .map((arg) => arg.value ?? arg.description ?? arg.type)
            .join(" "),
        };
      }
      if (event.method === "Runtime.exceptionThrown") {
        return {
          source: "exception",
          text: event.params.exceptionDetails?.text,
          description: event.params.exceptionDetails?.exception?.description,
        };
      }
      if (event.method === "Log.entryAdded" && event.params.entry.level === "error") {
        return {
          source: "log",
          text: event.params.entry.text,
          url: event.params.entry.url,
        };
      }
      return null;
    })
    .filter(Boolean);
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
  await client.send("Log.enable");
  await client.send("Page.enable");
  await client.send("Network.enable");
  await client.send("Network.setCookie", {
    name: "key",
    value: token,
    url: "http://api.ai4mde.localhost/",
    path: "/",
  });
  await client.send("Page.addScriptToEvaluateOnNewDocument", {
    source: `localStorage.setItem("auth-storage", ${JSON.stringify(
      authStorageValue(),
    )});`,
  });
  await client.send("Page.navigate", { url: targetUrl });
  await sleep(waitMs);

  const bodyText = await client.send("Runtime.evaluate", {
    expression: "document.body ? document.body.innerText.slice(0, 1000) : ''",
    returnByValue: true,
  });
  const pageInfo = await client.send("Runtime.evaluate", {
    expression: "({ href: location.href, title: document.title })",
    returnByValue: true,
  });
  if (screenshotPath) {
    const shot = await client.send("Page.captureScreenshot", {
      format: "png",
      captureBeyondViewport: false,
    });
    await writeFile(screenshotPath, Buffer.from(shot.data, "base64"));
  }

  const problems = collectProblems(client.events);
  const result = {
    targetUrl,
    page: pageInfo.result.value,
    bodyText: bodyText.result.value,
    consoleErrorCount: problems.length,
    consoleErrors: problems,
    screenshotPath: screenshotPath || null,
  };
  console.log(JSON.stringify(result, null, 2));
  if (problems.length > 0) {
    process.exitCode = 1;
  }
} finally {
  if (client) client.close();
  chrome.kill("SIGTERM");
  await Promise.race([
    new Promise((resolve) => chrome.once("exit", resolve)),
    sleep(2000),
  ]);
  await rm(profileDir, { recursive: true, force: true, maxRetries: 3 }).catch(
    () => {},
  );
  if (process.exitCode) {
    console.error(chromeOutput.join(""));
  }
}
