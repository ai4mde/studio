import {
  Label
} from "/build/_shared/chunk-OBK74UUR.js";
import {
  Input
} from "/build/_shared/chunk-DTNMODCA.js";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle
} from "/build/_shared/chunk-ANELKYHI.js";
import "/build/_shared/chunk-QATI3NSB.js";
import {
  Button
} from "/build/_shared/chunk-MI2YJZX6.js";
import "/build/_shared/chunk-2WFCNDEW.js";
import {
  require_node
} from "/build/_shared/chunk-NBEH4DGX.js";
import {
  Form,
  useActionData,
  useSearchParams
} from "/build/_shared/chunk-5SMQHKI5.js";
import {
  Eye,
  EyeOff
} from "/build/_shared/chunk-RFPV3BFZ.js";
import "/build/_shared/chunk-3DKJGO2R.js";
import "/build/_shared/chunk-2N23GYW7.js";
import {
  require_jsx_dev_runtime
} from "/build/_shared/chunk-G5LS6WKY.js";
import {
  require_react
} from "/build/_shared/chunk-QPVUD6NO.js";
import {
  createHotContext
} from "/build/_shared/chunk-YJEMTN56.js";
import "/build/_shared/chunk-MWML3QXM.js";
import {
  __commonJS,
  __toESM
} from "/build/_shared/chunk-PZDJHGND.js";

// empty-module:../services/auth.server
var require_auth = __commonJS({
  "empty-module:../services/auth.server"(exports, module) {
    module.exports = {};
  }
});

