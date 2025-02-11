import {
  Dialog,
  DialogContent
} from "/build/_shared/chunk-MSUXECYF.js";
import "/build/_shared/chunk-RX7TAKA2.js";
import "/build/_shared/chunk-QATI3NSB.js";
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
  ChevronLeft,
  ZoomIn
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
  __commonJS,
  __toESM
} from "/build/_shared/chunk-PZDJHGND.js";

// empty-module:../utils/plantuml.server
var require_plantuml = __commonJS({
  "empty-module:../utils/plantuml.server"(exports, module) {
    module.exports = {};
  }
});

// app/routes/srsdoc.$id.tsx
var React = __toESM(require_react(), 1);
var import_node = __toESM(require_node(), 1);
var import_gray_matter = __toESM(require_gray_matter(), 1);
var import_session = __toESM(require_session(), 1);
var import_plantuml = __toESM(require_plantuml(), 1);
var import_jsx_dev_runtime = __toESM(require_jsx_dev_runtime(), 1);
if (!window.$RefreshReg$ || !window.$RefreshSig$ || !window.$RefreshRuntime$) {
  console.warn("remix:hmr: React Fast Refresh only works when the Remix compiler is running in development mode.");
} else {
  prevRefreshReg = window.$RefreshReg$;
  prevRefreshSig = window.$RefreshSig$;
  window.$RefreshReg$ = (type, id) => {
    window.$RefreshRuntime$.register(type, '"app/routes/srsdoc.$id.tsx"' + id);
  };
  window.$RefreshSig$ = window.$RefreshRuntime$.createSignatureFunctionForTransform;
}
var prevRefreshReg;
var prevRefreshSig;
var _s = $RefreshSig$();
var _s2 = $RefreshSig$();
var _s3 = $RefreshSig$();
var _s4 = $RefreshSig$();
var _s5 = $RefreshSig$();
if (import.meta) {
  import.meta.hot = createHotContext(
    //@ts-expect-error
    "app/routes/srsdoc.$id.tsx"
  );
}
var meta = ({
  data
}) => {
  if (!data?.doc) {
    return [{
      title: "Document Not Found - AI4MDE"
    }, {
      description: "The requested SRS document could not be found."
    }];
  }
  return [{
    title: `${data.doc.data.title} - AI4MDE`
  }, {
    description: data.doc.data.description
  }];
};
function DiagramImage({
  src,
  alt
}) {
  _s();
  const [isOpen, setIsOpen] = React.useState(false);
  return /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)(import_jsx_dev_runtime.Fragment, { children: [
    /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)("div", { onClick: () => setIsOpen(true), className: "relative group cursor-zoom-in", children: [
      /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)("img", { src, alt, className: "max-w-full h-auto my-4 mx-auto rounded-lg shadow-md transition-opacity group-hover:opacity-95", loading: "lazy" }, void 0, false, {
        fileName: "app/routes/srsdoc.$id.tsx",
        lineNumber: 139,
        columnNumber: 9
      }, this),
      /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)("div", { className: "absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity", children: /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)("div", { className: "bg-background/80 p-2 rounded-full", children: /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)(ZoomIn, { className: "w-6 h-6 text-foreground" }, void 0, false, {
        fileName: "app/routes/srsdoc.$id.tsx",
        lineNumber: 143,
        columnNumber: 13
      }, this) }, void 0, false, {
        fileName: "app/routes/srsdoc.$id.tsx",
        lineNumber: 142,
        columnNumber: 11
      }, this) }, void 0, false, {
        fileName: "app/routes/srsdoc.$id.tsx",
        lineNumber: 141,
        columnNumber: 9
      }, this)
    ] }, void 0, true, {
      fileName: "app/routes/srsdoc.$id.tsx",
      lineNumber: 137,
      columnNumber: 7
    }, this),
    /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)(Dialog, { open: isOpen, onOpenChange: setIsOpen, children: /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)(DialogContent, { className: "max-w-[95vw] max-h-[95vh] p-0", children: /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)("div", { className: "w-full h-full overflow-auto p-6", children: /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)("img", { src, alt, className: "w-full h-full object-contain" }, void 0, false, {
      fileName: "app/routes/srsdoc.$id.tsx",
      lineNumber: 151,
      columnNumber: 13
    }, this) }, void 0, false, {
      fileName: "app/routes/srsdoc.$id.tsx",
      lineNumber: 150,
      columnNumber: 11
    }, this) }, void 0, false, {
      fileName: "app/routes/srsdoc.$id.tsx",
      lineNumber: 149,
      columnNumber: 9
    }, this) }, void 0, false, {
      fileName: "app/routes/srsdoc.$id.tsx",
      lineNumber: 148,
      columnNumber: 7
    }, this)
  ] }, void 0, true, {
    fileName: "app/routes/srsdoc.$id.tsx",
    lineNumber: 136,
    columnNumber: 10
  }, this);
}
_s(DiagramImage, "+sus0Lb0ewKHdwiUhiTAJFoFyQ0=");
_c = DiagramImage;
function EnlargeableTable({
  children
}) {
  _s2();
  const [isOpen, setIsOpen] = React.useState(false);
  return /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)(import_jsx_dev_runtime.Fragment, { children: [
    /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)("div", { onClick: () => setIsOpen(true), className: "relative group cursor-zoom-in overflow-auto", children: [
      /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)("div", { className: "my-4", children }, void 0, false, {
        fileName: "app/routes/srsdoc.$id.tsx",
        lineNumber: 170,
        columnNumber: 9
      }, this),
      /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)("div", { className: "absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity", children: /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)("div", { className: "bg-background/80 p-2 rounded-full", children: /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)(ZoomIn, { className: "w-6 h-6 text-foreground" }, void 0, false, {
        fileName: "app/routes/srsdoc.$id.tsx",
        lineNumber: 175,
        columnNumber: 13
      }, this) }, void 0, false, {
        fileName: "app/routes/srsdoc.$id.tsx",
        lineNumber: 174,
        columnNumber: 11
      }, this) }, void 0, false, {
        fileName: "app/routes/srsdoc.$id.tsx",
        lineNumber: 173,
        columnNumber: 9
      }, this)
    ] }, void 0, true, {
      fileName: "app/routes/srsdoc.$id.tsx",
      lineNumber: 168,
      columnNumber: 7
    }, this),
    /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)(Dialog, { open: isOpen, onOpenChange: setIsOpen, children: /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)(DialogContent, { className: "max-w-[95vw] max-h-[95vh] p-0", children: /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)("div", { className: "w-full h-full overflow-auto p-6", children }, void 0, false, {
      fileName: "app/routes/srsdoc.$id.tsx",
      lineNumber: 182,
      columnNumber: 11
    }, this) }, void 0, false, {
      fileName: "app/routes/srsdoc.$id.tsx",
      lineNumber: 181,
      columnNumber: 9
    }, this) }, void 0, false, {
      fileName: "app/routes/srsdoc.$id.tsx",
      lineNumber: 180,
      columnNumber: 7
    }, this)
  ] }, void 0, true, {
    fileName: "app/routes/srsdoc.$id.tsx",
    lineNumber: 167,
    columnNumber: 10
  }, this);
}
_s2(EnlargeableTable, "+sus0Lb0ewKHdwiUhiTAJFoFyQ0=");
_c2 = EnlargeableTable;
function EnlargeableCode({
  language,
  children,
  html
}) {
  _s3();
  const [isOpen, setIsOpen] = React.useState(false);
  return /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)(import_jsx_dev_runtime.Fragment, { children: [
    /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)("div", { onClick: () => setIsOpen(true), className: "relative group cursor-zoom-in", children: [
      /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)("pre", { className: "!p-0 !m-0 !bg-transparent mb-10", children: /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)("code", { className: `block p-4 rounded-lg bg-muted overflow-x-auto ${language ? `hljs language-${language}` : "hljs"}`, dangerouslySetInnerHTML: {
        __html: html
      } }, void 0, false, {
        fileName: "app/routes/srsdoc.$id.tsx",
        lineNumber: 204,
        columnNumber: 11
      }, this) }, void 0, false, {
        fileName: "app/routes/srsdoc.$id.tsx",
        lineNumber: 203,
        columnNumber: 9
      }, this),
      /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)("div", { className: "absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity", children: /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)("div", { className: "bg-background/80 p-2 rounded-full", children: /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)(ZoomIn, { className: "w-6 h-6 text-foreground" }, void 0, false, {
        fileName: "app/routes/srsdoc.$id.tsx",
        lineNumber: 211,
        columnNumber: 13
      }, this) }, void 0, false, {
        fileName: "app/routes/srsdoc.$id.tsx",
        lineNumber: 210,
        columnNumber: 11
      }, this) }, void 0, false, {
        fileName: "app/routes/srsdoc.$id.tsx",
        lineNumber: 209,
        columnNumber: 9
      }, this)
    ] }, void 0, true, {
      fileName: "app/routes/srsdoc.$id.tsx",
      lineNumber: 201,
      columnNumber: 7
    }, this),
    /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)(Dialog, { open: isOpen, onOpenChange: setIsOpen, children: /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)(DialogContent, { className: "max-w-[95vw] max-h-[95vh] p-0", children: /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)("div", { className: "w-full h-full overflow-auto p-6", children: /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)("pre", { className: "!p-0 !m-0 !bg-transparent", children: /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)("code", { className: `block p-4 rounded-lg bg-muted overflow-x-auto ${language ? `hljs language-${language}` : "hljs"}`, dangerouslySetInnerHTML: {
      __html: html
    } }, void 0, false, {
      fileName: "app/routes/srsdoc.$id.tsx",
      lineNumber: 220,
      columnNumber: 15
    }, this) }, void 0, false, {
      fileName: "app/routes/srsdoc.$id.tsx",
      lineNumber: 219,
      columnNumber: 13
    }, this) }, void 0, false, {
      fileName: "app/routes/srsdoc.$id.tsx",
      lineNumber: 218,
      columnNumber: 11
    }, this) }, void 0, false, {
      fileName: "app/routes/srsdoc.$id.tsx",
      lineNumber: 217,
      columnNumber: 9
    }, this) }, void 0, false, {
      fileName: "app/routes/srsdoc.$id.tsx",
      lineNumber: 216,
      columnNumber: 7
    }, this)
  ] }, void 0, true, {
    fileName: "app/routes/srsdoc.$id.tsx",
    lineNumber: 200,
    columnNumber: 10
  }, this);
}
_s3(EnlargeableCode, "+sus0Lb0ewKHdwiUhiTAJFoFyQ0=");
_c3 = EnlargeableCode;
function CodeBlock({
  className = "",
  children
}) {
  _s4();
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
  return /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)(EnlargeableCode, { language, html, children }, void 0, false, {
    fileName: "app/routes/srsdoc.$id.tsx",
    lineNumber: 252,
    columnNumber: 10
  }, this);
}
_s4(CodeBlock, "OtathaP3BKVCXaZtVNvoS+3QIcY=");
_c4 = CodeBlock;
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
    },
    div: {
      component: ({
        "data-diagram": isDiagram,
        "data-url": url,
        ...props
      }) => {
        if (isDiagram && url) {
          return /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)(DiagramImage, { src: url, alt: `Diagram ${isDiagram}` }, void 0, false, {
            fileName: "app/routes/srsdoc.$id.tsx",
            lineNumber: 351,
            columnNumber: 18
          }, this);
        }
        return /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)("div", { ...props }, void 0, false, {
          fileName: "app/routes/srsdoc.$id.tsx",
          lineNumber: 353,
          columnNumber: 16
        }, this);
      }
    },
    "plantuml": {
      component: ({
        children
      }) => /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)("div", { className: "hidden", children }, void 0, false, {
        fileName: "app/routes/srsdoc.$id.tsx",
        lineNumber: 359,
        columnNumber: 13
      }, this)
    },
    table: {
      component: ({
        children
      }) => /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)(EnlargeableTable, { children: /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)("table", { className: "w-full border-collapse border border-border", children }, void 0, false, {
        fileName: "app/routes/srsdoc.$id.tsx",
        lineNumber: 365,
        columnNumber: 11
      }, this) }, void 0, false, {
        fileName: "app/routes/srsdoc.$id.tsx",
        lineNumber: 364,
        columnNumber: 13
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
  _s5();
  const {
    doc
  } = useLoaderData();
  return /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)(MaxWidthWrapper, { className: "py-8", children: [
    /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)("div", { className: "mb-8", children: /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)(Button, { asChild: true, variant: "ghost", size: "sm", children: /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)(Link, { to: "/srsdocs", className: "flex items-center gap-2", children: [
      /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)(ChevronLeft, { className: "h-4 w-4" }, void 0, false, {
        fileName: "app/routes/srsdoc.$id.tsx",
        lineNumber: 391,
        columnNumber: 13
      }, this),
      "Back to Documents"
    ] }, void 0, true, {
      fileName: "app/routes/srsdoc.$id.tsx",
      lineNumber: 390,
      columnNumber: 11
    }, this) }, void 0, false, {
      fileName: "app/routes/srsdoc.$id.tsx",
      lineNumber: 389,
      columnNumber: 9
    }, this) }, void 0, false, {
      fileName: "app/routes/srsdoc.$id.tsx",
      lineNumber: 388,
      columnNumber: 7
    }, this),
    /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)("article", { className: cn("max-w-none", "[&>h1]:text-4xl [&>h1]:font-bold [&>h1]:mb-4", "[&>h2]:text-3xl [&>h2]:font-semibold [&>h2]:mb-3 [&>h2]:mt-8", "[&>h3]:text-2xl [&>h3]:font-semibold [&>h3]:mb-2 [&>h3]:mt-6", "[&>p]:text-muted-foreground [&>p]:mb-4", "[&>ul]:list-disc [&>ul]:ml-6 [&>ul]:mb-4", "[&>ol]:list-decimal [&>ol]:ml-6 [&>ol]:mb-4", "[&>li]:mb-1", "[&>blockquote]:border-l-4 [&>blockquote]:border-primary [&>blockquote]:pl-4 [&>blockquote]:italic [&>blockquote]:my-4", "[&>pre]:bg-muted [&>pre]:p-4 [&>pre]:rounded-lg [&>pre]:mb-4 [&>pre]:overflow-x-auto", "[&>code]:bg-muted [&>code]:px-1.5 [&>code]:py-0.5 [&>code]:rounded"), children: [
      /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)("h1", { className: "text-4xl font-bold mb-4", children: doc.data.title }, void 0, false, {
        fileName: "app/routes/srsdoc.$id.tsx",
        lineNumber: 398,
        columnNumber: 9
      }, this),
      doc.data.date && /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)("p", { className: "text-sm text-muted-foreground mb-8", children: new Date(doc.data.date).toLocaleDateString() }, void 0, false, {
        fileName: "app/routes/srsdoc.$id.tsx",
        lineNumber: 399,
        columnNumber: 27
      }, this),
      /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)(index_modern_default, { options: markdownOptions, children: doc.content }, void 0, false, {
        fileName: "app/routes/srsdoc.$id.tsx",
        lineNumber: 402,
        columnNumber: 9
      }, this)
    ] }, void 0, true, {
      fileName: "app/routes/srsdoc.$id.tsx",
      lineNumber: 397,
      columnNumber: 7
    }, this)
  ] }, void 0, true, {
    fileName: "app/routes/srsdoc.$id.tsx",
    lineNumber: 387,
    columnNumber: 10
  }, this);
}
_s5(SrsDoc, "5mQ0fr+20MRQuz2yTkZ8QV0pUXk=", false, function() {
  return [useLoaderData];
});
_c5 = SrsDoc;
var _c;
var _c2;
var _c3;
var _c4;
var _c5;
$RefreshReg$(_c, "DiagramImage");
$RefreshReg$(_c2, "EnlargeableTable");
$RefreshReg$(_c3, "EnlargeableCode");
$RefreshReg$(_c4, "CodeBlock");
$RefreshReg$(_c5, "SrsDoc");
window.$RefreshReg$ = prevRefreshReg;
window.$RefreshSig$ = prevRefreshSig;
export {
  SrsDoc as default,
  meta
};
//# sourceMappingURL=/build/routes/srsdoc.$id-6VZRP2SA.js.map
