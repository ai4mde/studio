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

// app/routes/guide.tsx
var import_jsx_dev_runtime = __toESM(require_jsx_dev_runtime(), 1);
if (!window.$RefreshReg$ || !window.$RefreshSig$ || !window.$RefreshRuntime$) {
  console.warn("remix:hmr: React Fast Refresh only works when the Remix compiler is running in development mode.");
} else {
  prevRefreshReg = window.$RefreshReg$;
  prevRefreshSig = window.$RefreshSig$;
  window.$RefreshReg$ = (type, id) => {
    window.$RefreshRuntime$.register(type, '"app/routes/guide.tsx"' + id);
  };
  window.$RefreshSig$ = window.$RefreshRuntime$.createSignatureFunctionForTransform;
}
var prevRefreshReg;
var prevRefreshSig;
if (import.meta) {
  import.meta.hot = createHotContext(
    //@ts-expect-error
    "app/routes/guide.tsx"
  );
  import.meta.hot.lastModified = "1738662837905.6753";
}
var meta = () => {
  return [{
    title: "Guide - AI4MDE"
  }, {
    name: "description",
    content: "Learn how to use our platform effectively"
  }];
};
var content = `
<div style="background: yellow; padding: 10px;">
<h1>\u{1F6A7} <strong>Attention:</strong> <br>
This page is under construction!</h1>
<h2>Nothing on this page is valid yet.</h2>
</div>

# Getting Started Guide

## 1. Creating Your Account
Learn how to set up your account and profile.

### 1.1 Sign Up Process
Step-by-step guide to creating your account.

### 1.2 Profile Setup
Customize your profile and preferences.

## 2. Basic Features

### 2.1 Navigation
Learn how to navigate through the platform.

### 2.2 Key Functions
Overview of essential features and tools.

## 3. Advanced Features

### 3.1 Advanced Tools
Explore powerful features for power users.

### 3.2 Customization
Personalize your experience.

## 4. Best Practices
Tips and tricks for getting the most out of our platform.

## 5. Need Help?
Contact our support team for assistance.
`;
function Guide() {
  return /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)(MaxWidthWrapper, { className: "px-4 py-10", children: [
    /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)("h1", { className: "text-4xl font-bold mb-8", children: "Guide" }, void 0, false, {
      fileName: "app/routes/guide.tsx",
      lineNumber: 74,
      columnNumber: 7
    }, this),
    /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)("div", { className: "prose prose-lg max-w-none dark:prose-invert\n        [&_p]:leading-tight \n        [&_li]:leading-tight \n        [&>*+*]:mt-3\n        [&_h2]:mb-3\n        [&_h3]:mb-2\n        [&_ul]:mt-2\n        [&_ul]:mb-2", children: /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)(index_modern_default, { children: content }, void 0, false, {
      fileName: "app/routes/guide.tsx",
      lineNumber: 83,
      columnNumber: 9
    }, this) }, void 0, false, {
      fileName: "app/routes/guide.tsx",
      lineNumber: 75,
      columnNumber: 7
    }, this)
  ] }, void 0, true, {
    fileName: "app/routes/guide.tsx",
    lineNumber: 73,
    columnNumber: 10
  }, this);
}
_c = Guide;
var _c;
$RefreshReg$(_c, "Guide");
window.$RefreshReg$ = prevRefreshReg;
window.$RefreshSig$ = prevRefreshSig;
export {
  Guide as default,
  meta
};
//# sourceMappingURL=/build/routes/guide-ICDI7MS6.js.map
