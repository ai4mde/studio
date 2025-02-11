import {
  useOptionalUser
} from "/build/_shared/chunk-IVLWEOHB.js";
import {
  ThemeProvider,
  ThemeToggle
} from "/build/_shared/chunk-LH4FQSYZ.js";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger
} from "/build/_shared/chunk-5SXLN5D2.js";
import {
  NotFound
} from "/build/_shared/chunk-PTI7Q65L.js";
import "/build/_shared/chunk-RX7TAKA2.js";
import "/build/_shared/chunk-QATI3NSB.js";
import {
  Button
} from "/build/_shared/chunk-MI2YJZX6.js";
import "/build/_shared/chunk-2WFCNDEW.js";
import "/build/_shared/chunk-X6FLJXIJ.js";
import {
  Link,
  Links,
  LiveReload,
  Meta,
  Outlet,
  Scripts,
  ScrollRestoration,
  isRouteErrorResponse,
  useNavigate,
  useRouteError,
  useSubmit
} from "/build/_shared/chunk-5SMQHKI5.js";
import {
  BookOpen,
  ChevronDown,
  FileText,
  Laptop,
  LogIn,
  LogOut,
  MessageSquare,
  User
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
  __commonJS,
  __toESM
} from "/build/_shared/chunk-PZDJHGND.js";

// empty-module:./services/session.server
var require_session = __commonJS({
  "empty-module:./services/session.server"(exports, module) {
    module.exports = {};
  }
});

// css-bundle-plugin-ns:@remix-run/css-bundle
var cssBundleHref = "/build/css-bundle-ESK4IE6X.css";

// app/components/layout/user-menu.tsx
var import_jsx_dev_runtime = __toESM(require_jsx_dev_runtime(), 1);
if (!window.$RefreshReg$ || !window.$RefreshSig$ || !window.$RefreshRuntime$) {
  console.warn("remix:hmr: React Fast Refresh only works when the Remix compiler is running in development mode.");
} else {
  prevRefreshReg = window.$RefreshReg$;
  prevRefreshSig = window.$RefreshSig$;
  window.$RefreshReg$ = (type, id) => {
    window.$RefreshRuntime$.register(type, '"app/components/layout/user-menu.tsx"' + id);
  };
  window.$RefreshSig$ = window.$RefreshRuntime$.createSignatureFunctionForTransform;
}
var prevRefreshReg;
var prevRefreshSig;
var _s = $RefreshSig$();
if (import.meta) {
  import.meta.hot = createHotContext(
    //@ts-expect-error
    "app/components/layout/user-menu.tsx"
  );
  import.meta.hot.lastModified = "1738662837908.6753";
}
function UserMenu({
  user
}) {
  _s();
  const submit = useSubmit();
  const handleLogout = () => {
    submit(null, {
      method: "post",
      action: "/logout"
    });
  };
  return /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)(DropdownMenu, { children: [
    /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)(DropdownMenuTrigger, { asChild: true, children: /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)(Button, { variant: "ghost", size: "icon", className: "relative", children: /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)(User, { className: "h-5 w-5" }, void 0, false, {
      fileName: "app/components/layout/user-menu.tsx",
      lineNumber: 41,
      columnNumber: 11
    }, this) }, void 0, false, {
      fileName: "app/components/layout/user-menu.tsx",
      lineNumber: 40,
      columnNumber: 9
    }, this) }, void 0, false, {
      fileName: "app/components/layout/user-menu.tsx",
      lineNumber: 39,
      columnNumber: 7
    }, this),
    /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)(DropdownMenuContent, { align: "end", className: "w-56", children: [
      /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)(DropdownMenuLabel, { children: "My Account" }, void 0, false, {
        fileName: "app/components/layout/user-menu.tsx",
        lineNumber: 45,
        columnNumber: 9
      }, this),
      /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)(DropdownMenuSeparator, {}, void 0, false, {
        fileName: "app/components/layout/user-menu.tsx",
        lineNumber: 46,
        columnNumber: 9
      }, this),
      /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)(DropdownMenuItem, { className: "flex flex-col items-start", children: [
        /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)("span", { className: "font-medium", children: [
          "User:  ",
          user.username
        ] }, void 0, true, {
          fileName: "app/components/layout/user-menu.tsx",
          lineNumber: 48,
          columnNumber: 11
        }, this),
        /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)("span", { className: "text-xs text-muted-foreground", children: [
          "Group: ",
          user.group_name
        ] }, void 0, true, {
          fileName: "app/components/layout/user-menu.tsx",
          lineNumber: 49,
          columnNumber: 11
        }, this)
      ] }, void 0, true, {
        fileName: "app/components/layout/user-menu.tsx",
        lineNumber: 47,
        columnNumber: 9
      }, this),
      /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)(DropdownMenuSeparator, {}, void 0, false, {
        fileName: "app/components/layout/user-menu.tsx",
        lineNumber: 51,
        columnNumber: 9
      }, this),
      /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)(DropdownMenuItem, { onSelect: handleLogout, className: "text-red-600 dark:text-red-400", children: [
        /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)(LogOut, { className: "mr-2 h-4 w-4" }, void 0, false, {
          fileName: "app/components/layout/user-menu.tsx",
          lineNumber: 53,
          columnNumber: 11
        }, this),
        /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)("span", { children: "Logout" }, void 0, false, {
          fileName: "app/components/layout/user-menu.tsx",
          lineNumber: 54,
          columnNumber: 11
        }, this)
      ] }, void 0, true, {
        fileName: "app/components/layout/user-menu.tsx",
        lineNumber: 52,
        columnNumber: 9
      }, this)
    ] }, void 0, true, {
      fileName: "app/components/layout/user-menu.tsx",
      lineNumber: 44,
      columnNumber: 7
    }, this)
  ] }, void 0, true, {
    fileName: "app/components/layout/user-menu.tsx",
    lineNumber: 38,
    columnNumber: 10
  }, this);
}
_s(UserMenu, "/qFIYzOq2OE/SSM69ffcyD0/sOE=", false, function() {
  return [useSubmit];
});
_c = UserMenu;
var _c;
$RefreshReg$(_c, "UserMenu");
window.$RefreshReg$ = prevRefreshReg;
window.$RefreshSig$ = prevRefreshSig;

