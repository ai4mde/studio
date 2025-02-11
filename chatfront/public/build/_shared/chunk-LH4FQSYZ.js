import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger
} from "/build/_shared/chunk-5SXLN5D2.js";
import {
  Button
} from "/build/_shared/chunk-MI2YJZX6.js";
import {
  Moon,
  Sun
} from "/build/_shared/chunk-RFPV3BFZ.js";
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

// app/components/layout/theme-provider.tsx
var import_react2 = __toESM(require_react(), 1);

// app/hooks/use-local-storage.ts
var import_react = __toESM(require_react(), 1);
if (import.meta) {
  import.meta.hot = createHotContext(
    //@ts-expect-error
    "app/hooks/use-local-storage.ts"
  );
  import.meta.hot.lastModified = "1738662837903.6753";
}
function useLocalStorage(key, initialValue) {
  const [storedValue, setStoredValue] = (0, import_react.useState)(() => {
    if (typeof window === "undefined") {
      return initialValue;
    }
    try {
      const item = window.localStorage.getItem(key);
      return item ? JSON.parse(item) : initialValue;
    } catch (error) {
      console.log(error);
      return initialValue;
    }
  });
  const setValue = (value) => {
    try {
      const valueToStore = value instanceof Function ? value(storedValue) : value;
      setStoredValue(valueToStore);
      if (typeof window !== "undefined") {
        window.localStorage.setItem(key, JSON.stringify(valueToStore));
      }
    } catch (error) {
      console.log(error);
    }
  };
  return [storedValue, setValue];
}

// app/components/layout/theme-provider.tsx
var import_jsx_dev_runtime = __toESM(require_jsx_dev_runtime(), 1);
if (!window.$RefreshReg$ || !window.$RefreshSig$ || !window.$RefreshRuntime$) {
  console.warn("remix:hmr: React Fast Refresh only works when the Remix compiler is running in development mode.");
} else {
  prevRefreshReg = window.$RefreshReg$;
  prevRefreshSig = window.$RefreshSig$;
  window.$RefreshReg$ = (type, id) => {
    window.$RefreshRuntime$.register(type, '"app/components/layout/theme-provider.tsx"' + id);
  };
  window.$RefreshSig$ = window.$RefreshRuntime$.createSignatureFunctionForTransform;
}
var prevRefreshReg;
var prevRefreshSig;
var _s = $RefreshSig$();
var _s2 = $RefreshSig$();
if (import.meta) {
  import.meta.hot = createHotContext(
    //@ts-expect-error
    "app/components/layout/theme-provider.tsx"
  );
  import.meta.hot.lastModified = "1738670853734.4736";
}
var initialState = {
  theme: "system",
  setTheme: () => null
};
var ThemeProviderContext = (0, import_react2.createContext)(initialState);
function ThemeProvider({
  children,
  defaultTheme = "system"
}) {
  _s();
  const [theme, setTheme] = useLocalStorage("theme", defaultTheme);
  (0, import_react2.useEffect)(() => {
    const root = window.document.documentElement;
    root.classList.remove("light", "dark");
    if (theme === "system") {
      const systemTheme = window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
      root.classList.add(systemTheme);
      return;
    }
    root.classList.add(theme);
  }, [theme]);
  const value = {
    theme,
    setTheme: (theme2) => {
      setTheme(theme2);
    }
  };
  return /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)(ThemeProviderContext.Provider, { value, children }, void 0, false, {
    fileName: "app/components/layout/theme-provider.tsx",
    lineNumber: 53,
    columnNumber: 10
  }, this);
}
_s(ThemeProvider, "YGS+s8CVEWRviNom18nwlIGWkHI=", false, function() {
  return [useLocalStorage];
});
_c = ThemeProvider;
var useTheme = () => {
  _s2();
  const context = (0, import_react2.useContext)(ThemeProviderContext);
  if (context === void 0)
    throw new Error("useTheme must be used within a ThemeProvider");
  return context;
};
_s2(useTheme, "b9L3QQ+jgeyIrH0NfHrJ8nn7VMU=");
var _c;
$RefreshReg$(_c, "ThemeProvider");
window.$RefreshReg$ = prevRefreshReg;
window.$RefreshSig$ = prevRefreshSig;

