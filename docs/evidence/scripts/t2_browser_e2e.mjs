#!/usr/bin/env node
import { spawn } from "node:child_process";
import { mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

const chromePath =
  process.env.CHROME_PATH ||
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const systemId = process.env.T2_SYSTEM_ID;
const prototypeName = process.env.T2_PROTOTYPE_NAME || "LibraryT2A";
const token = process.env.T2_BEARER_TOKEN;
const port = Number(process.env.T2_CHROME_PORT || 9231);
const resultPath =
  process.env.T2_BROWSER_RESULT_PATH || "docs/evidence/t2_browser_e2e_result.json";
const studioScreenshotPath =
  process.env.T2_BROWSER_STUDIO_SCREENSHOT || "docs/evidence/t2_browser_studio_run.png";
const loginScreenshotPath =
  process.env.T2_BROWSER_LOGIN_SCREENSHOT || "docs/evidence/t2_browser_login.png";
const createScreenshotPath =
  process.env.T2_BROWSER_CREATE_SCREENSHOT || "docs/evidence/t2_browser_create_form.png";
const listScreenshotPath =
  process.env.T2_BROWSER_LIST_SCREENSHOT || "docs/evidence/t2_browser_list_late_risk.png";

if (!systemId) throw new Error("T2_SYSTEM_ID is required");
if (!token) throw new Error("T2_BEARER_TOKEN is required");

const studioUrl = `http://ai4mde.localhost/systems/${systemId}/prototypes`;
const prototypeUrl = "http://prototype.ai4mde.localhost";

const profileDir = await mkdtemp(join(tmpdir(), "t2-chrome-"));
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
      user: { id: "1", email: "t2@example.local", username: "t2" },
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
    const description =
      response.exceptionDetails.exception?.description ||
      response.exceptionDetails.text ||
      "Runtime.evaluate failed";
    throw new Error(description);
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
  const shot = await client.send("Page.captureScreenshot", {
    format: "png",
    captureBeyondViewport: false,
  });
  await writeFile(path, Buffer.from(shot.data, "base64"));
}

