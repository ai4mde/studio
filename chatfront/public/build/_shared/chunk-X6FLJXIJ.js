import {
  cn
} from "/build/_shared/chunk-3DKJGO2R.js";
import {
  require_jsx_dev_runtime
} from "/build/_shared/chunk-G5LS6WKY.js";
import {
  createHotContext
} from "/build/_shared/chunk-YJEMTN56.js";
import {
  __toESM
} from "/build/_shared/chunk-PZDJHGND.js";

// app/components/layout/max-width-wrapper.tsx
var import_jsx_dev_runtime = __toESM(require_jsx_dev_runtime(), 1);
if (!window.$RefreshReg$ || !window.$RefreshSig$ || !window.$RefreshRuntime$) {
  console.warn("remix:hmr: React Fast Refresh only works when the Remix compiler is running in development mode.");
} else {
  prevRefreshReg = window.$RefreshReg$;
  prevRefreshSig = window.$RefreshSig$;
  window.$RefreshReg$ = (type, id) => {
    window.$RefreshRuntime$.register(type, '"app/components/layout/max-width-wrapper.tsx"' + id);
  };
  window.$RefreshSig$ = window.$RefreshRuntime$.createSignatureFunctionForTransform;
}
var prevRefreshReg;
var prevRefreshSig;
if (import.meta) {
  import.meta.hot = createHotContext(
    //@ts-expect-error
    "app/components/layout/max-width-wrapper.tsx"
  );
  import.meta.hot.lastModified = "1738662837908.6753";
}
function MaxWidthWrapper({
  className,
  ...props
}) {
  return /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)("div", { className: cn("mx-auto w-full max-w-screen-xl px-2.5 md:px-20", className), ...props }, void 0, false, {
    fileName: "app/components/layout/max-width-wrapper.tsx",
    lineNumber: 27,
    columnNumber: 10
  }, this);
}
_c = MaxWidthWrapper;
var _c;
$RefreshReg$(_c, "MaxWidthWrapper");
window.$RefreshReg$ = prevRefreshReg;
window.$RefreshSig$ = prevRefreshSig;

export {
  MaxWidthWrapper
};
//# sourceMappingURL=/build/_shared/chunk-X6FLJXIJ.js.map
