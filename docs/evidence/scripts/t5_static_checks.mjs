#!/usr/bin/env node
import { readFile, writeFile } from "node:fs/promises";

const outPath = process.env.T5_STATIC_OUT || "docs/evidence/t5_static_checks.json";

async function text(path) {
  return readFile(path, "utf8");
}

function assertTrue(label, condition, details = undefined) {
  if (!condition) {
    throw new Error(`${label}${details ? `: ${details}` : ""}`);
  }
  return { label, pass: true };
}

const files = {
  presets: await text("frontend/src/lib/features/diagram/components/modals/EditNodeModal/components/EditAttributes/aiPresets.ts"),
  section: await text("frontend/src/lib/features/diagram/components/modals/EditNodeModal/components/EditAttributes/AiConfigSection.tsx"),
  modal: await text("frontend/src/lib/features/diagram/components/modals/EditNodeModal/EditNodeModal.tsx"),
  queries: await text("frontend/src/lib/features/prototypes/queries.ts"),
  create: await text("frontend/src/lib/features/prototypes/components/CreatePrototype.tsx"),
  show: await text("frontend/src/lib/features/prototypes/components/ShowPrototypes.tsx"),
  pyproject: await text("prototypes/pyproject.toml"),
  lock: await text("prototypes/poetry.lock"),
};

const handleAllowedValuesChange = files.section.match(
  /const handleAllowedValuesChange = \(value: string\) => \{([\s\S]*?)\n    \};/,
)?.[1] ?? "";

const checks = [
  assertTrue("B05/B06 presets declare applicableTo", files.presets.includes("applicableTo")),
  assertTrue("B05/B06 BookLoan late_risk mapping", files.presets.includes('className: "BookLoan"') && files.presets.includes('attributeName: "late_risk"')),
  assertTrue("B05/B06 Customer reading_plan mapping", files.presets.includes('className: "Customer"') && files.presets.includes('attributeName: "reading_plan"')),
  assertTrue("B05/B06 presetsFor helper exists", files.presets.includes("export function presetsFor")),
  assertTrue("B11 findAiPreset does not fallback to aiPresets[0]", !/findAiPreset[\s\S]*\?\?\s*aiPresets\[0\]/.test(files.presets)),
  assertTrue("B11 unsupported branch exists", files.section.includes("Custom / unsupported configuration - edit via import")),
  assertTrue("B11 reconcile effect guards selectedPreset", files.section.includes("!selectedPreset || !dynamicAiConfig")),
  assertTrue("B08 draft change does not call applyConfig", !handleAllowedValuesChange.includes("applyConfig")),
  assertTrue("B08 allowed_values commits on blur", files.section.includes("onBlur={handleAllowedValuesBlur}")),
  assertTrue("B03 output writes-to label", files.section.includes("Writes to")),
  assertTrue("B03 output format label", files.section.includes("Format")),
  assertTrue("B07 raw follows node data", files.modal.includes("setRaw(JSON.stringify({ data: node?.data ?? {} }, null, 2));") && files.modal.includes("[node?.data]")),
  assertTrue("B01 prototypeQueryKey helper exported", files.queries.includes("export const prototypeQueryKey")),
  assertTrue("B01 query uses prototypeQueryKey", files.queries.includes("queryKey: prototypeQueryKey(systemId)")),
  assertTrue("B01 create invalidates prototypeQueryKey", files.create.includes("prototypeQueryKey(systemId)")),
  assertTrue("B01 show invalidates prototypeQueryKey", files.show.includes("prototypeQueryKey(systemId)")),
  assertTrue("B01 no prototype stale query key", !/\[['"]prototypes['"],\s*systemId\]/.test(`${files.create}\n${files.show}\n${files.queries}`)),
  assertTrue("B01 no window.location.reload", !files.show.includes("window.location.reload")),
  assertTrue("B02 pyproject pins openai", files.pyproject.includes('openai = "^1.47.0"')),
  assertTrue("B02 pyproject pins groq", files.pyproject.includes('groq = "^0.15.0"')),
  assertTrue("B02 lock has openai 1.47.0", /name = "openai"\nversion = "1\.47\.0"/.test(files.lock)),
  assertTrue("B02 lock has groq 0.15.0", /name = "groq"\nversion = "0\.15\.0"/.test(files.lock)),
];

const result = {
  pass: true,
  checks,
};
await writeFile(outPath, JSON.stringify(result, null, 2) + "\n");
console.log(JSON.stringify(result, null, 2));
