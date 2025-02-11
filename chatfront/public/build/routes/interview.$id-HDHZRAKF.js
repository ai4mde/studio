import {
  es_default
} from "/build/_shared/chunk-455JWECT.js";
import {
  index_modern_default
} from "/build/_shared/chunk-DIGYRLJS.js";
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
import {
  ChevronLeft
} from "/build/_shared/chunk-RFPV3BFZ.js";
import {
  cn
} from "/build/_shared/chunk-3DKJGO2R.js";
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
  __toESM
} from "/build/_shared/chunk-PZDJHGND.js";

// app/routes/interview.$id.tsx
var React = __toESM(require_react(), 1);
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
    window.$RefreshRuntime$.register(type, '"app/routes/interview.$id.tsx"' + id);
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
    "app/routes/interview.$id.tsx"
  );
}
var meta = ({
  data
}) => {
  if (!data?.interview) {
    return [{
      title: "Interview Not Found - AI4MDE"
    }, {
      description: "The requested interview log could not be found."
    }];
  }
  return [{
    title: `${data.interview.data.title} - AI4MDE`
  }, {
    description: data.interview.data.description
  }];
};
function CodeBlock({
  className = "",
  children
}) {
  _s();
  const language = className.replace(/language-/, "");
  const html = React.useMemo(() => {
    if (language && es_default.getLanguage(language)) {
      try {
        return es_default.highlight(children, {
          language
        }).value;
      } catch (err) {
        console.error("Error highlighting code:", err);
      }
    }
    return es_default.highlightAuto(children).value;
  }, [children, language]);
  return /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)("pre", { className: "!p-0 !m-0 !bg-transparent mb-10", children: /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)("code", { className: `block p-4 rounded-lg bg-muted overflow-x-auto ${language ? `hljs language-${language}` : "hljs"}`, dangerouslySetInnerHTML: {
    __html: html
  } }, void 0, false, {
    fileName: "app/routes/interview.$id.tsx",
    lineNumber: 141,
    columnNumber: 7
  }, this) }, void 0, false, {
    fileName: "app/routes/interview.$id.tsx",
    lineNumber: 140,
    columnNumber: 10
  }, this);
}
_s(CodeBlock, "OtathaP3BKVCXaZtVNvoS+3QIcY=");
_c = CodeBlock;
var markdownOptions = {
  options: {
    forceBlock: true,
    forceWrapper: true,
    wrapper: "div",
    disableParsingRawHTML: false,
    escapeHtml: false
  },
  overrides: {
    h1: {
      props: {
        className: "text-3xl font-bold mt-8 mb-4"
      }
    },
    h2: {
      props: {
        className: "text-2xl font-semibold mt-6 mb-3"
      }
    },
    h3: {
      props: {
        className: "text-xl font-semibold mt-4 mb-2"
      }
    },
    h4: {
      props: {
        className: "text-lg font-semibold mt-4 mb-2"
      }
    },
    p: {
      props: {
        className: "text-muted-foreground mb-4"
      }
    },
    ul: {
      props: {
        className: "list-disc list-inside mb-4 ml-4"
      }
    },
    ol: {
      props: {
        className: "list-decimal list-inside mb-4 ml-4"
      }
    },
    li: {
      props: {
        className: "mb-1"
      }
    },
    a: {
      props: {
        className: "text-primary hover:underline"
      }
    },
    blockquote: {
      props: {
        className: "border-l-4 border-primary pl-4 italic my-4"
      }
    },
    code: {
      component: CodeBlock
    },
    pre: {
      component: ({
        children
      }) => children
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
  _s2();
  const {
    interview
  } = useLoaderData();
  return /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)(MaxWidthWrapper, { className: "py-8", children: [
    /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)("div", { className: "mb-8", children: /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)(Button, { asChild: true, variant: "ghost", size: "sm", children: /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)(Link, { to: "/interviews", className: "flex items-center gap-2", children: [
      /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)(ChevronLeft, { className: "h-4 w-4" }, void 0, false, {
        fileName: "app/routes/interview.$id.tsx",
        lineNumber: 233,
        columnNumber: 13
      }, this),
      "Back to Interviews"
    ] }, void 0, true, {
      fileName: "app/routes/interview.$id.tsx",
      lineNumber: 232,
      columnNumber: 11
    }, this) }, void 0, false, {
      fileName: "app/routes/interview.$id.tsx",
      lineNumber: 231,
      columnNumber: 9
    }, this) }, void 0, false, {
      fileName: "app/routes/interview.$id.tsx",
      lineNumber: 230,
      columnNumber: 7
    }, this),
    /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)("article", { className: cn("max-w-none", "[&>h1]:text-4xl [&>h1]:font-bold [&>h1]:mb-4", "[&>h2]:text-3xl [&>h2]:font-semibold [&>h2]:mb-3 [&>h2]:mt-8", "[&>h3]:text-2xl [&>h3]:font-semibold [&>h3]:mb-2 [&>h3]:mt-6", "[&>p]:text-muted-foreground [&>p]:mb-4", "[&>ul]:list-disc [&>ul]:ml-6 [&>ul]:mb-4", "[&>ol]:list-decimal [&>ol]:ml-6 [&>ol]:mb-4", "[&>li]:mb-1", "[&>blockquote]:border-l-4 [&>blockquote]:border-primary [&>blockquote]:pl-4 [&>blockquote]:italic [&>blockquote]:my-4", "[&>pre]:bg-muted [&>pre]:p-4 [&>pre]:rounded-lg [&>pre]:mb-4 [&>pre]:overflow-x-auto", "[&>code]:bg-muted [&>code]:px-1.5 [&>code]:py-0.5 [&>code]:rounded"), children: [
      /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)("h1", { className: "text-4xl font-bold mb-4", children: interview.data.title }, void 0, false, {
        fileName: "app/routes/interview.$id.tsx",
        lineNumber: 240,
        columnNumber: 9
      }, this),
      interview.data.date && /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)("p", { className: "text-sm text-muted-foreground mb-8", children: new Date(interview.data.date).toLocaleDateString() }, void 0, false, {
        fileName: "app/routes/interview.$id.tsx",
        lineNumber: 241,
        columnNumber: 33
      }, this),
      /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)(index_modern_default, { options: markdownOptions, children: interview.content }, void 0, false, {
        fileName: "app/routes/interview.$id.tsx",
        lineNumber: 244,
        columnNumber: 9
      }, this)
    ] }, void 0, true, {
      fileName: "app/routes/interview.$id.tsx",
      lineNumber: 239,
      columnNumber: 7
    }, this)
  ] }, void 0, true, {
    fileName: "app/routes/interview.$id.tsx",
    lineNumber: 229,
    columnNumber: 10
  }, this);
}
_s2(InterviewLog, "WIL9pEnfJT/Tdm1Dj5LvAS9BZuo=", false, function() {
  return [useLoaderData];
});
_c2 = InterviewLog;
var _c;
var _c2;
$RefreshReg$(_c, "CodeBlock");
$RefreshReg$(_c2, "InterviewLog");
window.$RefreshReg$ = prevRefreshReg;
window.$RefreshSig$ = prevRefreshSig;
export {
  InterviewLog as default,
  meta
};
//# sourceMappingURL=/build/routes/interview.$id-HDHZRAKF.js.map
