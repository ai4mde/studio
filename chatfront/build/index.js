var __defProp = Object.defineProperty;
var __export = (target, all) => {
  for (var name in all)
    __defProp(target, name, { get: all[name], enumerable: !0 });
};

// node_modules/.pnpm/@remix-run+dev@2.15.2_@remix-run+react@2.15.2_react-dom@18.3.1_react@18.3.1__react@18.3_558bd7ed9818072fa785260deb0bdc45/node_modules/@remix-run/dev/dist/config/defaults/entry.server.node.tsx
var entry_server_node_exports = {};
__export(entry_server_node_exports, {
  default: () => handleRequest
});
import { PassThrough } from "node:stream";
import { createReadableStreamFromReadable } from "@remix-run/node";
import { RemixServer } from "@remix-run/react";
import * as isbotModule from "isbot";
import { renderToPipeableStream } from "react-dom/server";
import { jsxDEV } from "react/jsx-dev-runtime";
var ABORT_DELAY = 5e3;
function handleRequest(request, responseStatusCode, responseHeaders, remixContext, loadContext) {
  return isBotRequest(request.headers.get("user-agent")) || remixContext.isSpaMode ? handleBotRequest(
    request,
    responseStatusCode,
    responseHeaders,
    remixContext
  ) : handleBrowserRequest(
    request,
    responseStatusCode,
    responseHeaders,
    remixContext
  );
}
function isBotRequest(userAgent) {
  return userAgent ? "isbot" in isbotModule && typeof isbotModule.isbot == "function" ? isbotModule.isbot(userAgent) : "default" in isbotModule && typeof isbotModule.default == "function" ? isbotModule.default(userAgent) : !1 : !1;
}
function handleBotRequest(request, responseStatusCode, responseHeaders, remixContext) {
  return new Promise((resolve, reject) => {
    let shellRendered = !1, { pipe, abort } = renderToPipeableStream(
      /* @__PURE__ */ jsxDEV(
        RemixServer,
        {
          context: remixContext,
          url: request.url,
          abortDelay: ABORT_DELAY
        },
        void 0,
        !1,
        {
          fileName: "node_modules/.pnpm/@remix-run+dev@2.15.2_@remix-run+react@2.15.2_react-dom@18.3.1_react@18.3.1__react@18.3_558bd7ed9818072fa785260deb0bdc45/node_modules/@remix-run/dev/dist/config/defaults/entry.server.node.tsx",
          lineNumber: 66,
          columnNumber: 7
        },
        this
      ),
      {
        onAllReady() {
          shellRendered = !0;
          let body = new PassThrough(), stream = createReadableStreamFromReadable(body);
          responseHeaders.set("Content-Type", "text/html"), resolve(
            new Response(stream, {
              headers: responseHeaders,
              status: responseStatusCode
            })
          ), pipe(body);
        },
        onShellError(error) {
          reject(error);
        },
        onError(error) {
          responseStatusCode = 500, shellRendered && console.error(error);
        }
      }
    );
    setTimeout(abort, ABORT_DELAY);
  });
}
function handleBrowserRequest(request, responseStatusCode, responseHeaders, remixContext) {
  return new Promise((resolve, reject) => {
    let shellRendered = !1, { pipe, abort } = renderToPipeableStream(
      /* @__PURE__ */ jsxDEV(
        RemixServer,
        {
          context: remixContext,
          url: request.url,
          abortDelay: ABORT_DELAY
        },
        void 0,
        !1,
        {
          fileName: "node_modules/.pnpm/@remix-run+dev@2.15.2_@remix-run+react@2.15.2_react-dom@18.3.1_react@18.3.1__react@18.3_558bd7ed9818072fa785260deb0bdc45/node_modules/@remix-run/dev/dist/config/defaults/entry.server.node.tsx",
          lineNumber: 116,
          columnNumber: 7
        },
        this
      ),
      {
        onShellReady() {
          shellRendered = !0;
          let body = new PassThrough(), stream = createReadableStreamFromReadable(body);
          responseHeaders.set("Content-Type", "text/html"), resolve(
            new Response(stream, {
              headers: responseHeaders,
              status: responseStatusCode
            })
          ), pipe(body);
        },
        onShellError(error) {
          reject(error);
        },
        onError(error) {
          responseStatusCode = 500, shellRendered && console.error(error);
        }
      }
    );
    setTimeout(abort, ABORT_DELAY);
  });
}

// app/root.tsx
var root_exports = {};
__export(root_exports, {
  ErrorBoundary: () => ErrorBoundary,
  default: () => App,
  links: () => links,
  loader: () => loader,
  meta: () => meta
});

// css-bundle-plugin-ns:@remix-run/css-bundle
var cssBundleHref = "/build/css-bundle-ESK4IE6X.css";

// app/root.tsx
import {
  Links,
  LiveReload,
  Meta,
  Outlet,
  Scripts,
  ScrollRestoration,
  json as json2,
  isRouteErrorResponse,
  useRouteError,
  Link as Link4
} from "@remix-run/react";

// app/components/ui/button.tsx
import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva } from "class-variance-authority";

// app/lib/utils.ts
import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";
function cn(...inputs) {
  return twMerge(clsx(inputs));
}

// app/components/ui/button.tsx
import { jsxDEV as jsxDEV2 } from "react/jsx-dev-runtime";
var buttonVariants = cva(
  "inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground shadow hover:bg-primary/90",
        destructive: "bg-destructive text-destructive-foreground shadow-sm hover:bg-destructive/90",
        outline: "border border-input bg-background shadow-sm hover:bg-accent hover:text-accent-foreground",
        secondary: "bg-secondary text-secondary-foreground shadow-sm hover:bg-secondary/80",
        ghost: "hover:bg-accent hover:text-accent-foreground",
        link: "text-primary underline-offset-4 hover:underline"
      },
      size: {
        default: "h-9 px-4 py-2",
        sm: "h-8 rounded-md px-3 text-xs",
        lg: "h-10 rounded-md px-8",
        icon: "h-9 w-9"
      }
    },
    defaultVariants: {
      variant: "default",
      size: "default"
    }
  }
), Button = React.forwardRef(
  ({ className, variant, size, asChild = !1, ...props }, ref) => /* @__PURE__ */ jsxDEV2(
    asChild ? Slot : "button",
    {
      className: cn(buttonVariants({ variant, size, className })),
      ref,
      ...props
    },
    void 0,
    !1,
    {
      fileName: "app/components/ui/button.tsx",
      lineNumber: 47,
      columnNumber: 7
    },
    this
  )
);
Button.displayName = "Button";

// app/components/layout/header.tsx
import { Link, useNavigate } from "@remix-run/react";

// app/components/layout/theme-toggle.tsx
import { Moon, Sun } from "lucide-react";

// app/components/layout/theme-provider.tsx
import { createContext, useContext, useEffect as useEffect2 } from "react";

// app/hooks/use-local-storage.ts
import { useState } from "react";
function useLocalStorage(key, initialValue) {
  let [storedValue, setStoredValue] = useState(() => {
    if (typeof window > "u")
      return initialValue;
    try {
      let item = window.localStorage.getItem(key);
      return item ? JSON.parse(item) : initialValue;
    } catch (error) {
      return console.log(error), initialValue;
    }
  });
  return [storedValue, (value) => {
    try {
      let valueToStore = value instanceof Function ? value(storedValue) : value;
      setStoredValue(valueToStore), typeof window < "u" && window.localStorage.setItem(key, JSON.stringify(valueToStore));
    } catch (error) {
      console.log(error);
    }
  }];
}

// app/components/layout/theme-provider.tsx
import { jsxDEV as jsxDEV3 } from "react/jsx-dev-runtime";
var initialState = {
  theme: "system",
  setTheme: () => null
}, ThemeProviderContext = createContext(initialState);
function ThemeProvider({
  children,
  defaultTheme = "system"
}) {
  let [theme, setTheme] = useLocalStorage("theme", defaultTheme);
  useEffect2(() => {
    let root = window.document.documentElement;
    if (root.classList.remove("light", "dark"), theme === "system") {
      let systemTheme = window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
      root.classList.add(systemTheme);
      return;
    }
    root.classList.add(theme);
  }, [theme]);
  let value = {
    theme,
    setTheme: (theme2) => {
      setTheme(theme2);
    }
  };
  return /* @__PURE__ */ jsxDEV3(ThemeProviderContext.Provider, { value, children }, void 0, !1, {
    fileName: "app/components/layout/theme-provider.tsx",
    lineNumber: 55,
    columnNumber: 5
  }, this);
}
var useTheme = () => {
  let context = useContext(ThemeProviderContext);
  if (context === void 0)
    throw new Error("useTheme must be used within a ThemeProvider");
  return context;
};

// app/components/ui/dropdown-menu.tsx
import * as React2 from "react";
import * as DropdownMenuPrimitive from "@radix-ui/react-dropdown-menu";
import { ChevronRight } from "lucide-react";
import { jsxDEV as jsxDEV4 } from "react/jsx-dev-runtime";
var DropdownMenu = DropdownMenuPrimitive.Root, DropdownMenuTrigger = DropdownMenuPrimitive.Trigger;
var DropdownMenuSub = DropdownMenuPrimitive.Sub;
var DropdownMenuSubTrigger = React2.forwardRef(({ className, inset, children, ...props }, ref) => /* @__PURE__ */ jsxDEV4(
  DropdownMenuPrimitive.SubTrigger,
  {
    ref,
    className: cn(
      "flex cursor-default select-none items-center rounded-sm px-2 py-1.5 text-sm outline-none focus:bg-accent data-[state=open]:bg-accent",
      inset && "pl-8",
      className
    ),
    ...props,
    children: [
      children,
      /* @__PURE__ */ jsxDEV4(ChevronRight, { className: "ml-auto h-4 w-4" }, void 0, !1, {
        fileName: "app/components/ui/dropdown-menu.tsx",
        lineNumber: 35,
        columnNumber: 5
      }, this)
    ]
  },
  void 0,
  !0,
  {
    fileName: "app/components/ui/dropdown-menu.tsx",
    lineNumber: 25,
    columnNumber: 3
  },
  this
));
DropdownMenuSubTrigger.displayName = DropdownMenuPrimitive.SubTrigger.displayName;
var DropdownMenuSubContent = React2.forwardRef(({ className, ...props }, ref) => /* @__PURE__ */ jsxDEV4(
  DropdownMenuPrimitive.SubContent,
  {
    ref,
    className: cn(
      "z-50 min-w-[8rem] overflow-hidden rounded-md border bg-popover p-1 text-popover-foreground shadow-lg data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 data-[side=bottom]:slide-in-from-top-2 data-[side=left]:slide-in-from-right-2 data-[side=right]:slide-in-from-left-2 data-[side=top]:slide-in-from-bottom-2",
      className
    ),
    ...props
  },
  void 0,
  !1,
  {
    fileName: "app/components/ui/dropdown-menu.tsx",
    lineNumber: 45,
    columnNumber: 3
  },
  this
));
DropdownMenuSubContent.displayName = DropdownMenuPrimitive.SubContent.displayName;
var DropdownMenuContent = React2.forwardRef(({ className, sideOffset = 4, ...props }, ref) => /* @__PURE__ */ jsxDEV4(DropdownMenuPrimitive.Portal, { children: /* @__PURE__ */ jsxDEV4(
  DropdownMenuPrimitive.Content,
  {
    ref,
    sideOffset,
    className: cn(
      "z-50 min-w-[8rem] overflow-hidden rounded-md border bg-popover p-1 text-popover-foreground shadow-md data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 data-[side=bottom]:slide-in-from-top-2 data-[side=left]:slide-in-from-right-2 data-[side=right]:slide-in-from-left-2 data-[side=top]:slide-in-from-bottom-2",
      className
    ),
    ...props
  },
  void 0,
  !1,
  {
    fileName: "app/components/ui/dropdown-menu.tsx",
    lineNumber: 62,
    columnNumber: 5
  },
  this
) }, void 0, !1, {
  fileName: "app/components/ui/dropdown-menu.tsx",
  lineNumber: 61,
  columnNumber: 3
}, this));
DropdownMenuContent.displayName = DropdownMenuPrimitive.Content.displayName;
var DropdownMenuItem = React2.forwardRef(({ className, inset, ...props }, ref) => /* @__PURE__ */ jsxDEV4(
  DropdownMenuPrimitive.Item,
  {
    ref,
    className: cn(
      "relative flex cursor-default select-none items-center rounded-sm px-2 py-1.5 text-sm outline-none transition-colors focus:bg-accent focus:text-accent-foreground data-[disabled]:pointer-events-none data-[disabled]:opacity-50",
      inset && "pl-8",
      className
    ),
    ...props
  },
  void 0,
  !1,
  {
    fileName: "app/components/ui/dropdown-menu.tsx",
    lineNumber: 81,
    columnNumber: 3
  },
  this
));
DropdownMenuItem.displayName = DropdownMenuPrimitive.Item.displayName;
var DropdownMenuLabel = React2.forwardRef(({ className, inset, ...props }, ref) => /* @__PURE__ */ jsxDEV4(
  DropdownMenuPrimitive.Label,
  {
    ref,
    className: cn(
      "px-2 py-1.5 text-sm font-semibold",
      inset && "pl-8",
      className
    ),
    ...props
  },
  void 0,
  !1,
  {
    fileName: "app/components/ui/dropdown-menu.tsx",
    lineNumber: 99,
    columnNumber: 3
  },
  this
));
DropdownMenuLabel.displayName = DropdownMenuPrimitive.Label.displayName;
var DropdownMenuSeparator = React2.forwardRef(({ className, ...props }, ref) => /* @__PURE__ */ jsxDEV4(
  DropdownMenuPrimitive.Separator,
  {
    ref,
    className: cn("-mx-1 my-1 h-px bg-muted", className),
    ...props
  },
  void 0,
  !1,
  {
    fileName: "app/components/ui/dropdown-menu.tsx",
    lineNumber: 115,
    columnNumber: 3
  },
  this
));
DropdownMenuSeparator.displayName = DropdownMenuPrimitive.Separator.displayName;

// app/components/layout/theme-toggle.tsx
import { jsxDEV as jsxDEV5 } from "react/jsx-dev-runtime";
function ThemeToggle() {
  let { setTheme } = useTheme();
  return /* @__PURE__ */ jsxDEV5(DropdownMenu, { children: [
    /* @__PURE__ */ jsxDEV5(DropdownMenuTrigger, { asChild: !0, children: /* @__PURE__ */ jsxDEV5(Button, { variant: "outline", size: "icon", children: [
      /* @__PURE__ */ jsxDEV5(Sun, { className: "h-[1.2rem] w-[1.2rem] rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" }, void 0, !1, {
        fileName: "app/components/layout/theme-toggle.tsx",
        lineNumber: 19,
        columnNumber: 11
      }, this),
      /* @__PURE__ */ jsxDEV5(Moon, { className: "absolute h-[1.2rem] w-[1.2rem] rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" }, void 0, !1, {
        fileName: "app/components/layout/theme-toggle.tsx",
        lineNumber: 20,
        columnNumber: 11
      }, this),
      /* @__PURE__ */ jsxDEV5("span", { className: "sr-only", children: "Toggle theme" }, void 0, !1, {
        fileName: "app/components/layout/theme-toggle.tsx",
        lineNumber: 21,
        columnNumber: 11
      }, this)
    ] }, void 0, !0, {
      fileName: "app/components/layout/theme-toggle.tsx",
      lineNumber: 18,
      columnNumber: 9
    }, this) }, void 0, !1, {
      fileName: "app/components/layout/theme-toggle.tsx",
      lineNumber: 17,
      columnNumber: 7
    }, this),
    /* @__PURE__ */ jsxDEV5(DropdownMenuContent, { align: "end", children: [
      /* @__PURE__ */ jsxDEV5(DropdownMenuItem, { onClick: () => setTheme("light"), children: "Light" }, void 0, !1, {
        fileName: "app/components/layout/theme-toggle.tsx",
        lineNumber: 25,
        columnNumber: 9
      }, this),
      /* @__PURE__ */ jsxDEV5(DropdownMenuItem, { onClick: () => setTheme("dark"), children: "Dark" }, void 0, !1, {
        fileName: "app/components/layout/theme-toggle.tsx",
        lineNumber: 28,
        columnNumber: 9
      }, this),
      /* @__PURE__ */ jsxDEV5(DropdownMenuItem, { onClick: () => setTheme("system"), children: "System" }, void 0, !1, {
        fileName: "app/components/layout/theme-toggle.tsx",
        lineNumber: 31,
        columnNumber: 9
      }, this)
    ] }, void 0, !0, {
      fileName: "app/components/layout/theme-toggle.tsx",
      lineNumber: 24,
      columnNumber: 7
    }, this)
  ] }, void 0, !0, {
    fileName: "app/components/layout/theme-toggle.tsx",
    lineNumber: 16,
    columnNumber: 5
  }, this);
}

// app/hooks/use-user.ts
import { useRouteLoaderData } from "@remix-run/react";
function useOptionalUser() {
  return useRouteLoaderData("root")?.user;
}
function useUser() {
  let user = useOptionalUser();
  if (!user)
    throw new Error(
      "No user found in root loader, but user is required by useUser. If user is optional, try useOptionalUser instead."
    );
  return user;
}

// app/components/layout/user-menu.tsx
import { useSubmit } from "@remix-run/react";
import { User, LogOut } from "lucide-react";
import { jsxDEV as jsxDEV6 } from "react/jsx-dev-runtime";
function UserMenu({ user }) {
  let submit = useSubmit(), handleLogout = () => {
    submit(null, { method: "post", action: "/logout" });
  };
  return /* @__PURE__ */ jsxDEV6(DropdownMenu, { children: [
    /* @__PURE__ */ jsxDEV6(DropdownMenuTrigger, { asChild: !0, children: /* @__PURE__ */ jsxDEV6(Button, { variant: "ghost", size: "icon", className: "relative", children: /* @__PURE__ */ jsxDEV6(User, { className: "h-5 w-5" }, void 0, !1, {
      fileName: "app/components/layout/user-menu.tsx",
      lineNumber: 30,
      columnNumber: 11
    }, this) }, void 0, !1, {
      fileName: "app/components/layout/user-menu.tsx",
      lineNumber: 29,
      columnNumber: 9
    }, this) }, void 0, !1, {
      fileName: "app/components/layout/user-menu.tsx",
      lineNumber: 28,
      columnNumber: 7
    }, this),
    /* @__PURE__ */ jsxDEV6(DropdownMenuContent, { align: "end", className: "w-56", children: [
      /* @__PURE__ */ jsxDEV6(DropdownMenuLabel, { children: "My Account" }, void 0, !1, {
        fileName: "app/components/layout/user-menu.tsx",
        lineNumber: 34,
        columnNumber: 9
      }, this),
      /* @__PURE__ */ jsxDEV6(DropdownMenuSeparator, {}, void 0, !1, {
        fileName: "app/components/layout/user-menu.tsx",
        lineNumber: 35,
        columnNumber: 9
      }, this),
      /* @__PURE__ */ jsxDEV6(DropdownMenuItem, { className: "flex flex-col items-start", children: [
        /* @__PURE__ */ jsxDEV6("span", { className: "font-medium", children: [
          "User:  ",
          user.username
        ] }, void 0, !0, {
          fileName: "app/components/layout/user-menu.tsx",
          lineNumber: 37,
          columnNumber: 11
        }, this),
        /* @__PURE__ */ jsxDEV6("span", { className: "text-xs text-muted-foreground", children: [
          "Group: ",
          user.group_name
        ] }, void 0, !0, {
          fileName: "app/components/layout/user-menu.tsx",
          lineNumber: 38,
          columnNumber: 11
        }, this)
      ] }, void 0, !0, {
        fileName: "app/components/layout/user-menu.tsx",
        lineNumber: 36,
        columnNumber: 9
      }, this),
      /* @__PURE__ */ jsxDEV6(DropdownMenuSeparator, {}, void 0, !1, {
        fileName: "app/components/layout/user-menu.tsx",
        lineNumber: 40,
        columnNumber: 9
      }, this),
      /* @__PURE__ */ jsxDEV6(DropdownMenuItem, { onSelect: handleLogout, className: "text-red-600 dark:text-red-400", children: [
        /* @__PURE__ */ jsxDEV6(LogOut, { className: "mr-2 h-4 w-4" }, void 0, !1, {
          fileName: "app/components/layout/user-menu.tsx",
          lineNumber: 42,
          columnNumber: 11
        }, this),
        /* @__PURE__ */ jsxDEV6("span", { children: "Logout" }, void 0, !1, {
          fileName: "app/components/layout/user-menu.tsx",
          lineNumber: 43,
          columnNumber: 11
        }, this)
      ] }, void 0, !0, {
        fileName: "app/components/layout/user-menu.tsx",
        lineNumber: 41,
        columnNumber: 9
      }, this)
    ] }, void 0, !0, {
      fileName: "app/components/layout/user-menu.tsx",
      lineNumber: 33,
      columnNumber: 7
    }, this)
  ] }, void 0, !0, {
    fileName: "app/components/layout/user-menu.tsx",
    lineNumber: 27,
    columnNumber: 5
  }, this);
}

// app/components/layout/header.tsx
import {
  MessageSquare,
  BookOpen,
  FileText,
  LogIn,
  Laptop,
  ChevronDown
} from "lucide-react";
import { Fragment, jsxDEV as jsxDEV7 } from "react/jsx-dev-runtime";
function Header() {
  let user = useOptionalUser(), navigate = useNavigate();
  return /* @__PURE__ */ jsxDEV7("header", { className: "sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60", children: /* @__PURE__ */ jsxDEV7("div", { className: "container flex h-14 items-center", children: [
    /* @__PURE__ */ jsxDEV7("div", { className: "mr-4 flex", children: /* @__PURE__ */ jsxDEV7(Link, { to: "/", className: "mr-6 flex items-center space-x-2", children: [
      /* @__PURE__ */ jsxDEV7(
        "img",
        {
          src: "/images/logos/logo.svg",
          alt: "AI4MDE Logo",
          className: "h-6 w-6"
        },
        void 0,
        !1,
        {
          fileName: "app/components/layout/header.tsx",
          lineNumber: 32,
          columnNumber: 13
        },
        this
      ),
      /* @__PURE__ */ jsxDEV7("span", { className: "font-bold", children: "AI4MDE" }, void 0, !1, {
        fileName: "app/components/layout/header.tsx",
        lineNumber: 37,
        columnNumber: 13
      }, this)
    ] }, void 0, !0, {
      fileName: "app/components/layout/header.tsx",
      lineNumber: 31,
      columnNumber: 11
    }, this) }, void 0, !1, {
      fileName: "app/components/layout/header.tsx",
      lineNumber: 30,
      columnNumber: 9
    }, this),
    /* @__PURE__ */ jsxDEV7("div", { className: "flex flex-1 items-center justify-between space-x-2 md:justify-end", children: /* @__PURE__ */ jsxDEV7("nav", { className: "flex items-center space-x-2", children: [
      /* @__PURE__ */ jsxDEV7(Button, { asChild: !0, variant: "ghost", className: "gap-2", children: /* @__PURE__ */ jsxDEV7(Link, { to: "/chat", children: [
        /* @__PURE__ */ jsxDEV7(MessageSquare, { className: "h-4 w-4" }, void 0, !1, {
          fileName: "app/components/layout/header.tsx",
          lineNumber: 44,
          columnNumber: 17
        }, this),
        "Chat"
      ] }, void 0, !0, {
        fileName: "app/components/layout/header.tsx",
        lineNumber: 43,
        columnNumber: 15
      }, this) }, void 0, !1, {
        fileName: "app/components/layout/header.tsx",
        lineNumber: 42,
        columnNumber: 13
      }, this),
      /* @__PURE__ */ jsxDEV7(DropdownMenu, { children: [
        /* @__PURE__ */ jsxDEV7(DropdownMenuTrigger, { asChild: !0, children: /* @__PURE__ */ jsxDEV7(Button, { variant: "ghost", className: "gap-2", children: [
          /* @__PURE__ */ jsxDEV7(FileText, { className: "h-4 w-4" }, void 0, !1, {
            fileName: "app/components/layout/header.tsx",
            lineNumber: 52,
            columnNumber: 19
          }, this),
          "Docs",
          /* @__PURE__ */ jsxDEV7(ChevronDown, { className: "h-4 w-4" }, void 0, !1, {
            fileName: "app/components/layout/header.tsx",
            lineNumber: 54,
            columnNumber: 19
          }, this)
        ] }, void 0, !0, {
          fileName: "app/components/layout/header.tsx",
          lineNumber: 51,
          columnNumber: 17
        }, this) }, void 0, !1, {
          fileName: "app/components/layout/header.tsx",
          lineNumber: 50,
          columnNumber: 15
        }, this),
        /* @__PURE__ */ jsxDEV7(DropdownMenuContent, { align: "start", children: [
          /* @__PURE__ */ jsxDEV7(DropdownMenuItem, { asChild: !0, children: /* @__PURE__ */ jsxDEV7(Link, { to: "/guide", className: "flex items-center gap-2", children: [
            /* @__PURE__ */ jsxDEV7(BookOpen, { className: "h-4 w-4" }, void 0, !1, {
              fileName: "app/components/layout/header.tsx",
              lineNumber: 60,
              columnNumber: 21
            }, this),
            "Guide"
          ] }, void 0, !0, {
            fileName: "app/components/layout/header.tsx",
            lineNumber: 59,
            columnNumber: 19
          }, this) }, void 0, !1, {
            fileName: "app/components/layout/header.tsx",
            lineNumber: 58,
            columnNumber: 17
          }, this),
          user && /* @__PURE__ */ jsxDEV7(Fragment, { children: [
            /* @__PURE__ */ jsxDEV7(DropdownMenuItem, { asChild: !0, children: /* @__PURE__ */ jsxDEV7(Link, { to: "/srsdocs", className: "flex items-center gap-2", children: [
              /* @__PURE__ */ jsxDEV7(FileText, { className: "h-4 w-4" }, void 0, !1, {
                fileName: "app/components/layout/header.tsx",
                lineNumber: 68,
                columnNumber: 25
              }, this),
              "SRS Docs"
            ] }, void 0, !0, {
              fileName: "app/components/layout/header.tsx",
              lineNumber: 67,
              columnNumber: 23
            }, this) }, void 0, !1, {
              fileName: "app/components/layout/header.tsx",
              lineNumber: 66,
              columnNumber: 21
            }, this),
            /* @__PURE__ */ jsxDEV7(DropdownMenuItem, { asChild: !0, children: /* @__PURE__ */ jsxDEV7(Link, { to: "/interviews", className: "flex items-center gap-2", children: [
              /* @__PURE__ */ jsxDEV7(MessageSquare, { className: "h-4 w-4" }, void 0, !1, {
                fileName: "app/components/layout/header.tsx",
                lineNumber: 74,
                columnNumber: 25
              }, this),
              "Interviews"
            ] }, void 0, !0, {
              fileName: "app/components/layout/header.tsx",
              lineNumber: 73,
              columnNumber: 23
            }, this) }, void 0, !1, {
              fileName: "app/components/layout/header.tsx",
              lineNumber: 72,
              columnNumber: 21
            }, this)
          ] }, void 0, !0, {
            fileName: "app/components/layout/header.tsx",
            lineNumber: 65,
            columnNumber: 19
          }, this)
        ] }, void 0, !0, {
          fileName: "app/components/layout/header.tsx",
          lineNumber: 57,
          columnNumber: 15
        }, this)
      ] }, void 0, !0, {
        fileName: "app/components/layout/header.tsx",
        lineNumber: 49,
        columnNumber: 13
      }, this),
      user && /* @__PURE__ */ jsxDEV7(Button, { asChild: !0, variant: "ghost", className: "gap-2", children: /* @__PURE__ */ jsxDEV7(
        "a",
        {
          href: `https://${user.group_name}-studio.ai4mde.org`,
          target: "_blank",
          rel: "noopener noreferrer",
          children: [
            /* @__PURE__ */ jsxDEV7(Laptop, { className: "h-4 w-4" }, void 0, !1, {
              fileName: "app/components/layout/header.tsx",
              lineNumber: 90,
              columnNumber: 19
            }, this),
            "Studio"
          ]
        },
        void 0,
        !0,
        {
          fileName: "app/components/layout/header.tsx",
          lineNumber: 85,
          columnNumber: 17
        },
        this
      ) }, void 0, !1, {
        fileName: "app/components/layout/header.tsx",
        lineNumber: 84,
        columnNumber: 15
      }, this),
      /* @__PURE__ */ jsxDEV7(ThemeToggle, {}, void 0, !1, {
        fileName: "app/components/layout/header.tsx",
        lineNumber: 95,
        columnNumber: 13
      }, this),
      user ? /* @__PURE__ */ jsxDEV7(UserMenu, { user }, void 0, !1, {
        fileName: "app/components/layout/header.tsx",
        lineNumber: 97,
        columnNumber: 15
      }, this) : /* @__PURE__ */ jsxDEV7(Button, { asChild: !0, variant: "ghost", className: "gap-2", children: /* @__PURE__ */ jsxDEV7(Link, { to: "/login", children: [
        /* @__PURE__ */ jsxDEV7(LogIn, { className: "h-4 w-4" }, void 0, !1, {
          fileName: "app/components/layout/header.tsx",
          lineNumber: 101,
          columnNumber: 19
        }, this),
        "Login"
      ] }, void 0, !0, {
        fileName: "app/components/layout/header.tsx",
        lineNumber: 100,
        columnNumber: 17
      }, this) }, void 0, !1, {
        fileName: "app/components/layout/header.tsx",
        lineNumber: 99,
        columnNumber: 15
      }, this)
    ] }, void 0, !0, {
      fileName: "app/components/layout/header.tsx",
      lineNumber: 41,
      columnNumber: 11
    }, this) }, void 0, !1, {
      fileName: "app/components/layout/header.tsx",
      lineNumber: 40,
      columnNumber: 9
    }, this)
  ] }, void 0, !0, {
    fileName: "app/components/layout/header.tsx",
    lineNumber: 29,
    columnNumber: 7
  }, this) }, void 0, !1, {
    fileName: "app/components/layout/header.tsx",
    lineNumber: 28,
    columnNumber: 5
  }, this);
}

