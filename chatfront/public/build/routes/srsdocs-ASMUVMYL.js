import {
  Button
} from "/build/_shared/chunk-MI2YJZX6.js";
import "/build/_shared/chunk-2WFCNDEW.js";
import {
  require_gray_matter
} from "/build/_shared/chunk-YILOF2CX.js";
import {
  require_session
} from "/build/_shared/chunk-IWB4XMPA.js";
import {
  require_node
} from "/build/_shared/chunk-NBEH4DGX.js";
import {
  MaxWidthWrapper
} from "/build/_shared/chunk-X6FLJXIJ.js";
import {
  Link,
  useLoaderData
} from "/build/_shared/chunk-5SMQHKI5.js";
import "/build/_shared/chunk-3DKJGO2R.js";
import "/build/_shared/chunk-2N23GYW7.js";
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

// app/routes/srsdocs.tsx
var import_node = __toESM(require_node(), 1);
var import_gray_matter = __toESM(require_gray_matter(), 1);
var import_session = __toESM(require_session(), 1);
var import_node2 = __toESM(require_node(), 1);
var import_jsx_dev_runtime = __toESM(require_jsx_dev_runtime(), 1);
if (!window.$RefreshReg$ || !window.$RefreshSig$ || !window.$RefreshRuntime$) {
  console.warn("remix:hmr: React Fast Refresh only works when the Remix compiler is running in development mode.");
} else {
  prevRefreshReg = window.$RefreshReg$;
  prevRefreshSig = window.$RefreshSig$;
  window.$RefreshReg$ = (type, id) => {
    window.$RefreshRuntime$.register(type, '"app/routes/srsdocs.tsx"' + id);
  };
  window.$RefreshSig$ = window.$RefreshRuntime$.createSignatureFunctionForTransform;
}
var prevRefreshReg;
var prevRefreshSig;
var _s = $RefreshSig$();
if (import.meta) {
  import.meta.hot = createHotContext(
    //@ts-expect-error
    "app/routes/srsdocs.tsx"
  );
  import.meta.hot.lastModified = "1738662837905.6753";
}
var meta = () => {
  return [{
    title: "SRS Documentation - AI4MDE"
  }, {
    description: "Software Requirements Specification documentation for AI4MDE"
  }];
};
function DocCard({
  doc
}) {
  return /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)("div", { className: "rounded-lg border bg-card text-card-foreground shadow-sm hover:shadow-md transition-shadow", children: /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)("div", { className: "p-6", children: [
    /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)("h3", { className: "text-2xl font-semibold leading-none tracking-tight mb-2", children: doc.title }, void 0, false, {
      fileName: "app/routes/srsdocs.tsx",
      lineNumber: 113,
      columnNumber: 9
    }, this),
    /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)("p", { className: "text-sm text-muted-foreground mb-4", children: doc.description }, void 0, false, {
      fileName: "app/routes/srsdocs.tsx",
      lineNumber: 116,
      columnNumber: 9
    }, this),
    doc.date && /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)("p", { className: "text-xs text-muted-foreground mb-4", children: new Date(doc.date).toLocaleDateString() }, void 0, false, {
      fileName: "app/routes/srsdocs.tsx",
      lineNumber: 119,
      columnNumber: 22
    }, this),
    /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)(Button, { asChild: true, children: /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)(Link, { to: `/srsdoc/${doc.id}`, children: "Read More" }, void 0, false, {
      fileName: "app/routes/srsdocs.tsx",
      lineNumber: 123,
      columnNumber: 11
    }, this) }, void 0, false, {
      fileName: "app/routes/srsdocs.tsx",
      lineNumber: 122,
      columnNumber: 9
    }, this)
  ] }, void 0, true, {
    fileName: "app/routes/srsdocs.tsx",
    lineNumber: 112,
    columnNumber: 7
  }, this) }, void 0, false, {
    fileName: "app/routes/srsdocs.tsx",
    lineNumber: 111,
    columnNumber: 10
  }, this);
}
_c = DocCard;
function SrsDocs() {
  _s();
  const {
    docs
  } = useLoaderData();
  return /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)(MaxWidthWrapper, { className: "py-8", children: [
    /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)("h1", { className: "text-4xl font-bold mb-6", children: "SRS Documentation" }, void 0, false, {
      fileName: "app/routes/srsdocs.tsx",
      lineNumber: 135,
      columnNumber: 7
    }, this),
    docs.length === 0 ? /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)("div", { className: "text-center text-muted-foreground", children: /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)("p", { children: "No SRS documents found." }, void 0, false, {
      fileName: "app/routes/srsdocs.tsx",
      lineNumber: 137,
      columnNumber: 11
    }, this) }, void 0, false, {
      fileName: "app/routes/srsdocs.tsx",
      lineNumber: 136,
      columnNumber: 28
    }, this) : /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)("div", { className: "grid gap-4 md:grid-cols-2 lg:grid-cols-3", children: docs.map((doc) => /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)(DocCard, { doc }, doc.id, false, {
      fileName: "app/routes/srsdocs.tsx",
      lineNumber: 139,
      columnNumber: 28
    }, this)) }, void 0, false, {
      fileName: "app/routes/srsdocs.tsx",
      lineNumber: 138,
      columnNumber: 18
    }, this)
  ] }, void 0, true, {
    fileName: "app/routes/srsdocs.tsx",
    lineNumber: 134,
    columnNumber: 10
  }, this);
}
_s(SrsDocs, "6v3qFFGo5l8sdWw4idpAr1svAlg=", false, function() {
  return [useLoaderData];
});
_c2 = SrsDocs;
var _c;
var _c2;
$RefreshReg$(_c, "DocCard");
$RefreshReg$(_c2, "SrsDocs");
window.$RefreshReg$ = prevRefreshReg;
window.$RefreshSig$ = prevRefreshSig;
export {
  SrsDocs as default,
  meta
};
//# sourceMappingURL=/build/routes/srsdocs-ASMUVMYL.js.map