// app/components/layout/theme-toggle.tsx
var import_jsx_dev_runtime2 = __toESM(require_jsx_dev_runtime(), 1);
if (!window.$RefreshReg$ || !window.$RefreshSig$ || !window.$RefreshRuntime$) {
  console.warn("remix:hmr: React Fast Refresh only works when the Remix compiler is running in development mode.");
} else {
  prevRefreshReg = window.$RefreshReg$;
  prevRefreshSig = window.$RefreshSig$;
  window.$RefreshReg$ = (type, id) => {
    window.$RefreshRuntime$.register(type, '"app/components/layout/theme-toggle.tsx"' + id);
  };
  window.$RefreshSig$ = window.$RefreshRuntime$.createSignatureFunctionForTransform;
}
var prevRefreshReg;
var prevRefreshSig;
var _s3 = $RefreshSig$();
if (import.meta) {
  import.meta.hot = createHotContext(
    //@ts-expect-error
    "app/components/layout/theme-toggle.tsx"
  );
  import.meta.hot.lastModified = "1738670797996.6746";
}
function ThemeToggle() {
  _s3();
  const {
    setTheme
  } = useTheme();
  return /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)(DropdownMenu, { children: [
    /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)(DropdownMenuTrigger, { asChild: true, children: /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)(Button, { variant: "outline", size: "icon", children: [
      /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)(Sun, { className: "h-[1.2rem] w-[1.2rem] rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" }, void 0, false, {
        fileName: "app/components/layout/theme-toggle.tsx",
        lineNumber: 35,
        columnNumber: 11
      }, this),
      /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)(Moon, { className: "absolute h-[1.2rem] w-[1.2rem] rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" }, void 0, false, {
        fileName: "app/components/layout/theme-toggle.tsx",
        lineNumber: 36,
        columnNumber: 11
      }, this),
      /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)("span", { className: "sr-only", children: "Toggle theme" }, void 0, false, {
        fileName: "app/components/layout/theme-toggle.tsx",
        lineNumber: 37,
        columnNumber: 11
      }, this)
    ] }, void 0, true, {
      fileName: "app/components/layout/theme-toggle.tsx",
      lineNumber: 34,
      columnNumber: 9
    }, this) }, void 0, false, {
      fileName: "app/components/layout/theme-toggle.tsx",
      lineNumber: 33,
      columnNumber: 7
    }, this),
    /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)(DropdownMenuContent, { align: "end", children: [
      /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)(DropdownMenuItem, { onClick: () => setTheme("light"), children: "Light" }, void 0, false, {
        fileName: "app/components/layout/theme-toggle.tsx",
        lineNumber: 41,
        columnNumber: 9
      }, this),
      /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)(DropdownMenuItem, { onClick: () => setTheme("dark"), children: "Dark" }, void 0, false, {
        fileName: "app/components/layout/theme-toggle.tsx",
        lineNumber: 44,
        columnNumber: 9
      }, this),
      /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)(DropdownMenuItem, { onClick: () => setTheme("system"), children: "System" }, void 0, false, {
        fileName: "app/components/layout/theme-toggle.tsx",
        lineNumber: 47,
        columnNumber: 9
      }, this)
    ] }, void 0, true, {
      fileName: "app/components/layout/theme-toggle.tsx",
      lineNumber: 40,
      columnNumber: 7
    }, this)
  ] }, void 0, true, {
    fileName: "app/components/layout/theme-toggle.tsx",
    lineNumber: 32,
    columnNumber: 10
  }, this);
}
_s3(ThemeToggle, "a3u8LKbpX4CXbd+e8SJ1SuQ9KPw=", false, function() {
  return [useTheme];
});
_c2 = ThemeToggle;
var _c2;
$RefreshReg$(_c2, "ThemeToggle");
window.$RefreshReg$ = prevRefreshReg;
window.$RefreshSig$ = prevRefreshSig;

export {
  ThemeProvider,
  ThemeToggle
};
//# sourceMappingURL=/build/_shared/chunk-LH4FQSYZ.js.map