// app/components/layout/footer.tsx
import { Link as Link2 } from "@remix-run/react";
import { jsxDEV as jsxDEV8 } from "react/jsx-dev-runtime";
function Footer() {
  return /* @__PURE__ */ jsxDEV8("footer", { className: "border-t", children: /* @__PURE__ */ jsxDEV8("div", { className: "container flex flex-col items-center py-8 gap-4", children: [
    /* @__PURE__ */ jsxDEV8("nav", { className: "flex gap-4", children: [
      /* @__PURE__ */ jsxDEV8(Link2, { to: "/privacy", className: "text-sm underline underline-offset-4", children: "Privacy" }, void 0, !1, {
        fileName: "app/components/layout/footer.tsx",
        lineNumber: 9,
        columnNumber: 11
      }, this),
      /* @__PURE__ */ jsxDEV8(Link2, { to: "/terms", className: "text-sm underline underline-offset-4", children: "Terms" }, void 0, !1, {
        fileName: "app/components/layout/footer.tsx",
        lineNumber: 12,
        columnNumber: 11
      }, this),
      /* @__PURE__ */ jsxDEV8(Link2, { to: "/contact", className: "text-sm underline underline-offset-4", children: "Contact" }, void 0, !1, {
        fileName: "app/components/layout/footer.tsx",
        lineNumber: 15,
        columnNumber: 11
      }, this)
    ] }, void 0, !0, {
      fileName: "app/components/layout/footer.tsx",
      lineNumber: 8,
      columnNumber: 9
    }, this),
    /* @__PURE__ */ jsxDEV8("p", { className: "text-center text-sm leading-loose", children: [
      "Built by",
      " ",
      /* @__PURE__ */ jsxDEV8(
        "a",
        {
          href: "https://www.universiteitleiden.nl/en",
          target: "_blank",
          rel: "noreferrer",
          className: "font-medium underline underline-offset-4",
          children: "Leiden University"
        },
        void 0,
        !1,
        {
          fileName: "app/components/layout/footer.tsx",
          lineNumber: 21,
          columnNumber: 11
        },
        this
      ),
      ". The source code is available on",
      " ",
      /* @__PURE__ */ jsxDEV8(
        "a",
        {
          href: "https://github.com/LIACS/AI4MDE",
          target: "_blank",
          rel: "noreferrer",
          className: "font-medium underline underline-offset-4",
          children: "GitHub"
        },
        void 0,
        !1,
        {
          fileName: "app/components/layout/footer.tsx",
          lineNumber: 30,
          columnNumber: 11
        },
        this
      ),
      "."
    ] }, void 0, !0, {
      fileName: "app/components/layout/footer.tsx",
      lineNumber: 19,
      columnNumber: 9
    }, this)
  ] }, void 0, !0, {
    fileName: "app/components/layout/footer.tsx",
    lineNumber: 7,
    columnNumber: 7
  }, this) }, void 0, !1, {
    fileName: "app/components/layout/footer.tsx",
    lineNumber: 6,
    columnNumber: 5
  }, this);
}

// app/styles/globals.css
var globals_default = "/build/_assets/globals-IZMLHUF4.css";

// app/services/session.server.ts
import { createCookieSessionStorage, redirect as redirect2 } from "@remix-run/node";
var sessionSecret = process.env.SESSION_SECRET;
if (!sessionSecret)
  throw new Error("SESSION_SECRET must be set");
var sessionStorage = createCookieSessionStorage({
  cookie: {
    name: "__session",
    httpOnly: !0,
    path: "/",
    sameSite: "lax",
    secrets: [sessionSecret],
    secure: !1
  }
});
async function getSession(request) {
  let cookie = request.headers.get("Cookie");
  return sessionStorage.getSession(cookie);
}
async function getUserFromSession(request) {
  return (await getSession(request)).get("user") || null;
}
async function destroySession(request) {
  let session = await getSession(request);
  return redirect2("/login", {
    headers: {
      "Set-Cookie": await sessionStorage.destroySession(session)
    }
  });
}
async function requireUser2(request, redirectTo = new URL(request.url).pathname) {
  let user = await getUserFromSession(request);
  if (!user) {
    let searchParams = new URLSearchParams([["redirectTo", redirectTo]]);
    throw redirect2(`/login?${searchParams}`);
  }
  return user;
}
async function logout(request) {
  let session = await getSession(request);
  return redirect2("/", {
    headers: {
      "Set-Cookie": await sessionStorage.destroySession(session)
    }
  });
}

// app/routes/_error.404.tsx
var error_404_exports = {};
__export(error_404_exports, {
  default: () => NotFound
});
import { Link as Link3 } from "@remix-run/react";
import { Home } from "lucide-react";

// app/components/layout/max-width-wrapper.tsx
import { jsxDEV as jsxDEV9 } from "react/jsx-dev-runtime";
function MaxWidthWrapper({
  className,
  ...props
}) {
  return /* @__PURE__ */ jsxDEV9(
    "div",
    {
      className: cn(
        "mx-auto w-full max-w-screen-xl px-2.5 md:px-20",
        className
      ),
      ...props
    },
    void 0,
    !1,
    {
      fileName: "app/components/layout/max-width-wrapper.tsx",
      lineNumber: 11,
      columnNumber: 5
    },
    this
  );
}

// app/routes/_error.404.tsx
import { jsxDEV as jsxDEV10 } from "react/jsx-dev-runtime";
function NotFound() {
  return /* @__PURE__ */ jsxDEV10(MaxWidthWrapper, { children: /* @__PURE__ */ jsxDEV10("div", { className: "min-h-[80vh] flex flex-col items-center justify-center text-center gap-8", children: [
    /* @__PURE__ */ jsxDEV10("div", { className: "space-y-6", children: [
      /* @__PURE__ */ jsxDEV10(
        "img",
        {
          src: "/images/logos/logo.svg",
          alt: "AI4MDE Logo",
          className: "w-24 h-24 mx-auto opacity-50 dark:invert"
        },
        void 0,
        !1,
        {
          fileName: "app/routes/_error.404.tsx",
          lineNumber: 12,
          columnNumber: 11
        },
        this
      ),
      /* @__PURE__ */ jsxDEV10("h1", { className: "text-4xl font-bold tracking-tight", children: "Page not found" }, void 0, !1, {
        fileName: "app/routes/_error.404.tsx",
        lineNumber: 17,
        columnNumber: 11
      }, this),
      /* @__PURE__ */ jsxDEV10("p", { className: "text-xl text-muted-foreground", children: "Sorry, we couldn't find the page you're looking for." }, void 0, !1, {
        fileName: "app/routes/_error.404.tsx",
        lineNumber: 18,
        columnNumber: 11
      }, this)
    ] }, void 0, !0, {
      fileName: "app/routes/_error.404.tsx",
      lineNumber: 11,
      columnNumber: 9
    }, this),
    /* @__PURE__ */ jsxDEV10("div", { className: "flex flex-col sm:flex-row gap-4", children: [
      /* @__PURE__ */ jsxDEV10(Button, { asChild: !0, children: /* @__PURE__ */ jsxDEV10(Link3, { to: "/", className: "flex items-center gap-2", children: [
        /* @__PURE__ */ jsxDEV10(Home, { className: "w-4 h-4" }, void 0, !1, {
          fileName: "app/routes/_error.404.tsx",
          lineNumber: 26,
          columnNumber: 15
        }, this),
        "Back to Home"
      ] }, void 0, !0, {
        fileName: "app/routes/_error.404.tsx",
        lineNumber: 25,
        columnNumber: 13
      }, this) }, void 0, !1, {
        fileName: "app/routes/_error.404.tsx",
        lineNumber: 24,
        columnNumber: 11
      }, this),
      /* @__PURE__ */ jsxDEV10(Button, { variant: "outline", asChild: !0, children: /* @__PURE__ */ jsxDEV10(Link3, { to: "/srsdocs", children: "View Documents" }, void 0, !1, {
        fileName: "app/routes/_error.404.tsx",
        lineNumber: 31,
        columnNumber: 13
      }, this) }, void 0, !1, {
        fileName: "app/routes/_error.404.tsx",
        lineNumber: 30,
        columnNumber: 11
      }, this)
    ] }, void 0, !0, {
      fileName: "app/routes/_error.404.tsx",
      lineNumber: 23,
      columnNumber: 9
    }, this),
    /* @__PURE__ */ jsxDEV10("p", { className: "text-sm text-muted-foreground", children: "Error Code: 404" }, void 0, !1, {
      fileName: "app/routes/_error.404.tsx",
      lineNumber: 37,
      columnNumber: 9
    }, this)
  ] }, void 0, !0, {
    fileName: "app/routes/_error.404.tsx",
    lineNumber: 10,
    columnNumber: 7
  }, this) }, void 0, !1, {
    fileName: "app/routes/_error.404.tsx",
    lineNumber: 9,
    columnNumber: 5
  }, this);
}

// app/root.tsx
import { jsxDEV as jsxDEV11 } from "react/jsx-dev-runtime";
var meta = () => [
  { title: "AI4MDE" },
  { name: "description", content: "AI-powered Model-Driven Engineering" },
  { name: "viewport", content: "width=device-width,initial-scale=1" }
], links = () => [
  { rel: "preconnect", href: "https://fonts.googleapis.com" },
  { rel: "preconnect", href: "https://fonts.gstatic.com", crossOrigin: "anonymous" },
  { rel: "stylesheet", href: "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" },
  ...cssBundleHref ? [{ rel: "stylesheet", href: cssBundleHref }] : [],
  { rel: "stylesheet", href: globals_default }
];
async function loader({ request }) {
  let session = await getSession(request);
  return json2({
    user: session.get("user")
  });
}
function ErrorBoundary() {
  let error = useRouteError();
  return isRouteErrorResponse(error) && error.status === 404 ? /* @__PURE__ */ jsxDEV11(NotFound, {}, void 0, !1, {
    fileName: "app/root.tsx",
    lineNumber: 51,
    columnNumber: 12
  }, this) : /* @__PURE__ */ jsxDEV11("div", { className: "min-h-screen flex items-center justify-center", children: /* @__PURE__ */ jsxDEV11("div", { className: "text-center space-y-4", children: [
    /* @__PURE__ */ jsxDEV11("h1", { className: "text-4xl font-bold", children: "Oops!" }, void 0, !1, {
      fileName: "app/root.tsx",
      lineNumber: 57,
      columnNumber: 9
    }, this),
    /* @__PURE__ */ jsxDEV11("p", { className: "text-xl text-muted-foreground", children: "Something went wrong." }, void 0, !1, {
      fileName: "app/root.tsx",
      lineNumber: 58,
      columnNumber: 9
    }, this),
    /* @__PURE__ */ jsxDEV11(Button, { asChild: !0, children: /* @__PURE__ */ jsxDEV11(Link4, { to: "/", children: "Back to Home" }, void 0, !1, {
      fileName: "app/root.tsx",
      lineNumber: 60,
      columnNumber: 11
    }, this) }, void 0, !1, {
      fileName: "app/root.tsx",
      lineNumber: 59,
      columnNumber: 9
    }, this)
  ] }, void 0, !0, {
    fileName: "app/root.tsx",
    lineNumber: 56,
    columnNumber: 7
  }, this) }, void 0, !1, {
    fileName: "app/root.tsx",
    lineNumber: 55,
    columnNumber: 5
  }, this);
}
function App() {
  return /* @__PURE__ */ jsxDEV11("html", { lang: "en", suppressHydrationWarning: !0, children: [
    /* @__PURE__ */ jsxDEV11("head", { children: [
      /* @__PURE__ */ jsxDEV11("meta", { charSet: "utf-8" }, void 0, !1, {
        fileName: "app/root.tsx",
        lineNumber: 71,
        columnNumber: 9
      }, this),
      /* @__PURE__ */ jsxDEV11("meta", { name: "viewport", content: "width=device-width, initial-scale=1" }, void 0, !1, {
        fileName: "app/root.tsx",
        lineNumber: 72,
        columnNumber: 9
      }, this),
      /* @__PURE__ */ jsxDEV11("link", { rel: "icon", type: "image/svg+xml", href: "/images/logos/logo.svg" }, void 0, !1, {
        fileName: "app/root.tsx",
        lineNumber: 73,
        columnNumber: 9
      }, this),
      /* @__PURE__ */ jsxDEV11(Meta, {}, void 0, !1, {
        fileName: "app/root.tsx",
        lineNumber: 74,
        columnNumber: 9
      }, this),
      /* @__PURE__ */ jsxDEV11(Links, {}, void 0, !1, {
        fileName: "app/root.tsx",
        lineNumber: 75,
        columnNumber: 9
      }, this)
    ] }, void 0, !0, {
      fileName: "app/root.tsx",
      lineNumber: 70,
      columnNumber: 7
    }, this),
    /* @__PURE__ */ jsxDEV11("body", { className: "min-h-screen bg-background font-sans antialiased", children: [
      /* @__PURE__ */ jsxDEV11(ThemeProvider, { children: /* @__PURE__ */ jsxDEV11("div", { className: "relative flex min-h-screen flex-col", children: [
        /* @__PURE__ */ jsxDEV11(Header, {}, void 0, !1, {
          fileName: "app/root.tsx",
          lineNumber: 80,
          columnNumber: 13
        }, this),
        /* @__PURE__ */ jsxDEV11("main", { className: "flex-1", children: /* @__PURE__ */ jsxDEV11(Outlet, {}, void 0, !1, {
          fileName: "app/root.tsx",
          lineNumber: 82,
          columnNumber: 15
        }, this) }, void 0, !1, {
          fileName: "app/root.tsx",
          lineNumber: 81,
          columnNumber: 13
        }, this),
        /* @__PURE__ */ jsxDEV11(Footer, {}, void 0, !1, {
          fileName: "app/root.tsx",
          lineNumber: 84,
          columnNumber: 13
        }, this)
      ] }, void 0, !0, {
        fileName: "app/root.tsx",
        lineNumber: 79,
        columnNumber: 11
      }, this) }, void 0, !1, {
        fileName: "app/root.tsx",
        lineNumber: 78,
        columnNumber: 9
      }, this),
      /* @__PURE__ */ jsxDEV11(ScrollRestoration, {}, void 0, !1, {
        fileName: "app/root.tsx",
        lineNumber: 87,
        columnNumber: 9
      }, this),
      /* @__PURE__ */ jsxDEV11(Scripts, {}, void 0, !1, {
        fileName: "app/root.tsx",
        lineNumber: 88,
        columnNumber: 9
      }, this),
      /* @__PURE__ */ jsxDEV11(LiveReload, {}, void 0, !1, {
        fileName: "app/root.tsx",
        lineNumber: 89,
        columnNumber: 9
      }, this)
    ] }, void 0, !0, {
      fileName: "app/root.tsx",
      lineNumber: 77,
      columnNumber: 7
    }, this)
  ] }, void 0, !0, {
    fileName: "app/root.tsx",
    lineNumber: 69,
    columnNumber: 5
  }, this);
}

// app/routes/settings.theme.tsx
var settings_theme_exports = {};
__export(settings_theme_exports, {
  default: () => ThemeSettings
});

// app/components/layout/theme-colors.tsx
import { jsxDEV as jsxDEV12 } from "react/jsx-dev-runtime";
function ThemeColors({ className }) {
  return /* @__PURE__ */ jsxDEV12("div", { className: cn("grid gap-4", className), children: [
    /* @__PURE__ */ jsxDEV12("div", { className: "space-y-2", children: [
      /* @__PURE__ */ jsxDEV12("h3", { className: "text-sm font-medium", children: "Primary" }, void 0, !1, {
        fileName: "app/components/layout/theme-colors.tsx",
        lineNumber: 12,
        columnNumber: 9
      }, this),
      /* @__PURE__ */ jsxDEV12("div", { className: "grid grid-cols-2 gap-2", children: [
        /* @__PURE__ */ jsxDEV12("div", { className: "h-10 rounded-md bg-primary" }, void 0, !1, {
          fileName: "app/components/layout/theme-colors.tsx",
          lineNumber: 14,
          columnNumber: 11
        }, this),
        /* @__PURE__ */ jsxDEV12("div", { className: "h-10 rounded-md bg-primary-foreground" }, void 0, !1, {
          fileName: "app/components/layout/theme-colors.tsx",
          lineNumber: 15,
          columnNumber: 11
        }, this)
      ] }, void 0, !0, {
        fileName: "app/components/layout/theme-colors.tsx",
        lineNumber: 13,
        columnNumber: 9
      }, this)
    ] }, void 0, !0, {
      fileName: "app/components/layout/theme-colors.tsx",
      lineNumber: 11,
      columnNumber: 7
    }, this),
    /* @__PURE__ */ jsxDEV12("div", { className: "space-y-2", children: [
      /* @__PURE__ */ jsxDEV12("h3", { className: "text-sm font-medium", children: "Secondary" }, void 0, !1, {
        fileName: "app/components/layout/theme-colors.tsx",
        lineNumber: 19,
        columnNumber: 9
      }, this),
      /* @__PURE__ */ jsxDEV12("div", { className: "grid grid-cols-2 gap-2", children: [
        /* @__PURE__ */ jsxDEV12("div", { className: "h-10 rounded-md bg-secondary" }, void 0, !1, {
          fileName: "app/components/layout/theme-colors.tsx",
          lineNumber: 21,
          columnNumber: 11
        }, this),
        /* @__PURE__ */ jsxDEV12("div", { className: "h-10 rounded-md bg-secondary-foreground" }, void 0, !1, {
          fileName: "app/components/layout/theme-colors.tsx",
          lineNumber: 22,
          columnNumber: 11
        }, this)
      ] }, void 0, !0, {
        fileName: "app/components/layout/theme-colors.tsx",
        lineNumber: 20,
        columnNumber: 9
      }, this)
    ] }, void 0, !0, {
      fileName: "app/components/layout/theme-colors.tsx",
      lineNumber: 18,
      columnNumber: 7
    }, this),
    /* @__PURE__ */ jsxDEV12("div", { className: "space-y-2", children: [
      /* @__PURE__ */ jsxDEV12("h3", { className: "text-sm font-medium", children: "Accent" }, void 0, !1, {
        fileName: "app/components/layout/theme-colors.tsx",
        lineNumber: 26,
        columnNumber: 9
      }, this),
      /* @__PURE__ */ jsxDEV12("div", { className: "grid grid-cols-2 gap-2", children: [
        /* @__PURE__ */ jsxDEV12("div", { className: "h-10 rounded-md bg-accent" }, void 0, !1, {
          fileName: "app/components/layout/theme-colors.tsx",
          lineNumber: 28,
          columnNumber: 11
        }, this),
        /* @__PURE__ */ jsxDEV12("div", { className: "h-10 rounded-md bg-accent-foreground" }, void 0, !1, {
          fileName: "app/components/layout/theme-colors.tsx",
          lineNumber: 29,
          columnNumber: 11
        }, this)
      ] }, void 0, !0, {
        fileName: "app/components/layout/theme-colors.tsx",
        lineNumber: 27,
        columnNumber: 9
      }, this)
    ] }, void 0, !0, {
      fileName: "app/components/layout/theme-colors.tsx",
      lineNumber: 25,
      columnNumber: 7
    }, this),
    /* @__PURE__ */ jsxDEV12("div", { className: "space-y-2", children: [
      /* @__PURE__ */ jsxDEV12("h3", { className: "text-sm font-medium", children: "Destructive" }, void 0, !1, {
        fileName: "app/components/layout/theme-colors.tsx",
        lineNumber: 33,
        columnNumber: 9
      }, this),
      /* @__PURE__ */ jsxDEV12("div", { className: "grid grid-cols-2 gap-2", children: [
        /* @__PURE__ */ jsxDEV12("div", { className: "h-10 rounded-md bg-destructive" }, void 0, !1, {
          fileName: "app/components/layout/theme-colors.tsx",
          lineNumber: 35,
          columnNumber: 11
        }, this),
        /* @__PURE__ */ jsxDEV12("div", { className: "h-10 rounded-md bg-destructive-foreground" }, void 0, !1, {
          fileName: "app/components/layout/theme-colors.tsx",
          lineNumber: 36,
          columnNumber: 11
        }, this)
      ] }, void 0, !0, {
        fileName: "app/components/layout/theme-colors.tsx",
        lineNumber: 34,
        columnNumber: 9
      }, this)
    ] }, void 0, !0, {
      fileName: "app/components/layout/theme-colors.tsx",
      lineNumber: 32,
      columnNumber: 7
    }, this),
    /* @__PURE__ */ jsxDEV12("div", { className: "space-y-2", children: [
      /* @__PURE__ */ jsxDEV12("h3", { className: "text-sm font-medium", children: "Card" }, void 0, !1, {
        fileName: "app/components/layout/theme-colors.tsx",
        lineNumber: 40,
        columnNumber: 9
      }, this),
      /* @__PURE__ */ jsxDEV12("div", { className: "grid grid-cols-2 gap-2", children: [
        /* @__PURE__ */ jsxDEV12("div", { className: "h-10 rounded-md bg-card" }, void 0, !1, {
          fileName: "app/components/layout/theme-colors.tsx",
          lineNumber: 42,
          columnNumber: 11
        }, this),
        /* @__PURE__ */ jsxDEV12("div", { className: "h-10 rounded-md bg-card-foreground" }, void 0, !1, {
          fileName: "app/components/layout/theme-colors.tsx",
          lineNumber: 43,
          columnNumber: 11
        }, this)
      ] }, void 0, !0, {
        fileName: "app/components/layout/theme-colors.tsx",
        lineNumber: 41,
        columnNumber: 9
      }, this)
    ] }, void 0, !0, {
      fileName: "app/components/layout/theme-colors.tsx",
      lineNumber: 39,
      columnNumber: 7
    }, this),
    /* @__PURE__ */ jsxDEV12("div", { className: "space-y-2", children: [
      /* @__PURE__ */ jsxDEV12("h3", { className: "text-sm font-medium", children: "Muted" }, void 0, !1, {
        fileName: "app/components/layout/theme-colors.tsx",
        lineNumber: 47,
        columnNumber: 9
      }, this),
      /* @__PURE__ */ jsxDEV12("div", { className: "grid grid-cols-2 gap-2", children: [
        /* @__PURE__ */ jsxDEV12("div", { className: "h-10 rounded-md bg-muted" }, void 0, !1, {
          fileName: "app/components/layout/theme-colors.tsx",
          lineNumber: 49,
          columnNumber: 11
        }, this),
        /* @__PURE__ */ jsxDEV12("div", { className: "h-10 rounded-md bg-muted-foreground" }, void 0, !1, {
          fileName: "app/components/layout/theme-colors.tsx",
          lineNumber: 50,
          columnNumber: 11
        }, this)
      ] }, void 0, !0, {
        fileName: "app/components/layout/theme-colors.tsx",
        lineNumber: 48,
        columnNumber: 9
      }, this)
    ] }, void 0, !0, {
      fileName: "app/components/layout/theme-colors.tsx",
      lineNumber: 46,
      columnNumber: 7
    }, this),
    /* @__PURE__ */ jsxDEV12("div", { className: "space-y-2", children: [
      /* @__PURE__ */ jsxDEV12("h3", { className: "text-sm font-medium", children: "Background" }, void 0, !1, {
        fileName: "app/components/layout/theme-colors.tsx",
        lineNumber: 54,
        columnNumber: 9
      }, this),
      /* @__PURE__ */ jsxDEV12("div", { className: "grid grid-cols-2 gap-2", children: [
        /* @__PURE__ */ jsxDEV12("div", { className: "h-10 rounded-md bg-background" }, void 0, !1, {
          fileName: "app/components/layout/theme-colors.tsx",
          lineNumber: 56,
          columnNumber: 11
        }, this),
        /* @__PURE__ */ jsxDEV12("div", { className: "h-10 rounded-md bg-foreground" }, void 0, !1, {
          fileName: "app/components/layout/theme-colors.tsx",
          lineNumber: 57,
          columnNumber: 11
        }, this)
      ] }, void 0, !0, {
        fileName: "app/components/layout/theme-colors.tsx",
        lineNumber: 55,
        columnNumber: 9
      }, this)
    ] }, void 0, !0, {
      fileName: "app/components/layout/theme-colors.tsx",
      lineNumber: 53,
      columnNumber: 7
    }, this)
  ] }, void 0, !0, {
    fileName: "app/components/layout/theme-colors.tsx",
    lineNumber: 10,
    columnNumber: 5
  }, this);
}

// app/components/ui/card.tsx
import * as React3 from "react";
import { jsxDEV as jsxDEV13 } from "react/jsx-dev-runtime";
var Card = React3.forwardRef(({ className, ...props }, ref) => /* @__PURE__ */ jsxDEV13(
  "div",
  {
    ref,
    className: cn(
      "rounded-xl border bg-card text-card-foreground shadow",
      className
    ),
    ...props
  },
  void 0,
  !1,
  {
    fileName: "app/components/ui/card.tsx",
    lineNumber: 9,
    columnNumber: 3
  },
  this
));
Card.displayName = "Card";
var CardHeader = React3.forwardRef(({ className, ...props }, ref) => /* @__PURE__ */ jsxDEV13(
  "div",
  {
    ref,
    className: cn("flex flex-col space-y-1.5 p-6", className),
    ...props
  },
  void 0,
  !1,
  {
    fileName: "app/components/ui/card.tsx",
    lineNumber: 24,
    columnNumber: 3
  },
  this
));
CardHeader.displayName = "CardHeader";
var CardTitle = React3.forwardRef(({ className, ...props }, ref) => /* @__PURE__ */ jsxDEV13(
  "h3",
  {
    ref,
    className: cn("font-semibold leading-none tracking-tight", className),
    ...props
  },
  void 0,
  !1,
  {
    fileName: "app/components/ui/card.tsx",
    lineNumber: 36,
    columnNumber: 3
  },
  this
));
CardTitle.displayName = "CardTitle";
var CardDescription = React3.forwardRef(({ className, ...props }, ref) => /* @__PURE__ */ jsxDEV13(
  "p",
  {
    ref,
    className: cn("text-sm text-muted-foreground", className),
    ...props
  },
  void 0,
  !1,
  {
    fileName: "app/components/ui/card.tsx",
    lineNumber: 48,
    columnNumber: 3
  },
  this
));
CardDescription.displayName = "CardDescription";
var CardContent = React3.forwardRef(({ className, ...props }, ref) => /* @__PURE__ */ jsxDEV13("div", { ref, className: cn("p-6 pt-0", className), ...props }, void 0, !1, {
  fileName: "app/components/ui/card.tsx",
  lineNumber: 60,
  columnNumber: 3
}, this));
CardContent.displayName = "CardContent";
var CardFooter = React3.forwardRef(({ className, ...props }, ref) => /* @__PURE__ */ jsxDEV13(
  "div",
  {
    ref,
    className: cn("flex items-center p-6 pt-0", className),
    ...props
  },
  void 0,
  !1,
  {
    fileName: "app/components/ui/card.tsx",
    lineNumber: 68,
    columnNumber: 3
  },
  this
));
CardFooter.displayName = "CardFooter";