// app/components/layout/header.tsx
var import_jsx_dev_runtime2 = __toESM(require_jsx_dev_runtime(), 1);
if (!window.$RefreshReg$ || !window.$RefreshSig$ || !window.$RefreshRuntime$) {
  console.warn("remix:hmr: React Fast Refresh only works when the Remix compiler is running in development mode.");
} else {
  prevRefreshReg = window.$RefreshReg$;
  prevRefreshSig = window.$RefreshSig$;
  window.$RefreshReg$ = (type, id) => {
    window.$RefreshRuntime$.register(type, '"app/components/layout/header.tsx"' + id);
  };
  window.$RefreshSig$ = window.$RefreshRuntime$.createSignatureFunctionForTransform;
}
var prevRefreshReg;
var prevRefreshSig;
var _s2 = $RefreshSig$();
if (import.meta) {
  import.meta.hot = createHotContext(
    //@ts-expect-error
    "app/components/layout/header.tsx"
  );
  import.meta.hot.lastModified = "1738670752348.8333";
}
function Header() {
  _s2();
  const user = useOptionalUser();
  const navigate = useNavigate();
  return /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)("header", { className: "sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60", children: /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)("div", { className: "container flex h-14 items-center", children: [
    /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)("div", { className: "mr-4 flex", children: /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)(Link, { to: "/", className: "mr-6 flex items-center space-x-2", children: [
      /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)("img", { src: "/images/logos/logo.svg", alt: "AI4MDE Logo", className: "h-6 w-6" }, void 0, false, {
        fileName: "app/components/layout/header.tsx",
        lineNumber: 38,
        columnNumber: 13
      }, this),
      /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)("span", { className: "font-bold", children: "AI4MDE" }, void 0, false, {
        fileName: "app/components/layout/header.tsx",
        lineNumber: 39,
        columnNumber: 13
      }, this)
    ] }, void 0, true, {
      fileName: "app/components/layout/header.tsx",
      lineNumber: 37,
      columnNumber: 11
    }, this) }, void 0, false, {
      fileName: "app/components/layout/header.tsx",
      lineNumber: 36,
      columnNumber: 9
    }, this),
    /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)("div", { className: "flex flex-1 items-center justify-between space-x-2 md:justify-end", children: /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)("nav", { className: "flex items-center space-x-2", children: [
      /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)(Button, { asChild: true, variant: "ghost", className: "gap-2", children: /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)(Link, { to: "/chat", children: [
        /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)(MessageSquare, { className: "h-4 w-4" }, void 0, false, {
          fileName: "app/components/layout/header.tsx",
          lineNumber: 46,
          columnNumber: 17
        }, this),
        "Chat"
      ] }, void 0, true, {
        fileName: "app/components/layout/header.tsx",
        lineNumber: 45,
        columnNumber: 15
      }, this) }, void 0, false, {
        fileName: "app/components/layout/header.tsx",
        lineNumber: 44,
        columnNumber: 13
      }, this),
      /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)(DropdownMenu, { children: [
        /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)(DropdownMenuTrigger, { asChild: true, children: /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)(Button, { variant: "ghost", className: "gap-2", children: [
          /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)(FileText, { className: "h-4 w-4" }, void 0, false, {
            fileName: "app/components/layout/header.tsx",
            lineNumber: 54,
            columnNumber: 19
          }, this),
          "Docs",
          /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)(ChevronDown, { className: "h-4 w-4" }, void 0, false, {
            fileName: "app/components/layout/header.tsx",
            lineNumber: 56,
            columnNumber: 19
          }, this)
        ] }, void 0, true, {
          fileName: "app/components/layout/header.tsx",
          lineNumber: 53,
          columnNumber: 17
        }, this) }, void 0, false, {
          fileName: "app/components/layout/header.tsx",
          lineNumber: 52,
          columnNumber: 15
        }, this),
        /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)(DropdownMenuContent, { align: "start", children: [
          /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)(DropdownMenuItem, { asChild: true, children: /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)(Link, { to: "/guide", className: "flex items-center gap-2", children: [
            /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)(BookOpen, { className: "h-4 w-4" }, void 0, false, {
              fileName: "app/components/layout/header.tsx",
              lineNumber: 62,
              columnNumber: 21
            }, this),
            "Guide"
          ] }, void 0, true, {
            fileName: "app/components/layout/header.tsx",
            lineNumber: 61,
            columnNumber: 19
          }, this) }, void 0, false, {
            fileName: "app/components/layout/header.tsx",
            lineNumber: 60,
            columnNumber: 17
          }, this),
          user && /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)(import_jsx_dev_runtime2.Fragment, { children: [
            /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)(DropdownMenuItem, { asChild: true, children: /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)(Link, { to: "/srsdocs", className: "flex items-center gap-2", children: [
              /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)(FileText, { className: "h-4 w-4" }, void 0, false, {
                fileName: "app/components/layout/header.tsx",
                lineNumber: 69,
                columnNumber: 25
              }, this),
              "SRS Docs"
            ] }, void 0, true, {
              fileName: "app/components/layout/header.tsx",
              lineNumber: 68,
              columnNumber: 23
            }, this) }, void 0, false, {
              fileName: "app/components/layout/header.tsx",
              lineNumber: 67,
              columnNumber: 21
            }, this),
            /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)(DropdownMenuItem, { asChild: true, children: /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)(Link, { to: "/interviews", className: "flex items-center gap-2", children: [
              /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)(MessageSquare, { className: "h-4 w-4" }, void 0, false, {
                fileName: "app/components/layout/header.tsx",
                lineNumber: 75,
                columnNumber: 25
              }, this),
              "Interviews"
            ] }, void 0, true, {
              fileName: "app/components/layout/header.tsx",
              lineNumber: 74,
              columnNumber: 23
            }, this) }, void 0, false, {
              fileName: "app/components/layout/header.tsx",
              lineNumber: 73,
              columnNumber: 21
            }, this)
          ] }, void 0, true, {
            fileName: "app/components/layout/header.tsx",
            lineNumber: 66,
            columnNumber: 26
          }, this)
        ] }, void 0, true, {
          fileName: "app/components/layout/header.tsx",
          lineNumber: 59,
          columnNumber: 15
        }, this)
      ] }, void 0, true, {
        fileName: "app/components/layout/header.tsx",
        lineNumber: 51,
        columnNumber: 13
      }, this),
      user && /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)(Button, { asChild: true, variant: "ghost", className: "gap-2", children: /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)("a", { href: `https://${user.group_name}-studio.ai4mde.org`, target: "_blank", rel: "noopener noreferrer", children: [
        /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)(Laptop, { className: "h-4 w-4" }, void 0, false, {
          fileName: "app/components/layout/header.tsx",
          lineNumber: 85,
          columnNumber: 19
        }, this),
        "Studio"
      ] }, void 0, true, {
        fileName: "app/components/layout/header.tsx",
        lineNumber: 84,
        columnNumber: 17
      }, this) }, void 0, false, {
        fileName: "app/components/layout/header.tsx",
        lineNumber: 83,
        columnNumber: 22
      }, this),
      /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)(ThemeToggle, {}, void 0, false, {
        fileName: "app/components/layout/header.tsx",
        lineNumber: 89,
        columnNumber: 13
      }, this),
      user ? /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)(UserMenu, { user }, void 0, false, {
        fileName: "app/components/layout/header.tsx",
        lineNumber: 90,
        columnNumber: 21
      }, this) : /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)(Button, { asChild: true, variant: "ghost", className: "gap-2", children: /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)(Link, { to: "/login", children: [
        /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)(LogIn, { className: "h-4 w-4" }, void 0, false, {
          fileName: "app/components/layout/header.tsx",
          lineNumber: 92,
          columnNumber: 19
        }, this),
        "Login"
      ] }, void 0, true, {
        fileName: "app/components/layout/header.tsx",
        lineNumber: 91,
        columnNumber: 17
      }, this) }, void 0, false, {
        fileName: "app/components/layout/header.tsx",
        lineNumber: 90,
        columnNumber: 48
      }, this)
    ] }, void 0, true, {
      fileName: "app/components/layout/header.tsx",
      lineNumber: 43,
      columnNumber: 11
    }, this) }, void 0, false, {
      fileName: "app/components/layout/header.tsx",
      lineNumber: 42,
      columnNumber: 9
    }, this)
  ] }, void 0, true, {
    fileName: "app/components/layout/header.tsx",
    lineNumber: 35,
    columnNumber: 7
  }, this) }, void 0, false, {
    fileName: "app/components/layout/header.tsx",
    lineNumber: 34,
    columnNumber: 10
  }, this);
}
_s2(Header, "/1Q/kxBPVXVAAwL/ptPMeQeygug=", false, function() {
  return [useOptionalUser, useNavigate];
});
_c2 = Header;
var _c2;
$RefreshReg$(_c2, "Header");
window.$RefreshReg$ = prevRefreshReg;
window.$RefreshSig$ = prevRefreshSig;

