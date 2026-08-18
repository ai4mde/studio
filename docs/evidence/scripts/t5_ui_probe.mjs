#!/usr/bin/env node
import { spawn } from "node:child_process";
import { mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

const chromePath =
  process.env.CHROME_PATH ||
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const diagramId = process.env.T5_DIAGRAM_ID || "a9cb6660-0a0c-423a-9830-ec80067f459f";
const mode = process.env.T5_UI_MODE || "panel";
const skipAllowedValuesRestore = process.env.T5_SKIP_ALLOWED_RESTORE === "1";
const port = Number(process.env.T5_CHROME_PORT || 9255);
const resultPath = process.env.T5_UI_RESULT_PATH || `docs/evidence/t5_ui_${mode}.json`;
const username = process.env.T5_STUDIO_USERNAME || "admin";
const password = process.env.T5_STUDIO_PASSWORD || "sequoias";

const diagramUrl = `http://ai4mde.localhost/diagram/${diagramId}`;
const profileDir = await mkdtemp(join(tmpdir(), "t5-ui-chrome-"));
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

async function bearerToken() {
  const payload = await fetchJson("http://api.ai4mde.localhost/api/v1/auth/token", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  return payload.token;
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

function authStorageValue(token) {
  return JSON.stringify({
    state: {
      isAuthenticated: true,
      bearerToken: token,
      expires: Date.now() + 60 * 60 * 1000,
      user: { id: "1", email: "t5@example.local", username: "t5" },
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
        .find((candidate) => {
          const firstLine = candidate.innerText
            .split("\\n")
            .map((line) => line.trim())
            .find(Boolean);
          return firstLine === ${JSON.stringify(className)};
        });
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

async function closeModal(client) {
  await client.send("Input.dispatchKeyEvent", { type: "keyDown", key: "Escape", code: "Escape" });
  await client.send("Input.dispatchKeyEvent", { type: "keyUp", key: "Escape", code: "Escape" });
  await sleep(500);
}

async function sectionSummary(client) {
  return evaluate(
    client,
    `(() => [...document.querySelectorAll("[data-t4-ai-config-section]")]
      .map((section) => {
        const attr = section.getAttribute("data-t4-ai-config-section");
        const select = section.querySelector("[data-t4-ai-preset]");
        return {
          attr,
          enabled: section.querySelector('input[type="checkbox"]')?.checked ?? null,
          text: section.innerText,
          presetValue: select?.value ?? null,
          presetOptions: select ? [...select.options].map((option) => option.value) : [],
        };
      }))()`,
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
}

async function blurAllowedValues(client, attrName) {
  const selector = `[data-t4-allowed-values="${attrName}"]`;
  await evaluate(
    client,
    `(() => {
      const input = document.querySelector(${JSON.stringify(selector)});
      const reactPropsKey = Object.keys(input).find((key) => key.startsWith("__reactProps$"));
      const reactProps = reactPropsKey ? input[reactPropsKey] : null;
      reactProps?.onBlur?.({ currentTarget: input, target: input });
      input.dispatchEvent(new FocusEvent("blur", { bubbles: false }));
      input.blur();
      return input.value;
    })()`,
  );
}

async function allowedValue(client, attrName) {
  return evaluate(
    client,
    `document.querySelector('[data-t4-allowed-values="${attrName}"]')?.value ?? null`,
  );
}

async function waitForAttributesSaveEnabled(client) {
  await waitForExpression(
    client,
    `(() => [...document.querySelectorAll("button")]
      .filter((button) => button.innerText.trim() === "Save")
      .some((button) => !button.disabled))()`,
    10000,
    "Attributes Save enabled",
  );
}

async function clickEnabledSave(client) {
  const clicked = await evaluate(
    client,
    `(() => {
      const button = [...document.querySelectorAll("button")]
        .filter((candidate) => candidate.innerText.trim() === "Save")
        .find((candidate) => !candidate.disabled);
      if (!button) return false;
      button.click();
      return true;
    })()`,
  );
  if (!clicked) throw new Error("enabled Save button not found");
  await sleep(1600);
}

async function rawJsonState(client) {
  return evaluate(
    client,
    `(() => {
      const details = [...document.querySelectorAll("details")]
        .find((candidate) => candidate.innerText.includes("Raw JSON Editor"));
      if (!details) return null;
      details.open = true;
      const button = details.querySelector("button");
      const modelValues = window.monaco?.editor?.getModels?.().map((model) => model.getValue()) ?? [];
      return {
        rawSaveDisabled: button?.disabled ?? null,
        detailsTextHasAiConfig: details.innerText.includes("ai_config"),
        monacoHasAiConfig: modelValues.some((value) => value.includes('"ai_config"')),
        monacoValue: modelValues.find((value) => value.includes('"ai_config"'))?.slice(0, 3000) ?? null,
      };
    })()`,
  );
}

function assertCondition(label, condition, details) {
  if (!condition) {
    throw new Error(`${label}${details ? `: ${JSON.stringify(details)}` : ""}`);
  }
}

async function runPanelMode(client) {
  const screenshots = {
    nonApplicable: "docs/evidence/t5_non_applicable_book.png",
    applicableBookLoan: "docs/evidence/t5_applicable_bookloan.png",
    allowedValuesDraft: "docs/evidence/t5_allowed_values_draft.png",
    rawJsonAfterSave: "docs/evidence/t5_raw_json_after_save.png",
    customerReadingPlan: "docs/evidence/t5_customer_reading_plan.png",
  };

  await openNodeModal(client, "Book");
  const bookSections = await sectionSummary(client);
  assertCondition("Book has no AI sections", bookSections.length === 0, bookSections);
  await screenshot(client, screenshots.nonApplicable);
  await closeModal(client);

  await openNodeModal(client, "BookLoan");
  const bookLoanSections = await sectionSummary(client);
  const lateRisk = bookLoanSections.find((section) => section.attr === "late_risk");
  assertCondition("BookLoan.late_risk AI section exists", !!lateRisk, bookLoanSections);
  assertCondition("BookLoan late_risk preset filtered", lateRisk.presetOptions.length === 1 && lateRisk.presetOptions[0] === "late_return_risk", lateRisk);
  assertCondition("BookLoan output labels visible", lateRisk.text.includes("Writes to") && lateRisk.text.includes("Format"), lateRisk);
  await screenshot(client, screenshots.applicableBookLoan);

  await setAllowedValues(client, "late_risk", "SAFE, ");
  await sleep(600);
  const trailingDraft = await allowedValue(client, "late_risk");
  assertCondition("allowed_values preserves trailing comma draft", trailingDraft === "SAFE, ", trailingDraft);
  await setAllowedValues(client, "late_risk", "SAFE, RISKY");
  await sleep(600);
  const finalDraft = await allowedValue(client, "late_risk");
  assertCondition("allowed_values preserves final draft", finalDraft === "SAFE, RISKY", finalDraft);
  await screenshot(client, screenshots.allowedValuesDraft);
  await blurAllowedValues(client, "late_risk");
  await waitForAttributesSaveEnabled(client);
  await clickEnabledSave(client);

  await waitForExpression(
    client,
    `(() => {
      const details = [...document.querySelectorAll("details")]
        .find((candidate) => candidate.innerText.includes("Raw JSON Editor"));
      if (!details) return false;
      details.open = true;
      const button = details.querySelector("button");
      const modelValues = window.monaco?.editor?.getModels?.().map((model) => model.getValue()) ?? [];
      return button?.disabled === true && modelValues.some((value) => value.includes('"ai_config"'));
    })()`,
    15000,
    "Raw JSON ai_config echo and disabled save",
  );
  const rawJson = await rawJsonState(client);
  await screenshot(client, screenshots.rawJsonAfterSave);

  if (!skipAllowedValuesRestore) {
    await setAllowedValues(client, "late_risk", "LOW, MEDIUM, HIGH");
    await blurAllowedValues(client, "late_risk");
    await waitForAttributesSaveEnabled(client);
    await clickEnabledSave(client);
  }
  await closeModal(client);

  await openNodeModal(client, "Customer");
  const customerSections = await sectionSummary(client);
  const readingPlan = customerSections.find((section) => section.attr === "reading_plan");
  assertCondition("Customer.reading_plan AI section exists", !!readingPlan, customerSections);
  assertCondition("Customer only reading_plan has AI section", customerSections.length === 1, customerSections);
  assertCondition("Customer reading_plan preset filtered", readingPlan.presetOptions.length === 1 && readingPlan.presetOptions[0] === "reading_plan", readingPlan);
  assertCondition("Customer output labels visible", readingPlan.text.includes("Writes to") && readingPlan.text.includes("Format"), readingPlan);
  await screenshot(client, screenshots.customerReadingPlan);

  return {
    mode,
    screenshots,
    bookSections,
    bookLoanSections,
    customerSections,
    allowedValues: { trailingDraft, finalDraft },
    restoredAllowedValues: !skipAllowedValuesRestore,
    rawJson,
    pass: "G-B05/06 G-B03 G-B08 G-B07 UI probes passed",
  };
}

async function runUnsupportedMode(client) {
  const screenshotPath = "docs/evidence/t5_unsupported_bookloan.png";
  await openNodeModal(client, "BookLoan");
  const sections = await sectionSummary(client);
  const lateRisk = sections.find((section) => section.attr === "late_risk");
  assertCondition("unsupported late_risk section exists", !!lateRisk, sections);
  assertCondition("unsupported message visible", lateRisk.text.includes("Custom / unsupported configuration"), lateRisk);
  assertCondition("unsupported has no preset dropdown", lateRisk.presetOptions.length === 0, lateRisk);
  const saveEnabled = await evaluate(
    client,
    `(() => [...document.querySelectorAll("button")]
      .filter((button) => button.innerText.trim() === "Save")
      .some((button) => !button.disabled))()`,
  );
  assertCondition("unsupported open does not mark dirty", saveEnabled === false, { saveEnabled });
  await screenshot(client, screenshotPath);
  return {
    mode,
    screenshotPath,
    sections,
    saveEnabled,
    pass: "G-B11 unsupported UI did not auto-dirty or render preset controls",
  };
}

let client;
try {
  const token = await bearerToken();
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
    source: `localStorage.setItem("auth-storage", ${JSON.stringify(authStorageValue(token))});`,
  });

  const result = mode === "unsupported" ? await runUnsupportedMode(client) : await runPanelMode(client);
  await writeFile(resultPath, JSON.stringify(result, null, 2) + "\n");
  console.log(JSON.stringify({ ...result, token: undefined }, null, 2));
} finally {
  if (client) client.close();
  chrome.kill("SIGTERM");
  await Promise.race([
    new Promise((resolve) => chrome.once("exit", resolve)),
    sleep(2000),
  ]);
  await rm(profileDir, { recursive: true, force: true, maxRetries: 3 }).catch(() => {});
}