// app/components/ui/separator.tsx
import * as React4 from "react";
import * as SeparatorPrimitive from "@radix-ui/react-separator";
import { jsxDEV as jsxDEV14 } from "react/jsx-dev-runtime";
var Separator2 = React4.forwardRef(
  ({ className, orientation = "horizontal", decorative = !0, ...props }, ref) => /* @__PURE__ */ jsxDEV14(
    SeparatorPrimitive.Root,
    {
      ref,
      decorative,
      orientation,
      className: cn(
        "shrink-0 bg-border",
        orientation === "horizontal" ? "h-[1px] w-full" : "h-full w-[1px]",
        className
      ),
      ...props
    },
    void 0,
    !1,
    {
      fileName: "app/components/ui/separator.tsx",
      lineNumber: 13,
      columnNumber: 5
    },
    this
  )
);
Separator2.displayName = SeparatorPrimitive.Root.displayName;

// app/routes/settings.theme.tsx
import { jsxDEV as jsxDEV15 } from "react/jsx-dev-runtime";
function ThemeSettings() {
  return /* @__PURE__ */ jsxDEV15("div", { className: "container py-10", children: /* @__PURE__ */ jsxDEV15("div", { className: "space-y-6", children: [
    /* @__PURE__ */ jsxDEV15("div", { children: [
      /* @__PURE__ */ jsxDEV15("h3", { className: "text-lg font-medium", children: "Theme Settings" }, void 0, !1, {
        fileName: "app/routes/settings.theme.tsx",
        lineNumber: 12,
        columnNumber: 11
      }, this),
      /* @__PURE__ */ jsxDEV15("p", { className: "text-sm text-muted-foreground", children: "Customize how the application looks and feels." }, void 0, !1, {
        fileName: "app/routes/settings.theme.tsx",
        lineNumber: 13,
        columnNumber: 11
      }, this)
    ] }, void 0, !0, {
      fileName: "app/routes/settings.theme.tsx",
      lineNumber: 11,
      columnNumber: 9
    }, this),
    /* @__PURE__ */ jsxDEV15(Separator2, {}, void 0, !1, {
      fileName: "app/routes/settings.theme.tsx",
      lineNumber: 17,
      columnNumber: 9
    }, this),
    /* @__PURE__ */ jsxDEV15("div", { className: "grid gap-6 lg:grid-cols-2", children: [
      /* @__PURE__ */ jsxDEV15(Card, { children: [
        /* @__PURE__ */ jsxDEV15(CardHeader, { children: [
          /* @__PURE__ */ jsxDEV15(CardTitle, { children: "Theme" }, void 0, !1, {
            fileName: "app/routes/settings.theme.tsx",
            lineNumber: 21,
            columnNumber: 15
          }, this),
          /* @__PURE__ */ jsxDEV15(CardDescription, { children: "Select your preferred theme mode." }, void 0, !1, {
            fileName: "app/routes/settings.theme.tsx",
            lineNumber: 22,
            columnNumber: 15
          }, this)
        ] }, void 0, !0, {
          fileName: "app/routes/settings.theme.tsx",
          lineNumber: 20,
          columnNumber: 13
        }, this),
        /* @__PURE__ */ jsxDEV15(CardContent, { children: /* @__PURE__ */ jsxDEV15(ThemeToggle, {}, void 0, !1, {
          fileName: "app/routes/settings.theme.tsx",
          lineNumber: 27,
          columnNumber: 15
        }, this) }, void 0, !1, {
          fileName: "app/routes/settings.theme.tsx",
          lineNumber: 26,
          columnNumber: 13
        }, this)
      ] }, void 0, !0, {
        fileName: "app/routes/settings.theme.tsx",
        lineNumber: 19,
        columnNumber: 11
      }, this),
      /* @__PURE__ */ jsxDEV15(Card, { children: [
        /* @__PURE__ */ jsxDEV15(CardHeader, { children: [
          /* @__PURE__ */ jsxDEV15(CardTitle, { children: "Theme Colors" }, void 0, !1, {
            fileName: "app/routes/settings.theme.tsx",
            lineNumber: 32,
            columnNumber: 15
          }, this),
          /* @__PURE__ */ jsxDEV15(CardDescription, { children: "Preview of the current theme colors." }, void 0, !1, {
            fileName: "app/routes/settings.theme.tsx",
            lineNumber: 33,
            columnNumber: 15
          }, this)
        ] }, void 0, !0, {
          fileName: "app/routes/settings.theme.tsx",
          lineNumber: 31,
          columnNumber: 13
        }, this),
        /* @__PURE__ */ jsxDEV15(CardContent, { children: /* @__PURE__ */ jsxDEV15(ThemeColors, {}, void 0, !1, {
          fileName: "app/routes/settings.theme.tsx",
          lineNumber: 38,
          columnNumber: 15
        }, this) }, void 0, !1, {
          fileName: "app/routes/settings.theme.tsx",
          lineNumber: 37,
          columnNumber: 13
        }, this)
      ] }, void 0, !0, {
        fileName: "app/routes/settings.theme.tsx",
        lineNumber: 30,
        columnNumber: 11
      }, this)
    ] }, void 0, !0, {
      fileName: "app/routes/settings.theme.tsx",
      lineNumber: 18,
      columnNumber: 9
    }, this)
  ] }, void 0, !0, {
    fileName: "app/routes/settings.theme.tsx",
    lineNumber: 10,
    columnNumber: 7
  }, this) }, void 0, !1, {
    fileName: "app/routes/settings.theme.tsx",
    lineNumber: 9,
    columnNumber: 5
  }, this);
}

// app/routes/interview.$id.tsx
var interview_id_exports = {};
__export(interview_id_exports, {
  default: () => InterviewLog,
  loader: () => loader2,
  meta: () => meta2
});
import * as React5 from "react";
import { json as json3 } from "@remix-run/node";
import { Link as Link5, useLoaderData } from "@remix-run/react";
import { promises as fs } from "fs";
import path from "path";
import matter from "gray-matter";
import Markdown from "markdown-to-jsx";
import hljs from "highlight.js";
import { ChevronLeft } from "lucide-react";
import { redirect as redirect3 } from "@remix-run/node";
import { jsxDEV as jsxDEV16 } from "react/jsx-dev-runtime";
var meta2 = ({ data }) => data?.interview ? [
  { title: `${data.interview.data.title} - AI4MDE` },
  { description: data.interview.data.description }
] : [
  { title: "Interview Not Found - AI4MDE" },
  { description: "The requested interview log could not be found." }
];
async function getInterview(groupName, id) {
  let interviewsDir = path.join(process.cwd(), "data", groupName, "interviews");
  try {
    let mdFiles = (await fs.readdir(interviewsDir)).filter((file) => file.endsWith(".md"));
    for (let file of mdFiles) {
      let content4 = await fs.readFile(path.join(interviewsDir, file), "utf-8"), { data: frontMatter, content: interviewContent } = matter(content4), fileId = frontMatter.id || file.replace(".md", "");
      if (fileId === id)
        return {
          content: interviewContent,
          data: {
            id: fileId,
            title: frontMatter.title || file.replace(".md", "").replace(/-/g, " "),
            description: frontMatter.description || interviewContent.slice(0, 150) + "...",
            date: frontMatter.date || (/* @__PURE__ */ new Date()).toISOString(),
            filename: file
          }
        };
    }
    return null;
  } catch (error) {
    return console.error("Error reading interview:", error), null;
  }
}
async function loader2({ request, params }) {
  try {
    let user = await requireUser2(request);
    if (!user.group_name)
      throw new Response("User group not found", { status: 403 });
    let interview = await getInterview(user.group_name, params.id || "");
    if (!interview)
      throw new Response("Interview not found", { status: 404 });
    return json3(
      { interview },
      {
        headers: {
          "Cache-Control": "no-store, no-cache, must-revalidate, proxy-revalidate",
          Pragma: "no-cache",
          Expires: "0"
        }
      }
    );
  } catch (error) {
    if (error instanceof Response && error.status === 401)
      return redirect3(`/login?redirectTo=/interview/${params.id}`);
    throw error;
  }
}
function CodeBlock({ className = "", children }) {
  let language = className.replace(/language-/, ""), html = React5.useMemo(() => {
    if (language && hljs.getLanguage(language))
      try {
        return hljs.highlight(children, { language }).value;
      } catch (err) {
        console.error("Error highlighting code:", err);
      }
    return hljs.highlightAuto(children).value;
  }, [children, language]);
  return /* @__PURE__ */ jsxDEV16("pre", { className: "!p-0 !m-0 !bg-transparent mb-10", children: /* @__PURE__ */ jsxDEV16(
    "code",
    {
      className: `block p-4 rounded-lg bg-muted overflow-x-auto ${language ? `hljs language-${language}` : "hljs"}`,
      dangerouslySetInnerHTML: { __html: html }
    },
    void 0,
    !1,
    {
      fileName: "app/routes/interview.$id.tsx",
      lineNumber: 130,
      columnNumber: 7
    },
    this
  ) }, void 0, !1, {
    fileName: "app/routes/interview.$id.tsx",
    lineNumber: 129,
    columnNumber: 5
  }, this);
}
var markdownOptions = {
  options: {
    forceBlock: !0,
    forceWrapper: !0,
    wrapper: "div",
    disableParsingRawHTML: !1,
    escapeHtml: !1
  },
  overrides: {
    h1: { props: { className: "text-3xl font-bold mt-8 mb-4" } },
    h2: { props: { className: "text-2xl font-semibold mt-6 mb-3" } },
    h3: { props: { className: "text-xl font-semibold mt-4 mb-2" } },
    h4: { props: { className: "text-lg font-semibold mt-4 mb-2" } },
    p: { props: { className: "text-muted-foreground mb-4" } },
    ul: { props: { className: "list-disc list-inside mb-4 ml-4" } },
    ol: { props: { className: "list-decimal list-inside mb-4 ml-4" } },
    li: { props: { className: "mb-1" } },
    a: { props: { className: "text-primary hover:underline" } },
    blockquote: { props: { className: "border-l-4 border-primary pl-4 italic my-4" } },
    code: {
      component: CodeBlock
    },
    pre: {
      component: ({ children }) => children
    },
    img: {
      props: {
        className: "max-w-full h-auto my-4 mx-auto rounded-lg shadow-md",
        loading: "lazy"
      }
    }
  }
};
function InterviewLog() {
  let { interview } = useLoaderData();
  return /* @__PURE__ */ jsxDEV16(MaxWidthWrapper, { className: "py-8", children: [
    /* @__PURE__ */ jsxDEV16("div", { className: "mb-8", children: /* @__PURE__ */ jsxDEV16(Button, { asChild: !0, variant: "ghost", size: "sm", children: /* @__PURE__ */ jsxDEV16(Link5, { to: "/interviews", className: "flex items-center gap-2", children: [
      /* @__PURE__ */ jsxDEV16(ChevronLeft, { className: "h-4 w-4" }, void 0, !1, {
        fileName: "app/routes/interview.$id.tsx",
        lineNumber: 180,
        columnNumber: 13
      }, this),
      "Back to Interviews"
    ] }, void 0, !0, {
      fileName: "app/routes/interview.$id.tsx",
      lineNumber: 179,
      columnNumber: 11
    }, this) }, void 0, !1, {
      fileName: "app/routes/interview.$id.tsx",
      lineNumber: 178,
      columnNumber: 9
    }, this) }, void 0, !1, {
      fileName: "app/routes/interview.$id.tsx",
      lineNumber: 177,
      columnNumber: 7
    }, this),
    /* @__PURE__ */ jsxDEV16("article", { className: cn(
      "max-w-none",
      "[&>h1]:text-4xl [&>h1]:font-bold [&>h1]:mb-4",
      "[&>h2]:text-3xl [&>h2]:font-semibold [&>h2]:mb-3 [&>h2]:mt-8",
      "[&>h3]:text-2xl [&>h3]:font-semibold [&>h3]:mb-2 [&>h3]:mt-6",
      "[&>p]:text-muted-foreground [&>p]:mb-4",
      "[&>ul]:list-disc [&>ul]:ml-6 [&>ul]:mb-4",
      "[&>ol]:list-decimal [&>ol]:ml-6 [&>ol]:mb-4",
      "[&>li]:mb-1",
      "[&>blockquote]:border-l-4 [&>blockquote]:border-primary [&>blockquote]:pl-4 [&>blockquote]:italic [&>blockquote]:my-4",
      "[&>pre]:bg-muted [&>pre]:p-4 [&>pre]:rounded-lg [&>pre]:mb-4 [&>pre]:overflow-x-auto",
      "[&>code]:bg-muted [&>code]:px-1.5 [&>code]:py-0.5 [&>code]:rounded"
    ), children: [
      /* @__PURE__ */ jsxDEV16("h1", { className: "text-4xl font-bold mb-4", children: interview.data.title }, void 0, !1, {
        fileName: "app/routes/interview.$id.tsx",
        lineNumber: 199,
        columnNumber: 9
      }, this),
      interview.data.date && /* @__PURE__ */ jsxDEV16("p", { className: "text-sm text-muted-foreground mb-8", children: new Date(interview.data.date).toLocaleDateString() }, void 0, !1, {
        fileName: "app/routes/interview.$id.tsx",
        lineNumber: 201,
        columnNumber: 9
      }, this),
      /* @__PURE__ */ jsxDEV16(Markdown, { options: markdownOptions, children: interview.content }, void 0, !1, {
        fileName: "app/routes/interview.$id.tsx",
        lineNumber: 205,
        columnNumber: 9
      }, this)
    ] }, void 0, !0, {
      fileName: "app/routes/interview.$id.tsx",
      lineNumber: 186,
      columnNumber: 7
    }, this)
  ] }, void 0, !0, {
    fileName: "app/routes/interview.$id.tsx",
    lineNumber: 176,
    columnNumber: 5
  }, this);
}

// app/routes/srsdocs.$id.tsx
var srsdocs_id_exports = {};
__export(srsdocs_id_exports, {
  loader: () => loader3
});
async function loader3({ request, params }) {
  try {
    if (!(await requireUser(request)).group_name)
      throw new Response("User group not found", { status: 403 });
    let doc = await getDocument(params.id || "");
    if (!doc)
      throw new Response("Document not found", { status: 404 });
    let content4 = await processPlantUml(doc.content);
    return json(
      { doc: { ...doc, content: content4 } },
      {
        headers: {
          "Cache-Control": "no-store, no-cache, must-revalidate, proxy-revalidate",
          Pragma: "no-cache",
          Expires: "0"
        }
      }
    );
  } catch (error) {
    if (error instanceof Response && error.status === 401)
      return redirect(`/login?redirectTo=/srsdocs/${params.id}`);
    throw error;
  }
}

// app/routes/interviews.tsx
var interviews_exports = {};
__export(interviews_exports, {
  default: () => Interviews,
  loader: () => loader4,
  meta: () => meta3
});
import { json as json4, redirect as redirect4 } from "@remix-run/node";
import { Link as Link6, useLoaderData as useLoaderData2 } from "@remix-run/react";
import { promises as fs2 } from "fs";
import path2 from "path";
import matter2 from "gray-matter";
import { FileText as FileText2 } from "lucide-react";
import { jsxDEV as jsxDEV17 } from "react/jsx-dev-runtime";
var meta3 = () => [
  { title: "Interview Logs - AI4MDE" },
  { description: "Interview logs and transcripts for AI4MDE project" }
];
async function getGroupInterviews(groupName) {
  let interviewsDir = path2.join(process.cwd(), "data", groupName, "interviews");
  try {
    let mdFiles = (await fs2.readdir(interviewsDir)).filter((file) => file.endsWith(".md"));
    return (await Promise.all(
      mdFiles.map(async (file) => {
        let content4 = await fs2.readFile(path2.join(interviewsDir, file), "utf-8"), { data: frontMatter, content: interviewContent } = matter2(content4);
        return {
          id: frontMatter.id || file.replace(".md", ""),
          title: frontMatter.title || file.replace(".md", "").replace(/-/g, " "),
          description: frontMatter.description || interviewContent.slice(0, 150) + "...",
          date: frontMatter.date || (/* @__PURE__ */ new Date()).toISOString(),
          filename: file
        };
      })
    )).sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
  } catch (error) {
    return console.error("Error reading interviews:", error), [];
  }
}
async function loader4({ request }) {
  try {
    let user = await requireUser2(request);
    if (!user.group_name)
      throw new Response("User group not found", { status: 403 });
    let interviews = await getGroupInterviews(user.group_name);
    return json4(
      { interviews },
      {
        headers: {
          "Cache-Control": "no-store, no-cache, must-revalidate, proxy-revalidate",
          Pragma: "no-cache",
          Expires: "0"
        }
      }
    );
  } catch (error) {
    if (error instanceof Response && error.status === 401)
      return redirect4("/login?redirectTo=/interviews");
    throw error;
  }
}
function InterviewCard({ id, title, description, date }) {
  return /* @__PURE__ */ jsxDEV17(Card, { className: "group hover:shadow-md transition-shadow", children: /* @__PURE__ */ jsxDEV17(Link6, { to: `/interview/${id}`, className: "block h-full", children: [
    /* @__PURE__ */ jsxDEV17(CardHeader, { children: [
      /* @__PURE__ */ jsxDEV17(CardTitle, { className: "flex items-center gap-2", children: [
        /* @__PURE__ */ jsxDEV17(FileText2, { className: "h-5 w-5 text-muted-foreground group-hover:text-primary transition-colors" }, void 0, !1, {
          fileName: "app/routes/interviews.tsx",
          lineNumber: 92,
          columnNumber: 13
        }, this),
        title
      ] }, void 0, !0, {
        fileName: "app/routes/interviews.tsx",
        lineNumber: 91,
        columnNumber: 11
      }, this),
      date && /* @__PURE__ */ jsxDEV17(CardDescription, { children: new Date(date).toLocaleDateString() }, void 0, !1, {
        fileName: "app/routes/interviews.tsx",
        lineNumber: 96,
        columnNumber: 13
      }, this)
    ] }, void 0, !0, {
      fileName: "app/routes/interviews.tsx",
      lineNumber: 90,
      columnNumber: 9
    }, this),
    /* @__PURE__ */ jsxDEV17(CardContent, { children: /* @__PURE__ */ jsxDEV17("p", { className: "text-muted-foreground line-clamp-3", children: description }, void 0, !1, {
      fileName: "app/routes/interviews.tsx",
      lineNumber: 102,
      columnNumber: 11
    }, this) }, void 0, !1, {
      fileName: "app/routes/interviews.tsx",
      lineNumber: 101,
      columnNumber: 9
    }, this)
  ] }, void 0, !0, {
    fileName: "app/routes/interviews.tsx",
    lineNumber: 89,
    columnNumber: 7
  }, this) }, void 0, !1, {
    fileName: "app/routes/interviews.tsx",
    lineNumber: 88,
    columnNumber: 5
  }, this);
}
function Interviews() {
  let { interviews } = useLoaderData2();
  return /* @__PURE__ */ jsxDEV17(MaxWidthWrapper, { className: "py-8", children: [
    /* @__PURE__ */ jsxDEV17("div", { className: "mb-8", children: [
      /* @__PURE__ */ jsxDEV17("h1", { className: "text-3xl font-bold mb-2", children: "Interview Logs" }, void 0, !1, {
        fileName: "app/routes/interviews.tsx",
        lineNumber: 115,
        columnNumber: 9
      }, this),
      /* @__PURE__ */ jsxDEV17("p", { className: "text-muted-foreground", children: "Browse interview logs and transcripts for the AI4MDE project." }, void 0, !1, {
        fileName: "app/routes/interviews.tsx",
        lineNumber: 116,
        columnNumber: 9
      }, this)
    ] }, void 0, !0, {
      fileName: "app/routes/interviews.tsx",
      lineNumber: 114,
      columnNumber: 7
    }, this),
    interviews.length === 0 ? /* @__PURE__ */ jsxDEV17("div", { className: "text-center py-12", children: /* @__PURE__ */ jsxDEV17("p", { className: "text-muted-foreground", children: "No interview logs found." }, void 0, !1, {
      fileName: "app/routes/interviews.tsx",
      lineNumber: 123,
      columnNumber: 11
    }, this) }, void 0, !1, {
      fileName: "app/routes/interviews.tsx",
      lineNumber: 122,
      columnNumber: 9
    }, this) : /* @__PURE__ */ jsxDEV17("div", { className: "grid gap-6 sm:grid-cols-2 lg:grid-cols-3", children: interviews.map((interview) => /* @__PURE__ */ jsxDEV17(InterviewCard, { ...interview }, interview.id, !1, {
      fileName: "app/routes/interviews.tsx",
      lineNumber: 128,
      columnNumber: 13
    }, this)) }, void 0, !1, {
      fileName: "app/routes/interviews.tsx",
      lineNumber: 126,
      columnNumber: 9
    }, this)
  ] }, void 0, !0, {
    fileName: "app/routes/interviews.tsx",
    lineNumber: 113,
    columnNumber: 5
  }, this);
}

// app/routes/srsdoc.$id.tsx
var srsdoc_id_exports = {};
__export(srsdoc_id_exports, {
  default: () => SrsDoc,
  loader: () => loader5,
  meta: () => meta4
});
import * as React7 from "react";
import { json as json5, redirect as redirect5 } from "@remix-run/node";
import { Link as Link7, useLoaderData as useLoaderData3 } from "@remix-run/react";
import { promises as fs3 } from "fs";
import path3 from "path";
import matter3 from "gray-matter";
import Markdown2 from "markdown-to-jsx";
import hljs2 from "highlight.js";

// app/components/ui/dialog.tsx
import * as React6 from "react";
import * as DialogPrimitive from "@radix-ui/react-dialog";
import { Cross2Icon } from "@radix-ui/react-icons";
import { jsxDEV as jsxDEV18 } from "react/jsx-dev-runtime";
var Dialog = DialogPrimitive.Root;
var DialogPortal = DialogPrimitive.Portal;
var DialogOverlay = React6.forwardRef(({ className, ...props }, ref) => /* @__PURE__ */ jsxDEV18(
  DialogPrimitive.Overlay,
  {
    ref,
    className: cn(
      "fixed inset-0 z-50 bg-black/80 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0",
      className
    ),
    ...props
  },
  void 0,
  !1,
  {
    fileName: "app/components/ui/dialog.tsx",
    lineNumber: 18,
    columnNumber: 3
  },
  this
));
DialogOverlay.displayName = DialogPrimitive.Overlay.displayName;
var DialogContent = React6.forwardRef(({ className, children, ...props }, ref) => /* @__PURE__ */ jsxDEV18(DialogPortal, { children: [
  /* @__PURE__ */ jsxDEV18(DialogOverlay, {}, void 0, !1, {
    fileName: "app/components/ui/dialog.tsx",
    lineNumber: 34,
    columnNumber: 5
  }, this),
  /* @__PURE__ */ jsxDEV18(
    DialogPrimitive.Content,
    {
      ref,
      className: cn(
        "fixed left-[50%] top-[50%] z-50 grid w-full max-w-lg translate-x-[-50%] translate-y-[-50%] gap-4 border bg-background p-6 shadow-lg duration-200 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 data-[state=closed]:slide-out-to-left-1/2 data-[state=closed]:slide-out-to-top-[48%] data-[state=open]:slide-in-from-left-1/2 data-[state=open]:slide-in-from-top-[48%] sm:rounded-lg",
        className
      ),
      ...props,
      children: [
        children,
        /* @__PURE__ */ jsxDEV18(DialogPrimitive.Close, { className: "absolute right-4 top-4 rounded-sm opacity-70 ring-offset-background transition-opacity hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:pointer-events-none data-[state=open]:bg-accent data-[state=open]:text-muted-foreground", children: [
          /* @__PURE__ */ jsxDEV18(Cross2Icon, { className: "h-4 w-4" }, void 0, !1, {
            fileName: "app/components/ui/dialog.tsx",
            lineNumber: 45,
            columnNumber: 9
          }, this),
          /* @__PURE__ */ jsxDEV18("span", { className: "sr-only", children: "Close" }, void 0, !1, {
            fileName: "app/components/ui/dialog.tsx",
            lineNumber: 46,
            columnNumber: 9
          }, this)
        ] }, void 0, !0, {
          fileName: "app/components/ui/dialog.tsx",
          lineNumber: 44,
          columnNumber: 7
        }, this)
      ]
    },
    void 0,
    !0,
    {
      fileName: "app/components/ui/dialog.tsx",
      lineNumber: 35,
      columnNumber: 5
    },
    this
  )
] }, void 0, !0, {
  fileName: "app/components/ui/dialog.tsx",
  lineNumber: 33,
  columnNumber: 3
}, this));
DialogContent.displayName = DialogPrimitive.Content.displayName;
var DialogHeader = ({
  className,
  ...props
}) => /* @__PURE__ */ jsxDEV18(
  "div",
  {
    className: cn(
      "flex flex-col space-y-1.5 text-center sm:text-left",
      className
    ),
    ...props
  },
  void 0,
  !1,
  {
    fileName: "app/components/ui/dialog.tsx",
    lineNumber: 57,
    columnNumber: 3
  },
  this
);
DialogHeader.displayName = "DialogHeader";
var DialogFooter = ({
  className,
  ...props
}) => /* @__PURE__ */ jsxDEV18(
  "div",
  {
    className: cn(
      "flex flex-col-reverse sm:flex-row sm:justify-end sm:space-x-2",
      className
    ),
    ...props
  },
  void 0,
  !1,
  {
    fileName: "app/components/ui/dialog.tsx",
    lineNumber: 71,
    columnNumber: 3
  },
  this
);
DialogFooter.displayName = "DialogFooter";
var DialogTitle = React6.forwardRef(({ className, ...props }, ref) => /* @__PURE__ */ jsxDEV18(
  DialogPrimitive.Title,
  {
    ref,
    className: cn(
      "text-lg font-semibold leading-none tracking-tight",
      className
    ),
    ...props
  },
  void 0,
  !1,
  {
    fileName: "app/components/ui/dialog.tsx",
    lineNumber: 85,
    columnNumber: 3
  },
  this
));
DialogTitle.displayName = DialogPrimitive.Title.displayName;
var DialogDescription = React6.forwardRef(({ className, ...props }, ref) => /* @__PURE__ */ jsxDEV18(
  DialogPrimitive.Description,
  {
    ref,
    className: cn("text-sm text-muted-foreground", className),
    ...props
  },
  void 0,
  !1,
  {
    fileName: "app/components/ui/dialog.tsx",
    lineNumber: 100,
    columnNumber: 3
  },
  this
));
DialogDescription.displayName = DialogPrimitive.Description.displayName;

// app/routes/srsdoc.$id.tsx
import { ChevronLeft as ChevronLeft2, ZoomIn as ZoomIn2 } from "lucide-react";