// app/components/layout/footer.tsx
var import_jsx_dev_runtime3 = __toESM(require_jsx_dev_runtime(), 1);
if (!window.$RefreshReg$ || !window.$RefreshSig$ || !window.$RefreshRuntime$) {
  console.warn("remix:hmr: React Fast Refresh only works when the Remix compiler is running in development mode.");
} else {
  prevRefreshReg = window.$RefreshReg$;
  prevRefreshSig = window.$RefreshSig$;
  window.$RefreshReg$ = (type, id) => {
    window.$RefreshRuntime$.register(type, '"app/components/layout/footer.tsx"' + id);
  };
  window.$RefreshSig$ = window.$RefreshRuntime$.createSignatureFunctionForTransform;
}
var prevRefreshReg;
var prevRefreshSig;
if (import.meta) {
  import.meta.hot = createHotContext(
    //@ts-expect-error
    "app/components/layout/footer.tsx"
  );
  import.meta.hot.lastModified = "1738662837908.6753";
}
function Footer() {
  return /* @__PURE__ */ (0, import_jsx_dev_runtime3.jsxDEV)("footer", { className: "border-t", children: /* @__PURE__ */ (0, import_jsx_dev_runtime3.jsxDEV)("div", { className: "container flex flex-col items-center py-8 gap-4", children: [
    /* @__PURE__ */ (0, import_jsx_dev_runtime3.jsxDEV)("nav", { className: "flex gap-4", children: [
      /* @__PURE__ */ (0, import_jsx_dev_runtime3.jsxDEV)(Link, { to: "/privacy", className: "text-sm underline underline-offset-4", children: "Privacy" }, void 0, false, {
        fileName: "app/components/layout/footer.tsx",
        lineNumber: 27,
        columnNumber: 11
      }, this),
      /* @__PURE__ */ (0, import_jsx_dev_runtime3.jsxDEV)(Link, { to: "/terms", className: "text-sm underline underline-offset-4", children: "Terms" }, void 0, false, {
        fileName: "app/components/layout/footer.tsx",
        lineNumber: 30,
        columnNumber: 11
      }, this),
      /* @__PURE__ */ (0, import_jsx_dev_runtime3.jsxDEV)(Link, { to: "/contact", className: "text-sm underline underline-offset-4", children: "Contact" }, void 0, false, {
        fileName: "app/components/layout/footer.tsx",
        lineNumber: 33,
        columnNumber: 11
      }, this)
    ] }, void 0, true, {
      fileName: "app/components/layout/footer.tsx",
      lineNumber: 26,
      columnNumber: 9
    }, this),
    /* @__PURE__ */ (0, import_jsx_dev_runtime3.jsxDEV)("p", { className: "text-center text-sm leading-loose", children: [
      "Built by",
      " ",
      /* @__PURE__ */ (0, import_jsx_dev_runtime3.jsxDEV)("a", { href: "https://www.universiteitleiden.nl/en", target: "_blank", rel: "noreferrer", className: "font-medium underline underline-offset-4", children: "Leiden University" }, void 0, false, {
        fileName: "app/components/layout/footer.tsx",
        lineNumber: 39,
        columnNumber: 11
      }, this),
      ". The source code is available on",
      " ",
      /* @__PURE__ */ (0, import_jsx_dev_runtime3.jsxDEV)("a", { href: "https://github.com/LIACS/AI4MDE", target: "_blank", rel: "noreferrer", className: "font-medium underline underline-offset-4", children: "GitHub" }, void 0, false, {
        fileName: "app/components/layout/footer.tsx",
        lineNumber: 43,
        columnNumber: 11
      }, this),
      "."
    ] }, void 0, true, {
      fileName: "app/components/layout/footer.tsx",
      lineNumber: 37,
      columnNumber: 9
    }, this)
  ] }, void 0, true, {
    fileName: "app/components/layout/footer.tsx",
    lineNumber: 25,
    columnNumber: 7
  }, this) }, void 0, false, {
    fileName: "app/components/layout/footer.tsx",
    lineNumber: 24,
    columnNumber: 10
  }, this);
}
_c3 = Footer;
var _c3;
$RefreshReg$(_c3, "Footer");
window.$RefreshReg$ = prevRefreshReg;
window.$RefreshSig$ = prevRefreshSig;

