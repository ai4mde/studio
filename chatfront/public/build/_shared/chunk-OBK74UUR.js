import {
  Primitive
} from "/build/_shared/chunk-QATI3NSB.js";
import {
  cva
} from "/build/_shared/chunk-MI2YJZX6.js";
import {
  require_jsx_runtime
} from "/build/_shared/chunk-2WFCNDEW.js";
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

// app/components/ui/label.tsx
var React2 = __toESM(require_react(), 1);

// node_modules/.pnpm/@radix-ui+react-label@2.1.1_@types+react-dom@18.3.5_@types+react@18.3.18__@types+react@_68bbc4d281c59ddec5d7a3b34dc4b4f5/node_modules/@radix-ui/react-label/dist/index.mjs
var React = __toESM(require_react(), 1);
var import_jsx_runtime = __toESM(require_jsx_runtime(), 1);
"use client";
var NAME = "Label";
var Label = React.forwardRef((props, forwardedRef) => {
  return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(
    Primitive.label,
    {
      ...props,
      ref: forwardedRef,
      onMouseDown: (event) => {
        const target = event.target;
        if (target.closest("button, input, select, textarea"))
          return;
        props.onMouseDown?.(event);
        if (!event.defaultPrevented && event.detail > 1)
          event.preventDefault();
      }
    }
  );
});
Label.displayName = NAME;
var Root = Label;

// app/components/ui/label.tsx
var import_jsx_dev_runtime = __toESM(require_jsx_dev_runtime(), 1);
if (!window.$RefreshReg$ || !window.$RefreshSig$ || !window.$RefreshRuntime$) {
  console.warn("remix:hmr: React Fast Refresh only works when the Remix compiler is running in development mode.");
} else {
  prevRefreshReg = window.$RefreshReg$;
  prevRefreshSig = window.$RefreshSig$;
  window.$RefreshReg$ = (type, id) => {
    window.$RefreshRuntime$.register(type, '"app/components/ui/label.tsx"' + id);
  };
  window.$RefreshSig$ = window.$RefreshRuntime$.createSignatureFunctionForTransform;
}
var prevRefreshReg;
var prevRefreshSig;
if (import.meta) {
  import.meta.hot = createHotContext(
    //@ts-expect-error
    "app/components/ui/label.tsx"
  );
  import.meta.hot.lastModified = "1738662837907.6753";
}
var labelVariants = cva("text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70");
var Label2 = React2.forwardRef(_c = ({
  className,
  ...props
}, ref) => /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)(Root, { ref, className: cn(labelVariants(), className), ...props }, void 0, false, {
  fileName: "app/components/ui/label.tsx",
  lineNumber: 29,
  columnNumber: 12
}, this));
_c2 = Label2;
Label2.displayName = Root.displayName;
var _c;
var _c2;
$RefreshReg$(_c, "Label$React.forwardRef");
$RefreshReg$(_c2, "Label");
window.$RefreshReg$ = prevRefreshReg;
window.$RefreshSig$ = prevRefreshSig;

export {
  Label2 as Label
};
//# sourceMappingURL=/build/_shared/chunk-OBK74UUR.js.map