async function navigateAndWait(client, url, expression, label, timeoutMs = 30000) {
  const start = Date.now();
  let lastError = null;
  while (Date.now() - start < timeoutMs) {
    try {
      await client.send("Page.navigate", { url });
      await waitForExpression(client, expression, 5000, label);
      return;
    } catch (error) {
      lastError = error;
      await sleep(1000);
    }
  }
  throw new Error(`could not load ${label}: ${lastError?.message || "unknown error"}`);
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

  await client.send("Page.navigate", { url: studioUrl });
  await waitForExpression(
    client,
    `document.body && document.body.innerText.includes(${JSON.stringify(prototypeName)})`,
    30000,
    "Studio prototypes page with LibraryT2A",
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
    "LibraryT2A Run/Kill button",
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
  if (killClicked) {
    await sleep(7000);
  }

  const runClicked = await evaluate(
    client,
    `(() => {
      const row = [...document.querySelectorAll("tr")]
        .find((candidate) => candidate.innerText.includes(${JSON.stringify(prototypeName)}));
      if (!row) return false;
      const button = [...row.querySelectorAll("button")]
        .find((candidate) => candidate.innerText.trim() === "Run");
      if (!button) return false;
      button.click();
      return true;
    })()`,
  );
  if (!runClicked) throw new Error("Run button was not clicked for LibraryT2A");
  await sleep(8000);
  await screenshot(client, studioScreenshotPath);

  await navigateAndWait(
    client,
    prototypeUrl,
    `document.querySelector('input[name="username"]') && document.body.innerText.includes("Login")`,
    "prototype login page",
    45000,
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
      setInput('input[name="username"]', "demo_librarian");
      setInput('input[name="password"]', "ai4mde-demo");
      const submit = [...document.querySelectorAll('input[type="submit"]')]
        .find((input) => input.value === "Login");
      if (!submit) throw new Error("Login submit button missing");
      submit.click();
      return true;
    })()`,
  );
  await waitForExpression(
    client,
    `location.pathname.startsWith("/librarian") && document.body.innerText.includes("Librarian")`,
    20000,
    "librarian home after login",
  );

  await evaluate(
    client,
    `([...document.querySelectorAll("a")]
      .find((link) => link.innerText.trim() === "loans")).click()`,
  );
  await waitForExpression(
    client,
    `location.pathname.includes("render_librarian_loans") && document.body.innerText.includes("late_risk")`,
    20000,
    "loans list page",
  );

  await evaluate(
    client,
    `document.querySelector('input[name="create_book_loans"]')
      .closest("form")
      .querySelector("label")
      .click()`,
  );
  await waitForExpression(
    client,
    `document.querySelector('form[action*="loans_book_loans_create"]') !== null`,
    10000,
    "BookLoan create form",
  );

  const createFormState = await evaluate(
    client,
    `(() => {
      const form = document.querySelector('form[action*="loans_book_loans_create"]');
      const loanSelect = [...document.querySelectorAll('select[name="Loan"]')]
        .find((select) => select.form === form) || document.querySelector('select[name="Loan"]');
      const bookSelect = [...document.querySelectorAll('select[name="Book"]')]
        .find((select) => select.form === form) || document.querySelector('select[name="Book"]');
      const saveInput = [...document.querySelectorAll('input[type="submit"]')]
        .find((input) => input.value === "Save" && input.form === form)
        || [...document.querySelectorAll('input[type="submit"]')]
          .find((input) => input.value === "Save");
      return {
        hasForm: !!form,
        hasLateRiskInput: !!document.querySelector('[name="late_risk"]'),
        hasLoanSelect: !!loanSelect,
        hasBookSelect: !!bookSelect,
        loanAssociatedWithCreateForm: loanSelect?.form === form,
        bookAssociatedWithCreateForm: bookSelect?.form === form,
        saveAssociatedWithCreateForm: saveInput?.form === form,
        text: form?.innerText || "",
      };
    })()`,
  );
  if (!createFormState.hasForm) throw new Error("BookLoan create form missing");
  if (createFormState.hasLateRiskInput) throw new Error("late_risk input present in create form");
  if (!createFormState.hasLoanSelect || !createFormState.hasBookSelect) {
    throw new Error(`Loan/Book selects missing: ${JSON.stringify(createFormState)}`);
  }
  await screenshot(client, createScreenshotPath);

  await evaluate(
    client,
    `(() => {
      const form = document.querySelector('form[action*="loans_book_loans_create"]');
      const loan = [...document.querySelectorAll('select[name="Loan"]')]
        .find((select) => select.form === form) || document.querySelector('select[name="Loan"]');
      const book = [...document.querySelectorAll('select[name="Book"]')]
        .find((select) => select.form === form) || document.querySelector('select[name="Book"]');
      const submit = [...document.querySelectorAll('input[type="submit"]')]
        .find((input) => input.value === "Save" && input.form === form)
        || [...document.querySelectorAll('input[type="submit"]')]
          .find((input) => input.value === "Save");
      loan.selectedIndex = 0;
      book.selectedIndex = 0;
      loan.dispatchEvent(new Event("change", { bubbles: true }));
      book.dispatchEvent(new Event("change", { bubbles: true }));
      submit.click();
      return true;
    })()`,
  );
  await waitForExpression(
    client,
    `location.pathname.includes("render_librarian_loans")
      && document.body.innerText.includes("late_risk")
      && !document.querySelector('form[action*="loans_book_loans_create"]')`,
    20000,
    "loans list after BookLoan create",
  );
  await screenshot(client, listScreenshotPath);

  const finalPage = await evaluate(
    client,
    `({
      href: location.href,
      title: document.title,
      hasLateRiskHeader: document.body.innerText.includes("late_risk"),
      hasLowValue: document.body.innerText.includes("LOW"),
      bodyText: document.body.innerText.slice(0, 1200),
    })`,
  );

  result = {
    studioUrl,
    prototypeUrl,
    prototypeName,
    preRunState,
    killClicked,
    runClicked,
    login: "demo_librarian / ai4mde-demo",
    createFormState,
    finalPage,
    screenshots: {
      studio: studioScreenshotPath,
      login: loginScreenshotPath,
      createForm: createScreenshotPath,
      listLateRisk: listScreenshotPath,
    },
    manualAiRuntimeFakeExport: false,
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
