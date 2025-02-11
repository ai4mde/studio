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

// app/routes/privacy.tsx
var import_jsx_dev_runtime = __toESM(require_jsx_dev_runtime(), 1);
if (!window.$RefreshReg$ || !window.$RefreshSig$ || !window.$RefreshRuntime$) {
  console.warn("remix:hmr: React Fast Refresh only works when the Remix compiler is running in development mode.");
} else {
  prevRefreshReg = window.$RefreshReg$;
  prevRefreshSig = window.$RefreshSig$;
  window.$RefreshReg$ = (type, id) => {
    window.$RefreshRuntime$.register(type, '"app/routes/privacy.tsx"' + id);
  };
  window.$RefreshSig$ = window.$RefreshRuntime$.createSignatureFunctionForTransform;
}
var prevRefreshReg;
var prevRefreshSig;
if (import.meta) {
  import.meta.hot = createHotContext(
    //@ts-expect-error
    "app/routes/privacy.tsx"
  );
  import.meta.hot.lastModified = "1738662837905.6753";
}
var meta = () => {
  return [{
    title: "Privacy Policy - AI4MDE"
  }, {
    name: "description",
    content: "Privacy policy and data handling practices"
  }];
};
var content = `
## 1. Introduction
This privacy policy applies to the Requirements Engineering Automation Tool ("the Tool"), which is part of a university thesis project. This Tool is a proof of concept and will be available for a limited time during the research phase.

## 2. Information We Collect
We collect the following personal information when you register to use our Tool:
- First name and last name
- Professional email address
- Phone number
- Job description
- Company name

### 2.1 Research Data
The Tool collects data about how requirements engineering processes are conducted. We explicitly request that users:
- Use fictitious project scenarios
- Do not input any sensitive or confidential company information
- Use the Tool only for test purposes

## 3. How We Use Your Information

### 3.1 Primary Use
Your information is used for:
- Creating and managing your account
- Communication regarding the research project
- Analysis of the requirements engineering process
- Documentation in the thesis research

### 3.2 Research Publication
- Research findings will be published in the university thesis
- You have the option to remain anonymous in any research publications
- Aggregated data may be used for academic purposes

## 4. Data Protection and Storage

### 4.1 Data Security
- All data is stored securely using industry-standard encryption
- Access to personal data is strictly limited to the research team
- Data will be deleted after the completion of the thesis project

### 4.2 Data Retention
- All collected data will be retained only for the duration of the research project
- Upon completion of the thesis, personal data will be deleted
- Anonymized research findings may be retained for academic purposes

## 5. Your Rights
You have the right to:
- Access your personal data
- Request correction of your data
- Request deletion of your data
- Opt for anonymity in research publications
- Withdraw from the research at any time

## 6. Third-Party Access
- No personal data will be shared with third parties
- Anonymized research findings may be shared in academic contexts
- The tool may use essential third-party services for hosting and functionality

## 7. Research Ethics
This research project follows the ethical guidelines of [Your University Name] and has been approved by [relevant ethics committee if applicable].

## 8. Contact Information
For any questions about this privacy policy or the research project, please contact:

[Your Name]
[University Department]
[University Name]
Email: [your.email@university.edu]

## 9. Changes to This Policy
We may update this privacy policy during the course of the research. Users will be notified of any significant changes.

## 10. Duration
This privacy policy is effective from [Start Date] until the completion of the thesis project (estimated [End Date]).
`;
function Privacy() {
  return /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)(MaxWidthWrapper, { className: "px-4 py-10", children: [
    /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)("h1", { className: "text-4xl font-bold mb-8", children: "Privacy Policy" }, void 0, false, {
      fileName: "app/routes/privacy.tsx",
      lineNumber: 108,
      columnNumber: 7
    }, this),
    /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)("div", { className: "prose prose-lg max-w-none dark:prose-invert\n        [&_p]:leading-tight \n        [&_li]:leading-tight \n        [&>*+*]:mt-3\n        [&_h2]:mb-3\n        [&_h3]:mb-2\n        [&_ul]:mt-2\n        [&_ul]:mb-2", children: /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)(index_modern_default, { children: content }, void 0, false, {
      fileName: "app/routes/privacy.tsx",
      lineNumber: 117,
      columnNumber: 9
    }, this) }, void 0, false, {
      fileName: "app/routes/privacy.tsx",
      lineNumber: 109,
      columnNumber: 7
    }, this)
  ] }, void 0, true, {
    fileName: "app/routes/privacy.tsx",
    lineNumber: 107,
    columnNumber: 10
  }, this);
}
_c = Privacy;
var _c;
$RefreshReg$(_c, "Privacy");
window.$RefreshReg$ = prevRefreshReg;
window.$RefreshSig$ = prevRefreshSig;
export {
  Privacy as default,
  meta
};
//# sourceMappingURL=/build/routes/privacy-K6BBOSDB.js.map