// app/utils/plantuml.server.ts
import { encode } from "plantuml-encoder";
var PLANTUML_SERVER = "https://www.plantuml.com/plantuml/svg", THEME_SETTINGS = `
skinparam backgroundColor transparent
skinparam useBetaStyle false

skinparam defaultFontName Inter
skinparam defaultFontSize 12

skinparam sequence {
  ArrowColor hsl(var(--primary))
  LifeLineBorderColor hsl(var(--muted))
  LifeLineBackgroundColor hsl(var(--background))
  ParticipantBorderColor hsl(var(--primary))
  ParticipantBackgroundColor hsl(var(--background))
  ParticipantFontColor hsl(var(--foreground))
  ActorBorderColor hsl(var(--primary))
  ActorBackgroundColor hsl(var(--background))
  ActorFontColor hsl(var(--foreground))
}

skinparam class {
  BackgroundColor hsl(var(--background))
  BorderColor hsl(var(--primary))
  ArrowColor hsl(var(--primary))
  FontColor hsl(var(--foreground))
  AttributeFontColor hsl(var(--muted-foreground))
  StereotypeFontColor hsl(var(--accent))
}

skinparam component {
  BackgroundColor hsl(var(--background))
  BorderColor hsl(var(--primary))
  ArrowColor hsl(var(--primary))
  FontColor hsl(var(--foreground))
}

skinparam interface {
  BackgroundColor hsl(var(--background))
  BorderColor hsl(var(--primary))
  FontColor hsl(var(--foreground))
}

skinparam note {
  BackgroundColor hsl(var(--accent))
  BorderColor hsl(var(--accent-foreground))
  FontColor hsl(var(--accent-foreground))
}
`;
async function convertPlantUmlToSvg(plantUmlCode) {
  try {
    let cleanCode = plantUmlCode.replace(/```plantuml/g, "").replace(/```/g, "").trim(), themedCode = cleanCode.includes("@startuml") ? cleanCode.replace("@startuml", `@startuml
${THEME_SETTINGS}`) : `@startuml
${THEME_SETTINGS}
${cleanCode}
@enduml`, encoded = encode(themedCode);
    return `${PLANTUML_SERVER}/${encoded}`;
  } catch (error) {
    return console.error("Error converting PlantUML to SVG:", error), "";
  }
}

// app/routes/srsdoc.$id.tsx
import { Fragment as Fragment2, jsxDEV as jsxDEV19 } from "react/jsx-dev-runtime";
var meta4 = ({ data }) => data?.doc ? [
  { title: `${data.doc.data.title} - AI4MDE` },
  { description: data.doc.data.description }
] : [
  { title: "Document Not Found - AI4MDE" },
  { description: "The requested SRS document could not be found." }
];
async function getDocument2(id) {
  let docsDir = path3.join(process.cwd(), "data", "liacs", "srsdocs");
  try {
    let mdFiles = (await fs3.readdir(docsDir)).filter((file) => file.endsWith(".md"));
    for (let file of mdFiles) {
      let content4 = await fs3.readFile(path3.join(docsDir, file), "utf-8"), { data: frontMatter, content: docContent } = matter3(content4), fileId = frontMatter.id || file.replace(".md", "");
      if (fileId === id)
        return {
          content: docContent,
          data: {
            id: fileId,
            title: frontMatter.title || file.replace(".md", "").replace(/-/g, " "),
            description: frontMatter.description || docContent.slice(0, 150) + "...",
            date: frontMatter.date || (/* @__PURE__ */ new Date()).toISOString(),
            filename: file
          }
        };
    }
    return null;
  } catch (error) {
    return console.error("Error reading document:", error), null;
  }
}
async function loader5({ request, params }) {
  try {
    if (!(await requireUser2(request)).group_name)
      throw new Response("User group not found", { status: 403 });
    let doc = await getDocument2(params.id || "");
    if (!doc)
      throw new Response("Document not found", { status: 404 });
    let content4 = await processPlantUml2(doc.content);
    return json5(
      { doc: { ...doc, content: content4 } },
      {
        headers: {
          "Cache-Control": "no-store, no-cache, must-revalidate, proxy-revalidate",
          Pragma: "no-cache",
          Expires: "0"
        }
      }
    );
  } catch (error) {
    if (error instanceof Response && error.status === 401)
      return redirect5(`/login?redirectTo=/srsdoc/${params.id}`);
    throw error;
  }
}
function DiagramImage({ src, alt }) {
  let [isOpen, setIsOpen] = React7.useState(!1);
  return /* @__PURE__ */ jsxDEV19(Fragment2, { children: [
    /* @__PURE__ */ jsxDEV19(
      "div",
      {
        onClick: () => setIsOpen(!0),
        className: "relative group cursor-zoom-in",
        children: [
          /* @__PURE__ */ jsxDEV19(
            "img",
            {
              src,
              alt,
              className: "max-w-full h-auto my-4 mx-auto rounded-lg shadow-md transition-opacity group-hover:opacity-95",
              loading: "lazy"
            },
            void 0,
            !1,
            {
              fileName: "app/routes/srsdoc.$id.tsx",
              lineNumber: 125,
              columnNumber: 9
            },
            this
          ),
          /* @__PURE__ */ jsxDEV19("div", { className: "absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity", children: /* @__PURE__ */ jsxDEV19("div", { className: "bg-background/80 p-2 rounded-full", children: /* @__PURE__ */ jsxDEV19(ZoomIn2, { className: "w-6 h-6 text-foreground" }, void 0, !1, {
            fileName: "app/routes/srsdoc.$id.tsx",
            lineNumber: 133,
            columnNumber: 13
          }, this) }, void 0, !1, {
            fileName: "app/routes/srsdoc.$id.tsx",
            lineNumber: 132,
            columnNumber: 11
          }, this) }, void 0, !1, {
            fileName: "app/routes/srsdoc.$id.tsx",
            lineNumber: 131,
            columnNumber: 9
          }, this)
        ]
      },
      void 0,
      !0,
      {
        fileName: "app/routes/srsdoc.$id.tsx",
        lineNumber: 121,
        columnNumber: 7
      },
      this
    ),
    /* @__PURE__ */ jsxDEV19(Dialog, { open: isOpen, onOpenChange: setIsOpen, children: /* @__PURE__ */ jsxDEV19(DialogContent, { className: "max-w-[95vw] max-h-[95vh] p-0", children: /* @__PURE__ */ jsxDEV19("div", { className: "w-full h-full overflow-auto p-6", children: /* @__PURE__ */ jsxDEV19(
      "img",
      {
        src,
        alt,
        className: "w-full h-full object-contain"
      },
      void 0,
      !1,
      {
        fileName: "app/routes/srsdoc.$id.tsx",
        lineNumber: 141,
        columnNumber: 13
      },
      this
    ) }, void 0, !1, {
      fileName: "app/routes/srsdoc.$id.tsx",
      lineNumber: 140,
      columnNumber: 11
    }, this) }, void 0, !1, {
      fileName: "app/routes/srsdoc.$id.tsx",
      lineNumber: 139,
      columnNumber: 9
    }, this) }, void 0, !1, {
      fileName: "app/routes/srsdoc.$id.tsx",
      lineNumber: 138,
      columnNumber: 7
    }, this)
  ] }, void 0, !0, {
    fileName: "app/routes/srsdoc.$id.tsx",
    lineNumber: 120,
    columnNumber: 5
  }, this);
}
function EnlargeableTable({ children }) {
  let [isOpen, setIsOpen] = React7.useState(!1);
  return /* @__PURE__ */ jsxDEV19(Fragment2, { children: [
    /* @__PURE__ */ jsxDEV19(
      "div",
      {
        onClick: () => setIsOpen(!0),
        className: "relative group cursor-zoom-in overflow-auto",
        children: [
          /* @__PURE__ */ jsxDEV19("div", { className: "my-4", children }, void 0, !1, {
            fileName: "app/routes/srsdoc.$id.tsx",
            lineNumber: 163,
            columnNumber: 9
          }, this),
          /* @__PURE__ */ jsxDEV19("div", { className: "absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity", children: /* @__PURE__ */ jsxDEV19("div", { className: "bg-background/80 p-2 rounded-full", children: /* @__PURE__ */ jsxDEV19(ZoomIn2, { className: "w-6 h-6 text-foreground" }, void 0, !1, {
            fileName: "app/routes/srsdoc.$id.tsx",
            lineNumber: 168,
            columnNumber: 13
          }, this) }, void 0, !1, {
            fileName: "app/routes/srsdoc.$id.tsx",
            lineNumber: 167,
            columnNumber: 11
          }, this) }, void 0, !1, {
            fileName: "app/routes/srsdoc.$id.tsx",
            lineNumber: 166,
            columnNumber: 9
          }, this)
        ]
      },
      void 0,
      !0,
      {
        fileName: "app/routes/srsdoc.$id.tsx",
        lineNumber: 159,
        columnNumber: 7
      },
      this
    ),
    /* @__PURE__ */ jsxDEV19(Dialog, { open: isOpen, onOpenChange: setIsOpen, children: /* @__PURE__ */ jsxDEV19(DialogContent, { className: "max-w-[95vw] max-h-[95vh] p-0", children: /* @__PURE__ */ jsxDEV19("div", { className: "w-full h-full overflow-auto p-6", children }, void 0, !1, {
      fileName: "app/routes/srsdoc.$id.tsx",
      lineNumber: 175,
      columnNumber: 11
    }, this) }, void 0, !1, {
      fileName: "app/routes/srsdoc.$id.tsx",
      lineNumber: 174,
      columnNumber: 9
    }, this) }, void 0, !1, {
      fileName: "app/routes/srsdoc.$id.tsx",
      lineNumber: 173,
      columnNumber: 7
    }, this)
  ] }, void 0, !0, {
    fileName: "app/routes/srsdoc.$id.tsx",
    lineNumber: 158,
    columnNumber: 5
  }, this);
}
function EnlargeableCode({ language, children, html }) {
  let [isOpen, setIsOpen] = React7.useState(!1);
  return /* @__PURE__ */ jsxDEV19(Fragment2, { children: [
    /* @__PURE__ */ jsxDEV19(
      "div",
      {
        onClick: () => setIsOpen(!0),
        className: "relative group cursor-zoom-in",
        children: [
          /* @__PURE__ */ jsxDEV19("pre", { className: "!p-0 !m-0 !bg-transparent mb-10", children: /* @__PURE__ */ jsxDEV19(
            "code",
            {
              className: `block p-4 rounded-lg bg-muted overflow-x-auto ${language ? `hljs language-${language}` : "hljs"}`,
              dangerouslySetInnerHTML: { __html: html }
            },
            void 0,
            !1,
            {
              fileName: "app/routes/srsdoc.$id.tsx",
              lineNumber: 195,
              columnNumber: 11
            },
            this
          ) }, void 0, !1, {
            fileName: "app/routes/srsdoc.$id.tsx",
            lineNumber: 194,
            columnNumber: 9
          }, this),
          /* @__PURE__ */ jsxDEV19("div", { className: "absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity", children: /* @__PURE__ */ jsxDEV19("div", { className: "bg-background/80 p-2 rounded-full", children: /* @__PURE__ */ jsxDEV19(ZoomIn2, { className: "w-6 h-6 text-foreground" }, void 0, !1, {
            fileName: "app/routes/srsdoc.$id.tsx",
            lineNumber: 202,
            columnNumber: 13
          }, this) }, void 0, !1, {
            fileName: "app/routes/srsdoc.$id.tsx",
            lineNumber: 201,
            columnNumber: 11
          }, this) }, void 0, !1, {
            fileName: "app/routes/srsdoc.$id.tsx",
            lineNumber: 200,
            columnNumber: 9
          }, this)
        ]
      },
      void 0,
      !0,
      {
        fileName: "app/routes/srsdoc.$id.tsx",
        lineNumber: 190,
        columnNumber: 7
      },
      this
    ),
    /* @__PURE__ */ jsxDEV19(Dialog, { open: isOpen, onOpenChange: setIsOpen, children: /* @__PURE__ */ jsxDEV19(DialogContent, { className: "max-w-[95vw] max-h-[95vh] p-0", children: /* @__PURE__ */ jsxDEV19("div", { className: "w-full h-full overflow-auto p-6", children: /* @__PURE__ */ jsxDEV19("pre", { className: "!p-0 !m-0 !bg-transparent", children: /* @__PURE__ */ jsxDEV19(
      "code",
      {
        className: `block p-4 rounded-lg bg-muted overflow-x-auto ${language ? `hljs language-${language}` : "hljs"}`,
        dangerouslySetInnerHTML: { __html: html }
      },
      void 0,
      !1,
      {
        fileName: "app/routes/srsdoc.$id.tsx",
        lineNumber: 211,
        columnNumber: 15
      },
      this
    ) }, void 0, !1, {
      fileName: "app/routes/srsdoc.$id.tsx",
      lineNumber: 210,
      columnNumber: 13
    }, this) }, void 0, !1, {
      fileName: "app/routes/srsdoc.$id.tsx",
      lineNumber: 209,
      columnNumber: 11
    }, this) }, void 0, !1, {
      fileName: "app/routes/srsdoc.$id.tsx",
      lineNumber: 208,
      columnNumber: 9
    }, this) }, void 0, !1, {
      fileName: "app/routes/srsdoc.$id.tsx",
      lineNumber: 207,
      columnNumber: 7
    }, this)
  ] }, void 0, !0, {
    fileName: "app/routes/srsdoc.$id.tsx",
    lineNumber: 189,
    columnNumber: 5
  }, this);
}
function CodeBlock2({ className = "", children }) {
  let language = className.replace(/language-/, ""), html = React7.useMemo(() => {
    if (language && hljs2.getLanguage(language))
      try {
        return hljs2.highlight(children, { language }).value;
      } catch (err) {
        console.error("Error highlighting code:", err);
      }
    return hljs2.highlightAuto(children).value;
  }, [children, language]);
  return /* @__PURE__ */ jsxDEV19(EnlargeableCode, { language, html, children }, void 0, !1, {
    fileName: "app/routes/srsdoc.$id.tsx",
    lineNumber: 238,
    columnNumber: 5
  }, this);
}
async function processPlantUml2(content4) {
  let plantUmlRegex = /```plantuml\n([\s\S]*?)```/g, match, processedContent = content4, diagramCount = 0;
  for (; (match = plantUmlRegex.exec(content4)) !== null; ) {
    let [fullMatch, diagramCode] = match, svgUrl = await convertPlantUmlToSvg(diagramCode);
    svgUrl && (diagramCount++, processedContent = processedContent.replace(
      fullMatch,
      `<div data-diagram="${diagramCount}" data-url="${svgUrl}"></div>`
    ));
  }
  return processedContent;
}
var markdownOptions2 = {
  options: {
    forceBlock: !0,
    forceWrapper: !0,
    wrapper: "div",
    disableParsingRawHTML: !1,
    escapeHtml: !1
  },
  overrides: {
    h1: { props: { className: "text-3xl font-bold mt-8 mb-4" } },
    h2: { props: { className: "text-2xl font-semibold mt-6 mb-3" } },
    h3: { props: { className: "text-xl font-semibold mt-4 mb-2" } },
    h4: { props: { className: "text-lg font-semibold mt-4 mb-2" } },
    p: { props: { className: "text-muted-foreground mb-4" } },
    ul: { props: { className: "list-disc list-inside mb-4 ml-4" } },
    ol: { props: { className: "list-decimal list-inside mb-4 ml-4" } },
    li: { props: { className: "mb-1" } },
    a: { props: { className: "text-primary hover:underline" } },
    blockquote: { props: { className: "border-l-4 border-primary pl-4 italic my-4" } },
    code: {
      component: CodeBlock2
    },
    pre: {
      component: ({ children }) => children
    },
    img: {
      props: {
        className: "max-w-full h-auto my-4 mx-auto rounded-lg shadow-md",
        loading: "lazy"
      }
    },
    div: {
      component: ({ "data-diagram": isDiagram, "data-url": url, ...props }) => isDiagram && url ? /* @__PURE__ */ jsxDEV19(DiagramImage, { src: url, alt: `Diagram ${isDiagram}` }, void 0, !1, {
        fileName: "app/routes/srsdoc.$id.tsx",
        lineNumber: 297,
        columnNumber: 18
      }, this) : /* @__PURE__ */ jsxDEV19("div", { ...props }, void 0, !1, {
        fileName: "app/routes/srsdoc.$id.tsx",
        lineNumber: 299,
        columnNumber: 16
      }, this)
    },
    plantuml: {
      component: ({ children }) => /* @__PURE__ */ jsxDEV19("div", { className: "hidden", children }, void 0, !1, {
        fileName: "app/routes/srsdoc.$id.tsx",
        lineNumber: 303,
        columnNumber: 36
      }, this)
    },
    table: {
      component: ({ children }) => /* @__PURE__ */ jsxDEV19(EnlargeableTable, { children: /* @__PURE__ */ jsxDEV19("table", { className: "w-full border-collapse border border-border", children }, void 0, !1, {
        fileName: "app/routes/srsdoc.$id.tsx",
        lineNumber: 308,
        columnNumber: 11
      }, this) }, void 0, !1, {
        fileName: "app/routes/srsdoc.$id.tsx",
        lineNumber: 307,
        columnNumber: 7
      }, this)
    },
    th: {
      props: {
        className: "border border-border bg-muted p-2 text-left font-semibold"
      }
    },
    td: {
      props: {
        className: "border border-border p-2"
      }
    }
  }
};
function SrsDoc() {
  let { doc } = useLoaderData3();
  return /* @__PURE__ */ jsxDEV19(MaxWidthWrapper, { className: "py-8", children: [
    /* @__PURE__ */ jsxDEV19("div", { className: "mb-8", children: /* @__PURE__ */ jsxDEV19(Button, { asChild: !0, variant: "ghost", size: "sm", children: /* @__PURE__ */ jsxDEV19(Link7, { to: "/srsdocs", className: "flex items-center gap-2", children: [
      /* @__PURE__ */ jsxDEV19(ChevronLeft2, { className: "h-4 w-4" }, void 0, !1, {
        fileName: "app/routes/srsdoc.$id.tsx",
        lineNumber: 335,
        columnNumber: 13
      }, this),
      "Back to Documents"
    ] }, void 0, !0, {
      fileName: "app/routes/srsdoc.$id.tsx",
      lineNumber: 334,
      columnNumber: 11
    }, this) }, void 0, !1, {
      fileName: "app/routes/srsdoc.$id.tsx",
      lineNumber: 333,
      columnNumber: 9
    }, this) }, void 0, !1, {
      fileName: "app/routes/srsdoc.$id.tsx",
      lineNumber: 332,
      columnNumber: 7
    }, this),
    /* @__PURE__ */ jsxDEV19("article", { className: cn(
      "max-w-none",
      "[&>h1]:text-4xl [&>h1]:font-bold [&>h1]:mb-4",
      "[&>h2]:text-3xl [&>h2]:font-semibold [&>h2]:mb-3 [&>h2]:mt-8",
      "[&>h3]:text-2xl [&>h3]:font-semibold [&>h3]:mb-2 [&>h3]:mt-6",
      "[&>p]:text-muted-foreground [&>p]:mb-4",
      "[&>ul]:list-disc [&>ul]:ml-6 [&>ul]:mb-4",
      "[&>ol]:list-decimal [&>ol]:ml-6 [&>ol]:mb-4",
      "[&>li]:mb-1",
      "[&>blockquote]:border-l-4 [&>blockquote]:border-primary [&>blockquote]:pl-4 [&>blockquote]:italic [&>blockquote]:my-4",
      "[&>pre]:bg-muted [&>pre]:p-4 [&>pre]:rounded-lg [&>pre]:mb-4 [&>pre]:overflow-x-auto",
      "[&>code]:bg-muted [&>code]:px-1.5 [&>code]:py-0.5 [&>code]:rounded"
    ), children: [
      /* @__PURE__ */ jsxDEV19("h1", { className: "text-4xl font-bold mb-4", children: doc.data.title }, void 0, !1, {
        fileName: "app/routes/srsdoc.$id.tsx",
        lineNumber: 354,
        columnNumber: 9
      }, this),
      doc.data.date && /* @__PURE__ */ jsxDEV19("p", { className: "text-sm text-muted-foreground mb-8", children: new Date(doc.data.date).toLocaleDateString() }, void 0, !1, {
        fileName: "app/routes/srsdoc.$id.tsx",
        lineNumber: 356,
        columnNumber: 9
      }, this),
      /* @__PURE__ */ jsxDEV19(Markdown2, { options: markdownOptions2, children: doc.content }, void 0, !1, {
        fileName: "app/routes/srsdoc.$id.tsx",
        lineNumber: 360,
        columnNumber: 9
      }, this)
    ] }, void 0, !0, {
      fileName: "app/routes/srsdoc.$id.tsx",
      lineNumber: 341,
      columnNumber: 7
    }, this)
  ] }, void 0, !0, {
    fileName: "app/routes/srsdoc.$id.tsx",
    lineNumber: 331,
    columnNumber: 5
  }, this);
}

// app/routes/contact.tsx
var contact_exports = {};
__export(contact_exports, {
  action: () => action,
  default: () => Contact,
  meta: () => meta5
});
import * as React11 from "react";
import { json as json6 } from "@remix-run/node";
import { Form as Form2, useActionData, useNavigation } from "@remix-run/react";
import { z } from "zod";

// app/components/ui/input.tsx
import * as React8 from "react";
import { jsxDEV as jsxDEV20 } from "react/jsx-dev-runtime";
var Input = React8.forwardRef(
  ({ className, type, ...props }, ref) => /* @__PURE__ */ jsxDEV20(
    "input",
    {
      type,
      className: cn(
        "flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm transition-colors file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50",
        className
      ),
      ref,
      ...props
    },
    void 0,
    !1,
    {
      fileName: "app/components/ui/input.tsx",
      lineNumber: 11,
      columnNumber: 7
    },
    this
  )
);
Input.displayName = "Input";

// app/components/ui/textarea.tsx
import * as React9 from "react";
import { jsxDEV as jsxDEV21 } from "react/jsx-dev-runtime";
var Textarea = React9.forwardRef(
  ({ className, error, ...props }, ref) => /* @__PURE__ */ jsxDEV21(
    "textarea",
    {
      className: cn(
        "flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50",
        error && "border-red-500",
        className
      ),
      ref,
      ...props
    },
    void 0,
    !1,
    {
      fileName: "app/components/ui/textarea.tsx",
      lineNumber: 12,
      columnNumber: 7
    },
    this
  )
);
Textarea.displayName = "Textarea";

// app/components/ui/label.tsx
import * as React10 from "react";
import * as LabelPrimitive from "@radix-ui/react-label";
import { cva as cva2 } from "class-variance-authority";
import { jsxDEV as jsxDEV22 } from "react/jsx-dev-runtime";
var labelVariants = cva2(
  "text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
), Label2 = React10.forwardRef(({ className, ...props }, ref) => /* @__PURE__ */ jsxDEV22(
  LabelPrimitive.Root,
  {
    ref,
    className: cn(labelVariants(), className),
    ...props
  },
  void 0,
  !1,
  {
    fileName: "app/components/ui/label.tsx",
    lineNumber: 16,
    columnNumber: 3
  },
  this
));
Label2.displayName = LabelPrimitive.Root.displayName;