// app/routes/login.tsx
var React = __toESM(require_react(), 1);
var import_node = __toESM(require_node(), 1);
var import_auth = __toESM(require_auth(), 1);
var import_jsx_dev_runtime = __toESM(require_jsx_dev_runtime(), 1);
if (!window.$RefreshReg$ || !window.$RefreshSig$ || !window.$RefreshRuntime$) {
  console.warn("remix:hmr: React Fast Refresh only works when the Remix compiler is running in development mode.");
} else {
  prevRefreshReg = window.$RefreshReg$;
  prevRefreshSig = window.$RefreshSig$;
  window.$RefreshReg$ = (type, id) => {
    window.$RefreshRuntime$.register(type, '"app/routes/login.tsx"' + id);
  };
  window.$RefreshSig$ = window.$RefreshRuntime$.createSignatureFunctionForTransform;
}
var prevRefreshReg;
var prevRefreshSig;
var _s = $RefreshSig$();
if (import.meta) {
  import.meta.hot = createHotContext(
    //@ts-expect-error
    "app/routes/login.tsx"
  );
  import.meta.hot.lastModified = "1738662837905.6753";
}
function Login() {
  _s();
  const [searchParams] = useSearchParams();
  const redirectTo = searchParams.get("redirectTo") || "/";
  const actionData = useActionData();
  const [showPassword, setShowPassword] = React.useState(false);
  return /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)("main", { className: "flex-1 min-h-[calc(100vh-12rem)] grid place-items-center bg-muted/50 -mt-[1px]", children: /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)(Card, { className: "w-full max-w-md mx-4 shadow-lg", children: [
    /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)(CardHeader, { className: "space-y-4", children: [
      /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)("div", { className: "flex justify-center", children: /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)("img", { src: "/images/logos/logo.svg", alt: "AI4MDE Logo", className: "h-12 w-12" }, void 0, false, {
        fileName: "app/routes/login.tsx",
        lineNumber: 81,
        columnNumber: 13
      }, this) }, void 0, false, {
        fileName: "app/routes/login.tsx",
        lineNumber: 80,
        columnNumber: 11
      }, this),
      /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)("div", { className: "text-center", children: [
        /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)(CardTitle, { children: "Welcome to AI4MDE" }, void 0, false, {
          fileName: "app/routes/login.tsx",
          lineNumber: 84,
          columnNumber: 13
        }, this),
        /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)(CardDescription, { children: "Sign in to your account" }, void 0, false, {
          fileName: "app/routes/login.tsx",
          lineNumber: 85,
          columnNumber: 13
        }, this)
      ] }, void 0, true, {
        fileName: "app/routes/login.tsx",
        lineNumber: 83,
        columnNumber: 11
      }, this)
    ] }, void 0, true, {
      fileName: "app/routes/login.tsx",
      lineNumber: 79,
      columnNumber: 9
    }, this),
    /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)(CardContent, { children: /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)(Form, { method: "post", className: "space-y-4", children: [
      /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)("input", { type: "hidden", name: "redirectTo", value: redirectTo }, void 0, false, {
        fileName: "app/routes/login.tsx",
        lineNumber: 90,
        columnNumber: 13
      }, this),
      /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)("div", { className: "space-y-2", children: [
        /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)(Label, { htmlFor: "username", children: "Username" }, void 0, false, {
          fileName: "app/routes/login.tsx",
          lineNumber: 92,
          columnNumber: 15
        }, this),
        /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)(Input, { id: "username", name: "username", type: "text", required: true, placeholder: "Enter your username" }, void 0, false, {
          fileName: "app/routes/login.tsx",
          lineNumber: 93,
          columnNumber: 15
        }, this)
      ] }, void 0, true, {
        fileName: "app/routes/login.tsx",
        lineNumber: 91,
        columnNumber: 13
      }, this),
      /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)("div", { className: "space-y-2", children: [
        /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)(Label, { htmlFor: "password", children: "Password" }, void 0, false, {
          fileName: "app/routes/login.tsx",
          lineNumber: 96,
          columnNumber: 15
        }, this),
        /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)("div", { className: "relative", children: [
          /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)(Input, { id: "password", name: "password", type: showPassword ? "text" : "password", required: true, placeholder: "Enter your password" }, void 0, false, {
            fileName: "app/routes/login.tsx",
            lineNumber: 98,
            columnNumber: 17
          }, this),
          /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)(Button, { type: "button", variant: "ghost", size: "icon", className: "absolute right-0 top-0 h-full px-2 py-2 hover:bg-transparent", onClick: () => setShowPassword(!showPassword), children: [
            showPassword ? /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)(EyeOff, { className: "h-10 w-10 text-muted-foreground" }, void 0, false, {
              fileName: "app/routes/login.tsx",
              lineNumber: 100,
              columnNumber: 35
            }, this) : /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)(Eye, { className: "h-10 w-10 text-muted-foreground" }, void 0, false, {
              fileName: "app/routes/login.tsx",
              lineNumber: 100,
              columnNumber: 92
            }, this),
            /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)("span", { className: "sr-only", children: showPassword ? "Hide password" : "Show password" }, void 0, false, {
              fileName: "app/routes/login.tsx",
              lineNumber: 101,
              columnNumber: 19
            }, this)
          ] }, void 0, true, {
            fileName: "app/routes/login.tsx",
            lineNumber: 99,
            columnNumber: 17
          }, this)
        ] }, void 0, true, {
          fileName: "app/routes/login.tsx",
          lineNumber: 97,
          columnNumber: 15
        }, this)
      ] }, void 0, true, {
        fileName: "app/routes/login.tsx",
        lineNumber: 95,
        columnNumber: 13
      }, this),
      actionData?.error && /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)("div", { className: "text-sm text-red-500", children: actionData.error }, void 0, false, {
        fileName: "app/routes/login.tsx",
        lineNumber: 107,
        columnNumber: 35
      }, this),
      /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)(Button, { type: "submit", className: "w-full", children: "Sign in" }, void 0, false, {
        fileName: "app/routes/login.tsx",
        lineNumber: 108,
        columnNumber: 13
      }, this)
    ] }, void 0, true, {
      fileName: "app/routes/login.tsx",
      lineNumber: 89,
      columnNumber: 11
    }, this) }, void 0, false, {
      fileName: "app/routes/login.tsx",
      lineNumber: 88,
      columnNumber: 9
    }, this)
  ] }, void 0, true, {
    fileName: "app/routes/login.tsx",
    lineNumber: 78,
    columnNumber: 7
  }, this) }, void 0, false, {
    fileName: "app/routes/login.tsx",
    lineNumber: 77,
    columnNumber: 10
  }, this);
}
_s(Login, "4XgOQEnkOclHNsqnKB8ZaeWPE2o=", false, function() {
  return [useSearchParams, useActionData];
});
_c = Login;
var _c;
$RefreshReg$(_c, "Login");
window.$RefreshReg$ = prevRefreshReg;
window.$RefreshSig$ = prevRefreshSig;
export {
  Login as default
};
//# sourceMappingURL=/build/routes/login-ONMPRLQ2.js.map
