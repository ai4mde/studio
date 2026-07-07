#!/usr/bin/env node
import { spawn } from "node:child_process";
import { mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

const chromePath =
  process.env.CHROME_PATH ||
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const systemId = process.env.T4_SYSTEM_ID;
const token = process.env.T4_BEARER_TOKEN;
const port = Number(process.env.T4_CHROME_PORT || 9240);
const defaultName = process.env.T4_G0_DEFAULT_NAME || "LibraryT4G0Default";
const reselectName = process.env.T4_G0_RESELECT_NAME || "LibraryT4G0Reselect";
const resultPath =
  process.env.T4_G0_RESULT_PATH || "docs/evidence/t4_g0_selector_shape.json";
const defaultShapePath =
  process.env.T4_G0_DEFAULT_SHAPE_PATH || "docs/evidence/t4_g0_default_shape.json";
const reselectShapePath =
  process.env.T4_G0_RESELECT_SHAPE_PATH || "docs/evidence/t4_g0_reselect_shape.json";

if (!systemId) throw new Error("T4_SYSTEM_ID is required");
if (!token) throw new Error("T4_BEARER_TOKEN is required");

const targetUrl = `http://ai4mde.localhost/systems/${systemId}/prototypes`;
const profileDir = await mkdtemp(join(tmpdir(), "t4-g0-chrome-"));
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

function validateWrappedInterfaces(interfaces, label) {
  if (!Array.isArray(interfaces) || interfaces.length < 2) {
    throw new Error(`${label} interfaces must contain at least two wrapped options`);
  }
  for (const entry of interfaces) {
    if (!entry || typeof entry !== "object" || !("label" in entry) || !("value" in entry)) {
      throw new Error(`${label} interface entry is not {label,value}: ${JSON.stringify(entry)}`);
    }
    if (!entry.value || typeof entry.value !== "object" || !entry.value.id || !entry.value.name) {
      throw new Error(`${label} interface value is not a full interface object: ${JSON.stringify(entry)}`);
    }
  }
}

async function uniquePrototypeName(client, baseName) {
  const existing = await evaluate(
    client,
    `fetch("http://api.ai4mde.localhost:80/api/v1/generator/prototypes/?system=${systemId}", {
      headers: { Authorization: "Bearer ${token}" },
      credentials: "include",
    }).then(async (response) => {
      if (!response.ok) throw new Error(response.status + " " + await response.text());
      return response.json();
    })`,
    true,
  );
  const names = new Set(existing.map((prototype) => prototype.name));
  if (!names.has(baseName)) return baseName;
  for (let i = 2; i < 100; i += 1) {
    const candidate = `${baseName}${i}`;
    if (!names.has(candidate)) return candidate;
  }
  throw new Error(`could not find unique prototype name for ${baseName}`);
}

async function openCreateModal(client) {
  await client.send("Page.navigate", { url: targetUrl });
  await waitForExpression(
    client,
    `document.body && document.body.innerText.includes("Generate new prototype")`,
    30000,
    "prototypes page",
  );
  await sleep(1500);
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
  await waitForExpression(
    client,
    `document.body.innerText.includes("librarian") && document.body.innerText.includes("member")`,
    10000,
    "default interface chips",
  );
}

async function setPrototypeName(client, prototypeName) {
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
}

async function reselectInterfaces(client) {
  const clearSteps = [];
  for (let i = 0; i < 5; i += 1) {
    const clearResult = await evaluate(
      client,
      `(() => {
        const container = document.querySelectorAll(".css-b62m3t-container")[0];
        if (!container) return { ok: false, reason: "interfaces select container not found" };
        const before = container.innerText;
        const control = container.querySelector('[aria-label^="Remove "]');
        if (!control) return { ok: true, removed: false, before, after: container.innerText };
        control.dispatchEvent(new MouseEvent("mousedown", { bubbles: true, cancelable: true, button: 0 }));
        control.dispatchEvent(new MouseEvent("mouseup", { bubbles: true, cancelable: true, button: 0 }));
        control.dispatchEvent(new MouseEvent("click", { bubbles: true, cancelable: true, button: 0 }));
        return { ok: true, removed: true, before, after: container.innerText };
      })()`,
    );
    clearSteps.push(clearResult);
    if (!clearResult.ok) {
      throw new Error(`could not clear selected interfaces: ${JSON.stringify(clearSteps)}`);
    }
    await sleep(250);
    const remainingText = await evaluate(
      client,
      `(() => {
        const container = document.querySelectorAll(".css-b62m3t-container")[0];
        return container ? container.innerText : "";
      })()`,
    );
    if (!remainingText.includes("librarian") && !remainingText.includes("member")) break;
  }
  const clearedText = await evaluate(
    client,
    `(() => {
      const container = document.querySelectorAll(".css-b62m3t-container")[0];
      return container ? container.innerText : "";
    })()`,
  );
  if (clearedText.includes("librarian") || clearedText.includes("member")) {
    throw new Error(`could not clear selected interfaces: ${JSON.stringify({ clearSteps, clearedText })}`);
  }

  for (const label of ["librarian", "member"]) {
    const focused = await evaluate(
      client,
      `(() => {
        const container = document.querySelectorAll(".css-b62m3t-container")[0];
        if (!container) return false;
        const input = container.querySelector('input[id^="react-select"][type="text"]');
        if (!input) return false;
        input.focus();
        container.dispatchEvent(new MouseEvent("mousedown", { bubbles: true, cancelable: true, button: 0 }));
        container.dispatchEvent(new MouseEvent("mouseup", { bubbles: true, cancelable: true, button: 0 }));
        container.dispatchEvent(new MouseEvent("click", { bubbles: true, cancelable: true, button: 0 }));
        return true;
      })()`,
    );
    if (!focused) throw new Error(`could not focus interface select for ${label}`);
    await client.send("Input.insertText", { text: label });
    await sleep(500);
    await client.send("Input.dispatchKeyEvent", {
      type: "keyDown",
      key: "Enter",
      code: "Enter",
      windowsVirtualKeyCode: 13,
      nativeVirtualKeyCode: 13,
    });
    await client.send("Input.dispatchKeyEvent", {
      type: "keyUp",
      key: "Enter",
      code: "Enter",
      windowsVirtualKeyCode: 13,
      nativeVirtualKeyCode: 13,
    });
    await waitForExpression(
      client,
      `(() => {
        const container = document.querySelectorAll(".css-b62m3t-container")[0];
        return container ? container.innerText.includes(${JSON.stringify(label)}) : false;
      })()`,
      10000,
      `${label} reselected`,
    );
  }

  return evaluate(
    client,
    `(() => {
      const containers = [...document.querySelectorAll(".css-b62m3t-container")];
      const container = containers.find((candidate) =>
        candidate.innerText.includes("librarian") && candidate.innerText.includes("member")
      );
      return container ? container.innerText : "";
    })()`,
  );
}

function waitForPrototypePost(client, generationTimeoutMs = 420000) {
  return new Promise((resolve, reject) => {
    const started = Date.now();
    let requestId = null;
    let requestPayload = null;
    let responsePayload = null;
    const timer = setInterval(async () => {
      const requestEvent = client.events.find(
        (event) =>
          event.method === "Network.requestWillBeSent" &&
          event.params.request.method === "POST" &&
          event.params.request.url.includes("/api/v1/generator/prototypes/?database_prototype_name=") &&
          event.params.request.postData,
      );
      if (requestEvent && !requestId) {
        requestId = requestEvent.params.requestId;
        requestPayload = JSON.parse(requestEvent.params.request.postData);
      }
      const responseEvent = requestId
        ? client.events.find(
            (event) =>
              event.method === "Network.responseReceived" &&
              event.params.requestId === requestId,
          )
        : null;
      if (responseEvent && !responsePayload) {
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
      if (requestId && responsePayload && loaded) {
        clearInterval(timer);
        try {
          const body = await client.send("Network.getResponseBody", { requestId });
          resolve({
            ...responsePayload,
            body: body.body,
            request: requestPayload,
          });
        } catch (error) {
          resolve({
            ...responsePayload,
            body: null,
            bodyReadError: error.message,
            request: requestPayload,
          });
        }
      } else if (Date.now() - started > generationTimeoutMs) {
        clearInterval(timer);
        reject(new Error("timed out waiting for prototype POST response"));
      }
    }, 500);
  });
}

async function submitAndCapture(client, prototypeName) {
  const postPromise = waitForPrototypePost(client);
  await evaluate(
    client,
    `[...document.querySelectorAll("button")]
      .filter((button) => button.innerText.trim() === "Create")
      .at(-1)
      .click()`,
  );
  const postResponse = await postPromise;
  if (postResponse.status !== 200) {
    throw new Error(`prototype POST failed: ${postResponse.status} ${postResponse.body}`);
  }
  let responseJson = {};
  if (postResponse.body) {
    try {
      responseJson = JSON.parse(postResponse.body);
    } catch {
      responseJson = { raw: postResponse.body };
    }
  }
  let prototypeId = responseJson.id;
  if (!prototypeId) {
    const prototypes = await evaluate(
      client,
      `fetch("http://api.ai4mde.localhost:80/api/v1/generator/prototypes/?system=${systemId}", {
        headers: { Authorization: "Bearer ${token}" },
        credentials: "include",
      }).then(async (response) => {
        if (!response.ok) throw new Error(response.status + " " + await response.text());
        return response.json();
      })`,
      true,
    );
    prototypeId = [...prototypes].reverse().find((candidate) => candidate.name === prototypeName)?.id;
  }
  if (!prototypeId) throw new Error(`prototype id missing for ${prototypeName}`);

  const metadata = await evaluate(
    client,
    `fetch("http://api.ai4mde.localhost:80/api/v1/generator/prototypes/${prototypeId}/meta/", {
      headers: { Authorization: "Bearer ${token}" },
      credentials: "include",
    }).then(async (response) => {
      if (!response.ok) throw new Error(response.status + " " + await response.text());
      return response.json();
    })`,
    true,
  );
  return {
    prototypeName,
    prototypeId,
    postStatus: postResponse.status,
    postBodyReadError: postResponse.bodyReadError || null,
    requestInterfaces: postResponse.request.metadata.interfaces,
    metadataInterfaces: metadata.interfaces,
  };
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
    source: `localStorage.setItem("auth-storage", ${JSON.stringify(authStorageValue())});`,
  });

  await client.send("Page.navigate", { url: targetUrl });
  await waitForExpression(
    client,
    `document.body && document.body.innerText.includes("Generate new prototype")`,
    30000,
    "prototypes page",
  );

  const defaultPrototypeName = await uniquePrototypeName(client, defaultName);
  const reselectPrototypeName = await uniquePrototypeName(client, reselectName);

  await openCreateModal(client);
  const defaultVisibleShape = await evaluate(
    client,
    `(() => {
      const containers = [...document.querySelectorAll(".css-b62m3t-container")];
      const container = containers.find((candidate) =>
        candidate.innerText.includes("librarian") && candidate.innerText.includes("member")
      );
      return container ? container.innerText : "";
    })()`,
  );
  await setPrototypeName(client, defaultPrototypeName);
  const defaultResult = await submitAndCapture(client, defaultPrototypeName);
  validateWrappedInterfaces(defaultResult.requestInterfaces, "default POST");
  validateWrappedInterfaces(defaultResult.metadataInterfaces, "default /meta");
  await writeFile(
    defaultShapePath,
    JSON.stringify({ visibleShape: defaultVisibleShape, ...defaultResult }, null, 2) + "\n",
  );

  await waitForExpression(
    client,
    `document.body && document.body.innerText.includes("Generate new prototype")`,
    30000,
    "prototypes page after default generation",
  );

  await openCreateModal(client);
  const reselectedVisibleShape = await reselectInterfaces(client);
  await setPrototypeName(client, reselectPrototypeName);
  const reselectResult = await submitAndCapture(client, reselectPrototypeName);
  validateWrappedInterfaces(reselectResult.requestInterfaces, "reselect POST");
  validateWrappedInterfaces(reselectResult.metadataInterfaces, "reselect /meta");
  await writeFile(
    reselectShapePath,
    JSON.stringify({ visibleShape: reselectedVisibleShape, ...reselectResult }, null, 2) + "\n",
  );

  const result = {
    targetUrl,
    defaultShapePath,
    reselectShapePath,
    default: {
      prototypeName: defaultResult.prototypeName,
      prototypeId: defaultResult.prototypeId,
      postStatus: defaultResult.postStatus,
      requestInterfacesWrapped: true,
      metadataInterfacesWrapped: true,
    },
    reselect: {
      prototypeName: reselectResult.prototypeName,
      prototypeId: reselectResult.prototypeId,
      postStatus: reselectResult.postStatus,
      requestInterfacesWrapped: true,
      metadataInterfacesWrapped: true,
      visibleShape: reselectedVisibleShape,
    },
    pass: true,
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
  if (process.exitCode) {
    console.error(chromeOutput.join(""));
  }
}