// app/routes/contact.tsx
import { promises as fs4 } from "fs";
import path4 from "path";
import { Fragment as Fragment3, jsxDEV as jsxDEV23 } from "react/jsx-dev-runtime";
var meta5 = () => [
  { title: "Contact - AI4MDE" },
  { name: "description", content: "Get in touch with the AI4MDE team" }
], formSchema = z.object({
  firstName: z.string().min(2, "First name must be at least 2 characters").max(50),
  lastName: z.string().min(2, "Last name must be at least 2 characters").max(50),
  email: z.string().email("Invalid email address"),
  message: z.string().min(10, "Message must be at least 10 characters").max(1e3)
}), action = async ({ request }) => {
  let formData = Object.fromEntries(await request.formData());
  try {
    let validatedData = formSchema.parse(formData), timestamp = (/* @__PURE__ */ new Date()).toISOString(), filename = `${validatedData.firstName}_${validatedData.lastName}_${timestamp.replace(/[:.]/g, "-")}.md`, contactDir = path4.join(process.cwd(), "data", "contact");
    await fs4.mkdir(contactDir, { recursive: !0 });
    let markdown = `---
first_name: ${validatedData.firstName}
last_name: ${validatedData.lastName}
email: ${validatedData.email}
date: ${timestamp}
---

${validatedData.message}
`, filePath = path4.join(contactDir, filename);
    return await fs4.writeFile(filePath, markdown, "utf-8"), json6({ success: !0 });
  } catch (error) {
    return error instanceof z.ZodError ? json6({ errors: error.errors }, { status: 400 }) : (console.error("Failed to save contact form:", error), json6({ error: "Failed to send message. Please try again later." }, { status: 500 }));
  }
};
function Contact() {
  let actionData = useActionData(), [showThankYou, setShowThankYou] = React11.useState(!1), formRef = React11.useRef(null), isSubmitting = useNavigation().state === "submitting";
  React11.useEffect(() => {
    actionData?.success && (setShowThankYou(!0), formRef.current && formRef.current.reset());
  }, [actionData]);
  let handleDialogClose = () => {
    setShowThankYou(!1);
  };
  return /* @__PURE__ */ jsxDEV23(Fragment3, { children: [
    /* @__PURE__ */ jsxDEV23(MaxWidthWrapper, { className: "py-8", children: /* @__PURE__ */ jsxDEV23("div", { className: "flex flex-col items-center space-y-8", children: [
      /* @__PURE__ */ jsxDEV23("div", { className: "space-y-2 text-center", children: [
        /* @__PURE__ */ jsxDEV23("h1", { className: "text-3xl font-bold", children: "Get In Touch" }, void 0, !1, {
          fileName: "app/routes/contact.tsx",
          lineNumber: 110,
          columnNumber: 13
        }, this),
        /* @__PURE__ */ jsxDEV23("p", { className: "text-muted-foreground", children: "Have questions, feedback, or want to collaborate? Drop us a message!" }, void 0, !1, {
          fileName: "app/routes/contact.tsx",
          lineNumber: 111,
          columnNumber: 13
        }, this)
      ] }, void 0, !0, {
        fileName: "app/routes/contact.tsx",
        lineNumber: 109,
        columnNumber: 11
      }, this),
      /* @__PURE__ */ jsxDEV23(Card, { className: "w-full max-w-md md:max-w-2xl lg:max-w-4xl", children: /* @__PURE__ */ jsxDEV23(CardContent, { className: "pt-6", children: /* @__PURE__ */ jsxDEV23(Form2, { ref: formRef, method: "post", className: "space-y-6", children: [
        /* @__PURE__ */ jsxDEV23("div", { className: "grid grid-cols-2 gap-4", children: [
          /* @__PURE__ */ jsxDEV23("div", { className: "space-y-2", children: [
            /* @__PURE__ */ jsxDEV23(Label2, { htmlFor: "firstName", children: "First Name" }, void 0, !1, {
              fileName: "app/routes/contact.tsx",
              lineNumber: 121,
              columnNumber: 21
            }, this),
            /* @__PURE__ */ jsxDEV23(
              Input,
              {
                id: "firstName",
                name: "firstName",
                placeholder: "John",
                "aria-describedby": actionData?.errors?.find((e) => e.path[0] === "firstName") ? "firstName-error" : void 0
              },
              void 0,
              !1,
              {
                fileName: "app/routes/contact.tsx",
                lineNumber: 122,
                columnNumber: 21
              },
              this
            ),
            actionData?.errors?.find((e) => e.path[0] === "firstName") && /* @__PURE__ */ jsxDEV23("p", { className: "text-sm text-red-500", id: "firstName-error", children: actionData.errors.find((e) => e.path[0] === "firstName")?.message }, void 0, !1, {
              fileName: "app/routes/contact.tsx",
              lineNumber: 133,
              columnNumber: 23
            }, this)
          ] }, void 0, !0, {
            fileName: "app/routes/contact.tsx",
            lineNumber: 120,
            columnNumber: 19
          }, this),
          /* @__PURE__ */ jsxDEV23("div", { className: "space-y-2", children: [
            /* @__PURE__ */ jsxDEV23(Label2, { htmlFor: "lastName", children: "Last Name" }, void 0, !1, {
              fileName: "app/routes/contact.tsx",
              lineNumber: 139,
              columnNumber: 21
            }, this),
            /* @__PURE__ */ jsxDEV23(
              Input,
              {
                id: "lastName",
                name: "lastName",
                placeholder: "Doe",
                "aria-describedby": actionData?.errors?.find((e) => e.path[0] === "lastName") ? "lastName-error" : void 0
              },
              void 0,
              !1,
              {
                fileName: "app/routes/contact.tsx",
                lineNumber: 140,
                columnNumber: 21
              },
              this
            ),
            actionData?.errors?.find((e) => e.path[0] === "lastName") && /* @__PURE__ */ jsxDEV23("p", { className: "text-sm text-red-500", id: "lastName-error", children: actionData.errors.find((e) => e.path[0] === "lastName")?.message }, void 0, !1, {
              fileName: "app/routes/contact.tsx",
              lineNumber: 151,
              columnNumber: 23
            }, this)
          ] }, void 0, !0, {
            fileName: "app/routes/contact.tsx",
            lineNumber: 138,
            columnNumber: 19
          }, this)
        ] }, void 0, !0, {
          fileName: "app/routes/contact.tsx",
          lineNumber: 119,
          columnNumber: 17
        }, this),
        /* @__PURE__ */ jsxDEV23("div", { className: "space-y-2", children: [
          /* @__PURE__ */ jsxDEV23(Label2, { htmlFor: "email", children: "Email" }, void 0, !1, {
            fileName: "app/routes/contact.tsx",
            lineNumber: 159,
            columnNumber: 19
          }, this),
          /* @__PURE__ */ jsxDEV23(
            Input,
            {
              type: "email",
              id: "email",
              name: "email",
              placeholder: "john.doe@example.com",
              "aria-describedby": actionData?.errors?.find((e) => e.path[0] === "email") ? "email-error" : void 0
            },
            void 0,
            !1,
            {
              fileName: "app/routes/contact.tsx",
              lineNumber: 160,
              columnNumber: 19
            },
            this
          ),
          actionData?.errors?.find((e) => e.path[0] === "email") && /* @__PURE__ */ jsxDEV23("p", { className: "text-sm text-red-500", id: "email-error", children: actionData.errors.find((e) => e.path[0] === "email")?.message }, void 0, !1, {
            fileName: "app/routes/contact.tsx",
            lineNumber: 172,
            columnNumber: 21
          }, this)
        ] }, void 0, !0, {
          fileName: "app/routes/contact.tsx",
          lineNumber: 158,
          columnNumber: 17
        }, this),
        /* @__PURE__ */ jsxDEV23("div", { className: "space-y-2", children: [
          /* @__PURE__ */ jsxDEV23(Label2, { htmlFor: "message", children: "Message" }, void 0, !1, {
            fileName: "app/routes/contact.tsx",
            lineNumber: 179,
            columnNumber: 19
          }, this),
          /* @__PURE__ */ jsxDEV23(
            Textarea,
            {
              id: "message",
              name: "message",
              className: "min-h-[250px]",
              "aria-describedby": actionData?.errors?.find((e) => e.path[0] === "message") ? "message-error" : void 0
            },
            void 0,
            !1,
            {
              fileName: "app/routes/contact.tsx",
              lineNumber: 180,
              columnNumber: 19
            },
            this
          ),
          actionData?.errors?.find((e) => e.path[0] === "message") && /* @__PURE__ */ jsxDEV23("p", { className: "text-sm text-red-500", id: "message-error", children: actionData.errors.find((e) => e.path[0] === "message")?.message }, void 0, !1, {
            fileName: "app/routes/contact.tsx",
            lineNumber: 191,
            columnNumber: 21
          }, this)
        ] }, void 0, !0, {
          fileName: "app/routes/contact.tsx",
          lineNumber: 178,
          columnNumber: 17
        }, this),
        /* @__PURE__ */ jsxDEV23(Button, { type: "submit", className: "w-full", disabled: isSubmitting, children: isSubmitting ? "Sending..." : "Send Message" }, void 0, !1, {
          fileName: "app/routes/contact.tsx",
          lineNumber: 197,
          columnNumber: 17
        }, this)
      ] }, void 0, !0, {
        fileName: "app/routes/contact.tsx",
        lineNumber: 118,
        columnNumber: 15
      }, this) }, void 0, !1, {
        fileName: "app/routes/contact.tsx",
        lineNumber: 117,
        columnNumber: 13
      }, this) }, void 0, !1, {
        fileName: "app/routes/contact.tsx",
        lineNumber: 116,
        columnNumber: 11
      }, this)
    ] }, void 0, !0, {
      fileName: "app/routes/contact.tsx",
      lineNumber: 108,
      columnNumber: 9
    }, this) }, void 0, !1, {
      fileName: "app/routes/contact.tsx",
      lineNumber: 107,
      columnNumber: 7
    }, this),
    /* @__PURE__ */ jsxDEV23(Dialog, { open: showThankYou, onOpenChange: handleDialogClose, children: /* @__PURE__ */ jsxDEV23(DialogContent, { children: [
      /* @__PURE__ */ jsxDEV23(DialogHeader, { children: [
        /* @__PURE__ */ jsxDEV23(DialogTitle, { children: "Thank You!" }, void 0, !1, {
          fileName: "app/routes/contact.tsx",
          lineNumber: 209,
          columnNumber: 13
        }, this),
        /* @__PURE__ */ jsxDEV23(DialogDescription, { children: "We have received your message and will get back to you within 2 working days." }, void 0, !1, {
          fileName: "app/routes/contact.tsx",
          lineNumber: 210,
          columnNumber: 13
        }, this)
      ] }, void 0, !0, {
        fileName: "app/routes/contact.tsx",
        lineNumber: 208,
        columnNumber: 11
      }, this),
      /* @__PURE__ */ jsxDEV23("div", { className: "flex justify-end", children: /* @__PURE__ */ jsxDEV23(Button, { onClick: handleDialogClose, children: "Close" }, void 0, !1, {
        fileName: "app/routes/contact.tsx",
        lineNumber: 215,
        columnNumber: 13
      }, this) }, void 0, !1, {
        fileName: "app/routes/contact.tsx",
        lineNumber: 214,
        columnNumber: 11
      }, this)
    ] }, void 0, !0, {
      fileName: "app/routes/contact.tsx",
      lineNumber: 207,
      columnNumber: 9
    }, this) }, void 0, !1, {
      fileName: "app/routes/contact.tsx",
      lineNumber: 206,
      columnNumber: 7
    }, this)
  ] }, void 0, !0, {
    fileName: "app/routes/contact.tsx",
    lineNumber: 106,
    columnNumber: 5
  }, this);
}

// app/routes/privacy.tsx
var privacy_exports = {};
__export(privacy_exports, {
  default: () => Privacy,
  meta: () => meta6
});
import Markdown3 from "markdown-to-jsx";
import { jsxDEV as jsxDEV24 } from "react/jsx-dev-runtime";
var meta6 = () => [
  { title: "Privacy Policy - AI4MDE" },
  { name: "description", content: "Privacy policy and data handling practices" }
], content = `
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
  return /* @__PURE__ */ jsxDEV24(MaxWidthWrapper, { className: "px-4 py-10", children: [
    /* @__PURE__ */ jsxDEV24("h1", { className: "text-4xl font-bold mb-8", children: "Privacy Policy" }, void 0, !1, {
      fileName: "app/routes/privacy.tsx",
      lineNumber: 91,
      columnNumber: 7
    }, this),
    /* @__PURE__ */ jsxDEV24("div", { className: `prose prose-lg max-w-none dark:prose-invert
        [&_p]:leading-tight 
        [&_li]:leading-tight 
        [&>*+*]:mt-3
        [&_h2]:mb-3
        [&_h3]:mb-2
        [&_ul]:mt-2
        [&_ul]:mb-2`, children: /* @__PURE__ */ jsxDEV24(Markdown3, { children: content }, void 0, !1, {
      fileName: "app/routes/privacy.tsx",
      lineNumber: 100,
      columnNumber: 9
    }, this) }, void 0, !1, {
      fileName: "app/routes/privacy.tsx",
      lineNumber: 92,
      columnNumber: 7
    }, this)
  ] }, void 0, !0, {
    fileName: "app/routes/privacy.tsx",
    lineNumber: 90,
    columnNumber: 5
  }, this);
}

// app/routes/srsdocs.tsx
var srsdocs_exports = {};
__export(srsdocs_exports, {
  default: () => SrsDocs,
  loader: () => loader6,
  meta: () => meta7
});
import { json as json7 } from "@remix-run/node";
import { Link as Link8, useLoaderData as useLoaderData4 } from "@remix-run/react";
import { promises as fs5 } from "fs";
import path5 from "path";
import matter4 from "gray-matter";
import { redirect as redirect7 } from "@remix-run/node";
import { jsxDEV as jsxDEV25 } from "react/jsx-dev-runtime";
var meta7 = () => [
  { title: "SRS Documentation - AI4MDE" },
  { description: "Software Requirements Specification documentation for AI4MDE" }
];
async function getGroupDocuments(groupName) {
  let docsDir = path5.join(process.cwd(), "data", "liacs", "srsdocs");
  try {
    let files = await fs5.readdir(docsDir);
    return (await Promise.all(
      files.filter((file) => file.endsWith(".md")).map(async (file) => {
        try {
          let content4 = await fs5.readFile(path5.join(docsDir, file), "utf-8"), { data, content: docContent } = matter4(content4), id = data.id || file.replace(".md", ""), title = data.title || file.replace(".md", "").replace(/-/g, " "), description = data.description || docContent.slice(0, 150) + "...";
          return {
            id,
            title,
            description,
            date: data.date || (/* @__PURE__ */ new Date()).toISOString(),
            filename: file
          };
        } catch (error) {
          return console.error(`Error reading file ${file}:`, error), null;
        }
      })
    )).filter((doc) => doc !== null).sort((a, b) => !a.date || !b.date ? 0 : new Date(b.date).getTime() - new Date(a.date).getTime());
  } catch (error) {
    return console.error(`Error accessing directory ${docsDir}:`, error), [];
  }
}
async function loader6({ request }) {
  try {
    let user = await requireUser2(request);
    if (!user.group_name)
      throw new Response("User group not found", { status: 403 });
    let docs = await getGroupDocuments(user.group_name);
    return json7(
      { docs },
      {
        headers: {
          "Cache-Control": "no-store, no-cache, must-revalidate, proxy-revalidate",
          Pragma: "no-cache",
          Expires: "0"
        }
      }
    );
  } catch (error) {
    if (error instanceof Response && error.status === 401)
      return redirect7("/login?redirectTo=/srsdocs");
    throw error;
  }
}
function DocCard({ doc }) {
  return /* @__PURE__ */ jsxDEV25("div", { className: "rounded-lg border bg-card text-card-foreground shadow-sm hover:shadow-md transition-shadow", children: /* @__PURE__ */ jsxDEV25("div", { className: "p-6", children: [
    /* @__PURE__ */ jsxDEV25("h3", { className: "text-2xl font-semibold leading-none tracking-tight mb-2", children: doc.title }, void 0, !1, {
      fileName: "app/routes/srsdocs.tsx",
      lineNumber: 111,
      columnNumber: 9
    }, this),
    /* @__PURE__ */ jsxDEV25("p", { className: "text-sm text-muted-foreground mb-4", children: doc.description }, void 0, !1, {
      fileName: "app/routes/srsdocs.tsx",
      lineNumber: 114,
      columnNumber: 9
    }, this),
    doc.date && /* @__PURE__ */ jsxDEV25("p", { className: "text-xs text-muted-foreground mb-4", children: new Date(doc.date).toLocaleDateString() }, void 0, !1, {
      fileName: "app/routes/srsdocs.tsx",
      lineNumber: 118,
      columnNumber: 11
    }, this),
    /* @__PURE__ */ jsxDEV25(Button, { asChild: !0, children: /* @__PURE__ */ jsxDEV25(Link8, { to: `/srsdoc/${doc.id}`, children: "Read More" }, void 0, !1, {
      fileName: "app/routes/srsdocs.tsx",
      lineNumber: 123,
      columnNumber: 11
    }, this) }, void 0, !1, {
      fileName: "app/routes/srsdocs.tsx",
      lineNumber: 122,
      columnNumber: 9
    }, this)
  ] }, void 0, !0, {
    fileName: "app/routes/srsdocs.tsx",
    lineNumber: 110,
    columnNumber: 7
  }, this) }, void 0, !1, {
    fileName: "app/routes/srsdocs.tsx",
    lineNumber: 109,
    columnNumber: 5
  }, this);
}
function SrsDocs() {
  let { docs } = useLoaderData4();
  return /* @__PURE__ */ jsxDEV25(MaxWidthWrapper, { className: "py-8", children: [
    /* @__PURE__ */ jsxDEV25("h1", { className: "text-4xl font-bold mb-6", children: "SRS Documentation" }, void 0, !1, {
      fileName: "app/routes/srsdocs.tsx",
      lineNumber: 135,
      columnNumber: 7
    }, this),
    docs.length === 0 ? /* @__PURE__ */ jsxDEV25("div", { className: "text-center text-muted-foreground", children: /* @__PURE__ */ jsxDEV25("p", { children: "No SRS documents found." }, void 0, !1, {
      fileName: "app/routes/srsdocs.tsx",
      lineNumber: 138,
      columnNumber: 11
    }, this) }, void 0, !1, {
      fileName: "app/routes/srsdocs.tsx",
      lineNumber: 137,
      columnNumber: 9
    }, this) : /* @__PURE__ */ jsxDEV25("div", { className: "grid gap-4 md:grid-cols-2 lg:grid-cols-3", children: docs.map((doc) => /* @__PURE__ */ jsxDEV25(DocCard, { doc }, doc.id, !1, {
      fileName: "app/routes/srsdocs.tsx",
      lineNumber: 143,
      columnNumber: 13
    }, this)) }, void 0, !1, {
      fileName: "app/routes/srsdocs.tsx",
      lineNumber: 141,
      columnNumber: 9
    }, this)
  ] }, void 0, !0, {
    fileName: "app/routes/srsdocs.tsx",
    lineNumber: 134,
    columnNumber: 5
  }, this);
}

// app/routes/_index.tsx
var index_exports = {};
__export(index_exports, {
  default: () => Index
});
import { Link as Link9 } from "@remix-run/react";

// app/components/ui/carousel.tsx
import * as React12 from "react";
import useEmblaCarousel from "embla-carousel-react";
import { jsxDEV as jsxDEV26 } from "react/jsx-dev-runtime";
var CarouselContext = React12.createContext(null);
function useCarousel() {
  let context = React12.useContext(CarouselContext);
  if (!context)
    throw new Error("useCarousel must be used within a <Carousel />");
  return context;
}
var Carousel = React12.forwardRef(
  ({
    orientation = "horizontal",
    opts,
    setApi,
    plugins,
    className,
    children,
    ...props
  }, ref) => {
    let [carouselRef, api] = useEmblaCarousel(
      {
        ...opts,
        axis: orientation === "horizontal" ? "x" : "y"
      },
      plugins
    ), [canScrollPrev, setCanScrollPrev] = React12.useState(!1), [canScrollNext, setCanScrollNext] = React12.useState(!1), onSelect = React12.useCallback((api2) => {
      api2 && (setCanScrollPrev(api2.canScrollPrev()), setCanScrollNext(api2.canScrollNext()));
    }, []), scrollPrev = React12.useCallback(() => {
      api?.scrollPrev();
    }, [api]), scrollNext = React12.useCallback(() => {
      api?.scrollNext();
    }, [api]), onInit = React12.useCallback((api2) => {
    }, []);
    return React12.useEffect(() => {
      !api || !setApi || setApi(api);
    }, [api, setApi]), React12.useEffect(() => {
      if (api)
        return onInit(api), onSelect(api), api.on("reInit", onInit), api.on("select", onSelect), () => {
          api?.off("select", onSelect);
        };
    }, [api, onInit, onSelect]), /* @__PURE__ */ jsxDEV26(
      CarouselContext.Provider,
      {
        value: {
          carouselRef,
          api,
          opts,
          orientation: orientation || (opts?.axis === "y" ? "vertical" : "horizontal"),
          scrollPrev,
          scrollNext,
          canScrollPrev,
          canScrollNext
        },
        children: /* @__PURE__ */ jsxDEV26(
          "div",
          {
            ref,
            className: cn("relative", className),
            role: "region",
            "aria-roledescription": "carousel",
            ...props,
            children
          },
          void 0,
          !1,
          {
            fileName: "app/components/ui/carousel.tsx",
            lineNumber: 126,
            columnNumber: 9
          },
          this
        )
      },
      void 0,
      !1,
      {
        fileName: "app/components/ui/carousel.tsx",
        lineNumber: 113,
        columnNumber: 7
      },
      this
    );
  }
);
Carousel.displayName = "Carousel";
var CarouselContent = React12.forwardRef(({ className, ...props }, ref) => {
  let { carouselRef, orientation } = useCarousel();
  return /* @__PURE__ */ jsxDEV26("div", { ref: carouselRef, className: "overflow-hidden", children: /* @__PURE__ */ jsxDEV26(
    "div",
    {
      ref,
      className: cn(
        "flex",
        orientation === "horizontal" ? "-ml-4" : "-mt-4 flex-col",
        className
      ),
      ...props
    },
    void 0,
    !1,
    {
      fileName: "app/components/ui/carousel.tsx",
      lineNumber: 149,
      columnNumber: 7
    },
    this
  ) }, void 0, !1, {
    fileName: "app/components/ui/carousel.tsx",
    lineNumber: 148,
    columnNumber: 5
  }, this);
});
CarouselContent.displayName = "CarouselContent";
var CarouselItem = React12.forwardRef(({ className, ...props }, ref) => {
  let { orientation } = useCarousel();
  return /* @__PURE__ */ jsxDEV26(
    "div",
    {
      ref,
      role: "group",
      "aria-roledescription": "slide",
      className: cn(
        "min-w-0 shrink-0 grow-0 basis-full",
        orientation === "horizontal" ? "pl-4" : "pt-4",
        className
      ),
      ...props
    },
    void 0,
    !1,
    {
      fileName: "app/components/ui/carousel.tsx",
      lineNumber: 170,
      columnNumber: 5
    },
    this
  );
});
CarouselItem.displayName = "CarouselItem";

// app/routes/_index.tsx
import { TypeAnimation } from "react-type-animation";
import { jsxDEV as jsxDEV27 } from "react/jsx-dev-runtime";
function Index() {
  return /* @__PURE__ */ jsxDEV27("main", { children: [
    /* @__PURE__ */ jsxDEV27("section", { className: "body-font", children: /* @__PURE__ */ jsxDEV27("div", { className: "min-h-screen bg-background flex flex-col items-center justify-center", children: /* @__PURE__ */ jsxDEV27(MaxWidthWrapper, { children: [
      /* @__PURE__ */ jsxDEV27("div", { className: "w-full text-center mb-8", children: [
        /* @__PURE__ */ jsxDEV27("h1", { className: "text-5xl font-bold mb-4 text-foreground", children: "Welcome to" }, void 0, !1, {
          fileName: "app/routes/_index.tsx",
          lineNumber: 23,
          columnNumber: 15
        }, this),
        /* @__PURE__ */ jsxDEV27(
          TypeAnimation,
          {
            sequence: [
              "AI for Model-Driven Engineering!",
              5e3,
              "",
              500,
              "AI4MDE!",
              5e3,
              "",
              500
            ],
            wrapper: "h1",
            speed: 50,
            className: "text-5xl font-bold text-accent",
            repeat: 1 / 0
          },
          void 0,
          !1,
          {
            fileName: "app/routes/_index.tsx",
            lineNumber: 24,
            columnNumber: 15
          },
          this
        )
      ] }, void 0, !0, {
        fileName: "app/routes/_index.tsx",
        lineNumber: 22,
        columnNumber: 13
      }, this),
      /* @__PURE__ */ jsxDEV27(
        Carousel,
        {
          opts: {
            align: "start",
            loop: !0
          },
          className: "w-full max-w-5xl mx-auto mb-8",
          children: /* @__PURE__ */ jsxDEV27(CarouselContent, { children: [
            "/images/home/hero-01.jpg",
            "/images/home/hero-02.jpg",
            "/images/home/hero-03.jpg"
          ].map((image, index) => /* @__PURE__ */ jsxDEV27(CarouselItem, { children: /* @__PURE__ */ jsxDEV27("div", { className: "relative aspect-[16/9] w-full", children: /* @__PURE__ */ jsxDEV27(
            "img",
            {
              src: image,
              alt: `Hero image ${index + 1}`,
              className: "rounded-lg shadow-md object-cover w-full h-full"
            },
            void 0,
            !1,
            {
              fileName: "app/routes/_index.tsx",
              lineNumber: 54,
              columnNumber: 23
            },
            this
          ) }, void 0, !1, {
            fileName: "app/routes/_index.tsx",
            lineNumber: 53,
            columnNumber: 21
          }, this) }, index, !1, {
            fileName: "app/routes/_index.tsx",
            lineNumber: 52,
            columnNumber: 19
          }, this)) }, void 0, !1, {
            fileName: "app/routes/_index.tsx",
            lineNumber: 50,
            columnNumber: 15
          }, this)
        },
        void 0,
        !1,
        {
          fileName: "app/routes/_index.tsx",
          lineNumber: 43,
          columnNumber: 13
        },
        this
      ),
      /* @__PURE__ */ jsxDEV27("div", { className: "w-full md:w-2/3 text-center mx-auto mb-12", children: /* @__PURE__ */ jsxDEV27("p", { className: "text-xl leading-relaxed text-muted-foreground", children: "Artifacial Intelligence for Model-Driven Engineering in short AI4MDE is an initiative from Leiden University. Model-Driven Engineering (MDE) is a software development methodology that emphasizes the use of domain-specific models as primary artifacts throughout the development lifecycle. This project uses AI, more specific Large Language Models (LLMs) to conduct interviews with stakeholders and transforms these to requirements, models and documents required in the software development lifecycle. The aim of this project is to support Business Analysts and Architects speed up the software requirements engineering process." }, void 0, !1, {
        fileName: "app/routes/_index.tsx",
        lineNumber: 67,
        columnNumber: 15
      }, this) }, void 0, !1, {
        fileName: "app/routes/_index.tsx",
        lineNumber: 66,
        columnNumber: 13
      }, this),
      /* @__PURE__ */ jsxDEV27("div", { className: "text-center space-x-4", children: [
        /* @__PURE__ */ jsxDEV27(
          Button,
          {
            asChild: !0,
            className: "bg-accent hover:bg-accent/90 text-accent-foreground",
            children: /* @__PURE__ */ jsxDEV27(Link9, { to: "/guide", children: "Get Started" }, void 0, !1, {
              fileName: "app/routes/_index.tsx",
              lineNumber: 79,
              columnNumber: 17
            }, this)
          },
          void 0,
          !1,
          {
            fileName: "app/routes/_index.tsx",
            lineNumber: 75,
            columnNumber: 15
          },
          this
        ),
        /* @__PURE__ */ jsxDEV27(
          Button,
          {
            asChild: !0,
            variant: "outline",
            className: "border-accent hover:bg-accent hover:text-accent-foreground",
            children: /* @__PURE__ */ jsxDEV27(Link9, { to: "/contact", children: "Contact Us" }, void 0, !1, {
              fileName: "app/routes/_index.tsx",
              lineNumber: 86,
              columnNumber: 17
            }, this)
          },
          void 0,
          !1,
          {
            fileName: "app/routes/_index.tsx",
            lineNumber: 81,
            columnNumber: 15
          },
          this
        )
      ] }, void 0, !0, {
        fileName: "app/routes/_index.tsx",
        lineNumber: 74,
        columnNumber: 13
      }, this)
    ] }, void 0, !0, {
      fileName: "app/routes/_index.tsx",
      lineNumber: 20,
      columnNumber: 11
    }, this) }, void 0, !1, {
      fileName: "app/routes/_index.tsx",
      lineNumber: 19,
      columnNumber: 9
    }, this) }, void 0, !1, {
      fileName: "app/routes/_index.tsx",
      lineNumber: 18,
      columnNumber: 7
    }, this),
    /* @__PURE__ */ jsxDEV27("section", { className: "bg-card", children: /* @__PURE__ */ jsxDEV27("div", { className: "container px-5 py-24 mx-auto", children: [
      /* @__PURE__ */ jsxDEV27("h2", { className: "text-4xl pb-8 mb-4 font-bold text-center text-card-foreground", children: "Features" }, void 0, !1, {
        fileName: "app/routes/_index.tsx",
        lineNumber: 95,
        columnNumber: 11
      }, this),
      /* @__PURE__ */ jsxDEV27("div", { className: "flex flex-wrap -m-4", children: [
        /* @__PURE__ */ jsxDEV27("div", { className: "p-4 lg:w-1/3", children: /* @__PURE__ */ jsxDEV27(Card, { className: "h-full bg-background text-foreground", children: [
          /* @__PURE__ */ jsxDEV27(CardHeader, { children: /* @__PURE__ */ jsxDEV27(CardTitle, { className: "tracking-widest text-xs font-medium mb-1 text-muted-foreground", children: "CHATBOT DRIVEN BY LLM" }, void 0, !1, {
            fileName: "app/routes/_index.tsx",
            lineNumber: 103,
            columnNumber: 19
          }, this) }, void 0, !1, {
            fileName: "app/routes/_index.tsx",
            lineNumber: 102,
            columnNumber: 17
          }, this),
          /* @__PURE__ */ jsxDEV27(CardContent, { children: [
            /* @__PURE__ */ jsxDEV27("h1", { className: "title-font sm:text-2xl text-xl font-medium mb-3", children: "Intelligent Interaction" }, void 0, !1, {
              fileName: "app/routes/_index.tsx",
              lineNumber: 108,
              columnNumber: 19
            }, this),
            /* @__PURE__ */ jsxDEV27("p", { className: "leading-relaxed mb-3 text-muted-foreground", children: "Discover our modularly designed AI-driven chatbot for engaging with end users. The chatbot makes use of AI agents, each of which is responsible for a specific task or function. This makes it relatively simple to adjust existing functionalities or add new ones. functions relatively simple. Natural language conversations guide the user through a predetermined procedure. Using natural language dialogue, it guides users through a predetermined procedure." }, void 0, !1, {
              fileName: "app/routes/_index.tsx",
              lineNumber: 111,
              columnNumber: 19
            }, this)
          ] }, void 0, !0, {
            fileName: "app/routes/_index.tsx",
            lineNumber: 107,
            columnNumber: 17
          }, this),
          /* @__PURE__ */ jsxDEV27(CardFooter, { className: "flex justify-center", children: /* @__PURE__ */ jsxDEV27(
            Link9,
            {
              to: "/guide",
              className: "inline-flex items-center text-accent hover:text-accent/90",
              children: [
                "Learn More",
                /* @__PURE__ */ jsxDEV27(
                  "svg",
                  {
                    className: "w-4 h-4 ml-2",
                    viewBox: "0 0 24 24",
                    stroke: "currentColor",
                    strokeWidth: "2",
                    fill: "none",
                    strokeLinecap: "round",
                    strokeLinejoin: "round",
                    children: [
                      /* @__PURE__ */ jsxDEV27("path", { d: "M5 12h14" }, void 0, !1, {
                        fileName: "app/routes/_index.tsx",
                        lineNumber: 130,
                        columnNumber: 23
                      }, this),
                      /* @__PURE__ */ jsxDEV27("path", { d: "M12 5l7 7-7 7" }, void 0, !1, {
                        fileName: "app/routes/_index.tsx",
                        lineNumber: 131,
                        columnNumber: 23
                      }, this)
                    ]
                  },
                  void 0,
                  !0,
                  {
                    fileName: "app/routes/_index.tsx",
                    lineNumber: 121,
                    columnNumber: 21
                  },
                  this
                )
              ]
            },
            void 0,
            !0,
            {
              fileName: "app/routes/_index.tsx",
              lineNumber: 116,
              columnNumber: 19
            },
            this
          ) }, void 0, !1, {
            fileName: "app/routes/_index.tsx",
            lineNumber: 115,
            columnNumber: 17
          }, this)
        ] }, void 0, !0, {
          fileName: "app/routes/_index.tsx",
          lineNumber: 101,
          columnNumber: 15
        }, this) }, void 0, !1, {
          fileName: "app/routes/_index.tsx",
          lineNumber: 100,
          columnNumber: 13
        }, this),
        /* @__PURE__ */ jsxDEV27("div", { className: "p-4 lg:w-1/3", children: /* @__PURE__ */ jsxDEV27(Card, { className: "h-full bg-background text-foreground", children: [
          /* @__PURE__ */ jsxDEV27(CardHeader, { children: /* @__PURE__ */ jsxDEV27(CardTitle, { className: "tracking-widest text-xs font-medium mb-1 text-muted-foreground", children: "SOFTWARE REQUIREMENTS SPECIFICATION" }, void 0, !1, {
            fileName: "app/routes/_index.tsx",
            lineNumber: 141,
            columnNumber: 19
          }, this) }, void 0, !1, {
            fileName: "app/routes/_index.tsx",
            lineNumber: 140,
            columnNumber: 17
          }, this),
          /* @__PURE__ */ jsxDEV27(CardContent, { children: [
            /* @__PURE__ */ jsxDEV27("h1", { className: "title-font sm:text-2xl text-xl font-medium mb-3", children: "Automated SRS Generation" }, void 0, !1, {
              fileName: "app/routes/_index.tsx",
              lineNumber: 146,
              columnNumber: 19
            }, this),
            /* @__PURE__ */ jsxDEV27("p", { className: "leading-relaxed mb-3 text-muted-foreground", children: "Transform natural language conversations into comprehensive Software Requirements Specification documents. Our AI-powered system gathers and analyses user requirements through an interview and then automatically generates UML models. In conclusion, the system generates a software requirements specification (SRS) document that is compliant with the standards established by the IEEE." }, void 0, !1, {
              fileName: "app/routes/_index.tsx",
              lineNumber: 149,
              columnNumber: 19
            }, this)
          ] }, void 0, !0, {
            fileName: "app/routes/_index.tsx",
            lineNumber: 145,
            columnNumber: 17
          }, this),
          /* @__PURE__ */ jsxDEV27(CardFooter, { className: "flex justify-center", children: /* @__PURE__ */ jsxDEV27(
            Link9,
            {
              to: "/guide",
              className: "inline-flex items-center text-accent hover:text-accent/90",
              children: [
                "Learn More",
                /* @__PURE__ */ jsxDEV27(
                  "svg",
                  {
                    className: "w-4 h-4 ml-2",
                    viewBox: "0 0 24 24",
                    stroke: "currentColor",
                    strokeWidth: "2",
                    fill: "none",
                    strokeLinecap: "round",
                    strokeLinejoin: "round",
                    children: [
                      /* @__PURE__ */ jsxDEV27("path", { d: "M5 12h14" }, void 0, !1, {
                        fileName: "app/routes/_index.tsx",
                        lineNumber: 168,
                        columnNumber: 23
                      }, this),
                      /* @__PURE__ */ jsxDEV27("path", { d: "M12 5l7 7-7 7" }, void 0, !1, {
                        fileName: "app/routes/_index.tsx",
                        lineNumber: 169,
                        columnNumber: 23
                      }, this)
                    ]
                  },
                  void 0,
                  !0,
                  {
                    fileName: "app/routes/_index.tsx",
                    lineNumber: 159,
                    columnNumber: 21
                  },
                  this
                )
              ]
            },
            void 0,
            !0,
            {
              fileName: "app/routes/_index.tsx",
              lineNumber: 154,
              columnNumber: 19
            },
            this
          ) }, void 0, !1, {
            fileName: "app/routes/_index.tsx",
            lineNumber: 153,
            columnNumber: 17
          }, this)
        ] }, void 0, !0, {
          fileName: "app/routes/_index.tsx",
          lineNumber: 139,
          columnNumber: 15
        }, this) }, void 0, !1, {
          fileName: "app/routes/_index.tsx",
          lineNumber: 138,
          columnNumber: 13
        }, this),
        /* @__PURE__ */ jsxDEV27("div", { className: "p-4 lg:w-1/3", children: /* @__PURE__ */ jsxDEV27(Card, { className: "h-full bg-background text-foreground", children: [
          /* @__PURE__ */ jsxDEV27(CardHeader, { children: /* @__PURE__ */ jsxDEV27(CardTitle, { className: "tracking-widest text-xs font-medium mb-1 text-muted-foreground", children: "UML DIAGRAMS GENERATION" }, void 0, !1, {
            fileName: "app/routes/_index.tsx",
            lineNumber: 179,
            columnNumber: 19
          }, this) }, void 0, !1, {
            fileName: "app/routes/_index.tsx",
            lineNumber: 178,
            columnNumber: 17
          }, this),
          /* @__PURE__ */ jsxDEV27(CardContent, { children: [
            /* @__PURE__ */ jsxDEV27("h1", { className: "title-font sm:text-2xl text-xl font-medium mb-3", children: "Automated Design Visualization" }, void 0, !1, {
              fileName: "app/routes/_index.tsx",
              lineNumber: 184,
              columnNumber: 19
            }, this),
            /* @__PURE__ */ jsxDEV27("p", { className: "leading-relaxed mb-3 text-muted-foreground", children: "Convert natural language descriptions into precise UML diagrams automatically. Our AI system generates various diagram types, including class, sequence, and use case diagrams, providing clear visual representations of your software architecture and system behaviour while maintaining UML standards and best practices. Finaly the UML diagrams can be modified in the Studio app." }, void 0, !1, {
              fileName: "app/routes/_index.tsx",
              lineNumber: 187,
              columnNumber: 19
            }, this)
          ] }, void 0, !0, {
            fileName: "app/routes/_index.tsx",
            lineNumber: 183,
            columnNumber: 17
          }, this),
          /* @__PURE__ */ jsxDEV27(CardFooter, { className: "flex justify-center", children: /* @__PURE__ */ jsxDEV27(
            Link9,
            {
              to: "/guide",
              className: "inline-flex items-center text-accent hover:text-accent/90",
              children: [
                "Learn More",
                /* @__PURE__ */ jsxDEV27(
                  "svg",
                  {
                    className: "w-4 h-4 ml-2",
                    viewBox: "0 0 24 24",
                    stroke: "currentColor",
                    strokeWidth: "2",
                    fill: "none",
                    strokeLinecap: "round",
                    strokeLinejoin: "round",
                    children: [
                      /* @__PURE__ */ jsxDEV27("path", { d: "M5 12h14" }, void 0, !1, {
                        fileName: "app/routes/_index.tsx",
                        lineNumber: 206,
                        columnNumber: 23
                      }, this),
                      /* @__PURE__ */ jsxDEV27("path", { d: "M12 5l7 7-7 7" }, void 0, !1, {
                        fileName: "app/routes/_index.tsx",
                        lineNumber: 207,
                        columnNumber: 23
                      }, this)
                    ]
                  },
                  void 0,
                  !0,
                  {
                    fileName: "app/routes/_index.tsx",
                    lineNumber: 197,
                    columnNumber: 21
                  },
                  this
                )
              ]
            },
            void 0,
            !0,
            {
              fileName: "app/routes/_index.tsx",
              lineNumber: 192,
              columnNumber: 19
            },
            this
          ) }, void 0, !1, {
            fileName: "app/routes/_index.tsx",
            lineNumber: 191,
            columnNumber: 17
          }, this)
        ] }, void 0, !0, {
          fileName: "app/routes/_index.tsx",
          lineNumber: 177,
          columnNumber: 15
        }, this) }, void 0, !1, {
          fileName: "app/routes/_index.tsx",
          lineNumber: 176,
          columnNumber: 13
        }, this)
      ] }, void 0, !0, {
        fileName: "app/routes/_index.tsx",
        lineNumber: 98,
        columnNumber: 11
      }, this)
    ] }, void 0, !0, {
      fileName: "app/routes/_index.tsx",
      lineNumber: 94,
      columnNumber: 9
    }, this) }, void 0, !1, {
      fileName: "app/routes/_index.tsx",
      lineNumber: 93,
      columnNumber: 7
    }, this)
  ] }, void 0, !0, {
    fileName: "app/routes/_index.tsx",
    lineNumber: 17,
    columnNumber: 5
  }, this);
}

// app/routes/logout.tsx
var logout_exports = {};
__export(logout_exports, {
  action: () => action2,
  default: () => Logout
});
async function action2({ request }) {
  return await destroySession(request);
}
function Logout() {
  return null;
}

// app/routes/guide.tsx
var guide_exports = {};
__export(guide_exports, {
  default: () => Guide,
  meta: () => meta8
});
import Markdown4 from "markdown-to-jsx";
import { jsxDEV as jsxDEV28 } from "react/jsx-dev-runtime";
var meta8 = () => [
  { title: "Guide - AI4MDE" },
  { name: "description", content: "Learn how to use our platform effectively" }
], content2 = `
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
  return /* @__PURE__ */ jsxDEV28(MaxWidthWrapper, { className: "px-4 py-10", children: [
    /* @__PURE__ */ jsxDEV28("h1", { className: "text-4xl font-bold mb-8", children: "Guide" }, void 0, !1, {
      fileName: "app/routes/guide.tsx",
      lineNumber: 57,
      columnNumber: 7
    }, this),
    /* @__PURE__ */ jsxDEV28("div", { className: `prose prose-lg max-w-none dark:prose-invert
        [&_p]:leading-tight 
        [&_li]:leading-tight 
        [&>*+*]:mt-3
        [&_h2]:mb-3
        [&_h3]:mb-2
        [&_ul]:mt-2
        [&_ul]:mb-2`, children: /* @__PURE__ */ jsxDEV28(Markdown4, { children: content2 }, void 0, !1, {
      fileName: "app/routes/guide.tsx",
      lineNumber: 66,
      columnNumber: 9
    }, this) }, void 0, !1, {
      fileName: "app/routes/guide.tsx",
      lineNumber: 58,
      columnNumber: 7
    }, this)
  ] }, void 0, !0, {
    fileName: "app/routes/guide.tsx",
    lineNumber: 56,
    columnNumber: 5
  }, this);
}

