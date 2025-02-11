import {
  cn
} from "/build/_shared/chunk-3DKJGO2R.js";
import {
  require_jsx_dev_runtime
} from "/build/_shared/chunk-G5LS6WKY.js";
import {
  require_react
} from "/build/_shared/chunk-QPVUD6NO.js";
import {
  createHotContext
} from "/build/_shared/chunk-YJEMTN56.js";
import {
  __toESM
} from "/build/_shared/chunk-PZDJHGND.js";

// app/components/ui/textarea.tsx
var React = __toESM(require_react(), 1);
var import_jsx_dev_runtime = __toESM(require_jsx_dev_runtime(), 1);
if (!window.$RefreshReg$ || !window.$RefreshSig$ || !window.$RefreshRuntime$) {
  console.warn("remix:hmr: React Fast Refresh only works when the Remix compiler is running in development mode.");
} else {
  prevRefreshReg = window.$RefreshReg$;
  prevRefreshSig = window.$RefreshSig$;
  window.$RefreshReg$ = (type, id) => {
    window.$RefreshRuntime$.register(type, '"app/components/ui/textarea.tsx"' + id);
  };
  window.$RefreshSig$ = window.$RefreshRuntime$.createSignatureFunctionForTransform;
}
var prevRefreshReg;
var prevRefreshSig;
if (import.meta) {
  import.meta.hot = createHotContext(
    //@ts-expect-error
    "app/components/ui/textarea.tsx"
  );
  import.meta.hot.lastModified = "1738662837907.6753";
}
var Textarea = React.forwardRef(_c = ({
  className,
  error,
  ...props
}, ref) => {
  return /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)("textarea", { className: cn("flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50", error && "border-red-500", className), ref, ...props }, void 0, false, {
    fileName: "app/components/ui/textarea.tsx",
    lineNumber: 28,
    columnNumber: 10
  }, this);
});
_c2 = Textarea;
Textarea.displayName = "Textarea";
var _c;
var _c2;
$RefreshReg$(_c, "Textarea$React.forwardRef");
$RefreshReg$(_c2, "Textarea");
window.$RefreshReg$ = prevRefreshReg;
window.$RefreshSig$ = prevRefreshSig;

export {
  Textarea
};
//# sourceMappingURL=/build/_shared/chunk-QBWBT4RY.js.map
