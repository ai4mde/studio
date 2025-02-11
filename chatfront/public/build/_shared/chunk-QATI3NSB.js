import {
  Slot
} from "/build/_shared/chunk-MI2YJZX6.js";
import {
  require_jsx_runtime
} from "/build/_shared/chunk-2WFCNDEW.js";
import {
  require_react_dom
} from "/build/_shared/chunk-2N23GYW7.js";
import {
  require_react
} from "/build/_shared/chunk-QPVUD6NO.js";
import {
  __toESM
} from "/build/_shared/chunk-PZDJHGND.js";

// node_modules/.pnpm/@radix-ui+react-primitive@2.0.1_@types+react-dom@18.3.5_@types+react@18.3.18__@types+re_d6dca499db6cccec6402cd6217565902/node_modules/@radix-ui/react-primitive/dist/index.mjs
var React = __toESM(require_react(), 1);
var ReactDOM = __toESM(require_react_dom(), 1);
var import_jsx_runtime = __toESM(require_jsx_runtime(), 1);
var NODES = [
  "a",
  "button",
  "div",
  "form",
  "h2",
  "h3",
  "img",
  "input",
  "label",
  "li",
  "nav",
  "ol",
  "p",
  "span",
  "svg",
  "ul"
];
var Primitive = NODES.reduce((primitive, node) => {
  const Node = React.forwardRef((props, forwardedRef) => {
    const { asChild, ...primitiveProps } = props;
    const Comp = asChild ? Slot : node;
    if (typeof window !== "undefined") {
      window[Symbol.for("radix-ui")] = true;
    }
    return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Comp, { ...primitiveProps, ref: forwardedRef });
  });
  Node.displayName = `Primitive.${node}`;
  return { ...primitive, [node]: Node };
}, {});
function dispatchDiscreteCustomEvent(target, event) {
  if (target)
    ReactDOM.flushSync(() => target.dispatchEvent(event));
}

export {
  Primitive,
  dispatchDiscreteCustomEvent
};
//# sourceMappingURL=/build/_shared/chunk-QATI3NSB.js.map