// app/routes/login.tsx
var login_exports = {};
__export(login_exports, {
  action: () => action3,
  default: () => Login,
  loader: () => loader7
});
import * as React13 from "react";
import { json as json8, redirect as redirect8 } from "@remix-run/node";
import { Form as Form3, useActionData as useActionData2, useSearchParams } from "@remix-run/react";

// app/services/auth.server.ts
import { Authenticator } from "remix-auth";
import { FormStrategy } from "remix-auth-form";
var authenticator = new Authenticator(sessionStorage, {
  sessionKey: "user",
  // key for storing the user in the session
  sessionErrorKey: "error"
  // key for storing error messages
});
authenticator.use(
  new FormStrategy(async ({ form }) => {
    let username = form.get("username"), password = form.get("password");
    if (!username || !password)
      throw new Error("Username and password are required");
    try {
      console.log("Attempting login for user:", username);
      let formData = new URLSearchParams();
      formData.append("username", username), formData.append("password", password);
      let response = await fetch("http://localhost:8000/api/v1/auth/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
          Accept: "application/json"
        },
        body: formData
      });
      if (!response.ok) {
        let errorData = await response.json().catch(() => null);
        throw console.error("Login failed:", {
          status: response.status,
          statusText: response.statusText,
          error: errorData
        }), errorData?.detail ? new Error(errorData.detail) : new Error(`Login failed: ${response.statusText}`);
      }
      let data = await response.json();
      if (console.log("Login response:", data), !data.access_token)
        throw console.error("Invalid response data:", data), new Error("Invalid response from server");
      let user = {
        id: data.id || username,
        username: data.username || username,
        group_name: data.group_name,
        access_token: data.access_token,
        token_type: (data.token_type || "bearer").charAt(0).toUpperCase() + (data.token_type || "bearer").slice(1)
      };
      return console.log("Created user object:", user), user;
    } catch (error) {
      throw console.error("Authentication error:", {
        error,
        message: error instanceof Error ? error.message : "Unknown error",
        stack: error instanceof Error ? error.stack : void 0
      }), error;
    }
  }),
  "form"
);

// app/routes/login.tsx
import { Eye, EyeOff } from "lucide-react";
import { jsxDEV as jsxDEV29 } from "react/jsx-dev-runtime";
async function loader7({ request }) {
  return await authenticator.isAuthenticated(request) ? redirect8("/") : null;
}
async function action3({ request }) {
  let redirectTo = (await request.clone().formData()).get("redirectTo")?.toString() || "/";
  try {
    return await authenticator.authenticate("form", request, {
      successRedirect: redirectTo,
      failureRedirect: void 0,
      throwOnError: !0
    });
  } catch (error) {
    return error instanceof Response && error.status === 302 ? error : (console.error("Login action error:", {
      error,
      message: error instanceof Error ? error.message : "Unknown error",
      stack: error instanceof Error ? error.stack : void 0
    }), json8({
      error: error instanceof Error ? error.message : "Authentication failed. Please check your credentials and try again."
    }, {
      status: 400
    }));
  }
}
function Login() {
  let [searchParams] = useSearchParams(), redirectTo = searchParams.get("redirectTo") || "/", actionData = useActionData2(), [showPassword, setShowPassword] = React13.useState(!1);
  return /* @__PURE__ */ jsxDEV29("main", { className: "flex-1 min-h-[calc(100vh-12rem)] grid place-items-center bg-muted/50 -mt-[1px]", children: /* @__PURE__ */ jsxDEV29(Card, { className: "w-full max-w-md mx-4 shadow-lg", children: [
    /* @__PURE__ */ jsxDEV29(CardHeader, { className: "space-y-4", children: [
      /* @__PURE__ */ jsxDEV29("div", { className: "flex justify-center", children: /* @__PURE__ */ jsxDEV29(
        "img",
        {
          src: "/images/logos/logo.svg",
          alt: "AI4MDE Logo",
          className: "h-12 w-12"
        },
        void 0,
        !1,
        {
          fileName: "app/routes/login.tsx",
          lineNumber: 63,
          columnNumber: 13
        },
        this
      ) }, void 0, !1, {
        fileName: "app/routes/login.tsx",
        lineNumber: 62,
        columnNumber: 11
      }, this),
      /* @__PURE__ */ jsxDEV29("div", { className: "text-center", children: [
        /* @__PURE__ */ jsxDEV29(CardTitle, { children: "Welcome to AI4MDE" }, void 0, !1, {
          fileName: "app/routes/login.tsx",
          lineNumber: 70,
          columnNumber: 13
        }, this),
        /* @__PURE__ */ jsxDEV29(CardDescription, { children: "Sign in to your account" }, void 0, !1, {
          fileName: "app/routes/login.tsx",
          lineNumber: 71,
          columnNumber: 13
        }, this)
      ] }, void 0, !0, {
        fileName: "app/routes/login.tsx",
        lineNumber: 69,
        columnNumber: 11
      }, this)
    ] }, void 0, !0, {
      fileName: "app/routes/login.tsx",
      lineNumber: 61,
      columnNumber: 9
    }, this),
    /* @__PURE__ */ jsxDEV29(CardContent, { children: /* @__PURE__ */ jsxDEV29(Form3, { method: "post", className: "space-y-4", children: [
      /* @__PURE__ */ jsxDEV29("input", { type: "hidden", name: "redirectTo", value: redirectTo }, void 0, !1, {
        fileName: "app/routes/login.tsx",
        lineNumber: 76,
        columnNumber: 13
      }, this),
      /* @__PURE__ */ jsxDEV29("div", { className: "space-y-2", children: [
        /* @__PURE__ */ jsxDEV29(Label2, { htmlFor: "username", children: "Username" }, void 0, !1, {
          fileName: "app/routes/login.tsx",
          lineNumber: 78,
          columnNumber: 15
        }, this),
        /* @__PURE__ */ jsxDEV29(
          Input,
          {
            id: "username",
            name: "username",
            type: "text",
            required: !0,
            placeholder: "Enter your username"
          },
          void 0,
          !1,
          {
            fileName: "app/routes/login.tsx",
            lineNumber: 79,
            columnNumber: 15
          },
          this
        )
      ] }, void 0, !0, {
        fileName: "app/routes/login.tsx",
        lineNumber: 77,
        columnNumber: 13
      }, this),
      /* @__PURE__ */ jsxDEV29("div", { className: "space-y-2", children: [
        /* @__PURE__ */ jsxDEV29(Label2, { htmlFor: "password", children: "Password" }, void 0, !1, {
          fileName: "app/routes/login.tsx",
          lineNumber: 88,
          columnNumber: 15
        }, this),
        /* @__PURE__ */ jsxDEV29("div", { className: "relative", children: [
          /* @__PURE__ */ jsxDEV29(
            Input,
            {
              id: "password",
              name: "password",
              type: showPassword ? "text" : "password",
              required: !0,
              placeholder: "Enter your password"
            },
            void 0,
            !1,
            {
              fileName: "app/routes/login.tsx",
              lineNumber: 90,
              columnNumber: 17
            },
            this
          ),
          /* @__PURE__ */ jsxDEV29(
            Button,
            {
              type: "button",
              variant: "ghost",
              size: "icon",
              className: "absolute right-0 top-0 h-full px-2 py-2 hover:bg-transparent",
              onClick: () => setShowPassword(!showPassword),
              children: [
                showPassword ? /* @__PURE__ */ jsxDEV29(EyeOff, { className: "h-10 w-10 text-muted-foreground" }, void 0, !1, {
                  fileName: "app/routes/login.tsx",
                  lineNumber: 105,
                  columnNumber: 21
                }, this) : /* @__PURE__ */ jsxDEV29(Eye, { className: "h-10 w-10 text-muted-foreground" }, void 0, !1, {
                  fileName: "app/routes/login.tsx",
                  lineNumber: 107,
                  columnNumber: 21
                }, this),
                /* @__PURE__ */ jsxDEV29("span", { className: "sr-only", children: showPassword ? "Hide password" : "Show password" }, void 0, !1, {
                  fileName: "app/routes/login.tsx",
                  lineNumber: 109,
                  columnNumber: 19
                }, this)
              ]
            },
            void 0,
            !0,
            {
              fileName: "app/routes/login.tsx",
              lineNumber: 97,
              columnNumber: 17
            },
            this
          )
        ] }, void 0, !0, {
          fileName: "app/routes/login.tsx",
          lineNumber: 89,
          columnNumber: 15
        }, this)
      ] }, void 0, !0, {
        fileName: "app/routes/login.tsx",
        lineNumber: 87,
        columnNumber: 13
      }, this),
      actionData?.error && /* @__PURE__ */ jsxDEV29("div", { className: "text-sm text-red-500", children: actionData.error }, void 0, !1, {
        fileName: "app/routes/login.tsx",
        lineNumber: 116,
        columnNumber: 15
      }, this),
      /* @__PURE__ */ jsxDEV29(Button, { type: "submit", className: "w-full", children: "Sign in" }, void 0, !1, {
        fileName: "app/routes/login.tsx",
        lineNumber: 118,
        columnNumber: 13
      }, this)
    ] }, void 0, !0, {
      fileName: "app/routes/login.tsx",
      lineNumber: 75,
      columnNumber: 11
    }, this) }, void 0, !1, {
      fileName: "app/routes/login.tsx",
      lineNumber: 74,
      columnNumber: 9
    }, this)
  ] }, void 0, !0, {
    fileName: "app/routes/login.tsx",
    lineNumber: 60,
    columnNumber: 7
  }, this) }, void 0, !1, {
    fileName: "app/routes/login.tsx",
    lineNumber: 59,
    columnNumber: 5
  }, this);
}

// app/routes/terms.tsx
var terms_exports = {};
__export(terms_exports, {
  default: () => Terms,
  meta: () => meta9
});
import Markdown5 from "markdown-to-jsx";
import { jsxDEV as jsxDEV30 } from "react/jsx-dev-runtime";
var meta9 = () => [
  { title: "Terms of Service - AI4MDE" },
  { name: "description", content: "Our terms of service and usage conditions" }
], content3 = `
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
  return /* @__PURE__ */ jsxDEV30(MaxWidthWrapper, { className: "px-4 py-10", children: [
    /* @__PURE__ */ jsxDEV30("h1", { className: "text-4xl font-bold mb-8", children: "Terms of Service" }, void 0, !1, {
      fileName: "app/routes/terms.tsx",
      lineNumber: 127,
      columnNumber: 7
    }, this),
    /* @__PURE__ */ jsxDEV30("div", { className: `prose prose-lg max-w-none dark:prose-invert
        [&_p]:leading-tight 
        [&_li]:leading-tight 
        [&>*+*]:mt-3
        [&_h2]:mb-3
        [&_h3]:mb-2
        [&_ul]:mt-2
        [&_ul]:mb-2`, children: /* @__PURE__ */ jsxDEV30(Markdown5, { children: content3 }, void 0, !1, {
      fileName: "app/routes/terms.tsx",
      lineNumber: 136,
      columnNumber: 9
    }, this) }, void 0, !1, {
      fileName: "app/routes/terms.tsx",
      lineNumber: 128,
      columnNumber: 7
    }, this)
  ] }, void 0, !0, {
    fileName: "app/routes/terms.tsx",
    lineNumber: 126,
    columnNumber: 5
  }, this);
}

// app/routes/chat.tsx
var chat_exports = {};
__export(chat_exports, {
  action: () => action4,
  default: () => Chat,
  loader: () => loader8
});
import { useState as useState12, useRef as useRef3, useEffect as useEffect8 } from "react";
import { json as json9, redirect as redirect9 } from "@remix-run/node";

// app/hooks/use-chat.ts
import { useState as useState7, useCallback as useCallback2, useEffect as useEffect5 } from "react";

// app/services/chat.ts
var API_URL = "http://localhost:8000/api/v1";
function getAuthHeader(user) {
  return `${user.token_type.charAt(0).toUpperCase() + user.token_type.slice(1).toLowerCase()} ${user.access_token}`;
}
async function handleResponse(response) {
  if (!response.ok) {
    let error = await response.json().catch(() => null);
    return response.status === 401 || error?.detail === "Could not validate credentials" ? (window.location.href = `/login?redirectTo=${window.location.pathname}`, { error: "Session expired. Please log in again." }) : {
      error: error?.detail || `API error: ${response.status} ${response.statusText}`
    };
  }
  try {
    return { data: await response.json() };
  } catch {
    return {
      error: "Failed to parse response"
    };
  }
}
var chatApi = {
  async getSessions(user) {
    try {
      console.log("Auth header:", getAuthHeader(user));
      let response = await fetch(`${API_URL}/chat/sessions`, {
        headers: {
          Authorization: getAuthHeader(user),
          Accept: "application/json",
          "Content-Type": "application/json"
        },
        credentials: "include",
        mode: "cors"
      });
      return handleResponse(response);
    } catch (error) {
      return {
        error: error instanceof Error ? error.message : "Failed to fetch sessions"
      };
    }
  },
  async getSession(user, sessionId) {
    try {
      let response = await fetch(`${API_URL}/chat/sessions/${sessionId}`, {
        headers: {
          Authorization: getAuthHeader(user),
          Accept: "application/json",
          "Content-Type": "application/json"
        },
        credentials: "include",
        mode: "cors"
      });
      return handleResponse(response);
    } catch (error) {
      return {
        error: error instanceof Error ? error.message : "Failed to fetch session"
      };
    }
  },
  async createChatSession(title, user) {
    try {
      console.log("Creating chat session with title:", title), console.log("Auth header:", getAuthHeader(user));
      let response = await fetch(`${API_URL}/chat/sessions`, {
        method: "POST",
        headers: {
          Authorization: getAuthHeader(user),
          "Content-Type": "application/json",
          Accept: "application/json"
        },
        credentials: "include",
        mode: "cors",
        body: JSON.stringify({ title })
      });
      console.log("Response status:", response.status);
      let responseText = await response.text();
      if (console.log("Response text:", responseText), !response.ok)
        return {
          error: `Failed to create chat session: ${response.status} ${response.statusText}
