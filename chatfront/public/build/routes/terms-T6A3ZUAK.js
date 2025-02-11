import {
  index_modern_default
} from "/build/_shared/chunk-DIGYRLJS.js";
import {
  MaxWidthWrapper
} from "/build/_shared/chunk-X6FLJXIJ.js";
import "/build/_shared/chunk-3DKJGO2R.js";
import {
  require_jsx_dev_runtime
} from "/build/_shared/chunk-G5LS6WKY.js";
import "/build/_shared/chunk-QPVUD6NO.js";
import {
  createHotContext
} from "/build/_shared/chunk-YJEMTN56.js";
import "/build/_shared/chunk-MWML3QXM.js";
import {
  __toESM
} from "/build/_shared/chunk-PZDJHGND.js";

// app/routes/terms.tsx
var import_jsx_dev_runtime = __toESM(require_jsx_dev_runtime(), 1);
if (!window.$RefreshReg$ || !window.$RefreshSig$ || !window.$RefreshRuntime$) {
  console.warn("remix:hmr: React Fast Refresh only works when the Remix compiler is running in development mode.");
} else {
  prevRefreshReg = window.$RefreshReg$;
  prevRefreshSig = window.$RefreshSig$;
  window.$RefreshReg$ = (type, id) => {
    window.$RefreshRuntime$.register(type, '"app/routes/terms.tsx"' + id);
  };
  window.$RefreshSig$ = window.$RefreshRuntime$.createSignatureFunctionForTransform;
}
var prevRefreshReg;
var prevRefreshSig;
if (import.meta) {
  import.meta.hot = createHotContext(
    //@ts-expect-error
    "app/routes/terms.tsx"
  );
  import.meta.hot.lastModified = "1738662837905.6753";
}
var meta = () => {
  return [{
    title: "Terms of Service - AI4MDE"
  }, {
    name: "description",
    content: "Our terms of service and usage conditions"
  }];
};
var content = `
## 1. Acceptance of Terms
These Terms of Service ("Terms") govern your use of the Requirements Engineering Automation Tool ("the Tool"), a research project developed as part of a university thesis study.

## 2. Academic Research Purpose
2.1 You acknowledge that:
- This Tool is part of academic research
- It is a proof of concept
- It will be available only during the research phase
- The findings will be published in an academic thesis

2.2 By using this Tool, you agree to:
- Participate in academic research
- Allow your usage data to be analyzed for research purposes
- Be contacted regarding the research if necessary

## 3. Account Registration and Use

### 3.1 Registration Requirements
To use the Tool, you must:
- Provide accurate registration information
- Be authorized to participate on behalf of your company
- Be at least 18 years old
- Have the capacity to agree to these Terms

### 3.2 Usage Guidelines
You agree to:
- Use only fictitious project scenarios
- Not input any sensitive or confidential company information
- Use the Tool for test purposes only
- Not attempt to reverse engineer the Tool
- Not use the Tool for any commercial purposes

## 4. Intellectual Property

### 4.1 Ownership
- The Tool and its original content remain the property of [University Name]
- Research findings belong to the research project
- You retain ownership of your input data
- The source code is available at [your-repository-url]

### 4.2 Licensing
- The Tool is released under the MIT License
- You may use, modify, and distribute the code according to the MIT License terms
- No commercial use of the research data or findings is permitted
- No redistribution rights are granted for research data

## 5. Disclaimers and Limitations

### 5.1 Research Nature
- The Tool is experimental in nature
- No guarantees of accuracy or reliability are made
- The Tool is provided "as is" without warranty

### 5.2 Availability
- Access may be terminated at any time
- The Tool will be discontinued after research completion
- No guarantee of continuous availability

## 6. Data Usage

### 6.1 Research Data
You grant permission for:
- Collection of usage data
- Analysis of interaction patterns
- Publication of anonymized findings

### 6.2 Publication
- Research results will be published
- You may opt for anonymity in publications
- Aggregate data may be used in academic contexts

## 7. Termination

### 7.1 Your Rights
You may:
- Stop participating at any time
- Request deletion of your data
- Withdraw from the research study

### 7.2 Our Rights
We may:
- Terminate access without notice
- Remove accounts that violate these terms
- Discontinue the Tool upon research completion

## 8. Changes to Terms
- Terms may be updated during the research
- Users will be notified of significant changes
- Continued use implies acceptance of changes

## 9. Liability
- No liability for data loss or damages
- No responsibility for misuse of the Tool
- Users responsible for their input data

## 10. Contact
For questions about these Terms, contact:

[Your Name]
[University Department]
[University Name]
Email: [your.email@university.edu]

## 11. Duration
These Terms are effective from [Start Date] until the completion of the thesis project (estimated [End Date]).

## 12. Governing Law
These Terms are governed by the laws of [Your Country/State] and the policies of [University Name].
`;
function Terms() {
  return /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)(MaxWidthWrapper, { className: "px-4 py-10", children: [
    /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)("h1", { className: "text-4xl font-bold mb-8", children: "Terms of Service" }, void 0, false, {
      fileName: "app/routes/terms.tsx",
      lineNumber: 144,
      columnNumber: 7
    }, this),
    /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)("div", { className: "prose prose-lg max-w-none dark:prose-invert\n        [&_p]:leading-tight \n        [&_li]:leading-tight \n        [&>*+*]:mt-3\n        [&_h2]:mb-3\n        [&_h3]:mb-2\n        [&_ul]:mt-2\n        [&_ul]:mb-2", children: /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)(index_modern_default, { children: content }, void 0, false, {
      fileName: "app/routes/terms.tsx",
      lineNumber: 153,
      columnNumber: 9
    }, this) }, void 0, false, {
      fileName: "app/routes/terms.tsx",
      lineNumber: 145,
      columnNumber: 7
    }, this)
  ] }, void 0, true, {
    fileName: "app/routes/terms.tsx",
    lineNumber: 143,
    columnNumber: 10
  }, this);
}
_c = Terms;
var _c;
$RefreshReg$(_c, "Terms");
window.$RefreshReg$ = prevRefreshReg;
window.$RefreshSig$ = prevRefreshSig;
export {
  Terms as default,
  meta
};
//# sourceMappingURL=/build/routes/terms-T6A3ZUAK.js.map
