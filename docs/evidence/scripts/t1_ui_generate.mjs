#!/usr/bin/env node
import { spawn } from "node:child_process";
import { mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

const chromePath =
  process.env.CHROME_PATH ||
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const systemId = process.env.T1_SYSTEM_ID;
const prototypeName = process.env.T1_PROTOTYPE_NAME || "LibraryT1A";
const token = process.env.T1_BEARER_TOKEN;
const resultPath = process.env.T1_RESULT_PATH || "docs/evidence/t1_ui_result.json";
const metadataPath =
  process.env.T1_METADATA_PATH || "docs/evidence/t1_metadata_from_ui.json";
const screenshotPath =
  process.env.T1_SCREENSHOT_PATH || "docs/evidence/t1_ui_create_done.png";
const port = Number(process.env.T1_CHROME_PORT || 9224);
const generationTimeoutMs = Number(process.env.T1_GENERATION_TIMEOUT_MS || 420000);

if (!systemId) throw new Error("T1_SYSTEM_ID is required");
if (!token) throw new Error("T1_BEARER_TOKEN is required");

const targetUrl = `http://ai4mde.localhost/systems/${systemId}/prototypes`;
const apiBase = "http://api.ai4mde.localhost:80/api/v1";

const profileDir = await mkdtemp(join(tmpdir(), "t1-chrome-"));
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
      user: { id: "1", email: "t1@example.local", username: "t1" },
      tokenData: {},
    },
    version: 0,
  });
}

async function evaluate(client, expression, awaitPromise = false) {
  return client.send("Runtime.evaluate", {
    expression,
    awaitPromise,
    returnByValue: true,
  });
}

async function waitForExpression(client, expression, timeoutMs, label) {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    const result = await evaluate(client, expression);
    if (result.result?.value) return result.result.value;
    await sleep(250);
  }
  throw new Error(`timed out waiting for ${label}`);
}

function consoleProblems(events) {
  return events
    .map((event) => {
      if (event.method === "Runtime.consoleAPICalled" && event.params.type === "error") {
        return {
          source: "console",
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
let result = null;
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

  const responsePromise = new Promise((resolve, reject) => {
    const started = Date.now();
    let requestId = null;
    let responsePayload = null;
    const timer = setInterval(async () => {
      const responseEvent = client.events.find(
        (event) =>
          event.method === "Network.responseReceived" &&
          event.params.response.url.includes("/api/v1/generator/prototypes/?database_prototype_name=") &&
          event.params.requestId,
      );
      if (responseEvent && !requestId) {
        requestId = responseEvent.params.requestId;
        responsePayload = {
          status: responseEvent.params.response.status,
          url: responseEvent.params.response.url,
        };
      }
      const loaded = requestId
        ? client.events.some(
            (event) =>
              event.method === "Network.loadingFinished" &&
              event.params.requestId === requestId,
          )
        : false;
      if (requestId && loaded) {
        clearInterval(timer);
        try {
          const body = await client.send("Network.getResponseBody", {
            requestId,
          });
          resolve({
            ...responsePayload,
            body: body.body,
          });
        } catch (error) {
          reject(error);
        }
      } else if (Date.now() - started > generationTimeoutMs) {
        clearInterval(timer);
        reject(new Error("timed out waiting for prototype POST response"));
      }
    }, 500);
  });

  await client.send("Page.navigate", { url: targetUrl });
  await waitForExpression(
    client,
    `document.body && document.body.innerText.includes("Generate new prototype")`,
    30000,
    "prototypes page",
  );
  await sleep(5000);
  await evaluate(
    client,
    `[...document.querySelectorAll("button")]
      .find((button) => button.innerText.includes("Generate new prototype"))
      .click()`,
  );
  await waitForExpression(
    client,
    `document.querySelector('input[name="name"]') !== null`,
    10000,
    "create prototype modal",
  );
  const modalText = (
    await evaluate(client, `document.body ? document.body.innerText : ""`)
  ).result.value;
  if (!modalText.includes("librarian")) {
    throw new Error("default interface selection does not visibly include librarian");
  }

  await evaluate(
    client,
    `(() => {
      const input = document.querySelector('input[name="name"]');
      const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, "value").set;
      setter.call(input, ${JSON.stringify(prototypeName)});
      input.dispatchEvent(new Event("input", { bubbles: true }));
      input.dispatchEvent(new Event("change", { bubbles: true }));
      return input.value;
    })()`,
  );

  const startTime = new Date();
  await evaluate(
    client,
    `[...document.querySelectorAll("button")]
      .filter((button) => button.innerText.trim() === "Create")
      .at(-1)
      .click()`,
  );
  const postResponse = await responsePromise;
  const endTime = new Date();
  let responseJson = {};
  try {
    responseJson = JSON.parse(postResponse.body);
  } catch {
    responseJson = { raw: postResponse.body };
  }
  if (postResponse.status !== 200) {
    throw new Error(`prototype POST failed: ${postResponse.status} ${postResponse.body}`);
  }

  const prototypeId = responseJson.id;
  if (!prototypeId) throw new Error(`prototype id missing from response: ${postResponse.body}`);
  const metadata = await fetchJson(`${apiBase}/generator/prototypes/${prototypeId}/meta/`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  await writeFile(metadataPath, JSON.stringify(metadata, null, 2) + "\n");

  const pageInfo = await evaluate(
    client,
    `({ href: location.href, title: document.title, bodyText: document.body.innerText.slice(0, 1200) })`,
  );
  if (screenshotPath) {
    const shot = await client.send("Page.captureScreenshot", {
      format: "png",
      captureBeyondViewport: false,
    });
    await writeFile(screenshotPath, Buffer.from(shot.data, "base64"));
  }

  result = {
    targetUrl,
    prototypeName,
    prototypeId,
    systemId,
    postStatus: postResponse.status,
    generationStartedAt: startTime.toISOString(),
    generationFinishedAt: endTime.toISOString(),
    generationDurationSeconds: (endTime - startTime) / 1000,
    metadataPath,
    screenshotPath,
    page: pageInfo.result.value,
    defaultInterfaceObservation: "librarian visible before submit; selector was not changed",
    consoleErrors: consoleProblems(client.events),
  };
  await writeFile(resultPath, JSON.stringify(result, null, 2) + "\n");
  console.log(JSON.stringify(result, null, 2));
  if (result.consoleErrors.length) process.exitCode = 1;
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