${responseText}`
        };
      try {
        return { data: JSON.parse(responseText) };
      } catch (error) {
        return console.error("Failed to parse response:", error), {
          error: "Failed to parse server response"
        };
      }
    } catch (error) {
      return console.error("Failed to create chat session:", error), {
        error: error instanceof Error ? error.message : "Failed to create session"
      };
    }
  },
  async deleteSession(user, sessionId) {
    try {
      let response = await fetch(`${API_URL}/chat/sessions/${sessionId}`, {
        method: "DELETE",
        headers: {
          Authorization: getAuthHeader(user),
          Accept: "application/json",
          "Content-Type": "application/json"
        },
        credentials: "include",
        mode: "cors"
      });
      return handleResponse(response);
    } catch (error) {
      return {
        error: error instanceof Error ? error.message : "Failed to delete session"
      };
    }
  },
  async sendMessage(user, sessionId, content4) {
    try {
      let message_uuid = crypto.randomUUID(), response = await fetch(`${API_URL}/chat/sessions/${sessionId}/messages`, {
        method: "POST",
        headers: {
          Authorization: getAuthHeader(user),
          "Content-Type": "application/json",
          Accept: "application/json"
        },
        credentials: "include",
        mode: "cors",
        body: JSON.stringify({ content: content4, message_uuid })
      }), apiResponse = await handleResponse(response);
      return apiResponse.error ? { error: apiResponse.error } : apiResponse.data ? { data: {
        id: apiResponse.data.message_uuid,
        role: "ASSISTANT",
        content: apiResponse.data.message,
        created_at: (/* @__PURE__ */ new Date()).toISOString(),
        message_uuid: apiResponse.data.message_uuid,
        progress: apiResponse.data.progress
      } } : { error: "No data received from server" };
    } catch (error) {
      return {
        error: error instanceof Error ? error.message : "Failed to send message"
      };
    }
  },
  async getMessages(user, sessionId) {
    try {
      let response = await fetch(`${API_URL}/chat/sessions/${sessionId}/messages`, {
        headers: {
          Authorization: getAuthHeader(user),
          Accept: "application/json",
          "Content-Type": "application/json"
        },
        credentials: "include",
        mode: "cors"
      }), apiResponse = await handleResponse(response);
      return apiResponse.error ? { error: apiResponse.error } : apiResponse.data ? { data: apiResponse.data } : { error: "No messages received from server" };
    } catch (error) {
      return {
        error: error instanceof Error ? error.message : "Failed to fetch messages"
      };
    }
  }
};

// app/hooks/use-chat.ts
function useChat() {
  let user = useUser(), [state, setState] = useState7({
    messages: [],
    isLoading: !1,
    error: null,
    input: "",
    sessions: [],
    currentSession: null,
    progress: void 0,
    isAiThinking: !1
  }), setPartialState = (newState) => {
    setState((prev) => ({ ...prev, ...newState }));
  };
  useEffect5(() => {
    user && loadSessions();
  }, [user]);
  let loadSessions = async () => {
    if (user)
      try {
        let response = await chatApi.getSessions(user);
        if (response.error)
          throw new Error(response.error);
        response.data && setPartialState({ sessions: response.data });
      } catch (error) {
        setPartialState({
          error: error instanceof Error ? error.message : "Failed to load sessions"
        });
      }
  }, selectChat = async (sessionId) => {
    if (!user) {
      setPartialState({ error: "Not authenticated" });
      return;
    }
    try {
      let sessionResponse = await chatApi.getSession(user, sessionId);
      if (sessionResponse.error)
        throw new Error(sessionResponse.error);
      if (!sessionResponse.data)
        throw new Error("No session data received");
      let messagesResponse = await chatApi.getMessages(user, sessionId);
      if (messagesResponse.error)
        throw new Error(messagesResponse.error);
      let messages = messagesResponse.data || [], progress = messages[messages.length - 1]?.progress;
      setPartialState({
        currentSession: sessionResponse.data,
        messages,
        progress,
        error: null
      });
    } catch (error) {
      setPartialState({
        error: error instanceof Error ? error.message : "Failed to load chat session"
      });
    }
  }, sendMessage = async (content4) => {
    if (!user || !state.currentSession) {
      setPartialState({ error: "No active chat session" });
      return;
    }
    try {
      let userMessage = {
        id: crypto.randomUUID(),
        role: "USER",
        content: content4,
        created_at: (/* @__PURE__ */ new Date()).toISOString(),
        progress: state.progress
      };
      setPartialState({
        messages: [...state.messages, userMessage]
      }), setPartialState({
        isLoading: !0,
        error: null,
        isAiThinking: !0
      });
      let response = await chatApi.sendMessage(
        user,
        state.currentSession.id,
        content4
      );
      if (response.error) {
        if (response.error === "Session expired. Please log in again.") {
          setPartialState({
            messages: [],
            currentSession: null,
            sessions: [],
            error: response.error
          });
          return;
        }
        throw new Error(response.error);
      }
      response.data && setPartialState({
        messages: [...state.messages, userMessage, response.data],
        progress: response.data.progress
      });
    } catch (error) {
      setPartialState({
        error: error instanceof Error ? error.message : "Failed to send message"
      });
    } finally {
      setPartialState({ isLoading: !1, isAiThinking: !1 });
    }
  }, startNewChat = async (title) => {
    if (!user) {
      setPartialState({ error: "Not authenticated" });
      return;
    }
    try {
      let response = await chatApi.createChatSession(title, user);
      if (response.error)
        throw new Error(response.error);
      response.data && (setPartialState({
        currentSession: response.data,
        messages: [],
        progress: void 0
      }), await loadSessions());
    } catch (error) {
      setPartialState({
        error: error instanceof Error ? error.message : "Failed to create chat"
      });
    }
  }, deleteChat = useCallback2(async () => {
    if (!user || !state.currentSession) {
      setPartialState({ error: "No active chat session" });
      return;
    }
    try {
      let response = await chatApi.deleteSession(user, state.currentSession.id);
      if (response.error)
        throw new Error(response.error);
      setPartialState({
        currentSession: null,
        messages: [],
        progress: void 0
      }), await loadSessions();
    } catch (error) {
      setPartialState({
        error: error instanceof Error ? error.message : "Failed to delete chat"
      });
    }
  }, [user, state.currentSession]);
  return {
    ...state,
    handleInputChange: (e) => {
      setPartialState({ input: e.target.value });
    },
    handleSubmit: (e) => {
      e.preventDefault(), state.input.trim() && (sendMessage(state.input), setPartialState({ input: "" }));
    },
    startNewChat,
    deleteChat,
    selectChat,
    stop: () => {
      setPartialState({ isAiThinking: !1 });
    },
    reload: () => {
    }
  };
}

// app/components/chat/chat-header.tsx
import { useState as useState9 } from "react";
import { Loader2, Menu, Plus, Trash2 } from "lucide-react";

// app/components/chat/delete-chat-dialog.tsx
import * as React14 from "react";
import { jsxDEV as jsxDEV31 } from "react/jsx-dev-runtime";
function DeleteChatDialog({
  isOpen,
  onClose,
  onConfirm,
  currentSession
}) {
  let [isDeleting, setIsDeleting] = React14.useState(!1);
  return /* @__PURE__ */ jsxDEV31(Dialog, { open: isOpen, onOpenChange: onClose, children: /* @__PURE__ */ jsxDEV31(DialogContent, { children: [
    /* @__PURE__ */ jsxDEV31(DialogHeader, { children: [
      /* @__PURE__ */ jsxDEV31(DialogTitle, { children: "Delete Chat" }, void 0, !1, {
        fileName: "app/components/chat/delete-chat-dialog.tsx",
        lineNumber: 45,
        columnNumber: 11
      }, this),
      /* @__PURE__ */ jsxDEV31(DialogDescription, { children: "Are you sure you want to delete this chat? This action cannot be undone." }, void 0, !1, {
        fileName: "app/components/chat/delete-chat-dialog.tsx",
        lineNumber: 46,
        columnNumber: 11
      }, this)
    ] }, void 0, !0, {
      fileName: "app/components/chat/delete-chat-dialog.tsx",
      lineNumber: 44,
      columnNumber: 9
    }, this),
    /* @__PURE__ */ jsxDEV31(DialogFooter, { children: [
      /* @__PURE__ */ jsxDEV31(
        Button,
        {
          variant: "outline",
          onClick: onClose,
          disabled: isDeleting,
          children: "Cancel"
        },
        void 0,
        !1,
        {
          fileName: "app/components/chat/delete-chat-dialog.tsx",
          lineNumber: 51,
          columnNumber: 11
        },
        this
      ),
      /* @__PURE__ */ jsxDEV31(
        Button,
        {
          variant: "destructive",
          onClick: async () => {
            if (!(!currentSession || isDeleting))
              try {
                setIsDeleting(!0), await onConfirm();
              } catch (error) {
                console.error("Failed to delete chat:", error);
              } finally {
                setIsDeleting(!1);
              }
          },
          disabled: isDeleting,
          children: isDeleting ? "Deleting..." : "Delete"
        },
        void 0,
        !1,
        {
          fileName: "app/components/chat/delete-chat-dialog.tsx",
          lineNumber: 58,
          columnNumber: 11
        },
        this
      )
    ] }, void 0, !0, {
      fileName: "app/components/chat/delete-chat-dialog.tsx",
      lineNumber: 50,
      columnNumber: 9
    }, this)
  ] }, void 0, !0, {
    fileName: "app/components/chat/delete-chat-dialog.tsx",
    lineNumber: 43,
    columnNumber: 7
  }, this) }, void 0, !1, {
    fileName: "app/components/chat/delete-chat-dialog.tsx",
    lineNumber: 42,
    columnNumber: 5
  }, this);
}

// app/components/ui/progress.tsx
import * as React15 from "react";
import * as ProgressPrimitive from "@radix-ui/react-progress";
import { jsxDEV as jsxDEV32 } from "react/jsx-dev-runtime";
var Progress = React15.forwardRef(({ className, value, ...props }, ref) => /* @__PURE__ */ jsxDEV32(
  ProgressPrimitive.Root,
  {
    ref,
    className: cn(
      "relative h-2 w-full overflow-hidden rounded-full bg-primary/20",
      className
    ),
    ...props,
    children: /* @__PURE__ */ jsxDEV32(
      ProgressPrimitive.Indicator,
      {
        className: "h-full w-full flex-1 bg-primary transition-all",
        style: { transform: `translateX(-${100 - (value || 0)}%)` }
      },
      void 0,
      !1,
      {
        fileName: "app/components/ui/progress.tsx",
        lineNumber: 17,
        columnNumber: 5
      },
      this
    )
  },
  void 0,
  !1,
  {
    fileName: "app/components/ui/progress.tsx",
    lineNumber: 9,
    columnNumber: 3
  },
  this
));
Progress.displayName = ProgressPrimitive.Root.displayName;

// app/components/chat/chat-header.tsx
import { jsxDEV as jsxDEV33 } from "react/jsx-dev-runtime";
function ChatHeader({
  isLoading,
  onNewChat,
  onSelectChat,
  onClearChat,
  sessions = [],
  currentSession,
  progress
}) {
  let [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState9(!1), handleDeleteClick = () => {
    setIsDeleteDialogOpen(!0);
  }, handleDeleteConfirm = async () => {
    try {
      onClearChat && await onClearChat(), setIsDeleteDialogOpen(!1);
    } catch (error) {
      console.error("Failed to delete chat:", error);
    }
  };
  return /* @__PURE__ */ jsxDEV33("header", { className: "sticky top-0 z-10 bg-background border-b", children: [
    /* @__PURE__ */ jsxDEV33("div", { className: "flex items-center justify-between px-4 py-2", children: [
      /* @__PURE__ */ jsxDEV33("div", { className: "flex items-center gap-2", children: [
        isLoading && /* @__PURE__ */ jsxDEV33(Loader2, { className: "h-4 w-4 animate-spin" }, void 0, !1, {
          fileName: "app/components/chat/chat-header.tsx",
          lineNumber: 58,
          columnNumber: 25
        }, this),
        /* @__PURE__ */ jsxDEV33("span", { className: "font-bold text-foreground", children: currentSession?.title || "New Chat" }, void 0, !1, {
          fileName: "app/components/chat/chat-header.tsx",
          lineNumber: 59,
          columnNumber: 11
        }, this)
      ] }, void 0, !0, {
        fileName: "app/components/chat/chat-header.tsx",
        lineNumber: 57,
        columnNumber: 9
      }, this),
      /* @__PURE__ */ jsxDEV33(DropdownMenu, { children: [
        /* @__PURE__ */ jsxDEV33(DropdownMenuTrigger, { asChild: !0, children: /* @__PURE__ */ jsxDEV33(Button, { variant: "ghost", className: "flex items-center gap-2", children: [
          /* @__PURE__ */ jsxDEV33(Menu, { className: "h-4 w-4" }, void 0, !1, {
            fileName: "app/components/chat/chat-header.tsx",
            lineNumber: 66,
            columnNumber: 15
          }, this),
          /* @__PURE__ */ jsxDEV33("span", { children: "Chat Menu" }, void 0, !1, {
            fileName: "app/components/chat/chat-header.tsx",
            lineNumber: 67,
            columnNumber: 15
          }, this),
          /* @__PURE__ */ jsxDEV33("span", { className: "sr-only", children: "Open menu" }, void 0, !1, {
            fileName: "app/components/chat/chat-header.tsx",
            lineNumber: 68,
            columnNumber: 15
          }, this)
        ] }, void 0, !0, {
          fileName: "app/components/chat/chat-header.tsx",
          lineNumber: 65,
          columnNumber: 13
        }, this) }, void 0, !1, {
          fileName: "app/components/chat/chat-header.tsx",
          lineNumber: 64,
          columnNumber: 11
        }, this),
        /* @__PURE__ */ jsxDEV33(DropdownMenuContent, { align: "end", children: [
          /* @__PURE__ */ jsxDEV33(DropdownMenuItem, { onClick: onNewChat, children: [
            /* @__PURE__ */ jsxDEV33(Plus, { className: "h-4 w-4 mr-2" }, void 0, !1, {
              fileName: "app/components/chat/chat-header.tsx",
              lineNumber: 73,
              columnNumber: 15
            }, this),
            "New Chat"
          ] }, void 0, !0, {
            fileName: "app/components/chat/chat-header.tsx",
            lineNumber: 72,
            columnNumber: 13
          }, this),
          sessions.length > 0 && /* @__PURE__ */ jsxDEV33(DropdownMenuSub, { children: [
            /* @__PURE__ */ jsxDEV33(DropdownMenuSubTrigger, { children: [
              /* @__PURE__ */ jsxDEV33(Menu, { className: "h-4 w-4 mr-2" }, void 0, !1, {
                fileName: "app/components/chat/chat-header.tsx",
                lineNumber: 79,
                columnNumber: 19
              }, this),
              "Select Chat"
            ] }, void 0, !0, {
              fileName: "app/components/chat/chat-header.tsx",
              lineNumber: 78,
              columnNumber: 17
            }, this),
            /* @__PURE__ */ jsxDEV33(DropdownMenuSubContent, { children: sessions.map((session) => /* @__PURE__ */ jsxDEV33(
              DropdownMenuItem,
              {
                onClick: () => onSelectChat(session.id),
                children: session.title
              },
              session.id,
              !1,
              {
                fileName: "app/components/chat/chat-header.tsx",
                lineNumber: 84,
                columnNumber: 21
              },
              this
            )) }, void 0, !1, {
              fileName: "app/components/chat/chat-header.tsx",
              lineNumber: 82,
              columnNumber: 17
            }, this)
          ] }, void 0, !0, {
            fileName: "app/components/chat/chat-header.tsx",
            lineNumber: 77,
            columnNumber: 15
          }, this),
          currentSession && /* @__PURE__ */ jsxDEV33(
            DropdownMenuItem,
            {
              onClick: handleDeleteClick,
              className: "text-destructive focus:text-destructive",
              children: [
                /* @__PURE__ */ jsxDEV33(Trash2, { className: "h-4 w-4 mr-2" }, void 0, !1, {
                  fileName: "app/components/chat/chat-header.tsx",
                  lineNumber: 99,
                  columnNumber: 17
                }, this),
                "Delete Chat"
              ]
            },
            void 0,
            !0,
            {
              fileName: "app/components/chat/chat-header.tsx",
              lineNumber: 95,
              columnNumber: 15
            },
            this
          )
        ] }, void 0, !0, {
          fileName: "app/components/chat/chat-header.tsx",
          lineNumber: 71,
          columnNumber: 11
        }, this)
      ] }, void 0, !0, {
        fileName: "app/components/chat/chat-header.tsx",
        lineNumber: 63,
        columnNumber: 9
      }, this)
    ] }, void 0, !0, {
      fileName: "app/components/chat/chat-header.tsx",
      lineNumber: 56,
      columnNumber: 7
    }, this),
    progress !== void 0 && /* @__PURE__ */ jsxDEV33("div", { className: "px-4 pb-2", children: /* @__PURE__ */ jsxDEV33("div", { className: "flex items-center gap-2", children: [
      /* @__PURE__ */ jsxDEV33("div", { className: "flex-1", children: /* @__PURE__ */ jsxDEV33(Progress, { value: progress, className: "h-2" }, void 0, !1, {
        fileName: "app/components/chat/chat-header.tsx",
        lineNumber: 111,
        columnNumber: 15
      }, this) }, void 0, !1, {
        fileName: "app/components/chat/chat-header.tsx",
        lineNumber: 110,
        columnNumber: 13
      }, this),
      /* @__PURE__ */ jsxDEV33("span", { className: "text-sm text-muted-foreground w-12 text-right", children: [
        Math.round(progress),
        "%"
      ] }, void 0, !0, {
        fileName: "app/components/chat/chat-header.tsx",
        lineNumber: 113,
        columnNumber: 13
      }, this)
    ] }, void 0, !0, {
      fileName: "app/components/chat/chat-header.tsx",
      lineNumber: 109,
      columnNumber: 11
    }, this) }, void 0, !1, {
      fileName: "app/components/chat/chat-header.tsx",
      lineNumber: 108,
      columnNumber: 9
    }, this),
    /* @__PURE__ */ jsxDEV33(
      DeleteChatDialog,
      {
        isOpen: isDeleteDialogOpen,
        onClose: () => setIsDeleteDialogOpen(!1),
        onConfirm: handleDeleteConfirm,
        currentSession
      },
      void 0,
      !1,
      {
        fileName: "app/components/chat/chat-header.tsx",
        lineNumber: 120,
        columnNumber: 7
      },
      this
    )
  ] }, void 0, !0, {
    fileName: "app/components/chat/chat-header.tsx",
    lineNumber: 55,
    columnNumber: 5
  }, this);
}

// app/components/chat/chat-input.tsx
import { useRef as useRef2, useEffect as useEffect6 } from "react";
import { SendHorizontal, MessageCircleOff } from "lucide-react";
import { jsxDEV as jsxDEV34 } from "react/jsx-dev-runtime";
function ChatInput({
  input,
  handleInputChange,
  handleSubmit,
  isLoading,
  lastMessageId,
  hasActiveSession
}) {
  let textareaRef = useRef2(null);
  useEffect6(() => {
    textareaRef.current && (textareaRef.current.style.height = "auto", textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`);
  }, [input]), useEffect6(() => {
    !isLoading && textareaRef.current && hasActiveSession && textareaRef.current.focus();
  }, [isLoading, hasActiveSession]);
  let handleKeyDown = (e) => {
    e.key === "Enter" && !e.shiftKey && (e.preventDefault(), handleSubmit(e));
  }, handleFormSubmit = (e) => {
    e.preventDefault(), handleSubmit(e);
  };
  return hasActiveSession ? /* @__PURE__ */ jsxDEV34("form", { onSubmit: handleFormSubmit, children: /* @__PURE__ */ jsxDEV34("div", { className: cn(
    "relative flex items-center",
    "px-8 py-4",
    "max-w-7xl mx-auto w-full",
    "bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60"
  ), children: /* @__PURE__ */ jsxDEV34("div", { className: "relative w-full", children: [
    /* @__PURE__ */ jsxDEV34(
      Textarea,
      {
        ref: textareaRef,
        value: input,
        onChange: handleInputChange,
        onKeyDown: handleKeyDown,
        placeholder: "Type your message... (Press Enter to send, Shift+Enter for new line)",
        className: cn(
          "min-h-[80px] w-full resize-none pr-12",
          "bg-background",
          "rounded-md border border-input",
          "focus-visible:outline-none focus-visible:ring-1",
          "focus-visible:ring-ring",
          "disabled:opacity-50 disabled:cursor-not-allowed",
          "text-foreground placeholder:text-muted-foreground",
          "scrollbar-custom"
        ),
        disabled: isLoading
      },
      void 0,
      !1,
      {
        fileName: "app/components/chat/chat-input.tsx",
        lineNumber: 75,
        columnNumber: 11
      },
      this
    ),
    /* @__PURE__ */ jsxDEV34(
      Button,
      {
        type: "submit",
        size: "icon",
        disabled: isLoading || !input.trim(),
        className: cn(
          "absolute right-2 bottom-2",
          "bg-primary text-primary-foreground",
          "hover:bg-primary/90",
          "focus-visible:ring-1 focus-visible:ring-ring",
          "disabled:opacity-50"
        ),
        children: [
          /* @__PURE__ */ jsxDEV34(SendHorizontal, { className: "h-4 w-4" }, void 0, !1, {
            fileName: "app/components/chat/chat-input.tsx",
            lineNumber: 105,
            columnNumber: 13
          }, this),
          /* @__PURE__ */ jsxDEV34("span", { className: "sr-only", children: "Send message" }, void 0, !1, {
            fileName: "app/components/chat/chat-input.tsx",
            lineNumber: 106,
            columnNumber: 13
          }, this)
        ]
      },
      void 0,
      !0,
      {
        fileName: "app/components/chat/chat-input.tsx",
        lineNumber: 93,
        columnNumber: 11
      },
      this
    )
  ] }, void 0, !0, {
    fileName: "app/components/chat/chat-input.tsx",
    lineNumber: 74,
    columnNumber: 9
  }, this) }, void 0, !1, {
    fileName: "app/components/chat/chat-input.tsx",
    lineNumber: 68,
    columnNumber: 7
  }, this) }, void 0, !1, {
    fileName: "app/components/chat/chat-input.tsx",
    lineNumber: 67,
    columnNumber: 5
  }, this) : /* @__PURE__ */ jsxDEV34("div", { className: "flex flex-col items-center justify-center p-8 text-center", children: [
    /* @__PURE__ */ jsxDEV34(MessageCircleOff, { className: "h-8 w-8 mb-4 text-muted-foreground" }, void 0, !1, {
      fileName: "app/components/chat/chat-input.tsx",
      lineNumber: 55,
      columnNumber: 9
    }, this),
    /* @__PURE__ */ jsxDEV34("p", { className: "text-lg font-semibold", children: "No Active Chat" }, void 0, !1, {
      fileName: "app/components/chat/chat-input.tsx",
      lineNumber: 56,
      columnNumber: 9
    }, this),
    /* @__PURE__ */ jsxDEV34("p", { className: "text-sm text-muted-foreground mt-1", children: "Please start a new chat or select an existing one to continue." }, void 0, !1, {
      fileName: "app/components/chat/chat-input.tsx",
      lineNumber: 59,
      columnNumber: 9
    }, this)
  ] }, void 0, !0, {
    fileName: "app/components/chat/chat-input.tsx",
    lineNumber: 54,
    columnNumber: 7
  }, this);
}

// app/components/layout/markdown.tsx
import * as React16 from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { jsxDEV as jsxDEV35 } from "react/jsx-dev-runtime";
function Markdown6({ content: content4, className }) {
  return /* @__PURE__ */ jsxDEV35(ErrorBoundary2, { fallback: /* @__PURE__ */ jsxDEV35("div", { className: "text-destructive", children: "Error rendering markdown" }, void 0, !1, {
    fileName: "app/components/layout/markdown.tsx",
    lineNumber: 13,
    columnNumber: 30
  }, this), children: /* @__PURE__ */ jsxDEV35("div", { className: cn("prose dark:prose-invert max-w-none", className), children: /* @__PURE__ */ jsxDEV35(
    ReactMarkdown,
    {
      remarkPlugins: [remarkGfm],
      components: {
        code({ className: className2, children, ...props }) {
          let match = /language-(\w+)/.exec(className2 || "");
          return /* @__PURE__ */ jsxDEV35(
            "code",
            {
              className: cn(
                "bg-muted px-[0.4em] py-[0.2em] rounded font-mono text-sm",
                match ? "block overflow-x-auto p-4" : "inline-block",
                className2
              ),
              ...props,
              children
            },
            void 0,
            !1,
            {
              fileName: "app/components/layout/markdown.tsx",
              lineNumber: 21,
              columnNumber: 17
            },
            this
          );
        }
      },
      children: content4
    },
    void 0,
    !1,
    {
      fileName: "app/components/layout/markdown.tsx",
      lineNumber: 15,
      columnNumber: 9
    },
    this
  ) }, void 0, !1, {
    fileName: "app/components/layout/markdown.tsx",
    lineNumber: 14,
    columnNumber: 7
  }, this) }, void 0, !1, {
    fileName: "app/components/layout/markdown.tsx",
    lineNumber: 13,
    columnNumber: 5
  }, this);
}
var ErrorBoundary2 = class extends React16.Component {
  constructor(props) {
    super(props), this.state = { hasError: !1 };
  }
  static getDerivedStateFromError() {
    return { hasError: !0 };
  }
  componentDidCatch(error) {
    console.error("Markdown rendering error:", error);
  }
  render() {
    return this.state.hasError ? this.props.fallback : this.props.children;
  }
};

// app/components/chat/chat-message.tsx
import { Loader2 as Loader22 } from "lucide-react";

// app/components/ui/avatar.tsx
import * as React17 from "react";
import * as AvatarPrimitive from "@radix-ui/react-avatar";
import { jsxDEV as jsxDEV36 } from "react/jsx-dev-runtime";
var Avatar = React17.forwardRef(({ className, ...props }, ref) => /* @__PURE__ */ jsxDEV36(
  AvatarPrimitive.Root,
  {
    ref,
    className: cn(
      "relative flex h-10 w-10 shrink-0 overflow-hidden rounded-full",
      className
    ),
    ...props
  },
  void 0,
  !1,
  {
    fileName: "app/components/ui/avatar.tsx",
    lineNumber: 9,
    columnNumber: 3
  },
  this
));
Avatar.displayName = AvatarPrimitive.Root.displayName;
var AvatarImage = React17.forwardRef(({ className, ...props }, ref) => /* @__PURE__ */ jsxDEV36(
  AvatarPrimitive.Image,
  {
    ref,
    className: cn("aspect-square h-full w-full", className),
    ...props
  },
  void 0,
  !1,
  {
    fileName: "app/components/ui/avatar.tsx",
    lineNumber: 24,
    columnNumber: 3
  },
  this
));
AvatarImage.displayName = AvatarPrimitive.Image.displayName;
var AvatarFallback = React17.forwardRef(({ className, ...props }, ref) => /* @__PURE__ */ jsxDEV36(
  AvatarPrimitive.Fallback,
  {
    ref,
    className: cn(
      "flex h-full w-full items-center justify-center rounded-full bg-muted",
      className
    ),
    ...props
  },
  void 0,
  !1,
  {
    fileName: "app/components/ui/avatar.tsx",
    lineNumber: 36,
    columnNumber: 3
  },
  this
));
AvatarFallback.displayName = AvatarPrimitive.Fallback.displayName;

// app/components/chat/chat-message.tsx
import { jsxDEV as jsxDEV37 } from "react/jsx-dev-runtime";
function ChatMessage({ message, isLoading, className }) {
  let isUser = message.role === "USER";
  return /* @__PURE__ */ jsxDEV37("div", { className: cn("flex gap-4 p-4", isUser && "flex-row-reverse", className), children: [
    /* @__PURE__ */ jsxDEV37(Avatar, { className: cn(
      "h-8 w-8 shrink-0",
      isUser ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"
    ), children: /* @__PURE__ */ jsxDEV37(AvatarFallback, { children: isUser ? "U" : "A" }, void 0, !1, {
      fileName: "app/components/chat/chat-message.tsx",
      lineNumber: 24,
      columnNumber: 9
    }, this) }, void 0, !1, {
      fileName: "app/components/chat/chat-message.tsx",
      lineNumber: 20,
      columnNumber: 7
    }, this),
    /* @__PURE__ */ jsxDEV37(Card, { className: cn(
      "flex-1 p-4",
      isUser ? "bg-primary/5" : "bg-background",
      "border shadow-sm"
    ), children: isLoading ? /* @__PURE__ */ jsxDEV37("div", { className: "flex items-center gap-2 text-muted-foreground animate-pulse", children: [
      /* @__PURE__ */ jsxDEV37("span", { children: "Agent Smith is thinking" }, void 0, !1, {
        fileName: "app/components/chat/chat-message.tsx",
        lineNumber: 34,
        columnNumber: 13
      }, this),
      /* @__PURE__ */ jsxDEV37(Loader22, { className: "h-4 w-4 animate-spin" }, void 0, !1, {
        fileName: "app/components/chat/chat-message.tsx",
        lineNumber: 35,
        columnNumber: 13
      }, this)
    ] }, void 0, !0, {
      fileName: "app/components/chat/chat-message.tsx",
      lineNumber: 33,
      columnNumber: 11
    }, this) : /* @__PURE__ */ jsxDEV37("div", { className: cn(
      "prose dark:prose-invert max-w-none",
      "prose-p:leading-relaxed prose-pre:p-0",
      "prose-code:bg-muted prose-code:text-foreground",
      "prose-headings:text-foreground prose-a:text-primary"
    ), children: /* @__PURE__ */ jsxDEV37(Markdown6, { content: message.content }, void 0, !1, {
      fileName: "app/components/chat/chat-message.tsx",
      lineNumber: 44,
      columnNumber: 13
    }, this) }, void 0, !1, {
      fileName: "app/components/chat/chat-message.tsx",
      lineNumber: 38,
      columnNumber: 11
    }, this) }, void 0, !1, {
      fileName: "app/components/chat/chat-message.tsx",
      lineNumber: 27,
      columnNumber: 7
    }, this)
  ] }, void 0, !0, {
    fileName: "app/components/chat/chat-message.tsx",
    lineNumber: 19,
    columnNumber: 5
  }, this);
}

