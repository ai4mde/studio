import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle
} from "/build/_shared/chunk-ANELKYHI.js";
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
import {
  FileText
} from "/build/_shared/chunk-RFPV3BFZ.js";
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

// app/routes/interviews.tsx
var import_node = __toESM(require_node(), 1);
var import_gray_matter = __toESM(require_gray_matter(), 1);
var import_session = __toESM(require_session(), 1);
var import_jsx_dev_runtime = __toESM(require_jsx_dev_runtime(), 1);
if (!window.$RefreshReg$ || !window.$RefreshSig$ || !window.$RefreshRuntime$) {
  console.warn("remix:hmr: React Fast Refresh only works when the Remix compiler is running in development mode.");
} else {
  prevRefreshReg = window.$RefreshReg$;
  prevRefreshSig = window.$RefreshSig$;
  window.$RefreshReg$ = (type, id) => {
    window.$RefreshRuntime$.register(type, '"app/routes/interviews.tsx"' + id);
  };
  window.$RefreshSig$ = window.$RefreshRuntime$.createSignatureFunctionForTransform;
}
var prevRefreshReg;
var prevRefreshSig;
var _s = $RefreshSig$();
if (import.meta) {
  import.meta.hot = createHotContext(
    //@ts-expect-error
    "app/routes/interviews.tsx"
  );
  import.meta.hot.lastModified = "1738662837905.6753";
}
var meta = () => {
  return [{
    title: "Interview Logs - AI4MDE"
  }, {
    description: "Interview logs and transcripts for AI4MDE project"
  }];
};
function InterviewCard({
  id,
  title,
  description,
  date
}) {
  return /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)(Card, { className: "group hover:shadow-md transition-shadow", children: /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)(Link, { to: `/interview/${id}`, className: "block h-full", children: [
    /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)(CardHeader, { children: [
      /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)(CardTitle, { className: "flex items-center gap-2", children: [
        /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)(FileText, { className: "h-5 w-5 text-muted-foreground group-hover:text-primary transition-colors" }, void 0, false, {
          fileName: "app/routes/interviews.tsx",
          lineNumber: 102,
          columnNumber: 13
        }, this),
        title
      ] }, void 0, true, {
        fileName: "app/routes/interviews.tsx",
        lineNumber: 101,
        columnNumber: 11
      }, this),
      date && /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)(CardDescription, { children: new Date(date).toLocaleDateString() }, void 0, false, {
        fileName: "app/routes/interviews.tsx",
        lineNumber: 105,
        columnNumber: 20
      }, this)
    ] }, void 0, true, {
      fileName: "app/routes/interviews.tsx",
      lineNumber: 100,
      columnNumber: 9
    }, this),
    /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)(CardContent, { children: /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)("p", { className: "text-muted-foreground line-clamp-3", children: description }, void 0, false, {
      fileName: "app/routes/interviews.tsx",
      lineNumber: 110,
      columnNumber: 11
    }, this) }, void 0, false, {
      fileName: "app/routes/interviews.tsx",
      lineNumber: 109,
      columnNumber: 9
    }, this)
  ] }, void 0, true, {
    fileName: "app/routes/interviews.tsx",
    lineNumber: 99,
    columnNumber: 7
  }, this) }, void 0, false, {
    fileName: "app/routes/interviews.tsx",
    lineNumber: 98,
    columnNumber: 10
  }, this);
}
_c = InterviewCard;
function Interviews() {
  _s();
  const {
    interviews
  } = useLoaderData();
  return /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)(MaxWidthWrapper, { className: "py-8", children: [
    /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)("div", { className: "mb-8", children: [
      /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)("h1", { className: "text-3xl font-bold mb-2", children: "Interview Logs" }, void 0, false, {
        fileName: "app/routes/interviews.tsx",
        lineNumber: 123,
        columnNumber: 9
      }, this),
      /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)("p", { className: "text-muted-foreground", children: "Browse interview logs and transcripts for the AI4MDE project." }, void 0, false, {
        fileName: "app/routes/interviews.tsx",
        lineNumber: 124,
        columnNumber: 9
      }, this)
    ] }, void 0, true, {
      fileName: "app/routes/interviews.tsx",
      lineNumber: 122,
      columnNumber: 7
    }, this),
    interviews.length === 0 ? /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)("div", { className: "text-center py-12", children: /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)("p", { className: "text-muted-foreground", children: "No interview logs found." }, void 0, false, {
      fileName: "app/routes/interviews.tsx",
      lineNumber: 130,
      columnNumber: 11
    }, this) }, void 0, false, {
      fileName: "app/routes/interviews.tsx",
      lineNumber: 129,
      columnNumber: 34
    }, this) : /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)("div", { className: "grid gap-6 sm:grid-cols-2 lg:grid-cols-3", children: interviews.map((interview) => /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)(InterviewCard, { ...interview }, interview.id, false, {
      fileName: "app/routes/interviews.tsx",
      lineNumber: 132,
      columnNumber: 40
    }, this)) }, void 0, false, {
      fileName: "app/routes/interviews.tsx",
      lineNumber: 131,
      columnNumber: 18
    }, this)
  ] }, void 0, true, {
    fileName: "app/routes/interviews.tsx",
    lineNumber: 121,
    columnNumber: 10
  }, this);
}
_s(Interviews, "X0dMiTs0yV4pvdm2wkiaJQbfM4Y=", false, function() {
  return [useLoaderData];
});
_c2 = Interviews;
var _c;
var _c2;
$RefreshReg$(_c, "InterviewCard");
$RefreshReg$(_c2, "Interviews");
window.$RefreshReg$ = prevRefreshReg;
window.$RefreshSig$ = prevRefreshSig;
export {
  Interviews as default,
  meta
};
//# sourceMappingURL=/build/routes/interviews-NF7ZGZQT.js.map