// app/styles/globals.css
var globals_default = "/build/_assets/globals-IZMLHUF4.css";

// app/root.tsx
var import_session = __toESM(require_session(), 1);
var import_jsx_dev_runtime4 = __toESM(require_jsx_dev_runtime(), 1);
if (!window.$RefreshReg$ || !window.$RefreshSig$ || !window.$RefreshRuntime$) {
  console.warn("remix:hmr: React Fast Refresh only works when the Remix compiler is running in development mode.");
} else {
  prevRefreshReg = window.$RefreshReg$;
  prevRefreshSig = window.$RefreshSig$;
  window.$RefreshReg$ = (type, id) => {
    window.$RefreshRuntime$.register(type, '"app/root.tsx"' + id);
  };
  window.$RefreshSig$ = window.$RefreshRuntime$.createSignatureFunctionForTransform;
}
var prevRefreshReg;
var prevRefreshSig;
var _s3 = $RefreshSig$();
if (import.meta) {
  import.meta.hot = createHotContext(
    //@ts-expect-error
    "app/root.tsx"
  );
}
var meta = () => {
  return [{
    title: "AI4MDE"
  }, {
    name: "description",
    content: "AI-powered Model-Driven Engineering"
  }, {
    name: "viewport",
    content: "width=device-width,initial-scale=1"
  }];
};
var links = () => [{
  rel: "preconnect",
  href: "https://fonts.googleapis.com"
}, {
  rel: "preconnect",
  href: "https://fonts.gstatic.com",
  crossOrigin: "anonymous"
}, {
  rel: "stylesheet",
  href: "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap"
}, ...cssBundleHref ? [{
  rel: "stylesheet",
  href: cssBundleHref
}] : [], {
  rel: "stylesheet",
  href: globals_default
}];
function ErrorBoundary() {
  _s3();
  const error = useRouteError();
  if (isRouteErrorResponse(error) && error.status === 404) {
    return /* @__PURE__ */ (0, import_jsx_dev_runtime4.jsxDEV)(NotFound, {}, void 0, false, {
      fileName: "app/root.tsx",
      lineNumber: 71,
      columnNumber: 12
    }, this);
  }
  return /* @__PURE__ */ (0, import_jsx_dev_runtime4.jsxDEV)("div", { className: "min-h-screen flex items-center justify-center", children: /* @__PURE__ */ (0, import_jsx_dev_runtime4.jsxDEV)("div", { className: "text-center space-y-4", children: [
    /* @__PURE__ */ (0, import_jsx_dev_runtime4.jsxDEV)("h1", { className: "text-4xl font-bold", children: "Oops!" }, void 0, false, {
      fileName: "app/root.tsx",
      lineNumber: 75,
      columnNumber: 9
    }, this),
    /* @__PURE__ */ (0, import_jsx_dev_runtime4.jsxDEV)("p", { className: "text-xl text-muted-foreground", children: "Something went wrong." }, void 0, false, {
      fileName: "app/root.tsx",
      lineNumber: 76,
      columnNumber: 9
    }, this),
    /* @__PURE__ */ (0, import_jsx_dev_runtime4.jsxDEV)(Button, { asChild: true, children: /* @__PURE__ */ (0, import_jsx_dev_runtime4.jsxDEV)(Link, { to: "/", children: "Back to Home" }, void 0, false, {
      fileName: "app/root.tsx",
      lineNumber: 78,
      columnNumber: 11
    }, this) }, void 0, false, {
      fileName: "app/root.tsx",
      lineNumber: 77,
      columnNumber: 9
    }, this)
  ] }, void 0, true, {
    fileName: "app/root.tsx",
    lineNumber: 74,
    columnNumber: 7
  }, this) }, void 0, false, {
    fileName: "app/root.tsx",
    lineNumber: 73,
    columnNumber: 10
  }, this);
}
_s3(ErrorBoundary, "oAgjgbJzsRXlB89+MoVumxMQqKM=", false, function() {
  return [useRouteError];
});
_c4 = ErrorBoundary;
function App() {
  return /* @__PURE__ */ (0, import_jsx_dev_runtime4.jsxDEV)("html", { lang: "en", suppressHydrationWarning: true, children: [
    /* @__PURE__ */ (0, import_jsx_dev_runtime4.jsxDEV)("head", { children: [
      /* @__PURE__ */ (0, import_jsx_dev_runtime4.jsxDEV)("meta", { charSet: "utf-8" }, void 0, false, {
        fileName: "app/root.tsx",
        lineNumber: 90,
        columnNumber: 9
      }, this),
      /* @__PURE__ */ (0, import_jsx_dev_runtime4.jsxDEV)("meta", { name: "viewport", content: "width=device-width, initial-scale=1" }, void 0, false, {
        fileName: "app/root.tsx",
        lineNumber: 91,
        columnNumber: 9
      }, this),
      /* @__PURE__ */ (0, import_jsx_dev_runtime4.jsxDEV)("link", { rel: "icon", type: "image/svg+xml", href: "/images/logos/logo.svg" }, void 0, false, {
        fileName: "app/root.tsx",
        lineNumber: 92,
        columnNumber: 9
      }, this),
      /* @__PURE__ */ (0, import_jsx_dev_runtime4.jsxDEV)(Meta, {}, void 0, false, {
        fileName: "app/root.tsx",
        lineNumber: 93,
        columnNumber: 9
      }, this),
      /* @__PURE__ */ (0, import_jsx_dev_runtime4.jsxDEV)(Links, {}, void 0, false, {
        fileName: "app/root.tsx",
        lineNumber: 94,
        columnNumber: 9
      }, this)
    ] }, void 0, true, {
      fileName: "app/root.tsx",
      lineNumber: 89,
      columnNumber: 7
    }, this),
    /* @__PURE__ */ (0, import_jsx_dev_runtime4.jsxDEV)("body", { className: "min-h-screen bg-background font-sans antialiased", children: [
      /* @__PURE__ */ (0, import_jsx_dev_runtime4.jsxDEV)(ThemeProvider, { children: /* @__PURE__ */ (0, import_jsx_dev_runtime4.jsxDEV)("div", { className: "relative flex min-h-screen flex-col", children: [
        /* @__PURE__ */ (0, import_jsx_dev_runtime4.jsxDEV)(Header, {}, void 0, false, {
          fileName: "app/root.tsx",
          lineNumber: 99,
          columnNumber: 13
        }, this),
        /* @__PURE__ */ (0, import_jsx_dev_runtime4.jsxDEV)("main", { className: "flex-1", children: /* @__PURE__ */ (0, import_jsx_dev_runtime4.jsxDEV)(Outlet, {}, void 0, false, {
          fileName: "app/root.tsx",
          lineNumber: 101,
          columnNumber: 15
        }, this) }, void 0, false, {
          fileName: "app/root.tsx",
          lineNumber: 100,
          columnNumber: 13
        }, this),
        /* @__PURE__ */ (0, import_jsx_dev_runtime4.jsxDEV)(Footer, {}, void 0, false, {
          fileName: "app/root.tsx",
          lineNumber: 103,
          columnNumber: 13
        }, this)
      ] }, void 0, true, {
        fileName: "app/root.tsx",
        lineNumber: 98,
        columnNumber: 11
      }, this) }, void 0, false, {
        fileName: "app/root.tsx",
        lineNumber: 97,
        columnNumber: 9
      }, this),
      /* @__PURE__ */ (0, import_jsx_dev_runtime4.jsxDEV)(ScrollRestoration, {}, void 0, false, {
        fileName: "app/root.tsx",
        lineNumber: 106,
        columnNumber: 9
      }, this),
      /* @__PURE__ */ (0, import_jsx_dev_runtime4.jsxDEV)(Scripts, {}, void 0, false, {
        fileName: "app/root.tsx",
        lineNumber: 107,
        columnNumber: 9
      }, this),
      /* @__PURE__ */ (0, import_jsx_dev_runtime4.jsxDEV)(LiveReload, {}, void 0, false, {
        fileName: "app/root.tsx",
        lineNumber: 108,
        columnNumber: 9
      }, this)
    ] }, void 0, true, {
      fileName: "app/root.tsx",
      lineNumber: 96,
      columnNumber: 7
    }, this)
  ] }, void 0, true, {
    fileName: "app/root.tsx",
    lineNumber: 88,
    columnNumber: 10
  }, this);
}
_c22 = App;
var _c4;
var _c22;
$RefreshReg$(_c4, "ErrorBoundary");
$RefreshReg$(_c22, "App");
window.$RefreshReg$ = prevRefreshReg;
window.$RefreshSig$ = prevRefreshSig;
export {
  ErrorBoundary,
  App as default,
  links,
  meta
};
//# sourceMappingURL=/build/root-2W3GD42X.js.map