// app/components/chat/new-chat-dialog.tsx
import { useState as useState10 } from "react";
import { Loader2 as Loader23, MessageSquarePlus } from "lucide-react";
import { Fragment as Fragment4, jsxDEV as jsxDEV38 } from "react/jsx-dev-runtime";
function NewChatDialog({
  isOpen,
  onClose,
  onCreateChat
}) {
  let [title, setTitle] = useState10(""), [isCreating, setIsCreating] = useState10(!1), handleCreate = async () => {
    if (!(!title.trim() || isCreating))
      try {
        setIsCreating(!0), await onCreateChat(title), setTitle(""), onClose();
      } catch (error) {
        console.error("Failed to create chat:", error);
      } finally {
        setIsCreating(!1);
      }
  };
  return /* @__PURE__ */ jsxDEV38(Dialog, { open: isOpen, onOpenChange: onClose, children: /* @__PURE__ */ jsxDEV38(DialogContent, { children: [
    /* @__PURE__ */ jsxDEV38(DialogHeader, { children: [
      /* @__PURE__ */ jsxDEV38(DialogTitle, { className: "flex items-center gap-2", children: [
        /* @__PURE__ */ jsxDEV38(MessageSquarePlus, { className: "h-5 w-5" }, void 0, !1, {
          fileName: "app/components/chat/new-chat-dialog.tsx",
          lineNumber: 56,
          columnNumber: 13
        }, this),
        "New Chat"
      ] }, void 0, !0, {
        fileName: "app/components/chat/new-chat-dialog.tsx",
        lineNumber: 55,
        columnNumber: 11
      }, this),
      /* @__PURE__ */ jsxDEV38(DialogDescription, { children: "Create a new chat session. Give it a descriptive title." }, void 0, !1, {
        fileName: "app/components/chat/new-chat-dialog.tsx",
        lineNumber: 59,
        columnNumber: 11
      }, this)
    ] }, void 0, !0, {
      fileName: "app/components/chat/new-chat-dialog.tsx",
      lineNumber: 54,
      columnNumber: 9
    }, this),
    /* @__PURE__ */ jsxDEV38(
      Input,
      {
        value: title,
        onChange: (e) => setTitle(e.target.value),
        onKeyDown: (e) => {
          e.key === "Enter" && !e.shiftKey && (e.preventDefault(), handleCreate());
        },
        placeholder: "Enter chat title...",
        disabled: isCreating,
        autoFocus: !0
      },
      void 0,
      !1,
      {
        fileName: "app/components/chat/new-chat-dialog.tsx",
        lineNumber: 63,
        columnNumber: 9
      },
      this
    ),
    /* @__PURE__ */ jsxDEV38(DialogFooter, { children: [
      /* @__PURE__ */ jsxDEV38(
        Button,
        {
          variant: "outline",
          onClick: onClose,
          disabled: isCreating,
          children: "Cancel"
        },
        void 0,
        !1,
        {
          fileName: "app/components/chat/new-chat-dialog.tsx",
          lineNumber: 72,
          columnNumber: 11
        },
        this
      ),
      /* @__PURE__ */ jsxDEV38(
        Button,
        {
          onClick: handleCreate,
          disabled: !title.trim() || isCreating,
          children: isCreating ? /* @__PURE__ */ jsxDEV38(Fragment4, { children: [
            /* @__PURE__ */ jsxDEV38(Loader23, { className: "mr-2 h-4 w-4 animate-spin" }, void 0, !1, {
              fileName: "app/components/chat/new-chat-dialog.tsx",
              lineNumber: 85,
              columnNumber: 17
            }, this),
            "Creating..."
          ] }, void 0, !0, {
            fileName: "app/components/chat/new-chat-dialog.tsx",
            lineNumber: 84,
            columnNumber: 15
          }, this) : "Create"
        },
        void 0,
        !1,
        {
          fileName: "app/components/chat/new-chat-dialog.tsx",
          lineNumber: 79,
          columnNumber: 11
        },
        this
      )
    ] }, void 0, !0, {
      fileName: "app/components/chat/new-chat-dialog.tsx",
      lineNumber: 71,
      columnNumber: 9
    }, this)
  ] }, void 0, !0, {
    fileName: "app/components/chat/new-chat-dialog.tsx",
    lineNumber: 53,
    columnNumber: 7
  }, this) }, void 0, !1, {
    fileName: "app/components/chat/new-chat-dialog.tsx",
    lineNumber: 52,
    columnNumber: 5
  }, this);
}

// app/components/ui/alert.tsx
import * as React18 from "react";
import { cva as cva3 } from "class-variance-authority";
import { jsxDEV as jsxDEV39 } from "react/jsx-dev-runtime";
var alertVariants = cva3(
  "relative w-full rounded-lg border px-4 py-3 text-sm [&>svg+div]:translate-y-[-3px] [&>svg]:absolute [&>svg]:left-4 [&>svg]:top-4 [&>svg]:text-foreground [&>svg~*]:pl-7",
  {
    variants: {
      variant: {
        default: "bg-background text-foreground",
        destructive: "border-destructive/50 text-destructive dark:border-destructive [&>svg]:text-destructive"
      }
    },
    defaultVariants: {
      variant: "default"
    }
  }
), Alert = React18.forwardRef(({ className, variant, ...props }, ref) => /* @__PURE__ */ jsxDEV39(
  "div",
  {
    ref,
    role: "alert",
    className: cn(alertVariants({ variant }), className),
    ...props
  },
  void 0,
  !1,
  {
    fileName: "app/components/ui/alert.tsx",
    lineNumber: 25,
    columnNumber: 3
  },
  this
));
Alert.displayName = "Alert";
var AlertTitle = React18.forwardRef(({ className, ...props }, ref) => /* @__PURE__ */ jsxDEV39(
  "h5",
  {
    ref,
    className: cn("mb-1 font-medium leading-none tracking-tight", className),
    ...props
  },
  void 0,
  !1,
  {
    fileName: "app/components/ui/alert.tsx",
    lineNumber: 38,
    columnNumber: 3
  },
  this
));
AlertTitle.displayName = "AlertTitle";
var AlertDescription = React18.forwardRef(({ className, ...props }, ref) => /* @__PURE__ */ jsxDEV39(
  "div",
  {
    ref,
    className: cn("text-sm [&_p]:leading-relaxed", className),
    ...props
  },
  void 0,
  !1,
  {
    fileName: "app/components/ui/alert.tsx",
    lineNumber: 50,
    columnNumber: 3
  },
  this
));
AlertDescription.displayName = "AlertDescription";

// app/components/ui/scroll-area.tsx
import * as React19 from "react";
import * as ScrollAreaPrimitive from "@radix-ui/react-scroll-area";
import { jsxDEV as jsxDEV40 } from "react/jsx-dev-runtime";
var ScrollArea = React19.forwardRef(({ className, children, ...props }, ref) => /* @__PURE__ */ jsxDEV40(
  ScrollAreaPrimitive.Root,
  {
    ref,
    className: cn("relative overflow-hidden", className),
    ...props,
    children: [
      /* @__PURE__ */ jsxDEV40(ScrollAreaPrimitive.Viewport, { className: "h-full w-full rounded-[inherit]", children }, void 0, !1, {
        fileName: "app/components/ui/scroll-area.tsx",
        lineNumber: 14,
        columnNumber: 5
      }, this),
      /* @__PURE__ */ jsxDEV40(ScrollBar, {}, void 0, !1, {
        fileName: "app/components/ui/scroll-area.tsx",
        lineNumber: 17,
        columnNumber: 5
      }, this),
      /* @__PURE__ */ jsxDEV40(ScrollAreaPrimitive.Corner, {}, void 0, !1, {
        fileName: "app/components/ui/scroll-area.tsx",
        lineNumber: 18,
        columnNumber: 5
      }, this)
    ]
  },
  void 0,
  !0,
  {
    fileName: "app/components/ui/scroll-area.tsx",
    lineNumber: 9,
    columnNumber: 3
  },
  this
));
ScrollArea.displayName = ScrollAreaPrimitive.Root.displayName;
var ScrollBar = React19.forwardRef(({ className, orientation = "vertical", ...props }, ref) => /* @__PURE__ */ jsxDEV40(
  ScrollAreaPrimitive.ScrollAreaScrollbar,
  {
    ref,
    orientation,
    className: cn(
      "flex touch-none select-none transition-colors",
      orientation === "vertical" && "h-full w-2.5 border-l border-l-transparent p-[1px]",
      orientation === "horizontal" && "h-2.5 flex-col border-t border-t-transparent p-[1px]",
      className
    ),
    ...props,
    children: /* @__PURE__ */ jsxDEV40(ScrollAreaPrimitive.ScrollAreaThumb, { className: "relative flex-1 rounded-full bg-border" }, void 0, !1, {
      fileName: "app/components/ui/scroll-area.tsx",
      lineNumber: 40,
      columnNumber: 5
    }, this)
  },
  void 0,
  !1,
  {
    fileName: "app/components/ui/scroll-area.tsx",
    lineNumber: 27,
    columnNumber: 3
  },
  this
));
ScrollBar.displayName = ScrollAreaPrimitive.ScrollAreaScrollbar.displayName;

// app/components/layout/session-timeout-warning.tsx
import { useEffect as useEffect7, useState as useState11 } from "react";
import { jsxDEV as jsxDEV41 } from "react/jsx-dev-runtime";
function SessionTimeoutWarning({ timeoutMinutes, onTimeout }) {
  let [remainingTime, setRemainingTime] = useState11(timeoutMinutes * 60), [showWarning, setShowWarning] = useState11(!1), resetTimer = () => {
    setRemainingTime(timeoutMinutes * 60), setShowWarning(!1);
  };
  if (useEffect7(() => {
    let timer;
    return timer = setInterval(() => {
      setRemainingTime((prev) => {
        let newTime = prev - 1;
        return newTime <= 0 ? (onTimeout(), 0) : (newTime <= 60 && setShowWarning(!0), newTime);
      });
    }, 1e3), () => clearInterval(timer);
  }, [timeoutMinutes, onTimeout]), !showWarning)
    return null;
  let seconds = remainingTime % 60;
  return /* @__PURE__ */ jsxDEV41(Alert, { className: "fixed bottom-4 right-4 max-w-md bg-yellow-50 border-yellow-200 dark:bg-yellow-900/10 dark:border-yellow-900/20", children: /* @__PURE__ */ jsxDEV41(AlertDescription, { className: "flex flex-col gap-3", children: [
    /* @__PURE__ */ jsxDEV41("p", { children: [
      "Your session will expire in ",
      seconds,
      " seconds."
    ] }, void 0, !0, {
      fileName: "app/components/layout/session-timeout-warning.tsx",
      lineNumber: 52,
      columnNumber: 9
    }, this),
    /* @__PURE__ */ jsxDEV41("div", { className: "flex justify-end gap-2", children: [
      /* @__PURE__ */ jsxDEV41(Button, { variant: "outline", onClick: resetTimer, children: "Continue Session" }, void 0, !1, {
        fileName: "app/components/layout/session-timeout-warning.tsx",
        lineNumber: 54,
        columnNumber: 11
      }, this),
      /* @__PURE__ */ jsxDEV41(Button, { variant: "destructive", onClick: onTimeout, children: "Log Off" }, void 0, !1, {
        fileName: "app/components/layout/session-timeout-warning.tsx",
        lineNumber: 57,
        columnNumber: 11
      }, this)
    ] }, void 0, !0, {
      fileName: "app/components/layout/session-timeout-warning.tsx",
      lineNumber: 53,
      columnNumber: 9
    }, this)
  ] }, void 0, !0, {
    fileName: "app/components/layout/session-timeout-warning.tsx",
    lineNumber: 51,
    columnNumber: 7
  }, this) }, void 0, !1, {
    fileName: "app/components/layout/session-timeout-warning.tsx",
    lineNumber: 50,
    columnNumber: 5
  }, this);
}

// app/routes/chat.tsx
import { useNavigate as useNavigate2, useLoaderData as useLoaderData5, Form as Form4 } from "@remix-run/react";
import { jsxDEV as jsxDEV42 } from "react/jsx-dev-runtime";
var loader8 = async ({ request }) => {
  try {
    return await requireUser2(request), json9({
      sessionTimeoutMinutes: Number(process.env.SESSION_TIMEOUT_MINUTES) || 30
    });
  } catch {
    return redirect9("/login?redirectTo=/chat");
  }
}, action4 = async ({ request }) => request.method === "POST" ? logout(request) : null;
function Chat() {
  let {
    messages,
    input,
    handleInputChange,
    handleSubmit,
    isLoading,
    error,
    startNewChat,
    sessions,
    currentSession,
    selectChat,
    deleteChat,
    progress
  } = useChat(), [isNewChatOpen, setIsNewChatOpen] = useState12(!1), scrollAreaRef = useRef3(null), isAutoScrollEnabled = useRef3(!0), lastMessageRef = useRef3(null), navigate = useNavigate2(), { sessionTimeoutMinutes } = useLoaderData5();
  useEffect8(() => {
    if (scrollAreaRef.current && isAutoScrollEnabled.current) {
      let scrollContainer = scrollAreaRef.current.querySelector("[data-radix-scroll-area-viewport]");
      scrollContainer && (scrollContainer.scrollTop = scrollContainer.scrollHeight);
    }
  }, [messages, isLoading]), useEffect8(() => {
    let scrollContainer = scrollAreaRef.current?.querySelector("[data-radix-scroll-area-viewport]");
    if (!scrollContainer)
      return;
    let handleScroll = () => {
      let { scrollTop, scrollHeight, clientHeight } = scrollContainer, isNearBottom = scrollHeight - (scrollTop + clientHeight) < 100;
      isAutoScrollEnabled.current = isNearBottom;
    };
    return scrollContainer.addEventListener("scroll", handleScroll), () => scrollContainer.removeEventListener("scroll", handleScroll);
  }, []);
  let handleNewChat = async (title) => {
    await startNewChat(title), setIsNewChatOpen(!1);
  }, handleTimeout = () => {
    document.getElementById("logoutForm")?.submit();
  };
  return /* @__PURE__ */ jsxDEV42("div", { className: "container py-8 mx-auto", children: [
    /* @__PURE__ */ jsxDEV42(Card, { className: "h-[calc(100vh-16rem)] flex flex-col border-0", children: [
      /* @__PURE__ */ jsxDEV42(
        ChatHeader,
        {
          isLoading,
          onNewChat: () => setIsNewChatOpen(!0),
          onSelectChat: selectChat,
          onClearChat: deleteChat,
          sessions,
          currentSession,
          progress
        },
        void 0,
        !1,
        {
          fileName: "app/routes/chat.tsx",
          lineNumber: 97,
          columnNumber: 9
        },
        this
      ),
      /* @__PURE__ */ jsxDEV42(ScrollArea, { ref: scrollAreaRef, className: "flex-1 p-4", children: [
        messages.map((message, index) => /* @__PURE__ */ jsxDEV42(
          "div",
          {
            ref: index === messages.length - 1 ? lastMessageRef : null,
            children: /* @__PURE__ */ jsxDEV42(
              ChatMessage,
              {
                message,
                isLoading: isLoading && index === messages.length - 1
              },
              void 0,
              !1,
              {
                fileName: "app/routes/chat.tsx",
                lineNumber: 112,
                columnNumber: 15
              },
              this
            )
          },
          index,
          !1,
          {
            fileName: "app/routes/chat.tsx",
            lineNumber: 108,
            columnNumber: 13
          },
          this
        )),
        error && /* @__PURE__ */ jsxDEV42(Alert, { variant: "destructive", className: "mt-4", children: /* @__PURE__ */ jsxDEV42(AlertDescription, { children: error }, void 0, !1, {
          fileName: "app/routes/chat.tsx",
          lineNumber: 120,
          columnNumber: 15
        }, this) }, void 0, !1, {
          fileName: "app/routes/chat.tsx",
          lineNumber: 119,
          columnNumber: 13
        }, this)
      ] }, void 0, !0, {
        fileName: "app/routes/chat.tsx",
        lineNumber: 106,
        columnNumber: 9
      }, this),
      /* @__PURE__ */ jsxDEV42("div", { className: "p-4 border-t", children: /* @__PURE__ */ jsxDEV42(
        ChatInput,
        {
          input,
          handleInputChange,
          handleSubmit,
          isLoading,
          hasActiveSession: !!currentSession
        },
        void 0,
        !1,
        {
          fileName: "app/routes/chat.tsx",
          lineNumber: 125,
          columnNumber: 11
        },
        this
      ) }, void 0, !1, {
        fileName: "app/routes/chat.tsx",
        lineNumber: 124,
        columnNumber: 9
      }, this)
    ] }, void 0, !0, {
      fileName: "app/routes/chat.tsx",
      lineNumber: 96,
      columnNumber: 7
    }, this),
    /* @__PURE__ */ jsxDEV42(
      NewChatDialog,
      {
        isOpen: isNewChatOpen,
        onClose: () => setIsNewChatOpen(!1),
        onCreateChat: handleNewChat
      },
      void 0,
      !1,
      {
        fileName: "app/routes/chat.tsx",
        lineNumber: 134,
        columnNumber: 7
      },
      this
    ),
    /* @__PURE__ */ jsxDEV42(Form4, { method: "post", id: "logoutForm", className: "hidden" }, void 0, !1, {
      fileName: "app/routes/chat.tsx",
      lineNumber: 139,
      columnNumber: 7
    }, this),
    /* @__PURE__ */ jsxDEV42(
      SessionTimeoutWarning,
      {
        timeoutMinutes: sessionTimeoutMinutes,
        onTimeout: handleTimeout
      },
      void 0,
      !1,
      {
        fileName: "app/routes/chat.tsx",
        lineNumber: 140,
        columnNumber: 7
      },
      this
    )
  ] }, void 0, !0, {
    fileName: "app/routes/chat.tsx",
    lineNumber: 95,
    columnNumber: 5
  }, this);
}

// server-assets-manifest:@remix-run/dev/assets-manifest
var assets_manifest_default = { entry: { module: "/build/entry.client-DI7TCKA6.js", imports: ["/build/_shared/chunk-ZYLLRU7J.js", "/build/_shared/chunk-5SMQHKI5.js", "/build/_shared/chunk-2N23GYW7.js", "/build/_shared/chunk-G5LS6WKY.js", "/build/_shared/chunk-QPVUD6NO.js", "/build/_shared/chunk-YJEMTN56.js", "/build/_shared/chunk-MWML3QXM.js", "/build/_shared/chunk-PZDJHGND.js"] }, routes: { root: { id: "root", parentId: void 0, path: "", index: void 0, caseSensitive: void 0, module: "/build/root-2W3GD42X.js", imports: ["/build/_shared/chunk-IVLWEOHB.js", "/build/_shared/chunk-LH4FQSYZ.js", "/build/_shared/chunk-5SXLN5D2.js", "/build/_shared/chunk-PTI7Q65L.js", "/build/_shared/chunk-RX7TAKA2.js", "/build/_shared/chunk-QATI3NSB.js", "/build/_shared/chunk-MI2YJZX6.js", "/build/_shared/chunk-2WFCNDEW.js", "/build/_shared/chunk-X6FLJXIJ.js", "/build/_shared/chunk-RFPV3BFZ.js", "/build/_shared/chunk-3DKJGO2R.js"], hasAction: !1, hasLoader: !0, hasClientAction: !1, hasClientLoader: !1, hasErrorBoundary: !0 }, "routes/_error.404": { id: "routes/_error.404", parentId: "root", path: "404", index: void 0, caseSensitive: void 0, module: "/build/routes/_error.404-IC4RH5QW.js", imports: void 0, hasAction: !1, hasLoader: !1, hasClientAction: !1, hasClientLoader: !1, hasErrorBoundary: !1 }, "routes/_index": { id: "routes/_index", parentId: "root", path: void 0, index: !0, caseSensitive: void 0, module: "/build/routes/_index-KBADKMCX.js", imports: ["/build/_shared/chunk-ANELKYHI.js"], hasAction: !1, hasLoader: !1, hasClientAction: !1, hasClientLoader: !1, hasErrorBoundary: !1 }, "routes/chat": { id: "routes/chat", parentId: "root", path: "chat", index: void 0, caseSensitive: void 0, module: "/build/routes/chat-FPLFVKHX.js", imports: ["/build/_shared/chunk-QBWBT4RY.js", "/build/_shared/chunk-DTNMODCA.js", "/build/_shared/chunk-ANELKYHI.js", "/build/_shared/chunk-MSUXECYF.js", "/build/_shared/chunk-IWB4XMPA.js", "/build/_shared/chunk-NBEH4DGX.js"], hasAction: !0, hasLoader: !0, hasClientAction: !1, hasClientLoader: !1, hasErrorBoundary: !1 }, "routes/contact": { id: "routes/contact", parentId: "root", path: "contact", index: void 0, caseSensitive: void 0, module: "/build/routes/contact-BF3PMGXM.js", imports: ["/build/_shared/chunk-QBWBT4RY.js", "/build/_shared/chunk-OBK74UUR.js", "/build/_shared/chunk-DTNMODCA.js", "/build/_shared/chunk-ANELKYHI.js", "/build/_shared/chunk-MSUXECYF.js", "/build/_shared/chunk-NBEH4DGX.js"], hasAction: !0, hasLoader: !1, hasClientAction: !1, hasClientLoader: !1, hasErrorBoundary: !1 }, "routes/guide": { id: "routes/guide", parentId: "root", path: "guide", index: void 0, caseSensitive: void 0, module: "/build/routes/guide-ICDI7MS6.js", imports: ["/build/_shared/chunk-DIGYRLJS.js"], hasAction: !1, hasLoader: !1, hasClientAction: !1, hasClientLoader: !1, hasErrorBoundary: !1 }, "routes/interview.$id": { id: "routes/interview.$id", parentId: "root", path: "interview/:id", index: void 0, caseSensitive: void 0, module: "/build/routes/interview.$id-HDHZRAKF.js", imports: ["/build/_shared/chunk-455JWECT.js", "/build/_shared/chunk-DIGYRLJS.js", "/build/_shared/chunk-YILOF2CX.js", "/build/_shared/chunk-IWB4XMPA.js", "/build/_shared/chunk-NBEH4DGX.js"], hasAction: !1, hasLoader: !0, hasClientAction: !1, hasClientLoader: !1, hasErrorBoundary: !1 }, "routes/interviews": { id: "routes/interviews", parentId: "root", path: "interviews", index: void 0, caseSensitive: void 0, module: "/build/routes/interviews-NF7ZGZQT.js", imports: ["/build/_shared/chunk-ANELKYHI.js", "/build/_shared/chunk-YILOF2CX.js", "/build/_shared/chunk-IWB4XMPA.js", "/build/_shared/chunk-NBEH4DGX.js"], hasAction: !1, hasLoader: !0, hasClientAction: !1, hasClientLoader: !1, hasErrorBoundary: !1 }, "routes/login": { id: "routes/login", parentId: "root", path: "login", index: void 0, caseSensitive: void 0, module: "/build/routes/login-ONMPRLQ2.js", imports: ["/build/_shared/chunk-OBK74UUR.js", "/build/_shared/chunk-DTNMODCA.js", "/build/_shared/chunk-ANELKYHI.js", "/build/_shared/chunk-NBEH4DGX.js"], hasAction: !0, hasLoader: !0, hasClientAction: !1, hasClientLoader: !1, hasErrorBoundary: !1 }, "routes/logout": { id: "routes/logout", parentId: "root", path: "logout", index: void 0, caseSensitive: void 0, module: "/build/routes/logout-SKCKROSA.js", imports: ["/build/_shared/chunk-IWB4XMPA.js"], hasAction: !0, hasLoader: !1, hasClientAction: !1, hasClientLoader: !1, hasErrorBoundary: !1 }, "routes/privacy": { id: "routes/privacy", parentId: "root", path: "privacy", index: void 0, caseSensitive: void 0, module: "/build/routes/privacy-K6BBOSDB.js", imports: ["/build/_shared/chunk-DIGYRLJS.js"], hasAction: !1, hasLoader: !1, hasClientAction: !1, hasClientLoader: !1, hasErrorBoundary: !1 }, "routes/settings.theme": { id: "routes/settings.theme", parentId: "root", path: "settings/theme", index: void 0, caseSensitive: void 0, module: "/build/routes/settings.theme-DD3Y5IAL.js", imports: ["/build/_shared/chunk-ANELKYHI.js"], hasAction: !1, hasLoader: !1, hasClientAction: !1, hasClientLoader: !1, hasErrorBoundary: !1 }, "routes/srsdoc.$id": { id: "routes/srsdoc.$id", parentId: "root", path: "srsdoc/:id", index: void 0, caseSensitive: void 0, module: "/build/routes/srsdoc.$id-6VZRP2SA.js", imports: ["/build/_shared/chunk-MSUXECYF.js", "/build/_shared/chunk-455JWECT.js", "/build/_shared/chunk-DIGYRLJS.js", "/build/_shared/chunk-YILOF2CX.js", "/build/_shared/chunk-IWB4XMPA.js", "/build/_shared/chunk-NBEH4DGX.js"], hasAction: !1, hasLoader: !0, hasClientAction: !1, hasClientLoader: !1, hasErrorBoundary: !1 }, "routes/srsdocs": { id: "routes/srsdocs", parentId: "root", path: "srsdocs", index: void 0, caseSensitive: void 0, module: "/build/routes/srsdocs-ASMUVMYL.js", imports: ["/build/_shared/chunk-YILOF2CX.js", "/build/_shared/chunk-IWB4XMPA.js", "/build/_shared/chunk-NBEH4DGX.js"], hasAction: !1, hasLoader: !0, hasClientAction: !1, hasClientLoader: !1, hasErrorBoundary: !1 }, "routes/srsdocs.$id": { id: "routes/srsdocs.$id", parentId: "routes/srsdocs", path: ":id", index: void 0, caseSensitive: void 0, module: "/build/routes/srsdocs.$id-O2UIOKMY.js", imports: void 0, hasAction: !1, hasLoader: !0, hasClientAction: !1, hasClientLoader: !1, hasErrorBoundary: !1 }, "routes/terms": { id: "routes/terms", parentId: "root", path: "terms", index: void 0, caseSensitive: void 0, module: "/build/routes/terms-T6A3ZUAK.js", imports: ["/build/_shared/chunk-DIGYRLJS.js"], hasAction: !1, hasLoader: !1, hasClientAction: !1, hasClientLoader: !1, hasErrorBoundary: !1 } }, version: "54047865", hmr: { runtime: "/build/_shared/chunk-YJEMTN56.js", timestamp: 1739256979443 }, url: "/build/manifest-54047865.js" };

// server-entry-module:@remix-run/dev/server-build
var mode = "development", assetsBuildDirectory = "public/build", future = { v3_fetcherPersist: !0, v3_relativeSplatPath: !0, v3_throwAbortReason: !0, v3_routeConfig: !1, v3_singleFetch: !0, v3_lazyRouteDiscovery: !0, unstable_optimizeDeps: !1 }, publicPath = "/build/", entry = { module: entry_server_node_exports }, routes = {
  root: {
    id: "root",
    parentId: void 0,
    path: "",
    index: void 0,
    caseSensitive: void 0,
    module: root_exports
  },
  "routes/settings.theme": {
    id: "routes/settings.theme",
    parentId: "root",
    path: "settings/theme",
    index: void 0,
    caseSensitive: void 0,
    module: settings_theme_exports
  },
  "routes/interview.$id": {
    id: "routes/interview.$id",
    parentId: "root",
    path: "interview/:id",
    index: void 0,
    caseSensitive: void 0,
    module: interview_id_exports
  },
  "routes/srsdocs.$id": {
    id: "routes/srsdocs.$id",
    parentId: "routes/srsdocs",
    path: ":id",
    index: void 0,
    caseSensitive: void 0,
    module: srsdocs_id_exports
  },
  "routes/_error.404": {
    id: "routes/_error.404",
    parentId: "root",
    path: "404",
    index: void 0,
    caseSensitive: void 0,
    module: error_404_exports
  },
  "routes/interviews": {
    id: "routes/interviews",
    parentId: "root",
    path: "interviews",
    index: void 0,
    caseSensitive: void 0,
    module: interviews_exports
  },
  "routes/srsdoc.$id": {
    id: "routes/srsdoc.$id",
    parentId: "root",
    path: "srsdoc/:id",
    index: void 0,
    caseSensitive: void 0,
    module: srsdoc_id_exports
  },
  "routes/contact": {
    id: "routes/contact",
    parentId: "root",
    path: "contact",
    index: void 0,
    caseSensitive: void 0,
    module: contact_exports
  },
  "routes/privacy": {
    id: "routes/privacy",
    parentId: "root",
    path: "privacy",
    index: void 0,
    caseSensitive: void 0,
    module: privacy_exports
  },
  "routes/srsdocs": {
    id: "routes/srsdocs",
    parentId: "root",
    path: "srsdocs",
    index: void 0,
    caseSensitive: void 0,
    module: srsdocs_exports
  },
  "routes/_index": {
    id: "routes/_index",
    parentId: "root",
    path: void 0,
    index: !0,
    caseSensitive: void 0,
    module: index_exports
  },
  "routes/logout": {
    id: "routes/logout",
    parentId: "root",
    path: "logout",
    index: void 0,
    caseSensitive: void 0,
    module: logout_exports
  },
  "routes/guide": {
    id: "routes/guide",
    parentId: "root",
    path: "guide",
    index: void 0,
    caseSensitive: void 0,
    module: guide_exports
  },
  "routes/login": {
    id: "routes/login",
    parentId: "root",
    path: "login",
    index: void 0,
    caseSensitive: void 0,
    module: login_exports
  },
  "routes/terms": {
    id: "routes/terms",
    parentId: "root",
    path: "terms",
    index: void 0,
    caseSensitive: void 0,
    module: terms_exports
  },
  "routes/chat": {
    id: "routes/chat",
    parentId: "root",
    path: "chat",
    index: void 0,
    caseSensitive: void 0,
    module: chat_exports
  }
};
export {
  assets_manifest_default as assets,
  assetsBuildDirectory,
  entry,
  future,
  mode,
  publicPath,
  routes
};
//# sourceMappingURL=index.js.map
