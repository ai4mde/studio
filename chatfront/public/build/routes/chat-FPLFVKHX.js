import {
  Textarea
} from "/build/_shared/chunk-QBWBT4RY.js";
import {
  Input
} from "/build/_shared/chunk-DTNMODCA.js";
import {
  useUser
} from "/build/_shared/chunk-IVLWEOHB.js";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSub,
  DropdownMenuSubContent,
  DropdownMenuSubTrigger,
  DropdownMenuTrigger,
  useDirection
} from "/build/_shared/chunk-5SXLN5D2.js";
import {
  Card
} from "/build/_shared/chunk-ANELKYHI.js";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle
} from "/build/_shared/chunk-MSUXECYF.js";
import {
  Presence,
  composeEventHandlers,
  createContextScope,
  useCallbackRef,
  useLayoutEffect2
} from "/build/_shared/chunk-RX7TAKA2.js";
import {
  Primitive
} from "/build/_shared/chunk-QATI3NSB.js";
import {
  Button,
  cva,
  useComposedRefs
} from "/build/_shared/chunk-MI2YJZX6.js";
import {
  require_jsx_runtime
} from "/build/_shared/chunk-2WFCNDEW.js";
import {
  require_session
} from "/build/_shared/chunk-IWB4XMPA.js";
import {
  require_node
} from "/build/_shared/chunk-NBEH4DGX.js";
import {
  Form,
  useLoaderData,
  useNavigate
} from "/build/_shared/chunk-5SMQHKI5.js";
import {
  Loader2,
  Menu,
  MessageCircleOff,
  MessageSquarePlus,
  Plus,
  SendHorizontal,
  Trash2
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
  __export,
  __toESM
} from "/build/_shared/chunk-PZDJHGND.js";

// node_modules/.pnpm/is-buffer@2.0.5/node_modules/is-buffer/index.js
var require_is_buffer = __commonJS({
  "node_modules/.pnpm/is-buffer@2.0.5/node_modules/is-buffer/index.js"(exports, module) {
    module.exports = function isBuffer2(obj) {
      return obj != null && obj.constructor != null && typeof obj.constructor.isBuffer === "function" && obj.constructor.isBuffer(obj);
    };
  }
});

// node_modules/.pnpm/extend@3.0.2/node_modules/extend/index.js
var require_extend = __commonJS({
  "node_modules/.pnpm/extend@3.0.2/node_modules/extend/index.js"(exports, module) {
    "use strict";
    var hasOwn = Object.prototype.hasOwnProperty;
    var toStr = Object.prototype.toString;
    var defineProperty = Object.defineProperty;
    var gOPD = Object.getOwnPropertyDescriptor;
    var isArray = function isArray2(arr) {
      if (typeof Array.isArray === "function") {
        return Array.isArray(arr);
      }
      return toStr.call(arr) === "[object Array]";
    };
    var isPlainObject2 = function isPlainObject3(obj) {
      if (!obj || toStr.call(obj) !== "[object Object]") {
        return false;
      }
      var hasOwnConstructor = hasOwn.call(obj, "constructor");
      var hasIsPrototypeOf = obj.constructor && obj.constructor.prototype && hasOwn.call(obj.constructor.prototype, "isPrototypeOf");
      if (obj.constructor && !hasOwnConstructor && !hasIsPrototypeOf) {
        return false;
      }
      var key;
      for (key in obj) {
      }
      return typeof key === "undefined" || hasOwn.call(obj, key);
    };
    var setProperty = function setProperty2(target, options) {
      if (defineProperty && options.name === "__proto__") {
        defineProperty(target, options.name, {
          enumerable: true,
          configurable: true,
          value: options.newValue,
          writable: true
        });
      } else {
        target[options.name] = options.newValue;
      }
    };
    var getProperty = function getProperty2(obj, name) {
      if (name === "__proto__") {
        if (!hasOwn.call(obj, name)) {
          return void 0;
        } else if (gOPD) {
          return gOPD(obj, name).value;
        }
      }
      return obj[name];
    };
    module.exports = function extend2() {
      var options, name, src, copy, copyIsArray, clone;
      var target = arguments[0];
      var i = 1;
      var length = arguments.length;
      var deep = false;
      if (typeof target === "boolean") {
        deep = target;
        target = arguments[1] || {};
        i = 2;
      }
      if (target == null || typeof target !== "object" && typeof target !== "function") {
        target = {};
      }
      for (; i < length; ++i) {
        options = arguments[i];
        if (options != null) {
          for (name in options) {
            src = getProperty(target, name);
            copy = getProperty(options, name);
            if (target !== copy) {
              if (deep && copy && (isPlainObject2(copy) || (copyIsArray = isArray(copy)))) {
                if (copyIsArray) {
                  copyIsArray = false;
                  clone = src && isArray(src) ? src : [];
                } else {
                  clone = src && isPlainObject2(src) ? src : {};
                }
                setProperty(target, { name, newValue: extend2(deep, clone, copy) });
              } else if (typeof copy !== "undefined") {
                setProperty(target, { name, newValue: copy });
              }
            }
          }
        }
      }
      return target;
    };
  }
});

// node_modules/.pnpm/react-is@16.13.1/node_modules/react-is/cjs/react-is.development.js
var require_react_is_development = __commonJS({
  "node_modules/.pnpm/react-is@16.13.1/node_modules/react-is/cjs/react-is.development.js"(exports) {
    "use strict";
    if (true) {
      (function() {
        "use strict";
        var hasSymbol = typeof Symbol === "function" && Symbol.for;
        var REACT_ELEMENT_TYPE = hasSymbol ? Symbol.for("react.element") : 60103;
        var REACT_PORTAL_TYPE = hasSymbol ? Symbol.for("react.portal") : 60106;
        var REACT_FRAGMENT_TYPE = hasSymbol ? Symbol.for("react.fragment") : 60107;
        var REACT_STRICT_MODE_TYPE = hasSymbol ? Symbol.for("react.strict_mode") : 60108;
        var REACT_PROFILER_TYPE = hasSymbol ? Symbol.for("react.profiler") : 60114;
        var REACT_PROVIDER_TYPE = hasSymbol ? Symbol.for("react.provider") : 60109;
        var REACT_CONTEXT_TYPE = hasSymbol ? Symbol.for("react.context") : 60110;
        var REACT_ASYNC_MODE_TYPE = hasSymbol ? Symbol.for("react.async_mode") : 60111;
        var REACT_CONCURRENT_MODE_TYPE = hasSymbol ? Symbol.for("react.concurrent_mode") : 60111;
        var REACT_FORWARD_REF_TYPE = hasSymbol ? Symbol.for("react.forward_ref") : 60112;
        var REACT_SUSPENSE_TYPE = hasSymbol ? Symbol.for("react.suspense") : 60113;
        var REACT_SUSPENSE_LIST_TYPE = hasSymbol ? Symbol.for("react.suspense_list") : 60120;
        var REACT_MEMO_TYPE = hasSymbol ? Symbol.for("react.memo") : 60115;
        var REACT_LAZY_TYPE = hasSymbol ? Symbol.for("react.lazy") : 60116;
        var REACT_BLOCK_TYPE = hasSymbol ? Symbol.for("react.block") : 60121;
        var REACT_FUNDAMENTAL_TYPE = hasSymbol ? Symbol.for("react.fundamental") : 60117;
        var REACT_RESPONDER_TYPE = hasSymbol ? Symbol.for("react.responder") : 60118;
        var REACT_SCOPE_TYPE = hasSymbol ? Symbol.for("react.scope") : 60119;
        function isValidElementType(type) {
          return typeof type === "string" || typeof type === "function" || // Note: its typeof might be other than 'symbol' or 'number' if it's a polyfill.
          type === REACT_FRAGMENT_TYPE || type === REACT_CONCURRENT_MODE_TYPE || type === REACT_PROFILER_TYPE || type === REACT_STRICT_MODE_TYPE || type === REACT_SUSPENSE_TYPE || type === REACT_SUSPENSE_LIST_TYPE || typeof type === "object" && type !== null && (type.$$typeof === REACT_LAZY_TYPE || type.$$typeof === REACT_MEMO_TYPE || type.$$typeof === REACT_PROVIDER_TYPE || type.$$typeof === REACT_CONTEXT_TYPE || type.$$typeof === REACT_FORWARD_REF_TYPE || type.$$typeof === REACT_FUNDAMENTAL_TYPE || type.$$typeof === REACT_RESPONDER_TYPE || type.$$typeof === REACT_SCOPE_TYPE || type.$$typeof === REACT_BLOCK_TYPE);
        }
        function typeOf(object) {
          if (typeof object === "object" && object !== null) {
            var $$typeof = object.$$typeof;
            switch ($$typeof) {
              case REACT_ELEMENT_TYPE:
                var type = object.type;
                switch (type) {
                  case REACT_ASYNC_MODE_TYPE:
                  case REACT_CONCURRENT_MODE_TYPE:
                  case REACT_FRAGMENT_TYPE:
                  case REACT_PROFILER_TYPE:
                  case REACT_STRICT_MODE_TYPE:
                  case REACT_SUSPENSE_TYPE:
                    return type;
                  default:
                    var $$typeofType = type && type.$$typeof;
                    switch ($$typeofType) {
                      case REACT_CONTEXT_TYPE:
                      case REACT_FORWARD_REF_TYPE:
                      case REACT_LAZY_TYPE:
                      case REACT_MEMO_TYPE:
                      case REACT_PROVIDER_TYPE:
                        return $$typeofType;
                      default:
                        return $$typeof;
                    }
                }
              case REACT_PORTAL_TYPE:
                return $$typeof;
            }
          }
          return void 0;
        }
        var AsyncMode = REACT_ASYNC_MODE_TYPE;
        var ConcurrentMode = REACT_CONCURRENT_MODE_TYPE;
        var ContextConsumer = REACT_CONTEXT_TYPE;
        var ContextProvider = REACT_PROVIDER_TYPE;
        var Element = REACT_ELEMENT_TYPE;
        var ForwardRef = REACT_FORWARD_REF_TYPE;
        var Fragment3 = REACT_FRAGMENT_TYPE;
        var Lazy = REACT_LAZY_TYPE;
        var Memo = REACT_MEMO_TYPE;
        var Portal = REACT_PORTAL_TYPE;
        var Profiler = REACT_PROFILER_TYPE;
        var StrictMode = REACT_STRICT_MODE_TYPE;
        var Suspense = REACT_SUSPENSE_TYPE;
        var hasWarnedAboutDeprecatedIsAsyncMode = false;
        function isAsyncMode(object) {
          {
            if (!hasWarnedAboutDeprecatedIsAsyncMode) {
              hasWarnedAboutDeprecatedIsAsyncMode = true;
              console["warn"]("The ReactIs.isAsyncMode() alias has been deprecated, and will be removed in React 17+. Update your code to use ReactIs.isConcurrentMode() instead. It has the exact same API.");
            }
          }
          return isConcurrentMode(object) || typeOf(object) === REACT_ASYNC_MODE_TYPE;
        }
        function isConcurrentMode(object) {
          return typeOf(object) === REACT_CONCURRENT_MODE_TYPE;
        }
        function isContextConsumer(object) {
          return typeOf(object) === REACT_CONTEXT_TYPE;
        }
        function isContextProvider(object) {
          return typeOf(object) === REACT_PROVIDER_TYPE;
        }
        function isElement(object) {
          return typeof object === "object" && object !== null && object.$$typeof === REACT_ELEMENT_TYPE;
        }
        function isForwardRef(object) {
          return typeOf(object) === REACT_FORWARD_REF_TYPE;
        }
        function isFragment(object) {
          return typeOf(object) === REACT_FRAGMENT_TYPE;
        }
        function isLazy(object) {
          return typeOf(object) === REACT_LAZY_TYPE;
        }
        function isMemo(object) {
          return typeOf(object) === REACT_MEMO_TYPE;
        }
        function isPortal(object) {
          return typeOf(object) === REACT_PORTAL_TYPE;
        }
        function isProfiler(object) {
          return typeOf(object) === REACT_PROFILER_TYPE;
        }
        function isStrictMode(object) {
          return typeOf(object) === REACT_STRICT_MODE_TYPE;
        }
        function isSuspense(object) {
          return typeOf(object) === REACT_SUSPENSE_TYPE;
        }
        exports.AsyncMode = AsyncMode;
        exports.ConcurrentMode = ConcurrentMode;
        exports.ContextConsumer = ContextConsumer;
        exports.ContextProvider = ContextProvider;
        exports.Element = Element;
        exports.ForwardRef = ForwardRef;
        exports.Fragment = Fragment3;
        exports.Lazy = Lazy;
        exports.Memo = Memo;
        exports.Portal = Portal;
        exports.Profiler = Profiler;
        exports.StrictMode = StrictMode;
        exports.Suspense = Suspense;
        exports.isAsyncMode = isAsyncMode;
        exports.isConcurrentMode = isConcurrentMode;
        exports.isContextConsumer = isContextConsumer;
        exports.isContextProvider = isContextProvider;
        exports.isElement = isElement;
        exports.isForwardRef = isForwardRef;
        exports.isFragment = isFragment;
        exports.isLazy = isLazy;
        exports.isMemo = isMemo;
        exports.isPortal = isPortal;
        exports.isProfiler = isProfiler;
        exports.isStrictMode = isStrictMode;
        exports.isSuspense = isSuspense;
        exports.isValidElementType = isValidElementType;
        exports.typeOf = typeOf;
      })();
    }
  }
});

// node_modules/.pnpm/react-is@16.13.1/node_modules/react-is/index.js
var require_react_is = __commonJS({
  "node_modules/.pnpm/react-is@16.13.1/node_modules/react-is/index.js"(exports, module) {
    "use strict";
    if (false) {
      module.exports = null;
    } else {
      module.exports = require_react_is_development();
    }
  }
});

// node_modules/.pnpm/object-assign@4.1.1/node_modules/object-assign/index.js
var require_object_assign = __commonJS({
  "node_modules/.pnpm/object-assign@4.1.1/node_modules/object-assign/index.js"(exports, module) {
    "use strict";
    var getOwnPropertySymbols = Object.getOwnPropertySymbols;
    var hasOwnProperty3 = Object.prototype.hasOwnProperty;
    var propIsEnumerable = Object.prototype.propertyIsEnumerable;
    function toObject(val) {
      if (val === null || val === void 0) {
        throw new TypeError("Object.assign cannot be called with null or undefined");
      }
      return Object(val);
    }
    function shouldUseNative() {
      try {
        if (!Object.assign) {
          return false;
        }
        var test1 = new String("abc");
        test1[5] = "de";
        if (Object.getOwnPropertyNames(test1)[0] === "5") {
          return false;
        }
        var test2 = {};
        for (var i = 0; i < 10; i++) {
          test2["_" + String.fromCharCode(i)] = i;
        }
        var order2 = Object.getOwnPropertyNames(test2).map(function(n) {
          return test2[n];
        });
        if (order2.join("") !== "0123456789") {
          return false;
        }
        var test3 = {};
        "abcdefghijklmnopqrst".split("").forEach(function(letter) {
          test3[letter] = letter;
        });
        if (Object.keys(Object.assign({}, test3)).join("") !== "abcdefghijklmnopqrst") {
          return false;
        }
        return true;
      } catch (err) {
        return false;
      }
    }
    module.exports = shouldUseNative() ? Object.assign : function(target, source) {
      var from;
      var to = toObject(target);
      var symbols;
      for (var s = 1; s < arguments.length; s++) {
        from = Object(arguments[s]);
        for (var key in from) {
          if (hasOwnProperty3.call(from, key)) {
            to[key] = from[key];
          }
        }
        if (getOwnPropertySymbols) {
          symbols = getOwnPropertySymbols(from);
          for (var i = 0; i < symbols.length; i++) {
            if (propIsEnumerable.call(from, symbols[i])) {
              to[symbols[i]] = from[symbols[i]];
            }
          }
        }
      }
      return to;
    };
  }
});

// node_modules/.pnpm/prop-types@15.8.1/node_modules/prop-types/lib/ReactPropTypesSecret.js
var require_ReactPropTypesSecret = __commonJS({
  "node_modules/.pnpm/prop-types@15.8.1/node_modules/prop-types/lib/ReactPropTypesSecret.js"(exports, module) {
    "use strict";
    var ReactPropTypesSecret = "SECRET_DO_NOT_PASS_THIS_OR_YOU_WILL_BE_FIRED";
    module.exports = ReactPropTypesSecret;
  }
});

// node_modules/.pnpm/prop-types@15.8.1/node_modules/prop-types/lib/has.js
var require_has = __commonJS({
  "node_modules/.pnpm/prop-types@15.8.1/node_modules/prop-types/lib/has.js"(exports, module) {
    module.exports = Function.call.bind(Object.prototype.hasOwnProperty);
  }
});

// node_modules/.pnpm/prop-types@15.8.1/node_modules/prop-types/checkPropTypes.js
var require_checkPropTypes = __commonJS({
  "node_modules/.pnpm/prop-types@15.8.1/node_modules/prop-types/checkPropTypes.js"(exports, module) {
    "use strict";
    var printWarning = function() {
    };
    if (true) {
      ReactPropTypesSecret = require_ReactPropTypesSecret();
      loggedTypeFailures = {};
      has = require_has();
      printWarning = function(text6) {
        var message = "Warning: " + text6;
        if (typeof console !== "undefined") {
          console.error(message);
        }
        try {
          throw new Error(message);
        } catch (x) {
        }
      };
    }
    var ReactPropTypesSecret;
    var loggedTypeFailures;
    var has;
    function checkPropTypes(typeSpecs, values, location, componentName, getStack) {
      if (true) {
        for (var typeSpecName in typeSpecs) {
          if (has(typeSpecs, typeSpecName)) {
            var error;
            try {
              if (typeof typeSpecs[typeSpecName] !== "function") {
                var err = Error(
                  (componentName || "React class") + ": " + location + " type `" + typeSpecName + "` is invalid; it must be a function, usually from the `prop-types` package, but received `" + typeof typeSpecs[typeSpecName] + "`.This often happens because of typos such as `PropTypes.function` instead of `PropTypes.func`."
                );
                err.name = "Invariant Violation";
                throw err;
              }
              error = typeSpecs[typeSpecName](values, typeSpecName, componentName, location, null, ReactPropTypesSecret);
            } catch (ex) {
              error = ex;
            }
            if (error && !(error instanceof Error)) {
              printWarning(
                (componentName || "React class") + ": type specification of " + location + " `" + typeSpecName + "` is invalid; the type checker function must return `null` or an `Error` but returned a " + typeof error + ". You may have forgotten to pass an argument to the type checker creator (arrayOf, instanceOf, objectOf, oneOf, oneOfType, and shape all require an argument)."
              );
            }
            if (error instanceof Error && !(error.message in loggedTypeFailures)) {
              loggedTypeFailures[error.message] = true;
              var stack = getStack ? getStack() : "";
              printWarning(
                "Failed " + location + " type: " + error.message + (stack != null ? stack : "")
              );
            }
          }
        }
      }
    }
    checkPropTypes.resetWarningCache = function() {
      if (true) {
        loggedTypeFailures = {};
      }
    };
    module.exports = checkPropTypes;
  }
});

// node_modules/.pnpm/prop-types@15.8.1/node_modules/prop-types/factoryWithTypeCheckers.js
var require_factoryWithTypeCheckers = __commonJS({
  "node_modules/.pnpm/prop-types@15.8.1/node_modules/prop-types/factoryWithTypeCheckers.js"(exports, module) {
    "use strict";
    var ReactIs2 = require_react_is();
    var assign = require_object_assign();
    var ReactPropTypesSecret = require_ReactPropTypesSecret();
    var has = require_has();
    var checkPropTypes = require_checkPropTypes();
    var printWarning = function() {
    };
    if (true) {
      printWarning = function(text6) {
        var message = "Warning: " + text6;
        if (typeof console !== "undefined") {
          console.error(message);
        }
        try {
          throw new Error(message);
        } catch (x) {
        }
      };
    }
    function emptyFunctionThatReturnsNull() {
      return null;
    }
    module.exports = function(isValidElement, throwOnDirectAccess) {
      var ITERATOR_SYMBOL = typeof Symbol === "function" && Symbol.iterator;
      var FAUX_ITERATOR_SYMBOL = "@@iterator";
      function getIteratorFn(maybeIterable) {
        var iteratorFn = maybeIterable && (ITERATOR_SYMBOL && maybeIterable[ITERATOR_SYMBOL] || maybeIterable[FAUX_ITERATOR_SYMBOL]);
        if (typeof iteratorFn === "function") {
          return iteratorFn;
        }
      }
      var ANONYMOUS = "<<anonymous>>";
      var ReactPropTypes = {
        array: createPrimitiveTypeChecker("array"),
        bigint: createPrimitiveTypeChecker("bigint"),
        bool: createPrimitiveTypeChecker("boolean"),
        func: createPrimitiveTypeChecker("function"),
        number: createPrimitiveTypeChecker("number"),
        object: createPrimitiveTypeChecker("object"),
        string: createPrimitiveTypeChecker("string"),
        symbol: createPrimitiveTypeChecker("symbol"),
        any: createAnyTypeChecker(),
        arrayOf: createArrayOfTypeChecker,
        element: createElementTypeChecker(),
        elementType: createElementTypeTypeChecker(),
        instanceOf: createInstanceTypeChecker,
        node: createNodeChecker(),
        objectOf: createObjectOfTypeChecker,
        oneOf: createEnumTypeChecker,
        oneOfType: createUnionTypeChecker,
        shape: createShapeTypeChecker,
        exact: createStrictShapeTypeChecker
      };
      function is3(x, y) {
        if (x === y) {
          return x !== 0 || 1 / x === 1 / y;
        } else {
          return x !== x && y !== y;
        }
      }
      function PropTypeError(message, data) {
        this.message = message;
        this.data = data && typeof data === "object" ? data : {};
        this.stack = "";
      }
      PropTypeError.prototype = Error.prototype;
      function createChainableTypeChecker(validate) {
        if (true) {
          var manualPropTypeCallCache = {};
          var manualPropTypeWarningCount = 0;
        }
        function checkType(isRequired, props, propName, componentName, location, propFullName, secret) {
          componentName = componentName || ANONYMOUS;
          propFullName = propFullName || propName;
          if (secret !== ReactPropTypesSecret) {
            if (throwOnDirectAccess) {
              var err = new Error(
                "Calling PropTypes validators directly is not supported by the `prop-types` package. Use `PropTypes.checkPropTypes()` to call them. Read more at http://fb.me/use-check-prop-types"
              );
              err.name = "Invariant Violation";
              throw err;
            } else if (typeof console !== "undefined") {
              var cacheKey = componentName + ":" + propName;
              if (!manualPropTypeCallCache[cacheKey] && // Avoid spamming the console because they are often not actionable except for lib authors
              manualPropTypeWarningCount < 3) {
                printWarning(
                  "You are manually calling a React.PropTypes validation function for the `" + propFullName + "` prop on `" + componentName + "`. This is deprecated and will throw in the standalone `prop-types` package. You may be seeing this warning due to a third-party PropTypes library. See https://fb.me/react-warning-dont-call-proptypes for details."
                );
                manualPropTypeCallCache[cacheKey] = true;
                manualPropTypeWarningCount++;
              }
            }
          }
          if (props[propName] == null) {
            if (isRequired) {
              if (props[propName] === null) {
                return new PropTypeError("The " + location + " `" + propFullName + "` is marked as required " + ("in `" + componentName + "`, but its value is `null`."));
              }
              return new PropTypeError("The " + location + " `" + propFullName + "` is marked as required in " + ("`" + componentName + "`, but its value is `undefined`."));
            }
            return null;
          } else {
            return validate(props, propName, componentName, location, propFullName);
          }
        }
        var chainedCheckType = checkType.bind(null, false);
        chainedCheckType.isRequired = checkType.bind(null, true);
        return chainedCheckType;
      }
      function createPrimitiveTypeChecker(expectedType) {
        function validate(props, propName, componentName, location, propFullName, secret) {
          var propValue = props[propName];
          var propType = getPropType(propValue);
          if (propType !== expectedType) {
            var preciseType = getPreciseType(propValue);
            return new PropTypeError(
              "Invalid " + location + " `" + propFullName + "` of type " + ("`" + preciseType + "` supplied to `" + componentName + "`, expected ") + ("`" + expectedType + "`."),
              { expectedType }
            );
          }
          return null;
        }
        return createChainableTypeChecker(validate);
      }
      function createAnyTypeChecker() {
        return createChainableTypeChecker(emptyFunctionThatReturnsNull);
      }
      function createArrayOfTypeChecker(typeChecker) {
        function validate(props, propName, componentName, location, propFullName) {
          if (typeof typeChecker !== "function") {
            return new PropTypeError("Property `" + propFullName + "` of component `" + componentName + "` has invalid PropType notation inside arrayOf.");
          }
          var propValue = props[propName];
          if (!Array.isArray(propValue)) {
            var propType = getPropType(propValue);
            return new PropTypeError("Invalid " + location + " `" + propFullName + "` of type " + ("`" + propType + "` supplied to `" + componentName + "`, expected an array."));
          }
          for (var i = 0; i < propValue.length; i++) {
            var error = typeChecker(propValue, i, componentName, location, propFullName + "[" + i + "]", ReactPropTypesSecret);
            if (error instanceof Error) {
              return error;
            }
          }
          return null;
        }
        return createChainableTypeChecker(validate);
      }
      function createElementTypeChecker() {
        function validate(props, propName, componentName, location, propFullName) {
          var propValue = props[propName];
          if (!isValidElement(propValue)) {
            var propType = getPropType(propValue);
            return new PropTypeError("Invalid " + location + " `" + propFullName + "` of type " + ("`" + propType + "` supplied to `" + componentName + "`, expected a single ReactElement."));
          }
          return null;
        }
        return createChainableTypeChecker(validate);
      }
      function createElementTypeTypeChecker() {
        function validate(props, propName, componentName, location, propFullName) {
          var propValue = props[propName];
          if (!ReactIs2.isValidElementType(propValue)) {
            var propType = getPropType(propValue);
            return new PropTypeError("Invalid " + location + " `" + propFullName + "` of type " + ("`" + propType + "` supplied to `" + componentName + "`, expected a single ReactElement type."));
          }
          return null;
        }
        return createChainableTypeChecker(validate);
      }
      function createInstanceTypeChecker(expectedClass) {
        function validate(props, propName, componentName, location, propFullName) {
          if (!(props[propName] instanceof expectedClass)) {
            var expectedClassName = expectedClass.name || ANONYMOUS;
            var actualClassName = getClassName(props[propName]);
            return new PropTypeError("Invalid " + location + " `" + propFullName + "` of type " + ("`" + actualClassName + "` supplied to `" + componentName + "`, expected ") + ("instance of `" + expectedClassName + "`."));
          }
          return null;
        }
        return createChainableTypeChecker(validate);
      }
      function createEnumTypeChecker(expectedValues) {
        if (!Array.isArray(expectedValues)) {
          if (true) {
            if (arguments.length > 1) {
              printWarning(
                "Invalid arguments supplied to oneOf, expected an array, got " + arguments.length + " arguments. A common mistake is to write oneOf(x, y, z) instead of oneOf([x, y, z])."
              );
            } else {
              printWarning("Invalid argument supplied to oneOf, expected an array.");
            }
          }
          return emptyFunctionThatReturnsNull;
        }
        function validate(props, propName, componentName, location, propFullName) {
          var propValue = props[propName];
          for (var i = 0; i < expectedValues.length; i++) {
            if (is3(propValue, expectedValues[i])) {
              return null;
            }
          }
          var valuesString = JSON.stringify(expectedValues, function replacer(key, value) {
            var type = getPreciseType(value);
            if (type === "symbol") {
              return String(value);
            }
            return value;
          });
          return new PropTypeError("Invalid " + location + " `" + propFullName + "` of value `" + String(propValue) + "` " + ("supplied to `" + componentName + "`, expected one of " + valuesString + "."));
        }
        return createChainableTypeChecker(validate);
      }
      function createObjectOfTypeChecker(typeChecker) {
        function validate(props, propName, componentName, location, propFullName) {
          if (typeof typeChecker !== "function") {
            return new PropTypeError("Property `" + propFullName + "` of component `" + componentName + "` has invalid PropType notation inside objectOf.");
          }
          var propValue = props[propName];
          var propType = getPropType(propValue);
          if (propType !== "object") {
            return new PropTypeError("Invalid " + location + " `" + propFullName + "` of type " + ("`" + propType + "` supplied to `" + componentName + "`, expected an object."));
          }
          for (var key in propValue) {
            if (has(propValue, key)) {
              var error = typeChecker(propValue, key, componentName, location, propFullName + "." + key, ReactPropTypesSecret);
              if (error instanceof Error) {
                return error;
              }
            }
          }
          return null;
        }
        return createChainableTypeChecker(validate);
      }
      function createUnionTypeChecker(arrayOfTypeCheckers) {
        if (!Array.isArray(arrayOfTypeCheckers)) {
          true ? printWarning("Invalid argument supplied to oneOfType, expected an instance of array.") : void 0;
          return emptyFunctionThatReturnsNull;
        }
        for (var i = 0; i < arrayOfTypeCheckers.length; i++) {
          var checker = arrayOfTypeCheckers[i];
          if (typeof checker !== "function") {
            printWarning(
              "Invalid argument supplied to oneOfType. Expected an array of check functions, but received " + getPostfixForTypeWarning(checker) + " at index " + i + "."
            );
            return emptyFunctionThatReturnsNull;
          }
        }
        function validate(props, propName, componentName, location, propFullName) {
          var expectedTypes = [];
          for (var i2 = 0; i2 < arrayOfTypeCheckers.length; i2++) {
            var checker2 = arrayOfTypeCheckers[i2];
            var checkerResult = checker2(props, propName, componentName, location, propFullName, ReactPropTypesSecret);
            if (checkerResult == null) {
              return null;
            }
            if (checkerResult.data && has(checkerResult.data, "expectedType")) {
              expectedTypes.push(checkerResult.data.expectedType);
            }
          }
          var expectedTypesMessage = expectedTypes.length > 0 ? ", expected one of type [" + expectedTypes.join(", ") + "]" : "";
          return new PropTypeError("Invalid " + location + " `" + propFullName + "` supplied to " + ("`" + componentName + "`" + expectedTypesMessage + "."));
        }
        return createChainableTypeChecker(validate);
      }
      function createNodeChecker() {
        function validate(props, propName, componentName, location, propFullName) {
          if (!isNode(props[propName])) {
            return new PropTypeError("Invalid " + location + " `" + propFullName + "` supplied to " + ("`" + componentName + "`, expected a ReactNode."));
          }
          return null;
        }
        return createChainableTypeChecker(validate);
      }
      function invalidValidatorError(componentName, location, propFullName, key, type) {
        return new PropTypeError(
          (componentName || "React class") + ": " + location + " type `" + propFullName + "." + key + "` is invalid; it must be a function, usually from the `prop-types` package, but received `" + type + "`."
        );
      }
      function createShapeTypeChecker(shapeTypes) {
        function validate(props, propName, componentName, location, propFullName) {
          var propValue = props[propName];
          var propType = getPropType(propValue);
          if (propType !== "object") {
            return new PropTypeError("Invalid " + location + " `" + propFullName + "` of type `" + propType + "` " + ("supplied to `" + componentName + "`, expected `object`."));
          }
          for (var key in shapeTypes) {
            var checker = shapeTypes[key];
            if (typeof checker !== "function") {
              return invalidValidatorError(componentName, location, propFullName, key, getPreciseType(checker));
            }
            var error = checker(propValue, key, componentName, location, propFullName + "." + key, ReactPropTypesSecret);
            if (error) {
              return error;
            }
          }
          return null;
        }
        return createChainableTypeChecker(validate);
      }
      function createStrictShapeTypeChecker(shapeTypes) {
        function validate(props, propName, componentName, location, propFullName) {
          var propValue = props[propName];
          var propType = getPropType(propValue);
          if (propType !== "object") {
            return new PropTypeError("Invalid " + location + " `" + propFullName + "` of type `" + propType + "` " + ("supplied to `" + componentName + "`, expected `object`."));
          }
          var allKeys = assign({}, props[propName], shapeTypes);
          for (var key in allKeys) {
            var checker = shapeTypes[key];
            if (has(shapeTypes, key) && typeof checker !== "function") {
              return invalidValidatorError(componentName, location, propFullName, key, getPreciseType(checker));
            }
            if (!checker) {
              return new PropTypeError(
                "Invalid " + location + " `" + propFullName + "` key `" + key + "` supplied to `" + componentName + "`.\nBad object: " + JSON.stringify(props[propName], null, "  ") + "\nValid keys: " + JSON.stringify(Object.keys(shapeTypes), null, "  ")
              );
            }
            var error = checker(propValue, key, componentName, location, propFullName + "." + key, ReactPropTypesSecret);
            if (error) {
              return error;
            }
          }
          return null;
        }
        return createChainableTypeChecker(validate);
      }
      function isNode(propValue) {
        switch (typeof propValue) {
          case "number":
          case "string":
          case "undefined":
            return true;
          case "boolean":
            return !propValue;
          case "object":
            if (Array.isArray(propValue)) {
              return propValue.every(isNode);
            }
            if (propValue === null || isValidElement(propValue)) {
              return true;
            }
            var iteratorFn = getIteratorFn(propValue);
            if (iteratorFn) {
              var iterator = iteratorFn.call(propValue);
              var step;
              if (iteratorFn !== propValue.entries) {
                while (!(step = iterator.next()).done) {
                  if (!isNode(step.value)) {
                    return false;
                  }
                }
              } else {
                while (!(step = iterator.next()).done) {
                  var entry = step.value;
                  if (entry) {
                    if (!isNode(entry[1])) {
                      return false;
                    }
                  }
                }
              }
            } else {
              return false;
            }
            return true;
          default:
            return false;
        }
      }
      function isSymbol(propType, propValue) {
        if (propType === "symbol") {
          return true;
        }
        if (!propValue) {
          return false;
        }
        if (propValue["@@toStringTag"] === "Symbol") {
          return true;
        }
        if (typeof Symbol === "function" && propValue instanceof Symbol) {
          return true;
        }
        return false;
      }
      function getPropType(propValue) {
        var propType = typeof propValue;
        if (Array.isArray(propValue)) {
          return "array";
        }
        if (propValue instanceof RegExp) {
          return "object";
        }
        if (isSymbol(propType, propValue)) {
          return "symbol";
        }
        return propType;
      }
      function getPreciseType(propValue) {
        if (typeof propValue === "undefined" || propValue === null) {
          return "" + propValue;
        }
        var propType = getPropType(propValue);
        if (propType === "object") {
          if (propValue instanceof Date) {
            return "date";
          } else if (propValue instanceof RegExp) {
            return "regexp";
          }
        }
        return propType;
      }
      function getPostfixForTypeWarning(value) {
        var type = getPreciseType(value);
        switch (type) {
          case "array":
          case "object":
            return "an " + type;
          case "boolean":
          case "date":
          case "regexp":
            return "a " + type;
          default:
            return type;
        }
      }
      function getClassName(propValue) {
        if (!propValue.constructor || !propValue.constructor.name) {
          return ANONYMOUS;
        }
        return propValue.constructor.name;
      }
      ReactPropTypes.checkPropTypes = checkPropTypes;
      ReactPropTypes.resetWarningCache = checkPropTypes.resetWarningCache;
      ReactPropTypes.PropTypes = ReactPropTypes;
      return ReactPropTypes;
    };
  }
});

// node_modules/.pnpm/prop-types@15.8.1/node_modules/prop-types/index.js
var require_prop_types = __commonJS({
  "node_modules/.pnpm/prop-types@15.8.1/node_modules/prop-types/index.js"(exports, module) {
    if (true) {
      ReactIs2 = require_react_is();
      throwOnDirectAccess = true;
      module.exports = require_factoryWithTypeCheckers()(ReactIs2.isElement, throwOnDirectAccess);
    } else {
      module.exports = null();
    }
    var ReactIs2;
    var throwOnDirectAccess;
  }
});

// node_modules/.pnpm/react-is@18.3.1/node_modules/react-is/cjs/react-is.development.js
var require_react_is_development2 = __commonJS({
  "node_modules/.pnpm/react-is@18.3.1/node_modules/react-is/cjs/react-is.development.js"(exports) {
    "use strict";
    if (true) {
      (function() {
        "use strict";
        var REACT_ELEMENT_TYPE = Symbol.for("react.element");
        var REACT_PORTAL_TYPE = Symbol.for("react.portal");
        var REACT_FRAGMENT_TYPE = Symbol.for("react.fragment");
        var REACT_STRICT_MODE_TYPE = Symbol.for("react.strict_mode");
        var REACT_PROFILER_TYPE = Symbol.for("react.profiler");
        var REACT_PROVIDER_TYPE = Symbol.for("react.provider");
        var REACT_CONTEXT_TYPE = Symbol.for("react.context");
        var REACT_SERVER_CONTEXT_TYPE = Symbol.for("react.server_context");
        var REACT_FORWARD_REF_TYPE = Symbol.for("react.forward_ref");
        var REACT_SUSPENSE_TYPE = Symbol.for("react.suspense");
        var REACT_SUSPENSE_LIST_TYPE = Symbol.for("react.suspense_list");
        var REACT_MEMO_TYPE = Symbol.for("react.memo");
        var REACT_LAZY_TYPE = Symbol.for("react.lazy");
        var REACT_OFFSCREEN_TYPE = Symbol.for("react.offscreen");
        var enableScopeAPI = false;
        var enableCacheElement = false;
        var enableTransitionTracing = false;
        var enableLegacyHidden = false;
        var enableDebugTracing = false;
        var REACT_MODULE_REFERENCE;
        {
          REACT_MODULE_REFERENCE = Symbol.for("react.module.reference");
        }
        function isValidElementType(type) {
          if (typeof type === "string" || typeof type === "function") {
            return true;
          }
          if (type === REACT_FRAGMENT_TYPE || type === REACT_PROFILER_TYPE || enableDebugTracing || type === REACT_STRICT_MODE_TYPE || type === REACT_SUSPENSE_TYPE || type === REACT_SUSPENSE_LIST_TYPE || enableLegacyHidden || type === REACT_OFFSCREEN_TYPE || enableScopeAPI || enableCacheElement || enableTransitionTracing) {
            return true;
          }
          if (typeof type === "object" && type !== null) {
            if (type.$$typeof === REACT_LAZY_TYPE || type.$$typeof === REACT_MEMO_TYPE || type.$$typeof === REACT_PROVIDER_TYPE || type.$$typeof === REACT_CONTEXT_TYPE || type.$$typeof === REACT_FORWARD_REF_TYPE || // This needs to include all possible module reference object
            // types supported by any Flight configuration anywhere since
            // we don't know which Flight build this will end up being used
            // with.
            type.$$typeof === REACT_MODULE_REFERENCE || type.getModuleId !== void 0) {
              return true;
            }
          }
          return false;
        }
        function typeOf(object) {
          if (typeof object === "object" && object !== null) {
            var $$typeof = object.$$typeof;
            switch ($$typeof) {
              case REACT_ELEMENT_TYPE:
                var type = object.type;
                switch (type) {
                  case REACT_FRAGMENT_TYPE:
                  case REACT_PROFILER_TYPE:
                  case REACT_STRICT_MODE_TYPE:
                  case REACT_SUSPENSE_TYPE:
                  case REACT_SUSPENSE_LIST_TYPE:
                    return type;
                  default:
                    var $$typeofType = type && type.$$typeof;
                    switch ($$typeofType) {
                      case REACT_SERVER_CONTEXT_TYPE:
                      case REACT_CONTEXT_TYPE:
                      case REACT_FORWARD_REF_TYPE:
                      case REACT_LAZY_TYPE:
                      case REACT_MEMO_TYPE:
                      case REACT_PROVIDER_TYPE:
                        return $$typeofType;
                      default:
                        return $$typeof;
                    }
                }
              case REACT_PORTAL_TYPE:
                return $$typeof;
            }
          }
          return void 0;
        }
        var ContextConsumer = REACT_CONTEXT_TYPE;
        var ContextProvider = REACT_PROVIDER_TYPE;
        var Element = REACT_ELEMENT_TYPE;
        var ForwardRef = REACT_FORWARD_REF_TYPE;
        var Fragment3 = REACT_FRAGMENT_TYPE;
        var Lazy = REACT_LAZY_TYPE;
        var Memo = REACT_MEMO_TYPE;
        var Portal = REACT_PORTAL_TYPE;
        var Profiler = REACT_PROFILER_TYPE;
        var StrictMode = REACT_STRICT_MODE_TYPE;
        var Suspense = REACT_SUSPENSE_TYPE;
        var SuspenseList = REACT_SUSPENSE_LIST_TYPE;
        var hasWarnedAboutDeprecatedIsAsyncMode = false;
        var hasWarnedAboutDeprecatedIsConcurrentMode = false;
        function isAsyncMode(object) {
          {
            if (!hasWarnedAboutDeprecatedIsAsyncMode) {
              hasWarnedAboutDeprecatedIsAsyncMode = true;
              console["warn"]("The ReactIs.isAsyncMode() alias has been deprecated, and will be removed in React 18+.");
            }
          }
          return false;
        }
        function isConcurrentMode(object) {
          {
            if (!hasWarnedAboutDeprecatedIsConcurrentMode) {
              hasWarnedAboutDeprecatedIsConcurrentMode = true;
              console["warn"]("The ReactIs.isConcurrentMode() alias has been deprecated, and will be removed in React 18+.");
            }
          }
          return false;
        }
        function isContextConsumer(object) {
          return typeOf(object) === REACT_CONTEXT_TYPE;
        }
        function isContextProvider(object) {
          return typeOf(object) === REACT_PROVIDER_TYPE;
        }
        function isElement(object) {
          return typeof object === "object" && object !== null && object.$$typeof === REACT_ELEMENT_TYPE;
        }
        function isForwardRef(object) {
          return typeOf(object) === REACT_FORWARD_REF_TYPE;
        }
        function isFragment(object) {
          return typeOf(object) === REACT_FRAGMENT_TYPE;
        }
        function isLazy(object) {
          return typeOf(object) === REACT_LAZY_TYPE;
        }
        function isMemo(object) {
          return typeOf(object) === REACT_MEMO_TYPE;
        }
        function isPortal(object) {
          return typeOf(object) === REACT_PORTAL_TYPE;
        }
        function isProfiler(object) {
          return typeOf(object) === REACT_PROFILER_TYPE;
        }
        function isStrictMode(object) {
          return typeOf(object) === REACT_STRICT_MODE_TYPE;
        }
        function isSuspense(object) {
          return typeOf(object) === REACT_SUSPENSE_TYPE;
        }
        function isSuspenseList(object) {
          return typeOf(object) === REACT_SUSPENSE_LIST_TYPE;
        }
        exports.ContextConsumer = ContextConsumer;
        exports.ContextProvider = ContextProvider;
        exports.Element = Element;
        exports.ForwardRef = ForwardRef;
        exports.Fragment = Fragment3;
        exports.Lazy = Lazy;
        exports.Memo = Memo;
        exports.Portal = Portal;
        exports.Profiler = Profiler;
        exports.StrictMode = StrictMode;
        exports.Suspense = Suspense;
        exports.SuspenseList = SuspenseList;
        exports.isAsyncMode = isAsyncMode;
        exports.isConcurrentMode = isConcurrentMode;
        exports.isContextConsumer = isContextConsumer;
        exports.isContextProvider = isContextProvider;
        exports.isElement = isElement;
        exports.isForwardRef = isForwardRef;
        exports.isFragment = isFragment;
        exports.isLazy = isLazy;
        exports.isMemo = isMemo;
        exports.isPortal = isPortal;
        exports.isProfiler = isProfiler;
        exports.isStrictMode = isStrictMode;
        exports.isSuspense = isSuspense;
        exports.isSuspenseList = isSuspenseList;
        exports.isValidElementType = isValidElementType;
        exports.typeOf = typeOf;
      })();
    }
  }
});

// node_modules/.pnpm/react-is@18.3.1/node_modules/react-is/index.js
var require_react_is2 = __commonJS({
  "node_modules/.pnpm/react-is@18.3.1/node_modules/react-is/index.js"(exports, module) {
    "use strict";
    if (false) {
      module.exports = null;
    } else {
      module.exports = require_react_is_development2();
    }
  }
});

// node_modules/.pnpm/inline-style-parser@0.1.1/node_modules/inline-style-parser/index.js
var require_inline_style_parser = __commonJS({
  "node_modules/.pnpm/inline-style-parser@0.1.1/node_modules/inline-style-parser/index.js"(exports, module) {
    var COMMENT_REGEX = /\/\*[^*]*\*+([^/*][^*]*\*+)*\//g;
    var NEWLINE_REGEX = /\n/g;
    var WHITESPACE_REGEX = /^\s*/;
    var PROPERTY_REGEX = /^(\*?[-#/*\\\w]+(\[[0-9a-z_-]+\])?)\s*/;
    var COLON_REGEX = /^:\s*/;
    var VALUE_REGEX = /^((?:'(?:\\'|.)*?'|"(?:\\"|.)*?"|\([^)]*?\)|[^};])+)/;
    var SEMICOLON_REGEX = /^[;\s]*/;
    var TRIM_REGEX = /^\s+|\s+$/g;
    var NEWLINE = "\n";
    var FORWARD_SLASH = "/";
    var ASTERISK = "*";
    var EMPTY_STRING = "";
    var TYPE_COMMENT = "comment";
    var TYPE_DECLARATION = "declaration";
    module.exports = function(style, options) {
      if (typeof style !== "string") {
        throw new TypeError("First argument must be a string");
      }
      if (!style)
        return [];
      options = options || {};
      var lineno = 1;
      var column = 1;
      function updatePosition(str) {
        var lines = str.match(NEWLINE_REGEX);
        if (lines)
          lineno += lines.length;
        var i = str.lastIndexOf(NEWLINE);
        column = ~i ? str.length - i : column + str.length;
      }
      function position3() {
        var start = { line: lineno, column };
        return function(node3) {
          node3.position = new Position(start);
          whitespace2();
          return node3;
        };
      }
      function Position(start) {
        this.start = start;
        this.end = { line: lineno, column };
        this.source = options.source;
      }
      Position.prototype.content = style;
      var errorsList = [];
      function error(msg) {
        var err = new Error(
          options.source + ":" + lineno + ":" + column + ": " + msg
        );
        err.reason = msg;
        err.filename = options.source;
        err.line = lineno;
        err.column = column;
        err.source = style;
        if (options.silent) {
          errorsList.push(err);
        } else {
          throw err;
        }
      }
      function match(re) {
        var m = re.exec(style);
        if (!m)
          return;
        var str = m[0];
        updatePosition(str);
        style = style.slice(str.length);
        return m;
      }
      function whitespace2() {
        match(WHITESPACE_REGEX);
      }
      function comments(rules) {
        var c;
        rules = rules || [];
        while (c = comment()) {
          if (c !== false) {
            rules.push(c);
          }
        }
        return rules;
      }
      function comment() {
        var pos = position3();
        if (FORWARD_SLASH != style.charAt(0) || ASTERISK != style.charAt(1))
          return;
        var i = 2;
        while (EMPTY_STRING != style.charAt(i) && (ASTERISK != style.charAt(i) || FORWARD_SLASH != style.charAt(i + 1))) {
          ++i;
        }
        i += 2;
        if (EMPTY_STRING === style.charAt(i - 1)) {
          return error("End of comment missing");
        }
        var str = style.slice(2, i - 2);
        column += 2;
        updatePosition(str);
        style = style.slice(i);
        column += 2;
        return pos({
          type: TYPE_COMMENT,
          comment: str
        });
      }
      function declaration() {
        var pos = position3();
        var prop = match(PROPERTY_REGEX);
        if (!prop)
          return;
        comment();
        if (!match(COLON_REGEX))
          return error("property missing ':'");
        var val = match(VALUE_REGEX);
        var ret = pos({
          type: TYPE_DECLARATION,
          property: trim(prop[0].replace(COMMENT_REGEX, EMPTY_STRING)),
          value: val ? trim(val[0].replace(COMMENT_REGEX, EMPTY_STRING)) : EMPTY_STRING
        });
        match(SEMICOLON_REGEX);
        return ret;
      }
      function declarations() {
        var decls = [];
        comments(decls);
        var decl;
        while (decl = declaration()) {
          if (decl !== false) {
            decls.push(decl);
            comments(decls);
          }
        }
        return decls;
      }
      whitespace2();
      return declarations();
    };
    function trim(str) {
      return str ? str.replace(TRIM_REGEX, EMPTY_STRING) : EMPTY_STRING;
    }
  }
});

// node_modules/.pnpm/style-to-object@0.4.4/node_modules/style-to-object/index.js
var require_style_to_object = __commonJS({
  "node_modules/.pnpm/style-to-object@0.4.4/node_modules/style-to-object/index.js"(exports, module) {
    var parse2 = require_inline_style_parser();
    function StyleToObject2(style, iterator) {
      var output = null;
      if (!style || typeof style !== "string") {
        return output;
      }
      var declaration;
      var declarations = parse2(style);
      var hasIterator = typeof iterator === "function";
      var property;
      var value;
      for (var i = 0, len = declarations.length; i < len; i++) {
        declaration = declarations[i];
        property = declaration.property;
        value = declaration.value;
        if (hasIterator) {
          iterator(property, value, declaration);
        } else if (value) {
          output || (output = {});
          output[property] = value;
        }
      }
      return output;
    }
    module.exports = StyleToObject2;
    module.exports.default = StyleToObject2;
  }
});

// app/routes/chat.tsx
var import_react8 = __toESM(require_react(), 1);
var import_node = __toESM(require_node(), 1);

// app/hooks/use-chat.ts
var import_react = __toESM(require_react(), 1);

// app/services/chat.ts
if (import.meta) {
  import.meta.hot = createHotContext(
    //@ts-expect-error
    "app/services/chat.ts"
  );
  import.meta.hot.lastModified = "1738662837904.6753";
}
var API_URL = "http://localhost:8000/api/v1";
function getAuthHeader(user) {
  const tokenType = user.token_type.charAt(0).toUpperCase() + user.token_type.slice(1).toLowerCase();
  return `${tokenType} ${user.access_token}`;
}
async function handleResponse(response) {
  if (!response.ok) {
    const error = await response.json().catch(() => null);
    if (response.status === 401 || error?.detail === "Could not validate credentials") {
      window.location.href = `/login?redirectTo=${window.location.pathname}`;
      return { error: "Session expired. Please log in again." };
    }
    return {
      error: error?.detail || `API error: ${response.status} ${response.statusText}`
    };
  }
  try {
    const data = await response.json();
    return { data };
  } catch (error) {
    return {
      error: "Failed to parse response"
    };
  }
}
var chatApi = {
  async getSessions(user) {
    try {
      console.log("Auth header:", getAuthHeader(user));
      const response = await fetch(`${API_URL}/chat/sessions`, {
        headers: {
          "Authorization": getAuthHeader(user),
          "Accept": "application/json",
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
      const response = await fetch(`${API_URL}/chat/sessions/${sessionId}`, {
        headers: {
          "Authorization": getAuthHeader(user),
          "Accept": "application/json",
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
      console.log("Creating chat session with title:", title);
      console.log("Auth header:", getAuthHeader(user));
      const response = await fetch(`${API_URL}/chat/sessions`, {
        method: "POST",
        headers: {
          "Authorization": getAuthHeader(user),
          "Content-Type": "application/json",
          "Accept": "application/json"
        },
        credentials: "include",
        mode: "cors",
        body: JSON.stringify({ title })
      });
      console.log("Response status:", response.status);
      const responseText = await response.text();
      console.log("Response text:", responseText);
      if (!response.ok) {
        return {
          error: `Failed to create chat session: ${response.status} ${response.statusText}
${responseText}`
        };
      }
      try {
        const data = JSON.parse(responseText);
        return { data };
      } catch (error) {
        console.error("Failed to parse response:", error);
        return {
          error: "Failed to parse server response"
        };
      }
    } catch (error) {
      console.error("Failed to create chat session:", error);
      return {
        error: error instanceof Error ? error.message : "Failed to create session"
      };
    }
  },
  async deleteSession(user, sessionId) {
    try {
      const response = await fetch(`${API_URL}/chat/sessions/${sessionId}`, {
        method: "DELETE",
        headers: {
          "Authorization": getAuthHeader(user),
          "Accept": "application/json",
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
  async sendMessage(user, sessionId, content3) {
    try {
      const message_uuid = crypto.randomUUID();
      const response = await fetch(`${API_URL}/chat/sessions/${sessionId}/messages`, {
        method: "POST",
        headers: {
          "Authorization": getAuthHeader(user),
          "Content-Type": "application/json",
          "Accept": "application/json"
        },
        credentials: "include",
        mode: "cors",
        body: JSON.stringify({ content: content3, message_uuid })
      });
      const apiResponse = await handleResponse(response);
      if (apiResponse.error) {
        return { error: apiResponse.error };
      }
      if (!apiResponse.data) {
        return { error: "No data received from server" };
      }
      const message = {
        id: apiResponse.data.message_uuid,
        role: "ASSISTANT",
        content: apiResponse.data.message,
        created_at: (/* @__PURE__ */ new Date()).toISOString(),
        message_uuid: apiResponse.data.message_uuid,
        progress: apiResponse.data.progress
      };
      return { data: message };
    } catch (error) {
      return {
        error: error instanceof Error ? error.message : "Failed to send message"
      };
    }
  },
  async getMessages(user, sessionId) {
    try {
      const response = await fetch(`${API_URL}/chat/sessions/${sessionId}/messages`, {
        headers: {
          "Authorization": getAuthHeader(user),
          "Accept": "application/json",
          "Content-Type": "application/json"
        },
        credentials: "include",
        mode: "cors"
      });
      const apiResponse = await handleResponse(response);
      if (apiResponse.error) {
        return { error: apiResponse.error };
      }
      if (!apiResponse.data) {
        return { error: "No messages received from server" };
      }
      return { data: apiResponse.data };
    } catch (error) {
      return {
        error: error instanceof Error ? error.message : "Failed to fetch messages"
      };
    }
  }
};

// app/hooks/use-chat.ts
if (import.meta) {
  import.meta.hot = createHotContext(
    //@ts-expect-error
    "app/hooks/use-chat.ts"
  );
  import.meta.hot.lastModified = "1738669621876.1584";
}
function useChat() {
  const user = useUser();
  const [state, setState] = (0, import_react.useState)({
    messages: [],
    isLoading: false,
    error: null,
    input: "",
    sessions: [],
    currentSession: null,
    progress: void 0,
    isAiThinking: false
  });
  const setPartialState = (newState) => {
    setState((prev) => ({ ...prev, ...newState }));
  };
  (0, import_react.useEffect)(() => {
    if (user) {
      loadSessions();
    }
  }, [user]);
  const loadSessions = async () => {
    if (!user)
      return;
    try {
      const response = await chatApi.getSessions(user);
      if (response.error)
        throw new Error(response.error);
      if (response.data) {
        setPartialState({ sessions: response.data });
      }
    } catch (error) {
      setPartialState({
        error: error instanceof Error ? error.message : "Failed to load sessions"
      });
    }
  };
  const selectChat = async (sessionId) => {
    if (!user) {
      setPartialState({ error: "Not authenticated" });
      return;
    }
    try {
      const sessionResponse = await chatApi.getSession(user, sessionId);
      if (sessionResponse.error)
        throw new Error(sessionResponse.error);
      if (!sessionResponse.data)
        throw new Error("No session data received");
      const messagesResponse = await chatApi.getMessages(user, sessionId);
      if (messagesResponse.error)
        throw new Error(messagesResponse.error);
      const messages = messagesResponse.data || [];
      const lastMessage = messages[messages.length - 1];
      const progress = lastMessage?.progress;
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
  };
  const sendMessage = async (content3) => {
    if (!user || !state.currentSession) {
      setPartialState({ error: "No active chat session" });
      return;
    }
    try {
      const userMessage = {
        id: crypto.randomUUID(),
        role: "USER",
        content: content3,
        created_at: (/* @__PURE__ */ new Date()).toISOString(),
        progress: state.progress
      };
      setPartialState({
        messages: [...state.messages, userMessage]
      });
      setPartialState({
        isLoading: true,
        error: null,
        isAiThinking: true
      });
      const response = await chatApi.sendMessage(
        user,
        state.currentSession.id,
        content3
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
      if (response.data) {
        setPartialState({
          messages: [...state.messages, userMessage, response.data],
          progress: response.data.progress
        });
      }
    } catch (error) {
      setPartialState({
        error: error instanceof Error ? error.message : "Failed to send message"
      });
    } finally {
      setPartialState({ isLoading: false, isAiThinking: false });
    }
  };
  const startNewChat = async (title) => {
    if (!user) {
      setPartialState({ error: "Not authenticated" });
      return;
    }
    try {
      const response = await chatApi.createChatSession(title, user);
      if (response.error)
        throw new Error(response.error);
      if (response.data) {
        setPartialState({
          currentSession: response.data,
          messages: [],
          progress: void 0
        });
        await loadSessions();
      }
    } catch (error) {
      setPartialState({
        error: error instanceof Error ? error.message : "Failed to create chat"
      });
    }
  };
  const deleteChat = (0, import_react.useCallback)(async () => {
    if (!user || !state.currentSession) {
      setPartialState({ error: "No active chat session" });
      return;
    }
    try {
      const response = await chatApi.deleteSession(user, state.currentSession.id);
      if (response.error)
        throw new Error(response.error);
      setPartialState({
        currentSession: null,
        messages: [],
        progress: void 0
      });
      await loadSessions();
    } catch (error) {
      setPartialState({
        error: error instanceof Error ? error.message : "Failed to delete chat"
      });
    }
  }, [user, state.currentSession]);
  const handleInputChange = (e) => {
    setPartialState({ input: e.target.value });
  };
  const handleSubmit = (e) => {
    e.preventDefault();
    if (state.input.trim()) {
      sendMessage(state.input);
      setPartialState({ input: "" });
    }
  };
  const stop = () => {
    setPartialState({ isAiThinking: false });
  };
  const reload = () => {
  };
  return {
    ...state,
    handleInputChange,
    handleSubmit,
    startNewChat,
    deleteChat,
    selectChat,
    stop,
    reload
  };
}

// app/components/chat/chat-header.tsx
var import_react2 = __toESM(require_react(), 1);

// app/components/chat/delete-chat-dialog.tsx
var React = __toESM(require_react(), 1);
var import_jsx_dev_runtime = __toESM(require_jsx_dev_runtime(), 1);
if (!window.$RefreshReg$ || !window.$RefreshSig$ || !window.$RefreshRuntime$) {
  console.warn("remix:hmr: React Fast Refresh only works when the Remix compiler is running in development mode.");
} else {
  prevRefreshReg = window.$RefreshReg$;
  prevRefreshSig = window.$RefreshSig$;
  window.$RefreshReg$ = (type, id) => {
    window.$RefreshRuntime$.register(type, '"app/components/chat/delete-chat-dialog.tsx"' + id);
  };
  window.$RefreshSig$ = window.$RefreshRuntime$.createSignatureFunctionForTransform;
}
var prevRefreshReg;
var prevRefreshSig;
var _s = $RefreshSig$();
if (import.meta) {
  import.meta.hot = createHotContext(
    //@ts-expect-error
    "app/components/chat/delete-chat-dialog.tsx"
  );
  import.meta.hot.lastModified = "1738662837906.6753";
}
function DeleteChatDialog({
  isOpen,
  onClose,
  onConfirm,
  currentSession
}) {
  _s();
  const [isDeleting, setIsDeleting] = React.useState(false);
  const handleConfirm = async () => {
    if (!currentSession || isDeleting)
      return;
    try {
      setIsDeleting(true);
      await onConfirm();
    } catch (error) {
      console.error("Failed to delete chat:", error);
    } finally {
      setIsDeleting(false);
    }
  };
  return /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)(Dialog, { open: isOpen, onOpenChange: onClose, children: /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)(DialogContent, { children: [
    /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)(DialogHeader, { children: [
      /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)(DialogTitle, { children: "Delete Chat" }, void 0, false, {
        fileName: "app/components/chat/delete-chat-dialog.tsx",
        lineNumber: 47,
        columnNumber: 11
      }, this),
      /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)(DialogDescription, { children: "Are you sure you want to delete this chat? This action cannot be undone." }, void 0, false, {
        fileName: "app/components/chat/delete-chat-dialog.tsx",
        lineNumber: 48,
        columnNumber: 11
      }, this)
    ] }, void 0, true, {
      fileName: "app/components/chat/delete-chat-dialog.tsx",
      lineNumber: 46,
      columnNumber: 9
    }, this),
    /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)(DialogFooter, { children: [
      /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)(Button, { variant: "outline", onClick: onClose, disabled: isDeleting, children: "Cancel" }, void 0, false, {
        fileName: "app/components/chat/delete-chat-dialog.tsx",
        lineNumber: 53,
        columnNumber: 11
      }, this),
      /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)(Button, { variant: "destructive", onClick: handleConfirm, disabled: isDeleting, children: isDeleting ? "Deleting..." : "Delete" }, void 0, false, {
        fileName: "app/components/chat/delete-chat-dialog.tsx",
        lineNumber: 56,
        columnNumber: 11
      }, this)
    ] }, void 0, true, {
      fileName: "app/components/chat/delete-chat-dialog.tsx",
      lineNumber: 52,
      columnNumber: 9
    }, this)
  ] }, void 0, true, {
    fileName: "app/components/chat/delete-chat-dialog.tsx",
    lineNumber: 45,
    columnNumber: 7
  }, this) }, void 0, false, {
    fileName: "app/components/chat/delete-chat-dialog.tsx",
    lineNumber: 44,
    columnNumber: 10
  }, this);
}
_s(DeleteChatDialog, "PcvudgQ4pB1b8YUmRhNmcS3boU8=");
_c = DeleteChatDialog;
var _c;
$RefreshReg$(_c, "DeleteChatDialog");
window.$RefreshReg$ = prevRefreshReg;
window.$RefreshSig$ = prevRefreshSig;

// app/components/ui/progress.tsx
var React3 = __toESM(require_react(), 1);

// node_modules/.pnpm/@radix-ui+react-progress@1.1.1_@types+react-dom@18.3.5_@types+react@18.3.18__@types+rea_12d905cd66a35a01dab1a4244efb06ab/node_modules/@radix-ui/react-progress/dist/index.mjs
var React2 = __toESM(require_react(), 1);
var import_jsx_runtime = __toESM(require_jsx_runtime(), 1);
"use client";
var PROGRESS_NAME = "Progress";
var DEFAULT_MAX = 100;
var [createProgressContext, createProgressScope] = createContextScope(PROGRESS_NAME);
var [ProgressProvider, useProgressContext] = createProgressContext(PROGRESS_NAME);
var Progress = React2.forwardRef(
  (props, forwardedRef) => {
    const {
      __scopeProgress,
      value: valueProp = null,
      max: maxProp,
      getValueLabel = defaultGetValueLabel,
      ...progressProps
    } = props;
    if ((maxProp || maxProp === 0) && !isValidMaxNumber(maxProp)) {
      console.error(getInvalidMaxError(`${maxProp}`, "Progress"));
    }
    const max = isValidMaxNumber(maxProp) ? maxProp : DEFAULT_MAX;
    if (valueProp !== null && !isValidValueNumber(valueProp, max)) {
      console.error(getInvalidValueError(`${valueProp}`, "Progress"));
    }
    const value = isValidValueNumber(valueProp, max) ? valueProp : null;
    const valueLabel = isNumber(value) ? getValueLabel(value, max) : void 0;
    return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(ProgressProvider, { scope: __scopeProgress, value, max, children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(
      Primitive.div,
      {
        "aria-valuemax": max,
        "aria-valuemin": 0,
        "aria-valuenow": isNumber(value) ? value : void 0,
        "aria-valuetext": valueLabel,
        role: "progressbar",
        "data-state": getProgressState(value, max),
        "data-value": value ?? void 0,
        "data-max": max,
        ...progressProps,
        ref: forwardedRef
      }
    ) });
  }
);
Progress.displayName = PROGRESS_NAME;
var INDICATOR_NAME = "ProgressIndicator";
var ProgressIndicator = React2.forwardRef(
  (props, forwardedRef) => {
    const { __scopeProgress, ...indicatorProps } = props;
    const context = useProgressContext(INDICATOR_NAME, __scopeProgress);
    return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(
      Primitive.div,
      {
        "data-state": getProgressState(context.value, context.max),
        "data-value": context.value ?? void 0,
        "data-max": context.max,
        ...indicatorProps,
        ref: forwardedRef
      }
    );
  }
);
ProgressIndicator.displayName = INDICATOR_NAME;
function defaultGetValueLabel(value, max) {
  return `${Math.round(value / max * 100)}%`;
}
function getProgressState(value, maxValue) {
  return value == null ? "indeterminate" : value === maxValue ? "complete" : "loading";
}
function isNumber(value) {
  return typeof value === "number";
}
function isValidMaxNumber(max) {
  return isNumber(max) && !isNaN(max) && max > 0;
}
function isValidValueNumber(value, max) {
  return isNumber(value) && !isNaN(value) && value <= max && value >= 0;
}
function getInvalidMaxError(propValue, componentName) {
  return `Invalid prop \`max\` of value \`${propValue}\` supplied to \`${componentName}\`. Only numbers greater than 0 are valid max values. Defaulting to \`${DEFAULT_MAX}\`.`;
}
function getInvalidValueError(propValue, componentName) {
  return `Invalid prop \`value\` of value \`${propValue}\` supplied to \`${componentName}\`. The \`value\` prop must be:
  - a positive number
  - less than the value passed to \`max\` (or ${DEFAULT_MAX} if no \`max\` prop is set)
  - \`null\` or \`undefined\` if the progress is indeterminate.

Defaulting to \`null\`.`;
}
var Root = Progress;
var Indicator = ProgressIndicator;

// app/components/ui/progress.tsx
var import_jsx_dev_runtime2 = __toESM(require_jsx_dev_runtime(), 1);
if (!window.$RefreshReg$ || !window.$RefreshSig$ || !window.$RefreshRuntime$) {
  console.warn("remix:hmr: React Fast Refresh only works when the Remix compiler is running in development mode.");
} else {
  prevRefreshReg = window.$RefreshReg$;
  prevRefreshSig = window.$RefreshSig$;
  window.$RefreshReg$ = (type, id) => {
    window.$RefreshRuntime$.register(type, '"app/components/ui/progress.tsx"' + id);
  };
  window.$RefreshSig$ = window.$RefreshRuntime$.createSignatureFunctionForTransform;
}
var prevRefreshReg;
var prevRefreshSig;
if (import.meta) {
  import.meta.hot = createHotContext(
    //@ts-expect-error
    "app/components/ui/progress.tsx"
  );
  import.meta.hot.lastModified = "1738662837907.6753";
}
var Progress2 = React3.forwardRef(_c2 = ({
  className,
  value,
  ...props
}, ref) => /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)(Root, { ref, className: cn("relative h-2 w-full overflow-hidden rounded-full bg-primary/20", className), ...props, children: /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)(Indicator, { className: "h-full w-full flex-1 bg-primary transition-all", style: {
  transform: `translateX(-${100 - (value || 0)}%)`
} }, void 0, false, {
  fileName: "app/components/ui/progress.tsx",
  lineNumber: 29,
  columnNumber: 5
}, this) }, void 0, false, {
  fileName: "app/components/ui/progress.tsx",
  lineNumber: 28,
  columnNumber: 12
}, this));
_c22 = Progress2;
Progress2.displayName = Root.displayName;
var _c2;
var _c22;
$RefreshReg$(_c2, "Progress$React.forwardRef");
$RefreshReg$(_c22, "Progress");
window.$RefreshReg$ = prevRefreshReg;
window.$RefreshSig$ = prevRefreshSig;

// app/components/chat/chat-header.tsx
var import_jsx_dev_runtime3 = __toESM(require_jsx_dev_runtime(), 1);
if (!window.$RefreshReg$ || !window.$RefreshSig$ || !window.$RefreshRuntime$) {
  console.warn("remix:hmr: React Fast Refresh only works when the Remix compiler is running in development mode.");
} else {
  prevRefreshReg = window.$RefreshReg$;
  prevRefreshSig = window.$RefreshSig$;
  window.$RefreshReg$ = (type, id) => {
    window.$RefreshRuntime$.register(type, '"app/components/chat/chat-header.tsx"' + id);
  };
  window.$RefreshSig$ = window.$RefreshRuntime$.createSignatureFunctionForTransform;
}
var prevRefreshReg;
var prevRefreshSig;
var _s2 = $RefreshSig$();
if (import.meta) {
  import.meta.hot = createHotContext(
    //@ts-expect-error
    "app/components/chat/chat-header.tsx"
  );
  import.meta.hot.lastModified = "1738662837906.6753";
}
function ChatHeader({
  isLoading,
  onNewChat,
  onSelectChat,
  onClearChat,
  sessions = [],
  currentSession,
  progress
}) {
  _s2();
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = (0, import_react2.useState)(false);
  const handleDeleteClick = () => {
    setIsDeleteDialogOpen(true);
  };
  const handleDeleteConfirm = async () => {
    try {
      if (onClearChat) {
        await onClearChat();
      }
      setIsDeleteDialogOpen(false);
    } catch (error) {
      console.error("Failed to delete chat:", error);
    }
  };
  return /* @__PURE__ */ (0, import_jsx_dev_runtime3.jsxDEV)("header", { className: "sticky top-0 z-10 bg-background border-b", children: [
    /* @__PURE__ */ (0, import_jsx_dev_runtime3.jsxDEV)("div", { className: "flex items-center justify-between px-4 py-2", children: [
      /* @__PURE__ */ (0, import_jsx_dev_runtime3.jsxDEV)("div", { className: "flex items-center gap-2", children: [
        isLoading && /* @__PURE__ */ (0, import_jsx_dev_runtime3.jsxDEV)(Loader2, { className: "h-4 w-4 animate-spin" }, void 0, false, {
          fileName: "app/components/chat/chat-header.tsx",
          lineNumber: 56,
          columnNumber: 25
        }, this),
        /* @__PURE__ */ (0, import_jsx_dev_runtime3.jsxDEV)("span", { className: "font-bold text-foreground", children: currentSession?.title || "New Chat" }, void 0, false, {
          fileName: "app/components/chat/chat-header.tsx",
          lineNumber: 57,
          columnNumber: 11
        }, this)
      ] }, void 0, true, {
        fileName: "app/components/chat/chat-header.tsx",
        lineNumber: 55,
        columnNumber: 9
      }, this),
      /* @__PURE__ */ (0, import_jsx_dev_runtime3.jsxDEV)(DropdownMenu, { children: [
        /* @__PURE__ */ (0, import_jsx_dev_runtime3.jsxDEV)(DropdownMenuTrigger, { asChild: true, children: /* @__PURE__ */ (0, import_jsx_dev_runtime3.jsxDEV)(Button, { variant: "ghost", className: "flex items-center gap-2", children: [
          /* @__PURE__ */ (0, import_jsx_dev_runtime3.jsxDEV)(Menu, { className: "h-4 w-4" }, void 0, false, {
            fileName: "app/components/chat/chat-header.tsx",
            lineNumber: 64,
            columnNumber: 15
          }, this),
          /* @__PURE__ */ (0, import_jsx_dev_runtime3.jsxDEV)("span", { children: "Chat Menu" }, void 0, false, {
            fileName: "app/components/chat/chat-header.tsx",
            lineNumber: 65,
            columnNumber: 15
          }, this),
          /* @__PURE__ */ (0, import_jsx_dev_runtime3.jsxDEV)("span", { className: "sr-only", children: "Open menu" }, void 0, false, {
            fileName: "app/components/chat/chat-header.tsx",
            lineNumber: 66,
            columnNumber: 15
          }, this)
        ] }, void 0, true, {
          fileName: "app/components/chat/chat-header.tsx",
          lineNumber: 63,
          columnNumber: 13
        }, this) }, void 0, false, {
          fileName: "app/components/chat/chat-header.tsx",
          lineNumber: 62,
          columnNumber: 11
        }, this),
        /* @__PURE__ */ (0, import_jsx_dev_runtime3.jsxDEV)(DropdownMenuContent, { align: "end", children: [
          /* @__PURE__ */ (0, import_jsx_dev_runtime3.jsxDEV)(DropdownMenuItem, { onClick: onNewChat, children: [
            /* @__PURE__ */ (0, import_jsx_dev_runtime3.jsxDEV)(Plus, { className: "h-4 w-4 mr-2" }, void 0, false, {
              fileName: "app/components/chat/chat-header.tsx",
              lineNumber: 71,
              columnNumber: 15
            }, this),
            "New Chat"
          ] }, void 0, true, {
            fileName: "app/components/chat/chat-header.tsx",
            lineNumber: 70,
            columnNumber: 13
          }, this),
          sessions.length > 0 && /* @__PURE__ */ (0, import_jsx_dev_runtime3.jsxDEV)(DropdownMenuSub, { children: [
            /* @__PURE__ */ (0, import_jsx_dev_runtime3.jsxDEV)(DropdownMenuSubTrigger, { children: [
              /* @__PURE__ */ (0, import_jsx_dev_runtime3.jsxDEV)(Menu, { className: "h-4 w-4 mr-2" }, void 0, false, {
                fileName: "app/components/chat/chat-header.tsx",
                lineNumber: 76,
                columnNumber: 19
              }, this),
              "Select Chat"
            ] }, void 0, true, {
              fileName: "app/components/chat/chat-header.tsx",
              lineNumber: 75,
              columnNumber: 17
            }, this),
            /* @__PURE__ */ (0, import_jsx_dev_runtime3.jsxDEV)(DropdownMenuSubContent, { children: sessions.map((session) => /* @__PURE__ */ (0, import_jsx_dev_runtime3.jsxDEV)(DropdownMenuItem, { onClick: () => onSelectChat(session.id), children: session.title }, session.id, false, {
              fileName: "app/components/chat/chat-header.tsx",
              lineNumber: 80,
              columnNumber: 44
            }, this)) }, void 0, false, {
              fileName: "app/components/chat/chat-header.tsx",
              lineNumber: 79,
              columnNumber: 17
            }, this)
          ] }, void 0, true, {
            fileName: "app/components/chat/chat-header.tsx",
            lineNumber: 74,
            columnNumber: 37
          }, this),
          currentSession && /* @__PURE__ */ (0, import_jsx_dev_runtime3.jsxDEV)(DropdownMenuItem, { onClick: handleDeleteClick, className: "text-destructive focus:text-destructive", children: [
            /* @__PURE__ */ (0, import_jsx_dev_runtime3.jsxDEV)(Trash2, { className: "h-4 w-4 mr-2" }, void 0, false, {
              fileName: "app/components/chat/chat-header.tsx",
              lineNumber: 86,
              columnNumber: 17
            }, this),
            "Delete Chat"
          ] }, void 0, true, {
            fileName: "app/components/chat/chat-header.tsx",
            lineNumber: 85,
            columnNumber: 32
          }, this)
        ] }, void 0, true, {
          fileName: "app/components/chat/chat-header.tsx",
          lineNumber: 69,
          columnNumber: 11
        }, this)
      ] }, void 0, true, {
        fileName: "app/components/chat/chat-header.tsx",
        lineNumber: 61,
        columnNumber: 9
      }, this)
    ] }, void 0, true, {
      fileName: "app/components/chat/chat-header.tsx",
      lineNumber: 54,
      columnNumber: 7
    }, this),
    progress !== void 0 && /* @__PURE__ */ (0, import_jsx_dev_runtime3.jsxDEV)("div", { className: "px-4 pb-2", children: /* @__PURE__ */ (0, import_jsx_dev_runtime3.jsxDEV)("div", { className: "flex items-center gap-2", children: [
      /* @__PURE__ */ (0, import_jsx_dev_runtime3.jsxDEV)("div", { className: "flex-1", children: /* @__PURE__ */ (0, import_jsx_dev_runtime3.jsxDEV)(Progress2, { value: progress, className: "h-2" }, void 0, false, {
        fileName: "app/components/chat/chat-header.tsx",
        lineNumber: 96,
        columnNumber: 15
      }, this) }, void 0, false, {
        fileName: "app/components/chat/chat-header.tsx",
        lineNumber: 95,
        columnNumber: 13
      }, this),
      /* @__PURE__ */ (0, import_jsx_dev_runtime3.jsxDEV)("span", { className: "text-sm text-muted-foreground w-12 text-right", children: [
        Math.round(progress),
        "%"
      ] }, void 0, true, {
        fileName: "app/components/chat/chat-header.tsx",
        lineNumber: 98,
        columnNumber: 13
      }, this)
    ] }, void 0, true, {
      fileName: "app/components/chat/chat-header.tsx",
      lineNumber: 94,
      columnNumber: 11
    }, this) }, void 0, false, {
      fileName: "app/components/chat/chat-header.tsx",
      lineNumber: 93,
      columnNumber: 34
    }, this),
    /* @__PURE__ */ (0, import_jsx_dev_runtime3.jsxDEV)(DeleteChatDialog, { isOpen: isDeleteDialogOpen, onClose: () => setIsDeleteDialogOpen(false), onConfirm: handleDeleteConfirm, currentSession }, void 0, false, {
      fileName: "app/components/chat/chat-header.tsx",
      lineNumber: 104,
      columnNumber: 7
    }, this)
  ] }, void 0, true, {
    fileName: "app/components/chat/chat-header.tsx",
    lineNumber: 53,
    columnNumber: 10
  }, this);
}
_s2(ChatHeader, "Q/te/iKJ3y6/kmJRCLVmrh0U3Dc=");
_c3 = ChatHeader;
var _c3;
$RefreshReg$(_c3, "ChatHeader");
window.$RefreshReg$ = prevRefreshReg;
window.$RefreshSig$ = prevRefreshSig;

// app/components/chat/chat-input.tsx
var import_react3 = __toESM(require_react(), 1);
var import_jsx_dev_runtime4 = __toESM(require_jsx_dev_runtime(), 1);
if (!window.$RefreshReg$ || !window.$RefreshSig$ || !window.$RefreshRuntime$) {
  console.warn("remix:hmr: React Fast Refresh only works when the Remix compiler is running in development mode.");
} else {
  prevRefreshReg = window.$RefreshReg$;
  prevRefreshSig = window.$RefreshSig$;
  window.$RefreshReg$ = (type, id) => {
    window.$RefreshRuntime$.register(type, '"app/components/chat/chat-input.tsx"' + id);
  };
  window.$RefreshSig$ = window.$RefreshRuntime$.createSignatureFunctionForTransform;
}
var prevRefreshReg;
var prevRefreshSig;
var _s3 = $RefreshSig$();
if (import.meta) {
  import.meta.hot = createHotContext(
    //@ts-expect-error
    "app/components/chat/chat-input.tsx"
  );
  import.meta.hot.lastModified = "1738662837906.6753";
}
function ChatInput({
  input,
  handleInputChange,
  handleSubmit,
  isLoading,
  lastMessageId,
  hasActiveSession
}) {
  _s3();
  const textareaRef = (0, import_react3.useRef)(null);
  (0, import_react3.useEffect)(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [input]);
  (0, import_react3.useEffect)(() => {
    if (!isLoading && textareaRef.current && hasActiveSession) {
      textareaRef.current.focus();
    }
  }, [isLoading, hasActiveSession]);
  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };
  const handleFormSubmit = (e) => {
    e.preventDefault();
    handleSubmit(e);
  };
  if (!hasActiveSession) {
    return /* @__PURE__ */ (0, import_jsx_dev_runtime4.jsxDEV)("div", { className: "flex flex-col items-center justify-center p-8 text-center", children: [
      /* @__PURE__ */ (0, import_jsx_dev_runtime4.jsxDEV)(MessageCircleOff, { className: "h-8 w-8 mb-4 text-muted-foreground" }, void 0, false, {
        fileName: "app/components/chat/chat-input.tsx",
        lineNumber: 61,
        columnNumber: 9
      }, this),
      /* @__PURE__ */ (0, import_jsx_dev_runtime4.jsxDEV)("p", { className: "text-lg font-semibold", children: "No Active Chat" }, void 0, false, {
        fileName: "app/components/chat/chat-input.tsx",
        lineNumber: 62,
        columnNumber: 9
      }, this),
      /* @__PURE__ */ (0, import_jsx_dev_runtime4.jsxDEV)("p", { className: "text-sm text-muted-foreground mt-1", children: "Please start a new chat or select an existing one to continue." }, void 0, false, {
        fileName: "app/components/chat/chat-input.tsx",
        lineNumber: 65,
        columnNumber: 9
      }, this)
    ] }, void 0, true, {
      fileName: "app/components/chat/chat-input.tsx",
      lineNumber: 60,
      columnNumber: 12
    }, this);
  }
  return /* @__PURE__ */ (0, import_jsx_dev_runtime4.jsxDEV)("form", { onSubmit: handleFormSubmit, children: /* @__PURE__ */ (0, import_jsx_dev_runtime4.jsxDEV)("div", { className: cn("relative flex items-center", "px-8 py-4", "max-w-7xl mx-auto w-full", "bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60"), children: /* @__PURE__ */ (0, import_jsx_dev_runtime4.jsxDEV)("div", { className: "relative w-full", children: [
    /* @__PURE__ */ (0, import_jsx_dev_runtime4.jsxDEV)(Textarea, { ref: textareaRef, value: input, onChange: handleInputChange, onKeyDown: handleKeyDown, placeholder: "Type your message... (Press Enter to send, Shift+Enter for new line)", className: cn("min-h-[80px] w-full resize-none pr-12", "bg-background", "rounded-md border border-input", "focus-visible:outline-none focus-visible:ring-1", "focus-visible:ring-ring", "disabled:opacity-50 disabled:cursor-not-allowed", "text-foreground placeholder:text-muted-foreground", "scrollbar-custom"), disabled: isLoading }, void 0, false, {
      fileName: "app/components/chat/chat-input.tsx",
      lineNumber: 73,
      columnNumber: 11
    }, this),
    /* @__PURE__ */ (0, import_jsx_dev_runtime4.jsxDEV)(Button, { type: "submit", size: "icon", disabled: isLoading || !input.trim(), className: cn("absolute right-2 bottom-2", "bg-primary text-primary-foreground", "hover:bg-primary/90", "focus-visible:ring-1 focus-visible:ring-ring", "disabled:opacity-50"), children: [
      /* @__PURE__ */ (0, import_jsx_dev_runtime4.jsxDEV)(SendHorizontal, { className: "h-4 w-4" }, void 0, false, {
        fileName: "app/components/chat/chat-input.tsx",
        lineNumber: 75,
        columnNumber: 13
      }, this),
      /* @__PURE__ */ (0, import_jsx_dev_runtime4.jsxDEV)("span", { className: "sr-only", children: "Send message" }, void 0, false, {
        fileName: "app/components/chat/chat-input.tsx",
        lineNumber: 76,
        columnNumber: 13
      }, this)
    ] }, void 0, true, {
      fileName: "app/components/chat/chat-input.tsx",
      lineNumber: 74,
      columnNumber: 11
    }, this)
  ] }, void 0, true, {
    fileName: "app/components/chat/chat-input.tsx",
    lineNumber: 72,
    columnNumber: 9
  }, this) }, void 0, false, {
    fileName: "app/components/chat/chat-input.tsx",
    lineNumber: 71,
    columnNumber: 7
  }, this) }, void 0, false, {
    fileName: "app/components/chat/chat-input.tsx",
    lineNumber: 70,
    columnNumber: 10
  }, this);
}
_s3(ChatInput, "9N7qFGUrBoc4yXHMJAYm4PKHw3I=");
_c4 = ChatInput;
var _c4;
$RefreshReg$(_c4, "ChatInput");
window.$RefreshReg$ = prevRefreshReg;
window.$RefreshSig$ = prevRefreshSig;

// app/components/layout/markdown.tsx
var React6 = __toESM(require_react(), 1);

// node_modules/.pnpm/react-markdown@8.0.7_@types+react@18.3.18_react@18.3.1/node_modules/react-markdown/lib/uri-transformer.js
var protocols = ["http", "https", "mailto", "tel"];
function uriTransformer(uri) {
  const url = (uri || "").trim();
  const first = url.charAt(0);
  if (first === "#" || first === "/") {
    return url;
  }
  const colon = url.indexOf(":");
  if (colon === -1) {
    return url;
  }
  let index2 = -1;
  while (++index2 < protocols.length) {
    const protocol = protocols[index2];
    if (colon === protocol.length && url.slice(0, protocol.length).toLowerCase() === protocol) {
      return url;
    }
  }
  index2 = url.indexOf("?");
  if (index2 !== -1 && colon > index2) {
    return url;
  }
  index2 = url.indexOf("#");
  if (index2 !== -1 && colon > index2) {
    return url;
  }
  return "javascript:void(0)";
}

// node_modules/.pnpm/react-markdown@8.0.7_@types+react@18.3.18_react@18.3.1/node_modules/react-markdown/lib/react-markdown.js
var import_react5 = __toESM(require_react(), 1);

// node_modules/.pnpm/vfile@5.3.7/node_modules/vfile/lib/index.js
var import_is_buffer = __toESM(require_is_buffer(), 1);

// node_modules/.pnpm/unist-util-stringify-position@3.0.3/node_modules/unist-util-stringify-position/lib/index.js
function stringifyPosition(value) {
  if (!value || typeof value !== "object") {
    return "";
  }
  if ("position" in value || "type" in value) {
    return position(value.position);
  }
  if ("start" in value || "end" in value) {
    return position(value);
  }
  if ("line" in value || "column" in value) {
    return point(value);
  }
  return "";
}
function point(point4) {
  return index(point4 && point4.line) + ":" + index(point4 && point4.column);
}
function position(pos) {
  return point(pos && pos.start) + "-" + point(pos && pos.end);
}
function index(value) {
  return value && typeof value === "number" ? value : 1;
}

// node_modules/.pnpm/vfile-message@3.1.4/node_modules/vfile-message/lib/index.js
var VFileMessage = class extends Error {
  /**
   * Create a message for `reason` at `place` from `origin`.
   *
   * When an error is passed in as `reason`, the `stack` is copied.
   *
   * @param {string | Error | VFileMessage} reason
   *   Reason for message, uses the stack and message of the error if given.
   *
   *   > 👉 **Note**: you should use markdown.
   * @param {Node | NodeLike | Position | Point | null | undefined} [place]
   *   Place in file where the message occurred.
   * @param {string | null | undefined} [origin]
   *   Place in code where the message originates (example:
   *   `'my-package:my-rule'` or `'my-rule'`).
   * @returns
   *   Instance of `VFileMessage`.
   */
  // To do: next major: expose `undefined` everywhere instead of `null`.
  constructor(reason, place, origin) {
    const parts = [null, null];
    let position3 = {
      // @ts-expect-error: we always follows the structure of `position`.
      start: { line: null, column: null },
      // @ts-expect-error: "
      end: { line: null, column: null }
    };
    super();
    if (typeof place === "string") {
      origin = place;
      place = void 0;
    }
    if (typeof origin === "string") {
      const index2 = origin.indexOf(":");
      if (index2 === -1) {
        parts[1] = origin;
      } else {
        parts[0] = origin.slice(0, index2);
        parts[1] = origin.slice(index2 + 1);
      }
    }
    if (place) {
      if ("type" in place || "position" in place) {
        if (place.position) {
          position3 = place.position;
        }
      } else if ("start" in place || "end" in place) {
        position3 = place;
      } else if ("line" in place || "column" in place) {
        position3.start = place;
      }
    }
    this.name = stringifyPosition(place) || "1:1";
    this.message = typeof reason === "object" ? reason.message : reason;
    this.stack = "";
    if (typeof reason === "object" && reason.stack) {
      this.stack = reason.stack;
    }
    this.reason = this.message;
    this.fatal;
    this.line = position3.start.line;
    this.column = position3.start.column;
    this.position = position3;
    this.source = parts[0];
    this.ruleId = parts[1];
    this.file;
    this.actual;
    this.expected;
    this.url;
    this.note;
  }
};
VFileMessage.prototype.file = "";
VFileMessage.prototype.name = "";
VFileMessage.prototype.reason = "";
VFileMessage.prototype.message = "";
VFileMessage.prototype.stack = "";
VFileMessage.prototype.fatal = null;
VFileMessage.prototype.column = null;
VFileMessage.prototype.line = null;
VFileMessage.prototype.source = null;
VFileMessage.prototype.ruleId = null;
VFileMessage.prototype.position = null;

// node_modules/.pnpm/vfile@5.3.7/node_modules/vfile/lib/minpath.browser.js
var path = { basename, dirname, extname, join, sep: "/" };
function basename(path3, ext) {
  if (ext !== void 0 && typeof ext !== "string") {
    throw new TypeError('"ext" argument must be a string');
  }
  assertPath(path3);
  let start = 0;
  let end = -1;
  let index2 = path3.length;
  let seenNonSlash;
  if (ext === void 0 || ext.length === 0 || ext.length > path3.length) {
    while (index2--) {
      if (path3.charCodeAt(index2) === 47) {
        if (seenNonSlash) {
          start = index2 + 1;
          break;
        }
      } else if (end < 0) {
        seenNonSlash = true;
        end = index2 + 1;
      }
    }
    return end < 0 ? "" : path3.slice(start, end);
  }
  if (ext === path3) {
    return "";
  }
  let firstNonSlashEnd = -1;
  let extIndex = ext.length - 1;
  while (index2--) {
    if (path3.charCodeAt(index2) === 47) {
      if (seenNonSlash) {
        start = index2 + 1;
        break;
      }
    } else {
      if (firstNonSlashEnd < 0) {
        seenNonSlash = true;
        firstNonSlashEnd = index2 + 1;
      }
      if (extIndex > -1) {
        if (path3.charCodeAt(index2) === ext.charCodeAt(extIndex--)) {
          if (extIndex < 0) {
            end = index2;
          }
        } else {
          extIndex = -1;
          end = firstNonSlashEnd;
        }
      }
    }
  }
  if (start === end) {
    end = firstNonSlashEnd;
  } else if (end < 0) {
    end = path3.length;
  }
  return path3.slice(start, end);
}
function dirname(path3) {
  assertPath(path3);
  if (path3.length === 0) {
    return ".";
  }
  let end = -1;
  let index2 = path3.length;
  let unmatchedSlash;
  while (--index2) {
    if (path3.charCodeAt(index2) === 47) {
      if (unmatchedSlash) {
        end = index2;
        break;
      }
    } else if (!unmatchedSlash) {
      unmatchedSlash = true;
    }
  }
  return end < 0 ? path3.charCodeAt(0) === 47 ? "/" : "." : end === 1 && path3.charCodeAt(0) === 47 ? "//" : path3.slice(0, end);
}
function extname(path3) {
  assertPath(path3);
  let index2 = path3.length;
  let end = -1;
  let startPart = 0;
  let startDot = -1;
  let preDotState = 0;
  let unmatchedSlash;
  while (index2--) {
    const code4 = path3.charCodeAt(index2);
    if (code4 === 47) {
      if (unmatchedSlash) {
        startPart = index2 + 1;
        break;
      }
      continue;
    }
    if (end < 0) {
      unmatchedSlash = true;
      end = index2 + 1;
    }
    if (code4 === 46) {
      if (startDot < 0) {
        startDot = index2;
      } else if (preDotState !== 1) {
        preDotState = 1;
      }
    } else if (startDot > -1) {
      preDotState = -1;
    }
  }
  if (startDot < 0 || end < 0 || // We saw a non-dot character immediately before the dot.
  preDotState === 0 || // The (right-most) trimmed path component is exactly `..`.
  preDotState === 1 && startDot === end - 1 && startDot === startPart + 1) {
    return "";
  }
  return path3.slice(startDot, end);
}
function join(...segments) {
  let index2 = -1;
  let joined;
  while (++index2 < segments.length) {
    assertPath(segments[index2]);
    if (segments[index2]) {
      joined = joined === void 0 ? segments[index2] : joined + "/" + segments[index2];
    }
  }
  return joined === void 0 ? "." : normalize(joined);
}
function normalize(path3) {
  assertPath(path3);
  const absolute = path3.charCodeAt(0) === 47;
  let value = normalizeString(path3, !absolute);
  if (value.length === 0 && !absolute) {
    value = ".";
  }
  if (value.length > 0 && path3.charCodeAt(path3.length - 1) === 47) {
    value += "/";
  }
  return absolute ? "/" + value : value;
}
function normalizeString(path3, allowAboveRoot) {
  let result = "";
  let lastSegmentLength = 0;
  let lastSlash = -1;
  let dots = 0;
  let index2 = -1;
  let code4;
  let lastSlashIndex;
  while (++index2 <= path3.length) {
    if (index2 < path3.length) {
      code4 = path3.charCodeAt(index2);
    } else if (code4 === 47) {
      break;
    } else {
      code4 = 47;
    }
    if (code4 === 47) {
      if (lastSlash === index2 - 1 || dots === 1) {
      } else if (lastSlash !== index2 - 1 && dots === 2) {
        if (result.length < 2 || lastSegmentLength !== 2 || result.charCodeAt(result.length - 1) !== 46 || result.charCodeAt(result.length - 2) !== 46) {
          if (result.length > 2) {
            lastSlashIndex = result.lastIndexOf("/");
            if (lastSlashIndex !== result.length - 1) {
              if (lastSlashIndex < 0) {
                result = "";
                lastSegmentLength = 0;
              } else {
                result = result.slice(0, lastSlashIndex);
                lastSegmentLength = result.length - 1 - result.lastIndexOf("/");
              }
              lastSlash = index2;
              dots = 0;
              continue;
            }
          } else if (result.length > 0) {
            result = "";
            lastSegmentLength = 0;
            lastSlash = index2;
            dots = 0;
            continue;
          }
        }
        if (allowAboveRoot) {
          result = result.length > 0 ? result + "/.." : "..";
          lastSegmentLength = 2;
        }
      } else {
        if (result.length > 0) {
          result += "/" + path3.slice(lastSlash + 1, index2);
        } else {
          result = path3.slice(lastSlash + 1, index2);
        }
        lastSegmentLength = index2 - lastSlash - 1;
      }
      lastSlash = index2;
      dots = 0;
    } else if (code4 === 46 && dots > -1) {
      dots++;
    } else {
      dots = -1;
    }
  }
  return result;
}
function assertPath(path3) {
  if (typeof path3 !== "string") {
    throw new TypeError(
      "Path must be a string. Received " + JSON.stringify(path3)
    );
  }
}

// node_modules/.pnpm/vfile@5.3.7/node_modules/vfile/lib/minproc.browser.js
var proc = { cwd };
function cwd() {
  return "/";
}

// node_modules/.pnpm/vfile@5.3.7/node_modules/vfile/lib/minurl.shared.js
function isUrl(fileUrlOrPath) {
  return fileUrlOrPath !== null && typeof fileUrlOrPath === "object" && // @ts-expect-error: indexable.
  fileUrlOrPath.href && // @ts-expect-error: indexable.
  fileUrlOrPath.origin;
}

// node_modules/.pnpm/vfile@5.3.7/node_modules/vfile/lib/minurl.browser.js
function urlToPath(path3) {
  if (typeof path3 === "string") {
    path3 = new URL(path3);
  } else if (!isUrl(path3)) {
    const error = new TypeError(
      'The "path" argument must be of type string or an instance of URL. Received `' + path3 + "`"
    );
    error.code = "ERR_INVALID_ARG_TYPE";
    throw error;
  }
  if (path3.protocol !== "file:") {
    const error = new TypeError("The URL must be of scheme file");
    error.code = "ERR_INVALID_URL_SCHEME";
    throw error;
  }
  return getPathFromURLPosix(path3);
}
function getPathFromURLPosix(url) {
  if (url.hostname !== "") {
    const error = new TypeError(
      'File URL host must be "localhost" or empty on darwin'
    );
    error.code = "ERR_INVALID_FILE_URL_HOST";
    throw error;
  }
  const pathname = url.pathname;
  let index2 = -1;
  while (++index2 < pathname.length) {
    if (pathname.charCodeAt(index2) === 37 && pathname.charCodeAt(index2 + 1) === 50) {
      const third = pathname.charCodeAt(index2 + 2);
      if (third === 70 || third === 102) {
        const error = new TypeError(
          "File URL path must not include encoded / characters"
        );
        error.code = "ERR_INVALID_FILE_URL_PATH";
        throw error;
      }
    }
  }
  return decodeURIComponent(pathname);
}

// node_modules/.pnpm/vfile@5.3.7/node_modules/vfile/lib/index.js
var order = ["history", "path", "basename", "stem", "extname", "dirname"];
var VFile = class {
  /**
   * Create a new virtual file.
   *
   * `options` is treated as:
   *
   * *   `string` or `Buffer` — `{value: options}`
   * *   `URL` — `{path: options}`
   * *   `VFile` — shallow copies its data over to the new file
   * *   `object` — all fields are shallow copied over to the new file
   *
   * Path related fields are set in the following order (least specific to
   * most specific): `history`, `path`, `basename`, `stem`, `extname`,
   * `dirname`.
   *
   * You cannot set `dirname` or `extname` without setting either `history`,
   * `path`, `basename`, or `stem` too.
   *
   * @param {Compatible | null | undefined} [value]
   *   File value.
   * @returns
   *   New instance.
   */
  constructor(value) {
    let options;
    if (!value) {
      options = {};
    } else if (typeof value === "string" || buffer(value)) {
      options = { value };
    } else if (isUrl(value)) {
      options = { path: value };
    } else {
      options = value;
    }
    this.data = {};
    this.messages = [];
    this.history = [];
    this.cwd = proc.cwd();
    this.value;
    this.stored;
    this.result;
    this.map;
    let index2 = -1;
    while (++index2 < order.length) {
      const prop2 = order[index2];
      if (prop2 in options && options[prop2] !== void 0 && options[prop2] !== null) {
        this[prop2] = prop2 === "history" ? [...options[prop2]] : options[prop2];
      }
    }
    let prop;
    for (prop in options) {
      if (!order.includes(prop)) {
        this[prop] = options[prop];
      }
    }
  }
  /**
   * Get the full path (example: `'~/index.min.js'`).
   *
   * @returns {string}
   */
  get path() {
    return this.history[this.history.length - 1];
  }
  /**
   * Set the full path (example: `'~/index.min.js'`).
   *
   * Cannot be nullified.
   * You can set a file URL (a `URL` object with a `file:` protocol) which will
   * be turned into a path with `url.fileURLToPath`.
   *
   * @param {string | URL} path
   */
  set path(path3) {
    if (isUrl(path3)) {
      path3 = urlToPath(path3);
    }
    assertNonEmpty(path3, "path");
    if (this.path !== path3) {
      this.history.push(path3);
    }
  }
  /**
   * Get the parent path (example: `'~'`).
   */
  get dirname() {
    return typeof this.path === "string" ? path.dirname(this.path) : void 0;
  }
  /**
   * Set the parent path (example: `'~'`).
   *
   * Cannot be set if there’s no `path` yet.
   */
  set dirname(dirname2) {
    assertPath2(this.basename, "dirname");
    this.path = path.join(dirname2 || "", this.basename);
  }
  /**
   * Get the basename (including extname) (example: `'index.min.js'`).
   */
  get basename() {
    return typeof this.path === "string" ? path.basename(this.path) : void 0;
  }
  /**
   * Set basename (including extname) (`'index.min.js'`).
   *
   * Cannot contain path separators (`'/'` on unix, macOS, and browsers, `'\'`
   * on windows).
   * Cannot be nullified (use `file.path = file.dirname` instead).
   */
  set basename(basename2) {
    assertNonEmpty(basename2, "basename");
    assertPart(basename2, "basename");
    this.path = path.join(this.dirname || "", basename2);
  }
  /**
   * Get the extname (including dot) (example: `'.js'`).
   */
  get extname() {
    return typeof this.path === "string" ? path.extname(this.path) : void 0;
  }
  /**
   * Set the extname (including dot) (example: `'.js'`).
   *
   * Cannot contain path separators (`'/'` on unix, macOS, and browsers, `'\'`
   * on windows).
   * Cannot be set if there’s no `path` yet.
   */
  set extname(extname2) {
    assertPart(extname2, "extname");
    assertPath2(this.dirname, "extname");
    if (extname2) {
      if (extname2.charCodeAt(0) !== 46) {
        throw new Error("`extname` must start with `.`");
      }
      if (extname2.includes(".", 1)) {
        throw new Error("`extname` cannot contain multiple dots");
      }
    }
    this.path = path.join(this.dirname, this.stem + (extname2 || ""));
  }
  /**
   * Get the stem (basename w/o extname) (example: `'index.min'`).
   */
  get stem() {
    return typeof this.path === "string" ? path.basename(this.path, this.extname) : void 0;
  }
  /**
   * Set the stem (basename w/o extname) (example: `'index.min'`).
   *
   * Cannot contain path separators (`'/'` on unix, macOS, and browsers, `'\'`
   * on windows).
   * Cannot be nullified (use `file.path = file.dirname` instead).
   */
  set stem(stem) {
    assertNonEmpty(stem, "stem");
    assertPart(stem, "stem");
    this.path = path.join(this.dirname || "", stem + (this.extname || ""));
  }
  /**
   * Serialize the file.
   *
   * @param {BufferEncoding | null | undefined} [encoding='utf8']
   *   Character encoding to understand `value` as when it’s a `Buffer`
   *   (default: `'utf8'`).
   * @returns {string}
   *   Serialized file.
   */
  toString(encoding) {
    return (this.value || "").toString(encoding || void 0);
  }
  /**
   * Create a warning message associated with the file.
   *
   * Its `fatal` is set to `false` and `file` is set to the current file path.
   * Its added to `file.messages`.
   *
   * @param {string | Error | VFileMessage} reason
   *   Reason for message, uses the stack and message of the error if given.
   * @param {Node | NodeLike | Position | Point | null | undefined} [place]
   *   Place in file where the message occurred.
   * @param {string | null | undefined} [origin]
   *   Place in code where the message originates (example:
   *   `'my-package:my-rule'` or `'my-rule'`).
   * @returns {VFileMessage}
   *   Message.
   */
  message(reason, place, origin) {
    const message = new VFileMessage(reason, place, origin);
    if (this.path) {
      message.name = this.path + ":" + message.name;
      message.file = this.path;
    }
    message.fatal = false;
    this.messages.push(message);
    return message;
  }
  /**
   * Create an info message associated with the file.
   *
   * Its `fatal` is set to `null` and `file` is set to the current file path.
   * Its added to `file.messages`.
   *
   * @param {string | Error | VFileMessage} reason
   *   Reason for message, uses the stack and message of the error if given.
   * @param {Node | NodeLike | Position | Point | null | undefined} [place]
   *   Place in file where the message occurred.
   * @param {string | null | undefined} [origin]
   *   Place in code where the message originates (example:
   *   `'my-package:my-rule'` or `'my-rule'`).
   * @returns {VFileMessage}
   *   Message.
   */
  info(reason, place, origin) {
    const message = this.message(reason, place, origin);
    message.fatal = null;
    return message;
  }
  /**
   * Create a fatal error associated with the file.
   *
   * Its `fatal` is set to `true` and `file` is set to the current file path.
   * Its added to `file.messages`.
   *
   * > 👉 **Note**: a fatal error means that a file is no longer processable.
   *
   * @param {string | Error | VFileMessage} reason
   *   Reason for message, uses the stack and message of the error if given.
   * @param {Node | NodeLike | Position | Point | null | undefined} [place]
   *   Place in file where the message occurred.
   * @param {string | null | undefined} [origin]
   *   Place in code where the message originates (example:
   *   `'my-package:my-rule'` or `'my-rule'`).
   * @returns {never}
   *   Message.
   * @throws {VFileMessage}
   *   Message.
   */
  fail(reason, place, origin) {
    const message = this.message(reason, place, origin);
    message.fatal = true;
    throw message;
  }
};
function assertPart(part, name) {
  if (part && part.includes(path.sep)) {
    throw new Error(
      "`" + name + "` cannot be a path: did not expect `" + path.sep + "`"
    );
  }
}
function assertNonEmpty(part, name) {
  if (!part) {
    throw new Error("`" + name + "` cannot be empty");
  }
}
function assertPath2(path3, name) {
  if (!path3) {
    throw new Error("Setting `" + name + "` requires `path` to be set too");
  }
}
function buffer(value) {
  return (0, import_is_buffer.default)(value);
}

// node_modules/.pnpm/bail@2.0.2/node_modules/bail/index.js
function bail(error) {
  if (error) {
    throw error;
  }
}

// node_modules/.pnpm/unified@10.1.2/node_modules/unified/lib/index.js
var import_is_buffer2 = __toESM(require_is_buffer(), 1);
var import_extend = __toESM(require_extend(), 1);

// node_modules/.pnpm/is-plain-obj@4.1.0/node_modules/is-plain-obj/index.js
function isPlainObject(value) {
  if (typeof value !== "object" || value === null) {
    return false;
  }
  const prototype = Object.getPrototypeOf(value);
  return (prototype === null || prototype === Object.prototype || Object.getPrototypeOf(prototype) === null) && !(Symbol.toStringTag in value) && !(Symbol.iterator in value);
}

// node_modules/.pnpm/trough@2.2.0/node_modules/trough/lib/index.js
function trough() {
  const fns = [];
  const pipeline = { run, use };
  return pipeline;
  function run(...values) {
    let middlewareIndex = -1;
    const callback = values.pop();
    if (typeof callback !== "function") {
      throw new TypeError("Expected function as last argument, not " + callback);
    }
    next(null, ...values);
    function next(error, ...output) {
      const fn = fns[++middlewareIndex];
      let index2 = -1;
      if (error) {
        callback(error);
        return;
      }
      while (++index2 < values.length) {
        if (output[index2] === null || output[index2] === void 0) {
          output[index2] = values[index2];
        }
      }
      values = output;
      if (fn) {
        wrap(fn, next)(...output);
      } else {
        callback(null, ...output);
      }
    }
  }
  function use(middelware) {
    if (typeof middelware !== "function") {
      throw new TypeError(
        "Expected `middelware` to be a function, not " + middelware
      );
    }
    fns.push(middelware);
    return pipeline;
  }
}
function wrap(middleware, callback) {
  let called;
  return wrapped;
  function wrapped(...parameters) {
    const fnExpectsCallback = middleware.length > parameters.length;
    let result;
    if (fnExpectsCallback) {
      parameters.push(done);
    }
    try {
      result = middleware.apply(this, parameters);
    } catch (error) {
      const exception = (
        /** @type {Error} */
        error
      );
      if (fnExpectsCallback && called) {
        throw exception;
      }
      return done(exception);
    }
    if (!fnExpectsCallback) {
      if (result && result.then && typeof result.then === "function") {
        result.then(then, done);
      } else if (result instanceof Error) {
        done(result);
      } else {
        then(result);
      }
    }
  }
  function done(error, ...output) {
    if (!called) {
      called = true;
      callback(error, ...output);
    }
  }
  function then(value) {
    done(null, value);
  }
}

// node_modules/.pnpm/unified@10.1.2/node_modules/unified/lib/index.js
var unified = base().freeze();
var own = {}.hasOwnProperty;
function base() {
  const transformers = trough();
  const attachers = [];
  let namespace = {};
  let frozen;
  let freezeIndex = -1;
  processor.data = data;
  processor.Parser = void 0;
  processor.Compiler = void 0;
  processor.freeze = freeze;
  processor.attachers = attachers;
  processor.use = use;
  processor.parse = parse2;
  processor.stringify = stringify3;
  processor.run = run;
  processor.runSync = runSync;
  processor.process = process2;
  processor.processSync = processSync;
  return processor;
  function processor() {
    const destination = base();
    let index2 = -1;
    while (++index2 < attachers.length) {
      destination.use(...attachers[index2]);
    }
    destination.data((0, import_extend.default)(true, {}, namespace));
    return destination;
  }
  function data(key, value) {
    if (typeof key === "string") {
      if (arguments.length === 2) {
        assertUnfrozen("data", frozen);
        namespace[key] = value;
        return processor;
      }
      return own.call(namespace, key) && namespace[key] || null;
    }
    if (key) {
      assertUnfrozen("data", frozen);
      namespace = key;
      return processor;
    }
    return namespace;
  }
  function freeze() {
    if (frozen) {
      return processor;
    }
    while (++freezeIndex < attachers.length) {
      const [attacher, ...options] = attachers[freezeIndex];
      if (options[0] === false) {
        continue;
      }
      if (options[0] === true) {
        options[0] = void 0;
      }
      const transformer = attacher.call(processor, ...options);
      if (typeof transformer === "function") {
        transformers.use(transformer);
      }
    }
    frozen = true;
    freezeIndex = Number.POSITIVE_INFINITY;
    return processor;
  }
  function use(value, ...options) {
    let settings;
    assertUnfrozen("use", frozen);
    if (value === null || value === void 0) {
    } else if (typeof value === "function") {
      addPlugin(value, ...options);
    } else if (typeof value === "object") {
      if (Array.isArray(value)) {
        addList(value);
      } else {
        addPreset(value);
      }
    } else {
      throw new TypeError("Expected usable value, not `" + value + "`");
    }
    if (settings) {
      namespace.settings = Object.assign(namespace.settings || {}, settings);
    }
    return processor;
    function add(value2) {
      if (typeof value2 === "function") {
        addPlugin(value2);
      } else if (typeof value2 === "object") {
        if (Array.isArray(value2)) {
          const [plugin, ...options2] = value2;
          addPlugin(plugin, ...options2);
        } else {
          addPreset(value2);
        }
      } else {
        throw new TypeError("Expected usable value, not `" + value2 + "`");
      }
    }
    function addPreset(result) {
      addList(result.plugins);
      if (result.settings) {
        settings = Object.assign(settings || {}, result.settings);
      }
    }
    function addList(plugins) {
      let index2 = -1;
      if (plugins === null || plugins === void 0) {
      } else if (Array.isArray(plugins)) {
        while (++index2 < plugins.length) {
          const thing = plugins[index2];
          add(thing);
        }
      } else {
        throw new TypeError("Expected a list of plugins, not `" + plugins + "`");
      }
    }
    function addPlugin(plugin, value2) {
      let index2 = -1;
      let entry;
      while (++index2 < attachers.length) {
        if (attachers[index2][0] === plugin) {
          entry = attachers[index2];
          break;
        }
      }
      if (entry) {
        if (isPlainObject(entry[1]) && isPlainObject(value2)) {
          value2 = (0, import_extend.default)(true, entry[1], value2);
        }
        entry[1] = value2;
      } else {
        attachers.push([...arguments]);
      }
    }
  }
  function parse2(doc) {
    processor.freeze();
    const file = vfile(doc);
    const Parser = processor.Parser;
    assertParser("parse", Parser);
    if (newable(Parser, "parse")) {
      return new Parser(String(file), file).parse();
    }
    return Parser(String(file), file);
  }
  function stringify3(node3, doc) {
    processor.freeze();
    const file = vfile(doc);
    const Compiler = processor.Compiler;
    assertCompiler("stringify", Compiler);
    assertNode(node3);
    if (newable(Compiler, "compile")) {
      return new Compiler(node3, file).compile();
    }
    return Compiler(node3, file);
  }
  function run(node3, doc, callback) {
    assertNode(node3);
    processor.freeze();
    if (!callback && typeof doc === "function") {
      callback = doc;
      doc = void 0;
    }
    if (!callback) {
      return new Promise(executor);
    }
    executor(null, callback);
    function executor(resolve, reject) {
      transformers.run(node3, vfile(doc), done);
      function done(error, tree, file) {
        tree = tree || node3;
        if (error) {
          reject(error);
        } else if (resolve) {
          resolve(tree);
        } else {
          callback(null, tree, file);
        }
      }
    }
  }
  function runSync(node3, file) {
    let result;
    let complete;
    processor.run(node3, file, done);
    assertDone("runSync", "run", complete);
    return result;
    function done(error, tree) {
      bail(error);
      result = tree;
      complete = true;
    }
  }
  function process2(doc, callback) {
    processor.freeze();
    assertParser("process", processor.Parser);
    assertCompiler("process", processor.Compiler);
    if (!callback) {
      return new Promise(executor);
    }
    executor(null, callback);
    function executor(resolve, reject) {
      const file = vfile(doc);
      processor.run(processor.parse(file), file, (error, tree, file2) => {
        if (error || !tree || !file2) {
          done(error);
        } else {
          const result = processor.stringify(tree, file2);
          if (result === void 0 || result === null) {
          } else if (looksLikeAVFileValue(result)) {
            file2.value = result;
          } else {
            file2.result = result;
          }
          done(error, file2);
        }
      });
      function done(error, file2) {
        if (error || !file2) {
          reject(error);
        } else if (resolve) {
          resolve(file2);
        } else {
          callback(null, file2);
        }
      }
    }
  }
  function processSync(doc) {
    let complete;
    processor.freeze();
    assertParser("processSync", processor.Parser);
    assertCompiler("processSync", processor.Compiler);
    const file = vfile(doc);
    processor.process(file, done);
    assertDone("processSync", "process", complete);
    return file;
    function done(error) {
      complete = true;
      bail(error);
    }
  }
}
function newable(value, name) {
  return typeof value === "function" && // Prototypes do exist.
  // type-coverage:ignore-next-line
  value.prototype && // A function with keys in its prototype is probably a constructor.
  // Classes’ prototype methods are not enumerable, so we check if some value
  // exists in the prototype.
  // type-coverage:ignore-next-line
  (keys(value.prototype) || name in value.prototype);
}
function keys(value) {
  let key;
  for (key in value) {
    if (own.call(value, key)) {
      return true;
    }
  }
  return false;
}
function assertParser(name, value) {
  if (typeof value !== "function") {
    throw new TypeError("Cannot `" + name + "` without `Parser`");
  }
}
function assertCompiler(name, value) {
  if (typeof value !== "function") {
    throw new TypeError("Cannot `" + name + "` without `Compiler`");
  }
}
function assertUnfrozen(name, frozen) {
  if (frozen) {
    throw new Error(
      "Cannot call `" + name + "` on a frozen processor.\nCreate a new processor first, by calling it: use `processor()` instead of `processor`."
    );
  }
}
function assertNode(node3) {
  if (!isPlainObject(node3) || typeof node3.type !== "string") {
    throw new TypeError("Expected node, got `" + node3 + "`");
  }
}
function assertDone(name, asyncName, complete) {
  if (!complete) {
    throw new Error(
      "`" + name + "` finished async. Use `" + asyncName + "` instead"
    );
  }
}
function vfile(value) {
  return looksLikeAVFile(value) ? value : new VFile(value);
}
function looksLikeAVFile(value) {
  return Boolean(
    value && typeof value === "object" && "message" in value && "messages" in value
  );
}
function looksLikeAVFileValue(value) {
  return typeof value === "string" || (0, import_is_buffer2.default)(value);
}

// node_modules/.pnpm/mdast-util-to-string@3.2.0/node_modules/mdast-util-to-string/lib/index.js
var emptyOptions = {};
function toString(value, options) {
  const settings = options || emptyOptions;
  const includeImageAlt = typeof settings.includeImageAlt === "boolean" ? settings.includeImageAlt : true;
  const includeHtml = typeof settings.includeHtml === "boolean" ? settings.includeHtml : true;
  return one(value, includeImageAlt, includeHtml);
}
function one(value, includeImageAlt, includeHtml) {
  if (node(value)) {
    if ("value" in value) {
      return value.type === "html" && !includeHtml ? "" : value.value;
    }
    if (includeImageAlt && "alt" in value && value.alt) {
      return value.alt;
    }
    if ("children" in value) {
      return all(value.children, includeImageAlt, includeHtml);
    }
  }
  if (Array.isArray(value)) {
    return all(value, includeImageAlt, includeHtml);
  }
  return "";
}
function all(values, includeImageAlt, includeHtml) {
  const result = [];
  let index2 = -1;
  while (++index2 < values.length) {
    result[index2] = one(values[index2], includeImageAlt, includeHtml);
  }
  return result.join("");
}
function node(value) {
  return Boolean(value && typeof value === "object");
}

// node_modules/.pnpm/micromark-util-chunked@1.1.0/node_modules/micromark-util-chunked/index.js
function splice(list4, start, remove, items) {
  const end = list4.length;
  let chunkStart = 0;
  let parameters;
  if (start < 0) {
    start = -start > end ? 0 : end + start;
  } else {
    start = start > end ? end : start;
  }
  remove = remove > 0 ? remove : 0;
  if (items.length < 1e4) {
    parameters = Array.from(items);
    parameters.unshift(start, remove);
    list4.splice(...parameters);
  } else {
    if (remove)
      list4.splice(start, remove);
    while (chunkStart < items.length) {
      parameters = items.slice(chunkStart, chunkStart + 1e4);
      parameters.unshift(start, 0);
      list4.splice(...parameters);
      chunkStart += 1e4;
      start += 1e4;
    }
  }
}
function push(list4, items) {
  if (list4.length > 0) {
    splice(list4, list4.length, 0, items);
    return list4;
  }
  return items;
}

// node_modules/.pnpm/micromark-util-combine-extensions@1.1.0/node_modules/micromark-util-combine-extensions/index.js
var hasOwnProperty = {}.hasOwnProperty;
function combineExtensions(extensions) {
  const all4 = {};
  let index2 = -1;
  while (++index2 < extensions.length) {
    syntaxExtension(all4, extensions[index2]);
  }
  return all4;
}
function syntaxExtension(all4, extension2) {
  let hook;
  for (hook in extension2) {
    const maybe = hasOwnProperty.call(all4, hook) ? all4[hook] : void 0;
    const left = maybe || (all4[hook] = {});
    const right = extension2[hook];
    let code4;
    if (right) {
      for (code4 in right) {
        if (!hasOwnProperty.call(left, code4))
          left[code4] = [];
        const value = right[code4];
        constructs(
          // @ts-expect-error Looks like a list.
          left[code4],
          Array.isArray(value) ? value : value ? [value] : []
        );
      }
    }
  }
}
function constructs(existing, list4) {
  let index2 = -1;
  const before = [];
  while (++index2 < list4.length) {
    ;
    (list4[index2].add === "after" ? existing : before).push(list4[index2]);
  }
  splice(existing, 0, 0, before);
}

// node_modules/.pnpm/micromark-util-character@1.2.0/node_modules/micromark-util-character/lib/unicode-punctuation-regex.js
var unicodePunctuationRegex = /[!-\/:-@\[-`\{-~\xA1\xA7\xAB\xB6\xB7\xBB\xBF\u037E\u0387\u055A-\u055F\u0589\u058A\u05BE\u05C0\u05C3\u05C6\u05F3\u05F4\u0609\u060A\u060C\u060D\u061B\u061D-\u061F\u066A-\u066D\u06D4\u0700-\u070D\u07F7-\u07F9\u0830-\u083E\u085E\u0964\u0965\u0970\u09FD\u0A76\u0AF0\u0C77\u0C84\u0DF4\u0E4F\u0E5A\u0E5B\u0F04-\u0F12\u0F14\u0F3A-\u0F3D\u0F85\u0FD0-\u0FD4\u0FD9\u0FDA\u104A-\u104F\u10FB\u1360-\u1368\u1400\u166E\u169B\u169C\u16EB-\u16ED\u1735\u1736\u17D4-\u17D6\u17D8-\u17DA\u1800-\u180A\u1944\u1945\u1A1E\u1A1F\u1AA0-\u1AA6\u1AA8-\u1AAD\u1B5A-\u1B60\u1B7D\u1B7E\u1BFC-\u1BFF\u1C3B-\u1C3F\u1C7E\u1C7F\u1CC0-\u1CC7\u1CD3\u2010-\u2027\u2030-\u2043\u2045-\u2051\u2053-\u205E\u207D\u207E\u208D\u208E\u2308-\u230B\u2329\u232A\u2768-\u2775\u27C5\u27C6\u27E6-\u27EF\u2983-\u2998\u29D8-\u29DB\u29FC\u29FD\u2CF9-\u2CFC\u2CFE\u2CFF\u2D70\u2E00-\u2E2E\u2E30-\u2E4F\u2E52-\u2E5D\u3001-\u3003\u3008-\u3011\u3014-\u301F\u3030\u303D\u30A0\u30FB\uA4FE\uA4FF\uA60D-\uA60F\uA673\uA67E\uA6F2-\uA6F7\uA874-\uA877\uA8CE\uA8CF\uA8F8-\uA8FA\uA8FC\uA92E\uA92F\uA95F\uA9C1-\uA9CD\uA9DE\uA9DF\uAA5C-\uAA5F\uAADE\uAADF\uAAF0\uAAF1\uABEB\uFD3E\uFD3F\uFE10-\uFE19\uFE30-\uFE52\uFE54-\uFE61\uFE63\uFE68\uFE6A\uFE6B\uFF01-\uFF03\uFF05-\uFF0A\uFF0C-\uFF0F\uFF1A\uFF1B\uFF1F\uFF20\uFF3B-\uFF3D\uFF3F\uFF5B\uFF5D\uFF5F-\uFF65]/;

// node_modules/.pnpm/micromark-util-character@1.2.0/node_modules/micromark-util-character/index.js
var asciiAlpha = regexCheck(/[A-Za-z]/);
var asciiAlphanumeric = regexCheck(/[\dA-Za-z]/);
var asciiAtext = regexCheck(/[#-'*+\--9=?A-Z^-~]/);
function asciiControl(code4) {
  return (
    // Special whitespace codes (which have negative values), C0 and Control
    // character DEL
    code4 !== null && (code4 < 32 || code4 === 127)
  );
}
var asciiDigit = regexCheck(/\d/);
var asciiHexDigit = regexCheck(/[\dA-Fa-f]/);
var asciiPunctuation = regexCheck(/[!-/:-@[-`{-~]/);
function markdownLineEnding(code4) {
  return code4 !== null && code4 < -2;
}
function markdownLineEndingOrSpace(code4) {
  return code4 !== null && (code4 < 0 || code4 === 32);
}
function markdownSpace(code4) {
  return code4 === -2 || code4 === -1 || code4 === 32;
}
var unicodePunctuation = regexCheck(unicodePunctuationRegex);
var unicodeWhitespace = regexCheck(/\s/);
function regexCheck(regex) {
  return check;
  function check(code4) {
    return code4 !== null && regex.test(String.fromCharCode(code4));
  }
}

// node_modules/.pnpm/micromark-factory-space@1.1.0/node_modules/micromark-factory-space/index.js
function factorySpace(effects, ok4, type, max) {
  const limit = max ? max - 1 : Number.POSITIVE_INFINITY;
  let size = 0;
  return start;
  function start(code4) {
    if (markdownSpace(code4)) {
      effects.enter(type);
      return prefix(code4);
    }
    return ok4(code4);
  }
  function prefix(code4) {
    if (markdownSpace(code4) && size++ < limit) {
      effects.consume(code4);
      return prefix;
    }
    effects.exit(type);
    return ok4(code4);
  }
}

// node_modules/.pnpm/micromark@3.2.0/node_modules/micromark/lib/initialize/content.js
var content = {
  tokenize: initializeContent
};
function initializeContent(effects) {
  const contentStart = effects.attempt(
    this.parser.constructs.contentInitial,
    afterContentStartConstruct,
    paragraphInitial
  );
  let previous3;
  return contentStart;
  function afterContentStartConstruct(code4) {
    if (code4 === null) {
      effects.consume(code4);
      return;
    }
    effects.enter("lineEnding");
    effects.consume(code4);
    effects.exit("lineEnding");
    return factorySpace(effects, contentStart, "linePrefix");
  }
  function paragraphInitial(code4) {
    effects.enter("paragraph");
    return lineStart(code4);
  }
  function lineStart(code4) {
    const token = effects.enter("chunkText", {
      contentType: "text",
      previous: previous3
    });
    if (previous3) {
      previous3.next = token;
    }
    previous3 = token;
    return data(code4);
  }
  function data(code4) {
    if (code4 === null) {
      effects.exit("chunkText");
      effects.exit("paragraph");
      effects.consume(code4);
      return;
    }
    if (markdownLineEnding(code4)) {
      effects.consume(code4);
      effects.exit("chunkText");
      return lineStart;
    }
    effects.consume(code4);
    return data;
  }
}

// node_modules/.pnpm/micromark@3.2.0/node_modules/micromark/lib/initialize/document.js
var document2 = {
  tokenize: initializeDocument
};
var containerConstruct = {
  tokenize: tokenizeContainer
};
function initializeDocument(effects) {
  const self = this;
  const stack = [];
  let continued = 0;
  let childFlow;
  let childToken;
  let lineStartOffset;
  return start;
  function start(code4) {
    if (continued < stack.length) {
      const item = stack[continued];
      self.containerState = item[1];
      return effects.attempt(
        item[0].continuation,
        documentContinue,
        checkNewContainers
      )(code4);
    }
    return checkNewContainers(code4);
  }
  function documentContinue(code4) {
    continued++;
    if (self.containerState._closeFlow) {
      self.containerState._closeFlow = void 0;
      if (childFlow) {
        closeFlow();
      }
      const indexBeforeExits = self.events.length;
      let indexBeforeFlow = indexBeforeExits;
      let point4;
      while (indexBeforeFlow--) {
        if (self.events[indexBeforeFlow][0] === "exit" && self.events[indexBeforeFlow][1].type === "chunkFlow") {
          point4 = self.events[indexBeforeFlow][1].end;
          break;
        }
      }
      exitContainers(continued);
      let index2 = indexBeforeExits;
      while (index2 < self.events.length) {
        self.events[index2][1].end = Object.assign({}, point4);
        index2++;
      }
      splice(
        self.events,
        indexBeforeFlow + 1,
        0,
        self.events.slice(indexBeforeExits)
      );
      self.events.length = index2;
      return checkNewContainers(code4);
    }
    return start(code4);
  }
  function checkNewContainers(code4) {
    if (continued === stack.length) {
      if (!childFlow) {
        return documentContinued(code4);
      }
      if (childFlow.currentConstruct && childFlow.currentConstruct.concrete) {
        return flowStart(code4);
      }
      self.interrupt = Boolean(
        childFlow.currentConstruct && !childFlow._gfmTableDynamicInterruptHack
      );
    }
    self.containerState = {};
    return effects.check(
      containerConstruct,
      thereIsANewContainer,
      thereIsNoNewContainer
    )(code4);
  }
  function thereIsANewContainer(code4) {
    if (childFlow)
      closeFlow();
    exitContainers(continued);
    return documentContinued(code4);
  }
  function thereIsNoNewContainer(code4) {
    self.parser.lazy[self.now().line] = continued !== stack.length;
    lineStartOffset = self.now().offset;
    return flowStart(code4);
  }
  function documentContinued(code4) {
    self.containerState = {};
    return effects.attempt(
      containerConstruct,
      containerContinue,
      flowStart
    )(code4);
  }
  function containerContinue(code4) {
    continued++;
    stack.push([self.currentConstruct, self.containerState]);
    return documentContinued(code4);
  }
  function flowStart(code4) {
    if (code4 === null) {
      if (childFlow)
        closeFlow();
      exitContainers(0);
      effects.consume(code4);
      return;
    }
    childFlow = childFlow || self.parser.flow(self.now());
    effects.enter("chunkFlow", {
      contentType: "flow",
      previous: childToken,
      _tokenizer: childFlow
    });
    return flowContinue(code4);
  }
  function flowContinue(code4) {
    if (code4 === null) {
      writeToChild(effects.exit("chunkFlow"), true);
      exitContainers(0);
      effects.consume(code4);
      return;
    }
    if (markdownLineEnding(code4)) {
      effects.consume(code4);
      writeToChild(effects.exit("chunkFlow"));
      continued = 0;
      self.interrupt = void 0;
      return start;
    }
    effects.consume(code4);
    return flowContinue;
  }
  function writeToChild(token, eof) {
    const stream = self.sliceStream(token);
    if (eof)
      stream.push(null);
    token.previous = childToken;
    if (childToken)
      childToken.next = token;
    childToken = token;
    childFlow.defineSkip(token.start);
    childFlow.write(stream);
    if (self.parser.lazy[token.start.line]) {
      let index2 = childFlow.events.length;
      while (index2--) {
        if (
          // The token starts before the line ending…
          childFlow.events[index2][1].start.offset < lineStartOffset && // …and either is not ended yet…
          (!childFlow.events[index2][1].end || // …or ends after it.
          childFlow.events[index2][1].end.offset > lineStartOffset)
        ) {
          return;
        }
      }
      const indexBeforeExits = self.events.length;
      let indexBeforeFlow = indexBeforeExits;
      let seen;
      let point4;
      while (indexBeforeFlow--) {
        if (self.events[indexBeforeFlow][0] === "exit" && self.events[indexBeforeFlow][1].type === "chunkFlow") {
          if (seen) {
            point4 = self.events[indexBeforeFlow][1].end;
            break;
          }
          seen = true;
        }
      }
      exitContainers(continued);
      index2 = indexBeforeExits;
      while (index2 < self.events.length) {
        self.events[index2][1].end = Object.assign({}, point4);
        index2++;
      }
      splice(
        self.events,
        indexBeforeFlow + 1,
        0,
        self.events.slice(indexBeforeExits)
      );
      self.events.length = index2;
    }
  }
  function exitContainers(size) {
    let index2 = stack.length;
    while (index2-- > size) {
      const entry = stack[index2];
      self.containerState = entry[1];
      entry[0].exit.call(self, effects);
    }
    stack.length = size;
  }
  function closeFlow() {
    childFlow.write([null]);
    childToken = void 0;
    childFlow = void 0;
    self.containerState._closeFlow = void 0;
  }
}
function tokenizeContainer(effects, ok4, nok) {
  return factorySpace(
    effects,
    effects.attempt(this.parser.constructs.document, ok4, nok),
    "linePrefix",
    this.parser.constructs.disable.null.includes("codeIndented") ? void 0 : 4
  );
}

// node_modules/.pnpm/micromark-util-classify-character@1.1.0/node_modules/micromark-util-classify-character/index.js
function classifyCharacter(code4) {
  if (code4 === null || markdownLineEndingOrSpace(code4) || unicodeWhitespace(code4)) {
    return 1;
  }
  if (unicodePunctuation(code4)) {
    return 2;
  }
}

// node_modules/.pnpm/micromark-util-resolve-all@1.1.0/node_modules/micromark-util-resolve-all/index.js
function resolveAll(constructs3, events, context) {
  const called = [];
  let index2 = -1;
  while (++index2 < constructs3.length) {
    const resolve = constructs3[index2].resolveAll;
    if (resolve && !called.includes(resolve)) {
      events = resolve(events, context);
      called.push(resolve);
    }
  }
  return events;
}

// node_modules/.pnpm/micromark-core-commonmark@1.1.0/node_modules/micromark-core-commonmark/lib/attention.js
var attention = {
  name: "attention",
  tokenize: tokenizeAttention,
  resolveAll: resolveAllAttention
};
function resolveAllAttention(events, context) {
  let index2 = -1;
  let open;
  let group;
  let text6;
  let openingSequence;
  let closingSequence;
  let use;
  let nextEvents;
  let offset;
  while (++index2 < events.length) {
    if (events[index2][0] === "enter" && events[index2][1].type === "attentionSequence" && events[index2][1]._close) {
      open = index2;
      while (open--) {
        if (events[open][0] === "exit" && events[open][1].type === "attentionSequence" && events[open][1]._open && // If the markers are the same:
        context.sliceSerialize(events[open][1]).charCodeAt(0) === context.sliceSerialize(events[index2][1]).charCodeAt(0)) {
          if ((events[open][1]._close || events[index2][1]._open) && (events[index2][1].end.offset - events[index2][1].start.offset) % 3 && !((events[open][1].end.offset - events[open][1].start.offset + events[index2][1].end.offset - events[index2][1].start.offset) % 3)) {
            continue;
          }
          use = events[open][1].end.offset - events[open][1].start.offset > 1 && events[index2][1].end.offset - events[index2][1].start.offset > 1 ? 2 : 1;
          const start = Object.assign({}, events[open][1].end);
          const end = Object.assign({}, events[index2][1].start);
          movePoint(start, -use);
          movePoint(end, use);
          openingSequence = {
            type: use > 1 ? "strongSequence" : "emphasisSequence",
            start,
            end: Object.assign({}, events[open][1].end)
          };
          closingSequence = {
            type: use > 1 ? "strongSequence" : "emphasisSequence",
            start: Object.assign({}, events[index2][1].start),
            end
          };
          text6 = {
            type: use > 1 ? "strongText" : "emphasisText",
            start: Object.assign({}, events[open][1].end),
            end: Object.assign({}, events[index2][1].start)
          };
          group = {
            type: use > 1 ? "strong" : "emphasis",
            start: Object.assign({}, openingSequence.start),
            end: Object.assign({}, closingSequence.end)
          };
          events[open][1].end = Object.assign({}, openingSequence.start);
          events[index2][1].start = Object.assign({}, closingSequence.end);
          nextEvents = [];
          if (events[open][1].end.offset - events[open][1].start.offset) {
            nextEvents = push(nextEvents, [
              ["enter", events[open][1], context],
              ["exit", events[open][1], context]
            ]);
          }
          nextEvents = push(nextEvents, [
            ["enter", group, context],
            ["enter", openingSequence, context],
            ["exit", openingSequence, context],
            ["enter", text6, context]
          ]);
          nextEvents = push(
            nextEvents,
            resolveAll(
              context.parser.constructs.insideSpan.null,
              events.slice(open + 1, index2),
              context
            )
          );
          nextEvents = push(nextEvents, [
            ["exit", text6, context],
            ["enter", closingSequence, context],
            ["exit", closingSequence, context],
            ["exit", group, context]
          ]);
          if (events[index2][1].end.offset - events[index2][1].start.offset) {
            offset = 2;
            nextEvents = push(nextEvents, [
              ["enter", events[index2][1], context],
              ["exit", events[index2][1], context]
            ]);
          } else {
            offset = 0;
          }
          splice(events, open - 1, index2 - open + 3, nextEvents);
          index2 = open + nextEvents.length - offset - 2;
          break;
        }
      }
    }
  }
  index2 = -1;
  while (++index2 < events.length) {
    if (events[index2][1].type === "attentionSequence") {
      events[index2][1].type = "data";
    }
  }
  return events;
}
function tokenizeAttention(effects, ok4) {
  const attentionMarkers2 = this.parser.constructs.attentionMarkers.null;
  const previous3 = this.previous;
  const before = classifyCharacter(previous3);
  let marker;
  return start;
  function start(code4) {
    marker = code4;
    effects.enter("attentionSequence");
    return inside(code4);
  }
  function inside(code4) {
    if (code4 === marker) {
      effects.consume(code4);
      return inside;
    }
    const token = effects.exit("attentionSequence");
    const after = classifyCharacter(code4);
    const open = !after || after === 2 && before || attentionMarkers2.includes(code4);
    const close = !before || before === 2 && after || attentionMarkers2.includes(previous3);
    token._open = Boolean(marker === 42 ? open : open && (before || !close));
    token._close = Boolean(marker === 42 ? close : close && (after || !open));
    return ok4(code4);
  }
}
function movePoint(point4, offset) {
  point4.column += offset;
  point4.offset += offset;
  point4._bufferIndex += offset;
}

// node_modules/.pnpm/micromark-core-commonmark@1.1.0/node_modules/micromark-core-commonmark/lib/autolink.js
var autolink = {
  name: "autolink",
  tokenize: tokenizeAutolink
};
function tokenizeAutolink(effects, ok4, nok) {
  let size = 0;
  return start;
  function start(code4) {
    effects.enter("autolink");
    effects.enter("autolinkMarker");
    effects.consume(code4);
    effects.exit("autolinkMarker");
    effects.enter("autolinkProtocol");
    return open;
  }
  function open(code4) {
    if (asciiAlpha(code4)) {
      effects.consume(code4);
      return schemeOrEmailAtext;
    }
    return emailAtext(code4);
  }
  function schemeOrEmailAtext(code4) {
    if (code4 === 43 || code4 === 45 || code4 === 46 || asciiAlphanumeric(code4)) {
      size = 1;
      return schemeInsideOrEmailAtext(code4);
    }
    return emailAtext(code4);
  }
  function schemeInsideOrEmailAtext(code4) {
    if (code4 === 58) {
      effects.consume(code4);
      size = 0;
      return urlInside;
    }
    if ((code4 === 43 || code4 === 45 || code4 === 46 || asciiAlphanumeric(code4)) && size++ < 32) {
      effects.consume(code4);
      return schemeInsideOrEmailAtext;
    }
    size = 0;
    return emailAtext(code4);
  }
  function urlInside(code4) {
    if (code4 === 62) {
      effects.exit("autolinkProtocol");
      effects.enter("autolinkMarker");
      effects.consume(code4);
      effects.exit("autolinkMarker");
      effects.exit("autolink");
      return ok4;
    }
    if (code4 === null || code4 === 32 || code4 === 60 || asciiControl(code4)) {
      return nok(code4);
    }
    effects.consume(code4);
    return urlInside;
  }
  function emailAtext(code4) {
    if (code4 === 64) {
      effects.consume(code4);
      return emailAtSignOrDot;
    }
    if (asciiAtext(code4)) {
      effects.consume(code4);
      return emailAtext;
    }
    return nok(code4);
  }
  function emailAtSignOrDot(code4) {
    return asciiAlphanumeric(code4) ? emailLabel(code4) : nok(code4);
  }
  function emailLabel(code4) {
    if (code4 === 46) {
      effects.consume(code4);
      size = 0;
      return emailAtSignOrDot;
    }
    if (code4 === 62) {
      effects.exit("autolinkProtocol").type = "autolinkEmail";
      effects.enter("autolinkMarker");
      effects.consume(code4);
      effects.exit("autolinkMarker");
      effects.exit("autolink");
      return ok4;
    }
    return emailValue(code4);
  }
  function emailValue(code4) {
    if ((code4 === 45 || asciiAlphanumeric(code4)) && size++ < 63) {
      const next = code4 === 45 ? emailValue : emailLabel;
      effects.consume(code4);
      return next;
    }
    return nok(code4);
  }
}

// node_modules/.pnpm/micromark-core-commonmark@1.1.0/node_modules/micromark-core-commonmark/lib/blank-line.js
var blankLine = {
  tokenize: tokenizeBlankLine,
  partial: true
};
function tokenizeBlankLine(effects, ok4, nok) {
  return start;
  function start(code4) {
    return markdownSpace(code4) ? factorySpace(effects, after, "linePrefix")(code4) : after(code4);
  }
  function after(code4) {
    return code4 === null || markdownLineEnding(code4) ? ok4(code4) : nok(code4);
  }
}

// node_modules/.pnpm/micromark-core-commonmark@1.1.0/node_modules/micromark-core-commonmark/lib/block-quote.js
var blockQuote = {
  name: "blockQuote",
  tokenize: tokenizeBlockQuoteStart,
  continuation: {
    tokenize: tokenizeBlockQuoteContinuation
  },
  exit
};
function tokenizeBlockQuoteStart(effects, ok4, nok) {
  const self = this;
  return start;
  function start(code4) {
    if (code4 === 62) {
      const state = self.containerState;
      if (!state.open) {
        effects.enter("blockQuote", {
          _container: true
        });
        state.open = true;
      }
      effects.enter("blockQuotePrefix");
      effects.enter("blockQuoteMarker");
      effects.consume(code4);
      effects.exit("blockQuoteMarker");
      return after;
    }
    return nok(code4);
  }
  function after(code4) {
    if (markdownSpace(code4)) {
      effects.enter("blockQuotePrefixWhitespace");
      effects.consume(code4);
      effects.exit("blockQuotePrefixWhitespace");
      effects.exit("blockQuotePrefix");
      return ok4;
    }
    effects.exit("blockQuotePrefix");
    return ok4(code4);
  }
}
function tokenizeBlockQuoteContinuation(effects, ok4, nok) {
  const self = this;
  return contStart;
  function contStart(code4) {
    if (markdownSpace(code4)) {
      return factorySpace(
        effects,
        contBefore,
        "linePrefix",
        self.parser.constructs.disable.null.includes("codeIndented") ? void 0 : 4
      )(code4);
    }
    return contBefore(code4);
  }
  function contBefore(code4) {
    return effects.attempt(blockQuote, ok4, nok)(code4);
  }
}
function exit(effects) {
  effects.exit("blockQuote");
}

// node_modules/.pnpm/micromark-core-commonmark@1.1.0/node_modules/micromark-core-commonmark/lib/character-escape.js
var characterEscape = {
  name: "characterEscape",
  tokenize: tokenizeCharacterEscape
};
function tokenizeCharacterEscape(effects, ok4, nok) {
  return start;
  function start(code4) {
    effects.enter("characterEscape");
    effects.enter("escapeMarker");
    effects.consume(code4);
    effects.exit("escapeMarker");
    return inside;
  }
  function inside(code4) {
    if (asciiPunctuation(code4)) {
      effects.enter("characterEscapeValue");
      effects.consume(code4);
      effects.exit("characterEscapeValue");
      effects.exit("characterEscape");
      return ok4;
    }
    return nok(code4);
  }
}

// node_modules/.pnpm/decode-named-character-reference@1.0.2/node_modules/decode-named-character-reference/index.dom.js
var element = document.createElement("i");
function decodeNamedCharacterReference(value) {
  const characterReference2 = "&" + value + ";";
  element.innerHTML = characterReference2;
  const char = element.textContent;
  if (char.charCodeAt(char.length - 1) === 59 && value !== "semi") {
    return false;
  }
  return char === characterReference2 ? false : char;
}

// node_modules/.pnpm/micromark-core-commonmark@1.1.0/node_modules/micromark-core-commonmark/lib/character-reference.js
var characterReference = {
  name: "characterReference",
  tokenize: tokenizeCharacterReference
};
function tokenizeCharacterReference(effects, ok4, nok) {
  const self = this;
  let size = 0;
  let max;
  let test;
  return start;
  function start(code4) {
    effects.enter("characterReference");
    effects.enter("characterReferenceMarker");
    effects.consume(code4);
    effects.exit("characterReferenceMarker");
    return open;
  }
  function open(code4) {
    if (code4 === 35) {
      effects.enter("characterReferenceMarkerNumeric");
      effects.consume(code4);
      effects.exit("characterReferenceMarkerNumeric");
      return numeric;
    }
    effects.enter("characterReferenceValue");
    max = 31;
    test = asciiAlphanumeric;
    return value(code4);
  }
  function numeric(code4) {
    if (code4 === 88 || code4 === 120) {
      effects.enter("characterReferenceMarkerHexadecimal");
      effects.consume(code4);
      effects.exit("characterReferenceMarkerHexadecimal");
      effects.enter("characterReferenceValue");
      max = 6;
      test = asciiHexDigit;
      return value;
    }
    effects.enter("characterReferenceValue");
    max = 7;
    test = asciiDigit;
    return value(code4);
  }
  function value(code4) {
    if (code4 === 59 && size) {
      const token = effects.exit("characterReferenceValue");
      if (test === asciiAlphanumeric && !decodeNamedCharacterReference(self.sliceSerialize(token))) {
        return nok(code4);
      }
      effects.enter("characterReferenceMarker");
      effects.consume(code4);
      effects.exit("characterReferenceMarker");
      effects.exit("characterReference");
      return ok4;
    }
    if (test(code4) && size++ < max) {
      effects.consume(code4);
      return value;
    }
    return nok(code4);
  }
}

// node_modules/.pnpm/micromark-core-commonmark@1.1.0/node_modules/micromark-core-commonmark/lib/code-fenced.js
var nonLazyContinuation = {
  tokenize: tokenizeNonLazyContinuation,
  partial: true
};
var codeFenced = {
  name: "codeFenced",
  tokenize: tokenizeCodeFenced,
  concrete: true
};
function tokenizeCodeFenced(effects, ok4, nok) {
  const self = this;
  const closeStart = {
    tokenize: tokenizeCloseStart,
    partial: true
  };
  let initialPrefix = 0;
  let sizeOpen = 0;
  let marker;
  return start;
  function start(code4) {
    return beforeSequenceOpen(code4);
  }
  function beforeSequenceOpen(code4) {
    const tail = self.events[self.events.length - 1];
    initialPrefix = tail && tail[1].type === "linePrefix" ? tail[2].sliceSerialize(tail[1], true).length : 0;
    marker = code4;
    effects.enter("codeFenced");
    effects.enter("codeFencedFence");
    effects.enter("codeFencedFenceSequence");
    return sequenceOpen(code4);
  }
  function sequenceOpen(code4) {
    if (code4 === marker) {
      sizeOpen++;
      effects.consume(code4);
      return sequenceOpen;
    }
    if (sizeOpen < 3) {
      return nok(code4);
    }
    effects.exit("codeFencedFenceSequence");
    return markdownSpace(code4) ? factorySpace(effects, infoBefore, "whitespace")(code4) : infoBefore(code4);
  }
  function infoBefore(code4) {
    if (code4 === null || markdownLineEnding(code4)) {
      effects.exit("codeFencedFence");
      return self.interrupt ? ok4(code4) : effects.check(nonLazyContinuation, atNonLazyBreak, after)(code4);
    }
    effects.enter("codeFencedFenceInfo");
    effects.enter("chunkString", {
      contentType: "string"
    });
    return info(code4);
  }
  function info(code4) {
    if (code4 === null || markdownLineEnding(code4)) {
      effects.exit("chunkString");
      effects.exit("codeFencedFenceInfo");
      return infoBefore(code4);
    }
    if (markdownSpace(code4)) {
      effects.exit("chunkString");
      effects.exit("codeFencedFenceInfo");
      return factorySpace(effects, metaBefore, "whitespace")(code4);
    }
    if (code4 === 96 && code4 === marker) {
      return nok(code4);
    }
    effects.consume(code4);
    return info;
  }
  function metaBefore(code4) {
    if (code4 === null || markdownLineEnding(code4)) {
      return infoBefore(code4);
    }
    effects.enter("codeFencedFenceMeta");
    effects.enter("chunkString", {
      contentType: "string"
    });
    return meta(code4);
  }
  function meta(code4) {
    if (code4 === null || markdownLineEnding(code4)) {
      effects.exit("chunkString");
      effects.exit("codeFencedFenceMeta");
      return infoBefore(code4);
    }
    if (code4 === 96 && code4 === marker) {
      return nok(code4);
    }
    effects.consume(code4);
    return meta;
  }
  function atNonLazyBreak(code4) {
    return effects.attempt(closeStart, after, contentBefore)(code4);
  }
  function contentBefore(code4) {
    effects.enter("lineEnding");
    effects.consume(code4);
    effects.exit("lineEnding");
    return contentStart;
  }
  function contentStart(code4) {
    return initialPrefix > 0 && markdownSpace(code4) ? factorySpace(
      effects,
      beforeContentChunk,
      "linePrefix",
      initialPrefix + 1
    )(code4) : beforeContentChunk(code4);
  }
  function beforeContentChunk(code4) {
    if (code4 === null || markdownLineEnding(code4)) {
      return effects.check(nonLazyContinuation, atNonLazyBreak, after)(code4);
    }
    effects.enter("codeFlowValue");
    return contentChunk(code4);
  }
  function contentChunk(code4) {
    if (code4 === null || markdownLineEnding(code4)) {
      effects.exit("codeFlowValue");
      return beforeContentChunk(code4);
    }
    effects.consume(code4);
    return contentChunk;
  }
  function after(code4) {
    effects.exit("codeFenced");
    return ok4(code4);
  }
  function tokenizeCloseStart(effects2, ok5, nok2) {
    let size = 0;
    return startBefore;
    function startBefore(code4) {
      effects2.enter("lineEnding");
      effects2.consume(code4);
      effects2.exit("lineEnding");
      return start2;
    }
    function start2(code4) {
      effects2.enter("codeFencedFence");
      return markdownSpace(code4) ? factorySpace(
        effects2,
        beforeSequenceClose,
        "linePrefix",
        self.parser.constructs.disable.null.includes("codeIndented") ? void 0 : 4
      )(code4) : beforeSequenceClose(code4);
    }
    function beforeSequenceClose(code4) {
      if (code4 === marker) {
        effects2.enter("codeFencedFenceSequence");
        return sequenceClose(code4);
      }
      return nok2(code4);
    }
    function sequenceClose(code4) {
      if (code4 === marker) {
        size++;
        effects2.consume(code4);
        return sequenceClose;
      }
      if (size >= sizeOpen) {
        effects2.exit("codeFencedFenceSequence");
        return markdownSpace(code4) ? factorySpace(effects2, sequenceCloseAfter, "whitespace")(code4) : sequenceCloseAfter(code4);
      }
      return nok2(code4);
    }
    function sequenceCloseAfter(code4) {
      if (code4 === null || markdownLineEnding(code4)) {
        effects2.exit("codeFencedFence");
        return ok5(code4);
      }
      return nok2(code4);
    }
  }
}
function tokenizeNonLazyContinuation(effects, ok4, nok) {
  const self = this;
  return start;
  function start(code4) {
    if (code4 === null) {
      return nok(code4);
    }
    effects.enter("lineEnding");
    effects.consume(code4);
    effects.exit("lineEnding");
    return lineStart;
  }
  function lineStart(code4) {
    return self.parser.lazy[self.now().line] ? nok(code4) : ok4(code4);
  }
}

// node_modules/.pnpm/micromark-core-commonmark@1.1.0/node_modules/micromark-core-commonmark/lib/code-indented.js
var codeIndented = {
  name: "codeIndented",
  tokenize: tokenizeCodeIndented
};
var furtherStart = {
  tokenize: tokenizeFurtherStart,
  partial: true
};
function tokenizeCodeIndented(effects, ok4, nok) {
  const self = this;
  return start;
  function start(code4) {
    effects.enter("codeIndented");
    return factorySpace(effects, afterPrefix, "linePrefix", 4 + 1)(code4);
  }
  function afterPrefix(code4) {
    const tail = self.events[self.events.length - 1];
    return tail && tail[1].type === "linePrefix" && tail[2].sliceSerialize(tail[1], true).length >= 4 ? atBreak(code4) : nok(code4);
  }
  function atBreak(code4) {
    if (code4 === null) {
      return after(code4);
    }
    if (markdownLineEnding(code4)) {
      return effects.attempt(furtherStart, atBreak, after)(code4);
    }
    effects.enter("codeFlowValue");
    return inside(code4);
  }
  function inside(code4) {
    if (code4 === null || markdownLineEnding(code4)) {
      effects.exit("codeFlowValue");
      return atBreak(code4);
    }
    effects.consume(code4);
    return inside;
  }
  function after(code4) {
    effects.exit("codeIndented");
    return ok4(code4);
  }
}
function tokenizeFurtherStart(effects, ok4, nok) {
  const self = this;
  return furtherStart2;
  function furtherStart2(code4) {
    if (self.parser.lazy[self.now().line]) {
      return nok(code4);
    }
    if (markdownLineEnding(code4)) {
      effects.enter("lineEnding");
      effects.consume(code4);
      effects.exit("lineEnding");
      return furtherStart2;
    }
    return factorySpace(effects, afterPrefix, "linePrefix", 4 + 1)(code4);
  }
  function afterPrefix(code4) {
    const tail = self.events[self.events.length - 1];
    return tail && tail[1].type === "linePrefix" && tail[2].sliceSerialize(tail[1], true).length >= 4 ? ok4(code4) : markdownLineEnding(code4) ? furtherStart2(code4) : nok(code4);
  }
}

// node_modules/.pnpm/micromark-core-commonmark@1.1.0/node_modules/micromark-core-commonmark/lib/code-text.js
var codeText = {
  name: "codeText",
  tokenize: tokenizeCodeText,
  resolve: resolveCodeText,
  previous
};
function resolveCodeText(events) {
  let tailExitIndex = events.length - 4;
  let headEnterIndex = 3;
  let index2;
  let enter;
  if ((events[headEnterIndex][1].type === "lineEnding" || events[headEnterIndex][1].type === "space") && (events[tailExitIndex][1].type === "lineEnding" || events[tailExitIndex][1].type === "space")) {
    index2 = headEnterIndex;
    while (++index2 < tailExitIndex) {
      if (events[index2][1].type === "codeTextData") {
        events[headEnterIndex][1].type = "codeTextPadding";
        events[tailExitIndex][1].type = "codeTextPadding";
        headEnterIndex += 2;
        tailExitIndex -= 2;
        break;
      }
    }
  }
  index2 = headEnterIndex - 1;
  tailExitIndex++;
  while (++index2 <= tailExitIndex) {
    if (enter === void 0) {
      if (index2 !== tailExitIndex && events[index2][1].type !== "lineEnding") {
        enter = index2;
      }
    } else if (index2 === tailExitIndex || events[index2][1].type === "lineEnding") {
      events[enter][1].type = "codeTextData";
      if (index2 !== enter + 2) {
        events[enter][1].end = events[index2 - 1][1].end;
        events.splice(enter + 2, index2 - enter - 2);
        tailExitIndex -= index2 - enter - 2;
        index2 = enter + 2;
      }
      enter = void 0;
    }
  }
  return events;
}
function previous(code4) {
  return code4 !== 96 || this.events[this.events.length - 1][1].type === "characterEscape";
}
function tokenizeCodeText(effects, ok4, nok) {
  const self = this;
  let sizeOpen = 0;
  let size;
  let token;
  return start;
  function start(code4) {
    effects.enter("codeText");
    effects.enter("codeTextSequence");
    return sequenceOpen(code4);
  }
  function sequenceOpen(code4) {
    if (code4 === 96) {
      effects.consume(code4);
      sizeOpen++;
      return sequenceOpen;
    }
    effects.exit("codeTextSequence");
    return between(code4);
  }
  function between(code4) {
    if (code4 === null) {
      return nok(code4);
    }
    if (code4 === 32) {
      effects.enter("space");
      effects.consume(code4);
      effects.exit("space");
      return between;
    }
    if (code4 === 96) {
      token = effects.enter("codeTextSequence");
      size = 0;
      return sequenceClose(code4);
    }
    if (markdownLineEnding(code4)) {
      effects.enter("lineEnding");
      effects.consume(code4);
      effects.exit("lineEnding");
      return between;
    }
    effects.enter("codeTextData");
    return data(code4);
  }
  function data(code4) {
    if (code4 === null || code4 === 32 || code4 === 96 || markdownLineEnding(code4)) {
      effects.exit("codeTextData");
      return between(code4);
    }
    effects.consume(code4);
    return data;
  }
  function sequenceClose(code4) {
    if (code4 === 96) {
      effects.consume(code4);
      size++;
      return sequenceClose;
    }
    if (size === sizeOpen) {
      effects.exit("codeTextSequence");
      effects.exit("codeText");
      return ok4(code4);
    }
    token.type = "codeTextData";
    return data(code4);
  }
}

// node_modules/.pnpm/micromark-util-subtokenize@1.1.0/node_modules/micromark-util-subtokenize/index.js
function subtokenize(events) {
  const jumps = {};
  let index2 = -1;
  let event;
  let lineIndex;
  let otherIndex;
  let otherEvent;
  let parameters;
  let subevents;
  let more;
  while (++index2 < events.length) {
    while (index2 in jumps) {
      index2 = jumps[index2];
    }
    event = events[index2];
    if (index2 && event[1].type === "chunkFlow" && events[index2 - 1][1].type === "listItemPrefix") {
      subevents = event[1]._tokenizer.events;
      otherIndex = 0;
      if (otherIndex < subevents.length && subevents[otherIndex][1].type === "lineEndingBlank") {
        otherIndex += 2;
      }
      if (otherIndex < subevents.length && subevents[otherIndex][1].type === "content") {
        while (++otherIndex < subevents.length) {
          if (subevents[otherIndex][1].type === "content") {
            break;
          }
          if (subevents[otherIndex][1].type === "chunkText") {
            subevents[otherIndex][1]._isInFirstContentOfListItem = true;
            otherIndex++;
          }
        }
      }
    }
    if (event[0] === "enter") {
      if (event[1].contentType) {
        Object.assign(jumps, subcontent(events, index2));
        index2 = jumps[index2];
        more = true;
      }
    } else if (event[1]._container) {
      otherIndex = index2;
      lineIndex = void 0;
      while (otherIndex--) {
        otherEvent = events[otherIndex];
        if (otherEvent[1].type === "lineEnding" || otherEvent[1].type === "lineEndingBlank") {
          if (otherEvent[0] === "enter") {
            if (lineIndex) {
              events[lineIndex][1].type = "lineEndingBlank";
            }
            otherEvent[1].type = "lineEnding";
            lineIndex = otherIndex;
          }
        } else {
          break;
        }
      }
      if (lineIndex) {
        event[1].end = Object.assign({}, events[lineIndex][1].start);
        parameters = events.slice(lineIndex, index2);
        parameters.unshift(event);
        splice(events, lineIndex, index2 - lineIndex + 1, parameters);
      }
    }
  }
  return !more;
}
function subcontent(events, eventIndex) {
  const token = events[eventIndex][1];
  const context = events[eventIndex][2];
  let startPosition = eventIndex - 1;
  const startPositions = [];
  const tokenizer = token._tokenizer || context.parser[token.contentType](token.start);
  const childEvents = tokenizer.events;
  const jumps = [];
  const gaps = {};
  let stream;
  let previous3;
  let index2 = -1;
  let current = token;
  let adjust = 0;
  let start = 0;
  const breaks = [start];
  while (current) {
    while (events[++startPosition][1] !== current) {
    }
    startPositions.push(startPosition);
    if (!current._tokenizer) {
      stream = context.sliceStream(current);
      if (!current.next) {
        stream.push(null);
      }
      if (previous3) {
        tokenizer.defineSkip(current.start);
      }
      if (current._isInFirstContentOfListItem) {
        tokenizer._gfmTasklistFirstContentOfListItem = true;
      }
      tokenizer.write(stream);
      if (current._isInFirstContentOfListItem) {
        tokenizer._gfmTasklistFirstContentOfListItem = void 0;
      }
    }
    previous3 = current;
    current = current.next;
  }
  current = token;
  while (++index2 < childEvents.length) {
    if (
      // Find a void token that includes a break.
      childEvents[index2][0] === "exit" && childEvents[index2 - 1][0] === "enter" && childEvents[index2][1].type === childEvents[index2 - 1][1].type && childEvents[index2][1].start.line !== childEvents[index2][1].end.line
    ) {
      start = index2 + 1;
      breaks.push(start);
      current._tokenizer = void 0;
      current.previous = void 0;
      current = current.next;
    }
  }
  tokenizer.events = [];
  if (current) {
    current._tokenizer = void 0;
    current.previous = void 0;
  } else {
    breaks.pop();
  }
  index2 = breaks.length;
  while (index2--) {
    const slice = childEvents.slice(breaks[index2], breaks[index2 + 1]);
    const start2 = startPositions.pop();
    jumps.unshift([start2, start2 + slice.length - 1]);
    splice(events, start2, 2, slice);
  }
  index2 = -1;
  while (++index2 < jumps.length) {
    gaps[adjust + jumps[index2][0]] = adjust + jumps[index2][1];
    adjust += jumps[index2][1] - jumps[index2][0] - 1;
  }
  return gaps;
}

// node_modules/.pnpm/micromark-core-commonmark@1.1.0/node_modules/micromark-core-commonmark/lib/content.js
var content2 = {
  tokenize: tokenizeContent,
  resolve: resolveContent
};
var continuationConstruct = {
  tokenize: tokenizeContinuation,
  partial: true
};
function resolveContent(events) {
  subtokenize(events);
  return events;
}
function tokenizeContent(effects, ok4) {
  let previous3;
  return chunkStart;
  function chunkStart(code4) {
    effects.enter("content");
    previous3 = effects.enter("chunkContent", {
      contentType: "content"
    });
    return chunkInside(code4);
  }
  function chunkInside(code4) {
    if (code4 === null) {
      return contentEnd(code4);
    }
    if (markdownLineEnding(code4)) {
      return effects.check(
        continuationConstruct,
        contentContinue,
        contentEnd
      )(code4);
    }
    effects.consume(code4);
    return chunkInside;
  }
  function contentEnd(code4) {
    effects.exit("chunkContent");
    effects.exit("content");
    return ok4(code4);
  }
  function contentContinue(code4) {
    effects.consume(code4);
    effects.exit("chunkContent");
    previous3.next = effects.enter("chunkContent", {
      contentType: "content",
      previous: previous3
    });
    previous3 = previous3.next;
    return chunkInside;
  }
}
function tokenizeContinuation(effects, ok4, nok) {
  const self = this;
  return startLookahead;
  function startLookahead(code4) {
    effects.exit("chunkContent");
    effects.enter("lineEnding");
    effects.consume(code4);
    effects.exit("lineEnding");
    return factorySpace(effects, prefixed, "linePrefix");
  }
  function prefixed(code4) {
    if (code4 === null || markdownLineEnding(code4)) {
      return nok(code4);
    }
    const tail = self.events[self.events.length - 1];
    if (!self.parser.constructs.disable.null.includes("codeIndented") && tail && tail[1].type === "linePrefix" && tail[2].sliceSerialize(tail[1], true).length >= 4) {
      return ok4(code4);
    }
    return effects.interrupt(self.parser.constructs.flow, nok, ok4)(code4);
  }
}

// node_modules/.pnpm/micromark-factory-destination@1.1.0/node_modules/micromark-factory-destination/index.js
function factoryDestination(effects, ok4, nok, type, literalType, literalMarkerType, rawType, stringType, max) {
  const limit = max || Number.POSITIVE_INFINITY;
  let balance = 0;
  return start;
  function start(code4) {
    if (code4 === 60) {
      effects.enter(type);
      effects.enter(literalType);
      effects.enter(literalMarkerType);
      effects.consume(code4);
      effects.exit(literalMarkerType);
      return enclosedBefore;
    }
    if (code4 === null || code4 === 32 || code4 === 41 || asciiControl(code4)) {
      return nok(code4);
    }
    effects.enter(type);
    effects.enter(rawType);
    effects.enter(stringType);
    effects.enter("chunkString", {
      contentType: "string"
    });
    return raw(code4);
  }
  function enclosedBefore(code4) {
    if (code4 === 62) {
      effects.enter(literalMarkerType);
      effects.consume(code4);
      effects.exit(literalMarkerType);
      effects.exit(literalType);
      effects.exit(type);
      return ok4;
    }
    effects.enter(stringType);
    effects.enter("chunkString", {
      contentType: "string"
    });
    return enclosed(code4);
  }
  function enclosed(code4) {
    if (code4 === 62) {
      effects.exit("chunkString");
      effects.exit(stringType);
      return enclosedBefore(code4);
    }
    if (code4 === null || code4 === 60 || markdownLineEnding(code4)) {
      return nok(code4);
    }
    effects.consume(code4);
    return code4 === 92 ? enclosedEscape : enclosed;
  }
  function enclosedEscape(code4) {
    if (code4 === 60 || code4 === 62 || code4 === 92) {
      effects.consume(code4);
      return enclosed;
    }
    return enclosed(code4);
  }
  function raw(code4) {
    if (!balance && (code4 === null || code4 === 41 || markdownLineEndingOrSpace(code4))) {
      effects.exit("chunkString");
      effects.exit(stringType);
      effects.exit(rawType);
      effects.exit(type);
      return ok4(code4);
    }
    if (balance < limit && code4 === 40) {
      effects.consume(code4);
      balance++;
      return raw;
    }
    if (code4 === 41) {
      effects.consume(code4);
      balance--;
      return raw;
    }
    if (code4 === null || code4 === 32 || code4 === 40 || asciiControl(code4)) {
      return nok(code4);
    }
    effects.consume(code4);
    return code4 === 92 ? rawEscape : raw;
  }
  function rawEscape(code4) {
    if (code4 === 40 || code4 === 41 || code4 === 92) {
      effects.consume(code4);
      return raw;
    }
    return raw(code4);
  }
}

// node_modules/.pnpm/micromark-factory-label@1.1.0/node_modules/micromark-factory-label/index.js
function factoryLabel(effects, ok4, nok, type, markerType, stringType) {
  const self = this;
  let size = 0;
  let seen;
  return start;
  function start(code4) {
    effects.enter(type);
    effects.enter(markerType);
    effects.consume(code4);
    effects.exit(markerType);
    effects.enter(stringType);
    return atBreak;
  }
  function atBreak(code4) {
    if (size > 999 || code4 === null || code4 === 91 || code4 === 93 && !seen || // To do: remove in the future once we’ve switched from
    // `micromark-extension-footnote` to `micromark-extension-gfm-footnote`,
    // which doesn’t need this.
    // Hidden footnotes hook.
    /* c8 ignore next 3 */
    code4 === 94 && !size && "_hiddenFootnoteSupport" in self.parser.constructs) {
      return nok(code4);
    }
    if (code4 === 93) {
      effects.exit(stringType);
      effects.enter(markerType);
      effects.consume(code4);
      effects.exit(markerType);
      effects.exit(type);
      return ok4;
    }
    if (markdownLineEnding(code4)) {
      effects.enter("lineEnding");
      effects.consume(code4);
      effects.exit("lineEnding");
      return atBreak;
    }
    effects.enter("chunkString", {
      contentType: "string"
    });
    return labelInside(code4);
  }
  function labelInside(code4) {
    if (code4 === null || code4 === 91 || code4 === 93 || markdownLineEnding(code4) || size++ > 999) {
      effects.exit("chunkString");
      return atBreak(code4);
    }
    effects.consume(code4);
    if (!seen)
      seen = !markdownSpace(code4);
    return code4 === 92 ? labelEscape : labelInside;
  }
  function labelEscape(code4) {
    if (code4 === 91 || code4 === 92 || code4 === 93) {
      effects.consume(code4);
      size++;
      return labelInside;
    }
    return labelInside(code4);
  }
}

// node_modules/.pnpm/micromark-factory-title@1.1.0/node_modules/micromark-factory-title/index.js
function factoryTitle(effects, ok4, nok, type, markerType, stringType) {
  let marker;
  return start;
  function start(code4) {
    if (code4 === 34 || code4 === 39 || code4 === 40) {
      effects.enter(type);
      effects.enter(markerType);
      effects.consume(code4);
      effects.exit(markerType);
      marker = code4 === 40 ? 41 : code4;
      return begin;
    }
    return nok(code4);
  }
  function begin(code4) {
    if (code4 === marker) {
      effects.enter(markerType);
      effects.consume(code4);
      effects.exit(markerType);
      effects.exit(type);
      return ok4;
    }
    effects.enter(stringType);
    return atBreak(code4);
  }
  function atBreak(code4) {
    if (code4 === marker) {
      effects.exit(stringType);
      return begin(marker);
    }
    if (code4 === null) {
      return nok(code4);
    }
    if (markdownLineEnding(code4)) {
      effects.enter("lineEnding");
      effects.consume(code4);
      effects.exit("lineEnding");
      return factorySpace(effects, atBreak, "linePrefix");
    }
    effects.enter("chunkString", {
      contentType: "string"
    });
    return inside(code4);
  }
  function inside(code4) {
    if (code4 === marker || code4 === null || markdownLineEnding(code4)) {
      effects.exit("chunkString");
      return atBreak(code4);
    }
    effects.consume(code4);
    return code4 === 92 ? escape : inside;
  }
  function escape(code4) {
    if (code4 === marker || code4 === 92) {
      effects.consume(code4);
      return inside;
    }
    return inside(code4);
  }
}

// node_modules/.pnpm/micromark-factory-whitespace@1.1.0/node_modules/micromark-factory-whitespace/index.js
function factoryWhitespace(effects, ok4) {
  let seen;
  return start;
  function start(code4) {
    if (markdownLineEnding(code4)) {
      effects.enter("lineEnding");
      effects.consume(code4);
      effects.exit("lineEnding");
      seen = true;
      return start;
    }
    if (markdownSpace(code4)) {
      return factorySpace(
        effects,
        start,
        seen ? "linePrefix" : "lineSuffix"
      )(code4);
    }
    return ok4(code4);
  }
}

// node_modules/.pnpm/micromark-util-normalize-identifier@1.1.0/node_modules/micromark-util-normalize-identifier/index.js
function normalizeIdentifier(value) {
  return value.replace(/[\t\n\r ]+/g, " ").replace(/^ | $/g, "").toLowerCase().toUpperCase();
}

// node_modules/.pnpm/micromark-core-commonmark@1.1.0/node_modules/micromark-core-commonmark/lib/definition.js
var definition = {
  name: "definition",
  tokenize: tokenizeDefinition
};
var titleBefore = {
  tokenize: tokenizeTitleBefore,
  partial: true
};
function tokenizeDefinition(effects, ok4, nok) {
  const self = this;
  let identifier;
  return start;
  function start(code4) {
    effects.enter("definition");
    return before(code4);
  }
  function before(code4) {
    return factoryLabel.call(
      self,
      effects,
      labelAfter,
      // Note: we don’t need to reset the way `markdown-rs` does.
      nok,
      "definitionLabel",
      "definitionLabelMarker",
      "definitionLabelString"
    )(code4);
  }
  function labelAfter(code4) {
    identifier = normalizeIdentifier(
      self.sliceSerialize(self.events[self.events.length - 1][1]).slice(1, -1)
    );
    if (code4 === 58) {
      effects.enter("definitionMarker");
      effects.consume(code4);
      effects.exit("definitionMarker");
      return markerAfter;
    }
    return nok(code4);
  }
  function markerAfter(code4) {
    return markdownLineEndingOrSpace(code4) ? factoryWhitespace(effects, destinationBefore)(code4) : destinationBefore(code4);
  }
  function destinationBefore(code4) {
    return factoryDestination(
      effects,
      destinationAfter,
      // Note: we don’t need to reset the way `markdown-rs` does.
      nok,
      "definitionDestination",
      "definitionDestinationLiteral",
      "definitionDestinationLiteralMarker",
      "definitionDestinationRaw",
      "definitionDestinationString"
    )(code4);
  }
  function destinationAfter(code4) {
    return effects.attempt(titleBefore, after, after)(code4);
  }
  function after(code4) {
    return markdownSpace(code4) ? factorySpace(effects, afterWhitespace, "whitespace")(code4) : afterWhitespace(code4);
  }
  function afterWhitespace(code4) {
    if (code4 === null || markdownLineEnding(code4)) {
      effects.exit("definition");
      self.parser.defined.push(identifier);
      return ok4(code4);
    }
    return nok(code4);
  }
}
function tokenizeTitleBefore(effects, ok4, nok) {
  return titleBefore2;
  function titleBefore2(code4) {
    return markdownLineEndingOrSpace(code4) ? factoryWhitespace(effects, beforeMarker)(code4) : nok(code4);
  }
  function beforeMarker(code4) {
    return factoryTitle(
      effects,
      titleAfter,
      nok,
      "definitionTitle",
      "definitionTitleMarker",
      "definitionTitleString"
    )(code4);
  }
  function titleAfter(code4) {
    return markdownSpace(code4) ? factorySpace(effects, titleAfterOptionalWhitespace, "whitespace")(code4) : titleAfterOptionalWhitespace(code4);
  }
  function titleAfterOptionalWhitespace(code4) {
    return code4 === null || markdownLineEnding(code4) ? ok4(code4) : nok(code4);
  }
}

// node_modules/.pnpm/micromark-core-commonmark@1.1.0/node_modules/micromark-core-commonmark/lib/hard-break-escape.js
var hardBreakEscape = {
  name: "hardBreakEscape",
  tokenize: tokenizeHardBreakEscape
};
function tokenizeHardBreakEscape(effects, ok4, nok) {
  return start;
  function start(code4) {
    effects.enter("hardBreakEscape");
    effects.consume(code4);
    return after;
  }
  function after(code4) {
    if (markdownLineEnding(code4)) {
      effects.exit("hardBreakEscape");
      return ok4(code4);
    }
    return nok(code4);
  }
}

// node_modules/.pnpm/micromark-core-commonmark@1.1.0/node_modules/micromark-core-commonmark/lib/heading-atx.js
var headingAtx = {
  name: "headingAtx",
  tokenize: tokenizeHeadingAtx,
  resolve: resolveHeadingAtx
};
function resolveHeadingAtx(events, context) {
  let contentEnd = events.length - 2;
  let contentStart = 3;
  let content3;
  let text6;
  if (events[contentStart][1].type === "whitespace") {
    contentStart += 2;
  }
  if (contentEnd - 2 > contentStart && events[contentEnd][1].type === "whitespace") {
    contentEnd -= 2;
  }
  if (events[contentEnd][1].type === "atxHeadingSequence" && (contentStart === contentEnd - 1 || contentEnd - 4 > contentStart && events[contentEnd - 2][1].type === "whitespace")) {
    contentEnd -= contentStart + 1 === contentEnd ? 2 : 4;
  }
  if (contentEnd > contentStart) {
    content3 = {
      type: "atxHeadingText",
      start: events[contentStart][1].start,
      end: events[contentEnd][1].end
    };
    text6 = {
      type: "chunkText",
      start: events[contentStart][1].start,
      end: events[contentEnd][1].end,
      contentType: "text"
    };
    splice(events, contentStart, contentEnd - contentStart + 1, [
      ["enter", content3, context],
      ["enter", text6, context],
      ["exit", text6, context],
      ["exit", content3, context]
    ]);
  }
  return events;
}
function tokenizeHeadingAtx(effects, ok4, nok) {
  let size = 0;
  return start;
  function start(code4) {
    effects.enter("atxHeading");
    return before(code4);
  }
  function before(code4) {
    effects.enter("atxHeadingSequence");
    return sequenceOpen(code4);
  }
  function sequenceOpen(code4) {
    if (code4 === 35 && size++ < 6) {
      effects.consume(code4);
      return sequenceOpen;
    }
    if (code4 === null || markdownLineEndingOrSpace(code4)) {
      effects.exit("atxHeadingSequence");
      return atBreak(code4);
    }
    return nok(code4);
  }
  function atBreak(code4) {
    if (code4 === 35) {
      effects.enter("atxHeadingSequence");
      return sequenceFurther(code4);
    }
    if (code4 === null || markdownLineEnding(code4)) {
      effects.exit("atxHeading");
      return ok4(code4);
    }
    if (markdownSpace(code4)) {
      return factorySpace(effects, atBreak, "whitespace")(code4);
    }
    effects.enter("atxHeadingText");
    return data(code4);
  }
  function sequenceFurther(code4) {
    if (code4 === 35) {
      effects.consume(code4);
      return sequenceFurther;
    }
    effects.exit("atxHeadingSequence");
    return atBreak(code4);
  }
  function data(code4) {
    if (code4 === null || code4 === 35 || markdownLineEndingOrSpace(code4)) {
      effects.exit("atxHeadingText");
      return atBreak(code4);
    }
    effects.consume(code4);
    return data;
  }
}

// node_modules/.pnpm/micromark-util-html-tag-name@1.2.0/node_modules/micromark-util-html-tag-name/index.js
var htmlBlockNames = [
  "address",
  "article",
  "aside",
  "base",
  "basefont",
  "blockquote",
  "body",
  "caption",
  "center",
  "col",
  "colgroup",
  "dd",
  "details",
  "dialog",
  "dir",
  "div",
  "dl",
  "dt",
  "fieldset",
  "figcaption",
  "figure",
  "footer",
  "form",
  "frame",
  "frameset",
  "h1",
  "h2",
  "h3",
  "h4",
  "h5",
  "h6",
  "head",
  "header",
  "hr",
  "html",
  "iframe",
  "legend",
  "li",
  "link",
  "main",
  "menu",
  "menuitem",
  "nav",
  "noframes",
  "ol",
  "optgroup",
  "option",
  "p",
  "param",
  "search",
  "section",
  "summary",
  "table",
  "tbody",
  "td",
  "tfoot",
  "th",
  "thead",
  "title",
  "tr",
  "track",
  "ul"
];
var htmlRawNames = ["pre", "script", "style", "textarea"];

// node_modules/.pnpm/micromark-core-commonmark@1.1.0/node_modules/micromark-core-commonmark/lib/html-flow.js
var htmlFlow = {
  name: "htmlFlow",
  tokenize: tokenizeHtmlFlow,
  resolveTo: resolveToHtmlFlow,
  concrete: true
};
var blankLineBefore = {
  tokenize: tokenizeBlankLineBefore,
  partial: true
};
var nonLazyContinuationStart = {
  tokenize: tokenizeNonLazyContinuationStart,
  partial: true
};
function resolveToHtmlFlow(events) {
  let index2 = events.length;
  while (index2--) {
    if (events[index2][0] === "enter" && events[index2][1].type === "htmlFlow") {
      break;
    }
  }
  if (index2 > 1 && events[index2 - 2][1].type === "linePrefix") {
    events[index2][1].start = events[index2 - 2][1].start;
    events[index2 + 1][1].start = events[index2 - 2][1].start;
    events.splice(index2 - 2, 2);
  }
  return events;
}
function tokenizeHtmlFlow(effects, ok4, nok) {
  const self = this;
  let marker;
  let closingTag;
  let buffer2;
  let index2;
  let markerB;
  return start;
  function start(code4) {
    return before(code4);
  }
  function before(code4) {
    effects.enter("htmlFlow");
    effects.enter("htmlFlowData");
    effects.consume(code4);
    return open;
  }
  function open(code4) {
    if (code4 === 33) {
      effects.consume(code4);
      return declarationOpen;
    }
    if (code4 === 47) {
      effects.consume(code4);
      closingTag = true;
      return tagCloseStart;
    }
    if (code4 === 63) {
      effects.consume(code4);
      marker = 3;
      return self.interrupt ? ok4 : continuationDeclarationInside;
    }
    if (asciiAlpha(code4)) {
      effects.consume(code4);
      buffer2 = String.fromCharCode(code4);
      return tagName;
    }
    return nok(code4);
  }
  function declarationOpen(code4) {
    if (code4 === 45) {
      effects.consume(code4);
      marker = 2;
      return commentOpenInside;
    }
    if (code4 === 91) {
      effects.consume(code4);
      marker = 5;
      index2 = 0;
      return cdataOpenInside;
    }
    if (asciiAlpha(code4)) {
      effects.consume(code4);
      marker = 4;
      return self.interrupt ? ok4 : continuationDeclarationInside;
    }
    return nok(code4);
  }
  function commentOpenInside(code4) {
    if (code4 === 45) {
      effects.consume(code4);
      return self.interrupt ? ok4 : continuationDeclarationInside;
    }
    return nok(code4);
  }
  function cdataOpenInside(code4) {
    const value = "CDATA[";
    if (code4 === value.charCodeAt(index2++)) {
      effects.consume(code4);
      if (index2 === value.length) {
        return self.interrupt ? ok4 : continuation;
      }
      return cdataOpenInside;
    }
    return nok(code4);
  }
  function tagCloseStart(code4) {
    if (asciiAlpha(code4)) {
      effects.consume(code4);
      buffer2 = String.fromCharCode(code4);
      return tagName;
    }
    return nok(code4);
  }
  function tagName(code4) {
    if (code4 === null || code4 === 47 || code4 === 62 || markdownLineEndingOrSpace(code4)) {
      const slash = code4 === 47;
      const name = buffer2.toLowerCase();
      if (!slash && !closingTag && htmlRawNames.includes(name)) {
        marker = 1;
        return self.interrupt ? ok4(code4) : continuation(code4);
      }
      if (htmlBlockNames.includes(buffer2.toLowerCase())) {
        marker = 6;
        if (slash) {
          effects.consume(code4);
          return basicSelfClosing;
        }
        return self.interrupt ? ok4(code4) : continuation(code4);
      }
      marker = 7;
      return self.interrupt && !self.parser.lazy[self.now().line] ? nok(code4) : closingTag ? completeClosingTagAfter(code4) : completeAttributeNameBefore(code4);
    }
    if (code4 === 45 || asciiAlphanumeric(code4)) {
      effects.consume(code4);
      buffer2 += String.fromCharCode(code4);
      return tagName;
    }
    return nok(code4);
  }
  function basicSelfClosing(code4) {
    if (code4 === 62) {
      effects.consume(code4);
      return self.interrupt ? ok4 : continuation;
    }
    return nok(code4);
  }
  function completeClosingTagAfter(code4) {
    if (markdownSpace(code4)) {
      effects.consume(code4);
      return completeClosingTagAfter;
    }
    return completeEnd(code4);
  }
  function completeAttributeNameBefore(code4) {
    if (code4 === 47) {
      effects.consume(code4);
      return completeEnd;
    }
    if (code4 === 58 || code4 === 95 || asciiAlpha(code4)) {
      effects.consume(code4);
      return completeAttributeName;
    }
    if (markdownSpace(code4)) {
      effects.consume(code4);
      return completeAttributeNameBefore;
    }
    return completeEnd(code4);
  }
  function completeAttributeName(code4) {
    if (code4 === 45 || code4 === 46 || code4 === 58 || code4 === 95 || asciiAlphanumeric(code4)) {
      effects.consume(code4);
      return completeAttributeName;
    }
    return completeAttributeNameAfter(code4);
  }
  function completeAttributeNameAfter(code4) {
    if (code4 === 61) {
      effects.consume(code4);
      return completeAttributeValueBefore;
    }
    if (markdownSpace(code4)) {
      effects.consume(code4);
      return completeAttributeNameAfter;
    }
    return completeAttributeNameBefore(code4);
  }
  function completeAttributeValueBefore(code4) {
    if (code4 === null || code4 === 60 || code4 === 61 || code4 === 62 || code4 === 96) {
      return nok(code4);
    }
    if (code4 === 34 || code4 === 39) {
      effects.consume(code4);
      markerB = code4;
      return completeAttributeValueQuoted;
    }
    if (markdownSpace(code4)) {
      effects.consume(code4);
      return completeAttributeValueBefore;
    }
    return completeAttributeValueUnquoted(code4);
  }
  function completeAttributeValueQuoted(code4) {
    if (code4 === markerB) {
      effects.consume(code4);
      markerB = null;
      return completeAttributeValueQuotedAfter;
    }
    if (code4 === null || markdownLineEnding(code4)) {
      return nok(code4);
    }
    effects.consume(code4);
    return completeAttributeValueQuoted;
  }
  function completeAttributeValueUnquoted(code4) {
    if (code4 === null || code4 === 34 || code4 === 39 || code4 === 47 || code4 === 60 || code4 === 61 || code4 === 62 || code4 === 96 || markdownLineEndingOrSpace(code4)) {
      return completeAttributeNameAfter(code4);
    }
    effects.consume(code4);
    return completeAttributeValueUnquoted;
  }
  function completeAttributeValueQuotedAfter(code4) {
    if (code4 === 47 || code4 === 62 || markdownSpace(code4)) {
      return completeAttributeNameBefore(code4);
    }
    return nok(code4);
  }
  function completeEnd(code4) {
    if (code4 === 62) {
      effects.consume(code4);
      return completeAfter;
    }
    return nok(code4);
  }
  function completeAfter(code4) {
    if (code4 === null || markdownLineEnding(code4)) {
      return continuation(code4);
    }
    if (markdownSpace(code4)) {
      effects.consume(code4);
      return completeAfter;
    }
    return nok(code4);
  }
  function continuation(code4) {
    if (code4 === 45 && marker === 2) {
      effects.consume(code4);
      return continuationCommentInside;
    }
    if (code4 === 60 && marker === 1) {
      effects.consume(code4);
      return continuationRawTagOpen;
    }
    if (code4 === 62 && marker === 4) {
      effects.consume(code4);
      return continuationClose;
    }
    if (code4 === 63 && marker === 3) {
      effects.consume(code4);
      return continuationDeclarationInside;
    }
    if (code4 === 93 && marker === 5) {
      effects.consume(code4);
      return continuationCdataInside;
    }
    if (markdownLineEnding(code4) && (marker === 6 || marker === 7)) {
      effects.exit("htmlFlowData");
      return effects.check(
        blankLineBefore,
        continuationAfter,
        continuationStart
      )(code4);
    }
    if (code4 === null || markdownLineEnding(code4)) {
      effects.exit("htmlFlowData");
      return continuationStart(code4);
    }
    effects.consume(code4);
    return continuation;
  }
  function continuationStart(code4) {
    return effects.check(
      nonLazyContinuationStart,
      continuationStartNonLazy,
      continuationAfter
    )(code4);
  }
  function continuationStartNonLazy(code4) {
    effects.enter("lineEnding");
    effects.consume(code4);
    effects.exit("lineEnding");
    return continuationBefore;
  }
  function continuationBefore(code4) {
    if (code4 === null || markdownLineEnding(code4)) {
      return continuationStart(code4);
    }
    effects.enter("htmlFlowData");
    return continuation(code4);
  }
  function continuationCommentInside(code4) {
    if (code4 === 45) {
      effects.consume(code4);
      return continuationDeclarationInside;
    }
    return continuation(code4);
  }
  function continuationRawTagOpen(code4) {
    if (code4 === 47) {
      effects.consume(code4);
      buffer2 = "";
      return continuationRawEndTag;
    }
    return continuation(code4);
  }
  function continuationRawEndTag(code4) {
    if (code4 === 62) {
      const name = buffer2.toLowerCase();
      if (htmlRawNames.includes(name)) {
        effects.consume(code4);
        return continuationClose;
      }
      return continuation(code4);
    }
    if (asciiAlpha(code4) && buffer2.length < 8) {
      effects.consume(code4);
      buffer2 += String.fromCharCode(code4);
      return continuationRawEndTag;
    }
    return continuation(code4);
  }
  function continuationCdataInside(code4) {
    if (code4 === 93) {
      effects.consume(code4);
      return continuationDeclarationInside;
    }
    return continuation(code4);
  }
  function continuationDeclarationInside(code4) {
    if (code4 === 62) {
      effects.consume(code4);
      return continuationClose;
    }
    if (code4 === 45 && marker === 2) {
      effects.consume(code4);
      return continuationDeclarationInside;
    }
    return continuation(code4);
  }
  function continuationClose(code4) {
    if (code4 === null || markdownLineEnding(code4)) {
      effects.exit("htmlFlowData");
      return continuationAfter(code4);
    }
    effects.consume(code4);
    return continuationClose;
  }
  function continuationAfter(code4) {
    effects.exit("htmlFlow");
    return ok4(code4);
  }
}
function tokenizeNonLazyContinuationStart(effects, ok4, nok) {
  const self = this;
  return start;
  function start(code4) {
    if (markdownLineEnding(code4)) {
      effects.enter("lineEnding");
      effects.consume(code4);
      effects.exit("lineEnding");
      return after;
    }
    return nok(code4);
  }
  function after(code4) {
    return self.parser.lazy[self.now().line] ? nok(code4) : ok4(code4);
  }
}
function tokenizeBlankLineBefore(effects, ok4, nok) {
  return start;
  function start(code4) {
    effects.enter("lineEnding");
    effects.consume(code4);
    effects.exit("lineEnding");
    return effects.attempt(blankLine, ok4, nok);
  }
}

// node_modules/.pnpm/micromark-core-commonmark@1.1.0/node_modules/micromark-core-commonmark/lib/html-text.js
var htmlText = {
  name: "htmlText",
  tokenize: tokenizeHtmlText
};
function tokenizeHtmlText(effects, ok4, nok) {
  const self = this;
  let marker;
  let index2;
  let returnState;
  return start;
  function start(code4) {
    effects.enter("htmlText");
    effects.enter("htmlTextData");
    effects.consume(code4);
    return open;
  }
  function open(code4) {
    if (code4 === 33) {
      effects.consume(code4);
      return declarationOpen;
    }
    if (code4 === 47) {
      effects.consume(code4);
      return tagCloseStart;
    }
    if (code4 === 63) {
      effects.consume(code4);
      return instruction;
    }
    if (asciiAlpha(code4)) {
      effects.consume(code4);
      return tagOpen;
    }
    return nok(code4);
  }
  function declarationOpen(code4) {
    if (code4 === 45) {
      effects.consume(code4);
      return commentOpenInside;
    }
    if (code4 === 91) {
      effects.consume(code4);
      index2 = 0;
      return cdataOpenInside;
    }
    if (asciiAlpha(code4)) {
      effects.consume(code4);
      return declaration;
    }
    return nok(code4);
  }
  function commentOpenInside(code4) {
    if (code4 === 45) {
      effects.consume(code4);
      return commentEnd;
    }
    return nok(code4);
  }
  function comment(code4) {
    if (code4 === null) {
      return nok(code4);
    }
    if (code4 === 45) {
      effects.consume(code4);
      return commentClose;
    }
    if (markdownLineEnding(code4)) {
      returnState = comment;
      return lineEndingBefore(code4);
    }
    effects.consume(code4);
    return comment;
  }
  function commentClose(code4) {
    if (code4 === 45) {
      effects.consume(code4);
      return commentEnd;
    }
    return comment(code4);
  }
  function commentEnd(code4) {
    return code4 === 62 ? end(code4) : code4 === 45 ? commentClose(code4) : comment(code4);
  }
  function cdataOpenInside(code4) {
    const value = "CDATA[";
    if (code4 === value.charCodeAt(index2++)) {
      effects.consume(code4);
      return index2 === value.length ? cdata : cdataOpenInside;
    }
    return nok(code4);
  }
  function cdata(code4) {
    if (code4 === null) {
      return nok(code4);
    }
    if (code4 === 93) {
      effects.consume(code4);
      return cdataClose;
    }
    if (markdownLineEnding(code4)) {
      returnState = cdata;
      return lineEndingBefore(code4);
    }
    effects.consume(code4);
    return cdata;
  }
  function cdataClose(code4) {
    if (code4 === 93) {
      effects.consume(code4);
      return cdataEnd;
    }
    return cdata(code4);
  }
  function cdataEnd(code4) {
    if (code4 === 62) {
      return end(code4);
    }
    if (code4 === 93) {
      effects.consume(code4);
      return cdataEnd;
    }
    return cdata(code4);
  }
  function declaration(code4) {
    if (code4 === null || code4 === 62) {
      return end(code4);
    }
    if (markdownLineEnding(code4)) {
      returnState = declaration;
      return lineEndingBefore(code4);
    }
    effects.consume(code4);
    return declaration;
  }
  function instruction(code4) {
    if (code4 === null) {
      return nok(code4);
    }
    if (code4 === 63) {
      effects.consume(code4);
      return instructionClose;
    }
    if (markdownLineEnding(code4)) {
      returnState = instruction;
      return lineEndingBefore(code4);
    }
    effects.consume(code4);
    return instruction;
  }
  function instructionClose(code4) {
    return code4 === 62 ? end(code4) : instruction(code4);
  }
  function tagCloseStart(code4) {
    if (asciiAlpha(code4)) {
      effects.consume(code4);
      return tagClose;
    }
    return nok(code4);
  }
  function tagClose(code4) {
    if (code4 === 45 || asciiAlphanumeric(code4)) {
      effects.consume(code4);
      return tagClose;
    }
    return tagCloseBetween(code4);
  }
  function tagCloseBetween(code4) {
    if (markdownLineEnding(code4)) {
      returnState = tagCloseBetween;
      return lineEndingBefore(code4);
    }
    if (markdownSpace(code4)) {
      effects.consume(code4);
      return tagCloseBetween;
    }
    return end(code4);
  }
  function tagOpen(code4) {
    if (code4 === 45 || asciiAlphanumeric(code4)) {
      effects.consume(code4);
      return tagOpen;
    }
    if (code4 === 47 || code4 === 62 || markdownLineEndingOrSpace(code4)) {
      return tagOpenBetween(code4);
    }
    return nok(code4);
  }
  function tagOpenBetween(code4) {
    if (code4 === 47) {
      effects.consume(code4);
      return end;
    }
    if (code4 === 58 || code4 === 95 || asciiAlpha(code4)) {
      effects.consume(code4);
      return tagOpenAttributeName;
    }
    if (markdownLineEnding(code4)) {
      returnState = tagOpenBetween;
      return lineEndingBefore(code4);
    }
    if (markdownSpace(code4)) {
      effects.consume(code4);
      return tagOpenBetween;
    }
    return end(code4);
  }
  function tagOpenAttributeName(code4) {
    if (code4 === 45 || code4 === 46 || code4 === 58 || code4 === 95 || asciiAlphanumeric(code4)) {
      effects.consume(code4);
      return tagOpenAttributeName;
    }
    return tagOpenAttributeNameAfter(code4);
  }
  function tagOpenAttributeNameAfter(code4) {
    if (code4 === 61) {
      effects.consume(code4);
      return tagOpenAttributeValueBefore;
    }
    if (markdownLineEnding(code4)) {
      returnState = tagOpenAttributeNameAfter;
      return lineEndingBefore(code4);
    }
    if (markdownSpace(code4)) {
      effects.consume(code4);
      return tagOpenAttributeNameAfter;
    }
    return tagOpenBetween(code4);
  }
  function tagOpenAttributeValueBefore(code4) {
    if (code4 === null || code4 === 60 || code4 === 61 || code4 === 62 || code4 === 96) {
      return nok(code4);
    }
    if (code4 === 34 || code4 === 39) {
      effects.consume(code4);
      marker = code4;
      return tagOpenAttributeValueQuoted;
    }
    if (markdownLineEnding(code4)) {
      returnState = tagOpenAttributeValueBefore;
      return lineEndingBefore(code4);
    }
    if (markdownSpace(code4)) {
      effects.consume(code4);
      return tagOpenAttributeValueBefore;
    }
    effects.consume(code4);
    return tagOpenAttributeValueUnquoted;
  }
  function tagOpenAttributeValueQuoted(code4) {
    if (code4 === marker) {
      effects.consume(code4);
      marker = void 0;
      return tagOpenAttributeValueQuotedAfter;
    }
    if (code4 === null) {
      return nok(code4);
    }
    if (markdownLineEnding(code4)) {
      returnState = tagOpenAttributeValueQuoted;
      return lineEndingBefore(code4);
    }
    effects.consume(code4);
    return tagOpenAttributeValueQuoted;
  }
  function tagOpenAttributeValueUnquoted(code4) {
    if (code4 === null || code4 === 34 || code4 === 39 || code4 === 60 || code4 === 61 || code4 === 96) {
      return nok(code4);
    }
    if (code4 === 47 || code4 === 62 || markdownLineEndingOrSpace(code4)) {
      return tagOpenBetween(code4);
    }
    effects.consume(code4);
    return tagOpenAttributeValueUnquoted;
  }
  function tagOpenAttributeValueQuotedAfter(code4) {
    if (code4 === 47 || code4 === 62 || markdownLineEndingOrSpace(code4)) {
      return tagOpenBetween(code4);
    }
    return nok(code4);
  }
  function end(code4) {
    if (code4 === 62) {
      effects.consume(code4);
      effects.exit("htmlTextData");
      effects.exit("htmlText");
      return ok4;
    }
    return nok(code4);
  }
  function lineEndingBefore(code4) {
    effects.exit("htmlTextData");
    effects.enter("lineEnding");
    effects.consume(code4);
    effects.exit("lineEnding");
    return lineEndingAfter;
  }
  function lineEndingAfter(code4) {
    return markdownSpace(code4) ? factorySpace(
      effects,
      lineEndingAfterPrefix,
      "linePrefix",
      self.parser.constructs.disable.null.includes("codeIndented") ? void 0 : 4
    )(code4) : lineEndingAfterPrefix(code4);
  }
  function lineEndingAfterPrefix(code4) {
    effects.enter("htmlTextData");
    return returnState(code4);
  }
}

// node_modules/.pnpm/micromark-core-commonmark@1.1.0/node_modules/micromark-core-commonmark/lib/label-end.js
var labelEnd = {
  name: "labelEnd",
  tokenize: tokenizeLabelEnd,
  resolveTo: resolveToLabelEnd,
  resolveAll: resolveAllLabelEnd
};
var resourceConstruct = {
  tokenize: tokenizeResource
};
var referenceFullConstruct = {
  tokenize: tokenizeReferenceFull
};
var referenceCollapsedConstruct = {
  tokenize: tokenizeReferenceCollapsed
};
function resolveAllLabelEnd(events) {
  let index2 = -1;
  while (++index2 < events.length) {
    const token = events[index2][1];
    if (token.type === "labelImage" || token.type === "labelLink" || token.type === "labelEnd") {
      events.splice(index2 + 1, token.type === "labelImage" ? 4 : 2);
      token.type = "data";
      index2++;
    }
  }
  return events;
}
function resolveToLabelEnd(events, context) {
  let index2 = events.length;
  let offset = 0;
  let token;
  let open;
  let close;
  let media;
  while (index2--) {
    token = events[index2][1];
    if (open) {
      if (token.type === "link" || token.type === "labelLink" && token._inactive) {
        break;
      }
      if (events[index2][0] === "enter" && token.type === "labelLink") {
        token._inactive = true;
      }
    } else if (close) {
      if (events[index2][0] === "enter" && (token.type === "labelImage" || token.type === "labelLink") && !token._balanced) {
        open = index2;
        if (token.type !== "labelLink") {
          offset = 2;
          break;
        }
      }
    } else if (token.type === "labelEnd") {
      close = index2;
    }
  }
  const group = {
    type: events[open][1].type === "labelLink" ? "link" : "image",
    start: Object.assign({}, events[open][1].start),
    end: Object.assign({}, events[events.length - 1][1].end)
  };
  const label = {
    type: "label",
    start: Object.assign({}, events[open][1].start),
    end: Object.assign({}, events[close][1].end)
  };
  const text6 = {
    type: "labelText",
    start: Object.assign({}, events[open + offset + 2][1].end),
    end: Object.assign({}, events[close - 2][1].start)
  };
  media = [
    ["enter", group, context],
    ["enter", label, context]
  ];
  media = push(media, events.slice(open + 1, open + offset + 3));
  media = push(media, [["enter", text6, context]]);
  media = push(
    media,
    resolveAll(
      context.parser.constructs.insideSpan.null,
      events.slice(open + offset + 4, close - 3),
      context
    )
  );
  media = push(media, [
    ["exit", text6, context],
    events[close - 2],
    events[close - 1],
    ["exit", label, context]
  ]);
  media = push(media, events.slice(close + 1));
  media = push(media, [["exit", group, context]]);
  splice(events, open, events.length, media);
  return events;
}
function tokenizeLabelEnd(effects, ok4, nok) {
  const self = this;
  let index2 = self.events.length;
  let labelStart;
  let defined;
  while (index2--) {
    if ((self.events[index2][1].type === "labelImage" || self.events[index2][1].type === "labelLink") && !self.events[index2][1]._balanced) {
      labelStart = self.events[index2][1];
      break;
    }
  }
  return start;
  function start(code4) {
    if (!labelStart) {
      return nok(code4);
    }
    if (labelStart._inactive) {
      return labelEndNok(code4);
    }
    defined = self.parser.defined.includes(
      normalizeIdentifier(
        self.sliceSerialize({
          start: labelStart.end,
          end: self.now()
        })
      )
    );
    effects.enter("labelEnd");
    effects.enter("labelMarker");
    effects.consume(code4);
    effects.exit("labelMarker");
    effects.exit("labelEnd");
    return after;
  }
  function after(code4) {
    if (code4 === 40) {
      return effects.attempt(
        resourceConstruct,
        labelEndOk,
        defined ? labelEndOk : labelEndNok
      )(code4);
    }
    if (code4 === 91) {
      return effects.attempt(
        referenceFullConstruct,
        labelEndOk,
        defined ? referenceNotFull : labelEndNok
      )(code4);
    }
    return defined ? labelEndOk(code4) : labelEndNok(code4);
  }
  function referenceNotFull(code4) {
    return effects.attempt(
      referenceCollapsedConstruct,
      labelEndOk,
      labelEndNok
    )(code4);
  }
  function labelEndOk(code4) {
    return ok4(code4);
  }
  function labelEndNok(code4) {
    labelStart._balanced = true;
    return nok(code4);
  }
}
function tokenizeResource(effects, ok4, nok) {
  return resourceStart;
  function resourceStart(code4) {
    effects.enter("resource");
    effects.enter("resourceMarker");
    effects.consume(code4);
    effects.exit("resourceMarker");
    return resourceBefore;
  }
  function resourceBefore(code4) {
    return markdownLineEndingOrSpace(code4) ? factoryWhitespace(effects, resourceOpen)(code4) : resourceOpen(code4);
  }
  function resourceOpen(code4) {
    if (code4 === 41) {
      return resourceEnd(code4);
    }
    return factoryDestination(
      effects,
      resourceDestinationAfter,
      resourceDestinationMissing,
      "resourceDestination",
      "resourceDestinationLiteral",
      "resourceDestinationLiteralMarker",
      "resourceDestinationRaw",
      "resourceDestinationString",
      32
    )(code4);
  }
  function resourceDestinationAfter(code4) {
    return markdownLineEndingOrSpace(code4) ? factoryWhitespace(effects, resourceBetween)(code4) : resourceEnd(code4);
  }
  function resourceDestinationMissing(code4) {
    return nok(code4);
  }
  function resourceBetween(code4) {
    if (code4 === 34 || code4 === 39 || code4 === 40) {
      return factoryTitle(
        effects,
        resourceTitleAfter,
        nok,
        "resourceTitle",
        "resourceTitleMarker",
        "resourceTitleString"
      )(code4);
    }
    return resourceEnd(code4);
  }
  function resourceTitleAfter(code4) {
    return markdownLineEndingOrSpace(code4) ? factoryWhitespace(effects, resourceEnd)(code4) : resourceEnd(code4);
  }
  function resourceEnd(code4) {
    if (code4 === 41) {
      effects.enter("resourceMarker");
      effects.consume(code4);
      effects.exit("resourceMarker");
      effects.exit("resource");
      return ok4;
    }
    return nok(code4);
  }
}
function tokenizeReferenceFull(effects, ok4, nok) {
  const self = this;
  return referenceFull;
  function referenceFull(code4) {
    return factoryLabel.call(
      self,
      effects,
      referenceFullAfter,
      referenceFullMissing,
      "reference",
      "referenceMarker",
      "referenceString"
    )(code4);
  }
  function referenceFullAfter(code4) {
    return self.parser.defined.includes(
      normalizeIdentifier(
        self.sliceSerialize(self.events[self.events.length - 1][1]).slice(1, -1)
      )
    ) ? ok4(code4) : nok(code4);
  }
  function referenceFullMissing(code4) {
    return nok(code4);
  }
}
function tokenizeReferenceCollapsed(effects, ok4, nok) {
  return referenceCollapsedStart;
  function referenceCollapsedStart(code4) {
    effects.enter("reference");
    effects.enter("referenceMarker");
    effects.consume(code4);
    effects.exit("referenceMarker");
    return referenceCollapsedOpen;
  }
  function referenceCollapsedOpen(code4) {
    if (code4 === 93) {
      effects.enter("referenceMarker");
      effects.consume(code4);
      effects.exit("referenceMarker");
      effects.exit("reference");
      return ok4;
    }
    return nok(code4);
  }
}

// node_modules/.pnpm/micromark-core-commonmark@1.1.0/node_modules/micromark-core-commonmark/lib/label-start-image.js
var labelStartImage = {
  name: "labelStartImage",
  tokenize: tokenizeLabelStartImage,
  resolveAll: labelEnd.resolveAll
};
function tokenizeLabelStartImage(effects, ok4, nok) {
  const self = this;
  return start;
  function start(code4) {
    effects.enter("labelImage");
    effects.enter("labelImageMarker");
    effects.consume(code4);
    effects.exit("labelImageMarker");
    return open;
  }
  function open(code4) {
    if (code4 === 91) {
      effects.enter("labelMarker");
      effects.consume(code4);
      effects.exit("labelMarker");
      effects.exit("labelImage");
      return after;
    }
    return nok(code4);
  }
  function after(code4) {
    return code4 === 94 && "_hiddenFootnoteSupport" in self.parser.constructs ? nok(code4) : ok4(code4);
  }
}

// node_modules/.pnpm/micromark-core-commonmark@1.1.0/node_modules/micromark-core-commonmark/lib/label-start-link.js
var labelStartLink = {
  name: "labelStartLink",
  tokenize: tokenizeLabelStartLink,
  resolveAll: labelEnd.resolveAll
};
function tokenizeLabelStartLink(effects, ok4, nok) {
  const self = this;
  return start;
  function start(code4) {
    effects.enter("labelLink");
    effects.enter("labelMarker");
    effects.consume(code4);
    effects.exit("labelMarker");
    effects.exit("labelLink");
    return after;
  }
  function after(code4) {
    return code4 === 94 && "_hiddenFootnoteSupport" in self.parser.constructs ? nok(code4) : ok4(code4);
  }
}

// node_modules/.pnpm/micromark-core-commonmark@1.1.0/node_modules/micromark-core-commonmark/lib/line-ending.js
var lineEnding = {
  name: "lineEnding",
  tokenize: tokenizeLineEnding
};
function tokenizeLineEnding(effects, ok4) {
  return start;
  function start(code4) {
    effects.enter("lineEnding");
    effects.consume(code4);
    effects.exit("lineEnding");
    return factorySpace(effects, ok4, "linePrefix");
  }
}

// node_modules/.pnpm/micromark-core-commonmark@1.1.0/node_modules/micromark-core-commonmark/lib/thematic-break.js
var thematicBreak = {
  name: "thematicBreak",
  tokenize: tokenizeThematicBreak
};
function tokenizeThematicBreak(effects, ok4, nok) {
  let size = 0;
  let marker;
  return start;
  function start(code4) {
    effects.enter("thematicBreak");
    return before(code4);
  }
  function before(code4) {
    marker = code4;
    return atBreak(code4);
  }
  function atBreak(code4) {
    if (code4 === marker) {
      effects.enter("thematicBreakSequence");
      return sequence(code4);
    }
    if (size >= 3 && (code4 === null || markdownLineEnding(code4))) {
      effects.exit("thematicBreak");
      return ok4(code4);
    }
    return nok(code4);
  }
  function sequence(code4) {
    if (code4 === marker) {
      effects.consume(code4);
      size++;
      return sequence;
    }
    effects.exit("thematicBreakSequence");
    return markdownSpace(code4) ? factorySpace(effects, atBreak, "whitespace")(code4) : atBreak(code4);
  }
}

// node_modules/.pnpm/micromark-core-commonmark@1.1.0/node_modules/micromark-core-commonmark/lib/list.js
var list = {
  name: "list",
  tokenize: tokenizeListStart,
  continuation: {
    tokenize: tokenizeListContinuation
  },
  exit: tokenizeListEnd
};
var listItemPrefixWhitespaceConstruct = {
  tokenize: tokenizeListItemPrefixWhitespace,
  partial: true
};
var indentConstruct = {
  tokenize: tokenizeIndent,
  partial: true
};
function tokenizeListStart(effects, ok4, nok) {
  const self = this;
  const tail = self.events[self.events.length - 1];
  let initialSize = tail && tail[1].type === "linePrefix" ? tail[2].sliceSerialize(tail[1], true).length : 0;
  let size = 0;
  return start;
  function start(code4) {
    const kind = self.containerState.type || (code4 === 42 || code4 === 43 || code4 === 45 ? "listUnordered" : "listOrdered");
    if (kind === "listUnordered" ? !self.containerState.marker || code4 === self.containerState.marker : asciiDigit(code4)) {
      if (!self.containerState.type) {
        self.containerState.type = kind;
        effects.enter(kind, {
          _container: true
        });
      }
      if (kind === "listUnordered") {
        effects.enter("listItemPrefix");
        return code4 === 42 || code4 === 45 ? effects.check(thematicBreak, nok, atMarker)(code4) : atMarker(code4);
      }
      if (!self.interrupt || code4 === 49) {
        effects.enter("listItemPrefix");
        effects.enter("listItemValue");
        return inside(code4);
      }
    }
    return nok(code4);
  }
  function inside(code4) {
    if (asciiDigit(code4) && ++size < 10) {
      effects.consume(code4);
      return inside;
    }
    if ((!self.interrupt || size < 2) && (self.containerState.marker ? code4 === self.containerState.marker : code4 === 41 || code4 === 46)) {
      effects.exit("listItemValue");
      return atMarker(code4);
    }
    return nok(code4);
  }
  function atMarker(code4) {
    effects.enter("listItemMarker");
    effects.consume(code4);
    effects.exit("listItemMarker");
    self.containerState.marker = self.containerState.marker || code4;
    return effects.check(
      blankLine,
      // Can’t be empty when interrupting.
      self.interrupt ? nok : onBlank,
      effects.attempt(
        listItemPrefixWhitespaceConstruct,
        endOfPrefix,
        otherPrefix
      )
    );
  }
  function onBlank(code4) {
    self.containerState.initialBlankLine = true;
    initialSize++;
    return endOfPrefix(code4);
  }
  function otherPrefix(code4) {
    if (markdownSpace(code4)) {
      effects.enter("listItemPrefixWhitespace");
      effects.consume(code4);
      effects.exit("listItemPrefixWhitespace");
      return endOfPrefix;
    }
    return nok(code4);
  }
  function endOfPrefix(code4) {
    self.containerState.size = initialSize + self.sliceSerialize(effects.exit("listItemPrefix"), true).length;
    return ok4(code4);
  }
}
function tokenizeListContinuation(effects, ok4, nok) {
  const self = this;
  self.containerState._closeFlow = void 0;
  return effects.check(blankLine, onBlank, notBlank);
  function onBlank(code4) {
    self.containerState.furtherBlankLines = self.containerState.furtherBlankLines || self.containerState.initialBlankLine;
    return factorySpace(
      effects,
      ok4,
      "listItemIndent",
      self.containerState.size + 1
    )(code4);
  }
  function notBlank(code4) {
    if (self.containerState.furtherBlankLines || !markdownSpace(code4)) {
      self.containerState.furtherBlankLines = void 0;
      self.containerState.initialBlankLine = void 0;
      return notInCurrentItem(code4);
    }
    self.containerState.furtherBlankLines = void 0;
    self.containerState.initialBlankLine = void 0;
    return effects.attempt(indentConstruct, ok4, notInCurrentItem)(code4);
  }
  function notInCurrentItem(code4) {
    self.containerState._closeFlow = true;
    self.interrupt = void 0;
    return factorySpace(
      effects,
      effects.attempt(list, ok4, nok),
      "linePrefix",
      self.parser.constructs.disable.null.includes("codeIndented") ? void 0 : 4
    )(code4);
  }
}
function tokenizeIndent(effects, ok4, nok) {
  const self = this;
  return factorySpace(
    effects,
    afterPrefix,
    "listItemIndent",
    self.containerState.size + 1
  );
  function afterPrefix(code4) {
    const tail = self.events[self.events.length - 1];
    return tail && tail[1].type === "listItemIndent" && tail[2].sliceSerialize(tail[1], true).length === self.containerState.size ? ok4(code4) : nok(code4);
  }
}
function tokenizeListEnd(effects) {
  effects.exit(this.containerState.type);
}
function tokenizeListItemPrefixWhitespace(effects, ok4, nok) {
  const self = this;
  return factorySpace(
    effects,
    afterPrefix,
    "listItemPrefixWhitespace",
    self.parser.constructs.disable.null.includes("codeIndented") ? void 0 : 4 + 1
  );
  function afterPrefix(code4) {
    const tail = self.events[self.events.length - 1];
    return !markdownSpace(code4) && tail && tail[1].type === "listItemPrefixWhitespace" ? ok4(code4) : nok(code4);
  }
}

// node_modules/.pnpm/micromark-core-commonmark@1.1.0/node_modules/micromark-core-commonmark/lib/setext-underline.js
var setextUnderline = {
  name: "setextUnderline",
  tokenize: tokenizeSetextUnderline,
  resolveTo: resolveToSetextUnderline
};
function resolveToSetextUnderline(events, context) {
  let index2 = events.length;
  let content3;
  let text6;
  let definition3;
  while (index2--) {
    if (events[index2][0] === "enter") {
      if (events[index2][1].type === "content") {
        content3 = index2;
        break;
      }
      if (events[index2][1].type === "paragraph") {
        text6 = index2;
      }
    } else {
      if (events[index2][1].type === "content") {
        events.splice(index2, 1);
      }
      if (!definition3 && events[index2][1].type === "definition") {
        definition3 = index2;
      }
    }
  }
  const heading3 = {
    type: "setextHeading",
    start: Object.assign({}, events[text6][1].start),
    end: Object.assign({}, events[events.length - 1][1].end)
  };
  events[text6][1].type = "setextHeadingText";
  if (definition3) {
    events.splice(text6, 0, ["enter", heading3, context]);
    events.splice(definition3 + 1, 0, ["exit", events[content3][1], context]);
    events[content3][1].end = Object.assign({}, events[definition3][1].end);
  } else {
    events[content3][1] = heading3;
  }
  events.push(["exit", heading3, context]);
  return events;
}
function tokenizeSetextUnderline(effects, ok4, nok) {
  const self = this;
  let marker;
  return start;
  function start(code4) {
    let index2 = self.events.length;
    let paragraph3;
    while (index2--) {
      if (self.events[index2][1].type !== "lineEnding" && self.events[index2][1].type !== "linePrefix" && self.events[index2][1].type !== "content") {
        paragraph3 = self.events[index2][1].type === "paragraph";
        break;
      }
    }
    if (!self.parser.lazy[self.now().line] && (self.interrupt || paragraph3)) {
      effects.enter("setextHeadingLine");
      marker = code4;
      return before(code4);
    }
    return nok(code4);
  }
  function before(code4) {
    effects.enter("setextHeadingLineSequence");
    return inside(code4);
  }
  function inside(code4) {
    if (code4 === marker) {
      effects.consume(code4);
      return inside;
    }
    effects.exit("setextHeadingLineSequence");
    return markdownSpace(code4) ? factorySpace(effects, after, "lineSuffix")(code4) : after(code4);
  }
  function after(code4) {
    if (code4 === null || markdownLineEnding(code4)) {
      effects.exit("setextHeadingLine");
      return ok4(code4);
    }
    return nok(code4);
  }
}

// node_modules/.pnpm/micromark@3.2.0/node_modules/micromark/lib/initialize/flow.js
var flow = {
  tokenize: initializeFlow
};
function initializeFlow(effects) {
  const self = this;
  const initial = effects.attempt(
    // Try to parse a blank line.
    blankLine,
    atBlankEnding,
    // Try to parse initial flow (essentially, only code).
    effects.attempt(
      this.parser.constructs.flowInitial,
      afterConstruct,
      factorySpace(
        effects,
        effects.attempt(
          this.parser.constructs.flow,
          afterConstruct,
          effects.attempt(content2, afterConstruct)
        ),
        "linePrefix"
      )
    )
  );
  return initial;
  function atBlankEnding(code4) {
    if (code4 === null) {
      effects.consume(code4);
      return;
    }
    effects.enter("lineEndingBlank");
    effects.consume(code4);
    effects.exit("lineEndingBlank");
    self.currentConstruct = void 0;
    return initial;
  }
  function afterConstruct(code4) {
    if (code4 === null) {
      effects.consume(code4);
      return;
    }
    effects.enter("lineEnding");
    effects.consume(code4);
    effects.exit("lineEnding");
    self.currentConstruct = void 0;
    return initial;
  }
}

// node_modules/.pnpm/micromark@3.2.0/node_modules/micromark/lib/initialize/text.js
var resolver = {
  resolveAll: createResolver()
};
var string = initializeFactory("string");
var text = initializeFactory("text");
function initializeFactory(field) {
  return {
    tokenize: initializeText,
    resolveAll: createResolver(
      field === "text" ? resolveAllLineSuffixes : void 0
    )
  };
  function initializeText(effects) {
    const self = this;
    const constructs3 = this.parser.constructs[field];
    const text6 = effects.attempt(constructs3, start, notText);
    return start;
    function start(code4) {
      return atBreak(code4) ? text6(code4) : notText(code4);
    }
    function notText(code4) {
      if (code4 === null) {
        effects.consume(code4);
        return;
      }
      effects.enter("data");
      effects.consume(code4);
      return data;
    }
    function data(code4) {
      if (atBreak(code4)) {
        effects.exit("data");
        return text6(code4);
      }
      effects.consume(code4);
      return data;
    }
    function atBreak(code4) {
      if (code4 === null) {
        return true;
      }
      const list4 = constructs3[code4];
      let index2 = -1;
      if (list4) {
        while (++index2 < list4.length) {
          const item = list4[index2];
          if (!item.previous || item.previous.call(self, self.previous)) {
            return true;
          }
        }
      }
      return false;
    }
  }
}
function createResolver(extraResolver) {
  return resolveAllText;
  function resolveAllText(events, context) {
    let index2 = -1;
    let enter;
    while (++index2 <= events.length) {
      if (enter === void 0) {
        if (events[index2] && events[index2][1].type === "data") {
          enter = index2;
          index2++;
        }
      } else if (!events[index2] || events[index2][1].type !== "data") {
        if (index2 !== enter + 2) {
          events[enter][1].end = events[index2 - 1][1].end;
          events.splice(enter + 2, index2 - enter - 2);
          index2 = enter + 2;
        }
        enter = void 0;
      }
    }
    return extraResolver ? extraResolver(events, context) : events;
  }
}
function resolveAllLineSuffixes(events, context) {
  let eventIndex = 0;
  while (++eventIndex <= events.length) {
    if ((eventIndex === events.length || events[eventIndex][1].type === "lineEnding") && events[eventIndex - 1][1].type === "data") {
      const data = events[eventIndex - 1][1];
      const chunks = context.sliceStream(data);
      let index2 = chunks.length;
      let bufferIndex = -1;
      let size = 0;
      let tabs;
      while (index2--) {
        const chunk = chunks[index2];
        if (typeof chunk === "string") {
          bufferIndex = chunk.length;
          while (chunk.charCodeAt(bufferIndex - 1) === 32) {
            size++;
            bufferIndex--;
          }
          if (bufferIndex)
            break;
          bufferIndex = -1;
        } else if (chunk === -2) {
          tabs = true;
          size++;
        } else if (chunk === -1) {
        } else {
          index2++;
          break;
        }
      }
      if (size) {
        const token = {
          type: eventIndex === events.length || tabs || size < 2 ? "lineSuffix" : "hardBreakTrailing",
          start: {
            line: data.end.line,
            column: data.end.column - size,
            offset: data.end.offset - size,
            _index: data.start._index + index2,
            _bufferIndex: index2 ? bufferIndex : data.start._bufferIndex + bufferIndex
          },
          end: Object.assign({}, data.end)
        };
        data.end = Object.assign({}, token.start);
        if (data.start.offset === data.end.offset) {
          Object.assign(data, token);
        } else {
          events.splice(
            eventIndex,
            0,
            ["enter", token, context],
            ["exit", token, context]
          );
          eventIndex += 2;
        }
      }
      eventIndex++;
    }
  }
  return events;
}

// node_modules/.pnpm/micromark@3.2.0/node_modules/micromark/lib/create-tokenizer.js
function createTokenizer(parser, initialize, from) {
  let point4 = Object.assign(
    from ? Object.assign({}, from) : {
      line: 1,
      column: 1,
      offset: 0
    },
    {
      _index: 0,
      _bufferIndex: -1
    }
  );
  const columnStart = {};
  const resolveAllConstructs = [];
  let chunks = [];
  let stack = [];
  let consumed = true;
  const effects = {
    consume,
    enter,
    exit: exit3,
    attempt: constructFactory(onsuccessfulconstruct),
    check: constructFactory(onsuccessfulcheck),
    interrupt: constructFactory(onsuccessfulcheck, {
      interrupt: true
    })
  };
  const context = {
    previous: null,
    code: null,
    containerState: {},
    events: [],
    parser,
    sliceStream,
    sliceSerialize,
    now,
    defineSkip,
    write
  };
  let state = initialize.tokenize.call(context, effects);
  let expectedCode;
  if (initialize.resolveAll) {
    resolveAllConstructs.push(initialize);
  }
  return context;
  function write(slice) {
    chunks = push(chunks, slice);
    main();
    if (chunks[chunks.length - 1] !== null) {
      return [];
    }
    addResult(initialize, 0);
    context.events = resolveAll(resolveAllConstructs, context.events, context);
    return context.events;
  }
  function sliceSerialize(token, expandTabs) {
    return serializeChunks(sliceStream(token), expandTabs);
  }
  function sliceStream(token) {
    return sliceChunks(chunks, token);
  }
  function now() {
    const { line, column, offset, _index, _bufferIndex } = point4;
    return {
      line,
      column,
      offset,
      _index,
      _bufferIndex
    };
  }
  function defineSkip(value) {
    columnStart[value.line] = value.column;
    accountForPotentialSkip();
  }
  function main() {
    let chunkIndex;
    while (point4._index < chunks.length) {
      const chunk = chunks[point4._index];
      if (typeof chunk === "string") {
        chunkIndex = point4._index;
        if (point4._bufferIndex < 0) {
          point4._bufferIndex = 0;
        }
        while (point4._index === chunkIndex && point4._bufferIndex < chunk.length) {
          go(chunk.charCodeAt(point4._bufferIndex));
        }
      } else {
        go(chunk);
      }
    }
  }
  function go(code4) {
    consumed = void 0;
    expectedCode = code4;
    state = state(code4);
  }
  function consume(code4) {
    if (markdownLineEnding(code4)) {
      point4.line++;
      point4.column = 1;
      point4.offset += code4 === -3 ? 2 : 1;
      accountForPotentialSkip();
    } else if (code4 !== -1) {
      point4.column++;
      point4.offset++;
    }
    if (point4._bufferIndex < 0) {
      point4._index++;
    } else {
      point4._bufferIndex++;
      if (point4._bufferIndex === chunks[point4._index].length) {
        point4._bufferIndex = -1;
        point4._index++;
      }
    }
    context.previous = code4;
    consumed = true;
  }
  function enter(type, fields) {
    const token = fields || {};
    token.type = type;
    token.start = now();
    context.events.push(["enter", token, context]);
    stack.push(token);
    return token;
  }
  function exit3(type) {
    const token = stack.pop();
    token.end = now();
    context.events.push(["exit", token, context]);
    return token;
  }
  function onsuccessfulconstruct(construct, info) {
    addResult(construct, info.from);
  }
  function onsuccessfulcheck(_, info) {
    info.restore();
  }
  function constructFactory(onreturn, fields) {
    return hook;
    function hook(constructs3, returnState, bogusState) {
      let listOfConstructs;
      let constructIndex;
      let currentConstruct;
      let info;
      return Array.isArray(constructs3) ? handleListOfConstructs(constructs3) : "tokenize" in constructs3 ? (
        // @ts-expect-error Looks like a construct.
        handleListOfConstructs([constructs3])
      ) : handleMapOfConstructs(constructs3);
      function handleMapOfConstructs(map4) {
        return start;
        function start(code4) {
          const def = code4 !== null && map4[code4];
          const all4 = code4 !== null && map4.null;
          const list4 = [
            // To do: add more extension tests.
            /* c8 ignore next 2 */
            ...Array.isArray(def) ? def : def ? [def] : [],
            ...Array.isArray(all4) ? all4 : all4 ? [all4] : []
          ];
          return handleListOfConstructs(list4)(code4);
        }
      }
      function handleListOfConstructs(list4) {
        listOfConstructs = list4;
        constructIndex = 0;
        if (list4.length === 0) {
          return bogusState;
        }
        return handleConstruct(list4[constructIndex]);
      }
      function handleConstruct(construct) {
        return start;
        function start(code4) {
          info = store();
          currentConstruct = construct;
          if (!construct.partial) {
            context.currentConstruct = construct;
          }
          if (construct.name && context.parser.constructs.disable.null.includes(construct.name)) {
            return nok(code4);
          }
          return construct.tokenize.call(
            // If we do have fields, create an object w/ `context` as its
            // prototype.
            // This allows a “live binding”, which is needed for `interrupt`.
            fields ? Object.assign(Object.create(context), fields) : context,
            effects,
            ok4,
            nok
          )(code4);
        }
      }
      function ok4(code4) {
        consumed = true;
        onreturn(currentConstruct, info);
        return returnState;
      }
      function nok(code4) {
        consumed = true;
        info.restore();
        if (++constructIndex < listOfConstructs.length) {
          return handleConstruct(listOfConstructs[constructIndex]);
        }
        return bogusState;
      }
    }
  }
  function addResult(construct, from2) {
    if (construct.resolveAll && !resolveAllConstructs.includes(construct)) {
      resolveAllConstructs.push(construct);
    }
    if (construct.resolve) {
      splice(
        context.events,
        from2,
        context.events.length - from2,
        construct.resolve(context.events.slice(from2), context)
      );
    }
    if (construct.resolveTo) {
      context.events = construct.resolveTo(context.events, context);
    }
  }
  function store() {
    const startPoint = now();
    const startPrevious = context.previous;
    const startCurrentConstruct = context.currentConstruct;
    const startEventsIndex = context.events.length;
    const startStack = Array.from(stack);
    return {
      restore,
      from: startEventsIndex
    };
    function restore() {
      point4 = startPoint;
      context.previous = startPrevious;
      context.currentConstruct = startCurrentConstruct;
      context.events.length = startEventsIndex;
      stack = startStack;
      accountForPotentialSkip();
    }
  }
  function accountForPotentialSkip() {
    if (point4.line in columnStart && point4.column < 2) {
      point4.column = columnStart[point4.line];
      point4.offset += columnStart[point4.line] - 1;
    }
  }
}
function sliceChunks(chunks, token) {
  const startIndex = token.start._index;
  const startBufferIndex = token.start._bufferIndex;
  const endIndex = token.end._index;
  const endBufferIndex = token.end._bufferIndex;
  let view;
  if (startIndex === endIndex) {
    view = [chunks[startIndex].slice(startBufferIndex, endBufferIndex)];
  } else {
    view = chunks.slice(startIndex, endIndex);
    if (startBufferIndex > -1) {
      const head = view[0];
      if (typeof head === "string") {
        view[0] = head.slice(startBufferIndex);
      } else {
        view.shift();
      }
    }
    if (endBufferIndex > 0) {
      view.push(chunks[endIndex].slice(0, endBufferIndex));
    }
  }
  return view;
}
function serializeChunks(chunks, expandTabs) {
  let index2 = -1;
  const result = [];
  let atTab;
  while (++index2 < chunks.length) {
    const chunk = chunks[index2];
    let value;
    if (typeof chunk === "string") {
      value = chunk;
    } else
      switch (chunk) {
        case -5: {
          value = "\r";
          break;
        }
        case -4: {
          value = "\n";
          break;
        }
        case -3: {
          value = "\r\n";
          break;
        }
        case -2: {
          value = expandTabs ? " " : "	";
          break;
        }
        case -1: {
          if (!expandTabs && atTab)
            continue;
          value = " ";
          break;
        }
        default: {
          value = String.fromCharCode(chunk);
        }
      }
    atTab = chunk === -2;
    result.push(value);
  }
  return result.join("");
}

// node_modules/.pnpm/micromark@3.2.0/node_modules/micromark/lib/constructs.js
var constructs_exports = {};
__export(constructs_exports, {
  attentionMarkers: () => attentionMarkers,
  contentInitial: () => contentInitial,
  disable: () => disable,
  document: () => document3,
  flow: () => flow2,
  flowInitial: () => flowInitial,
  insideSpan: () => insideSpan,
  string: () => string2,
  text: () => text2
});
var document3 = {
  [42]: list,
  [43]: list,
  [45]: list,
  [48]: list,
  [49]: list,
  [50]: list,
  [51]: list,
  [52]: list,
  [53]: list,
  [54]: list,
  [55]: list,
  [56]: list,
  [57]: list,
  [62]: blockQuote
};
var contentInitial = {
  [91]: definition
};
var flowInitial = {
  [-2]: codeIndented,
  [-1]: codeIndented,
  [32]: codeIndented
};
var flow2 = {
  [35]: headingAtx,
  [42]: thematicBreak,
  [45]: [setextUnderline, thematicBreak],
  [60]: htmlFlow,
  [61]: setextUnderline,
  [95]: thematicBreak,
  [96]: codeFenced,
  [126]: codeFenced
};
var string2 = {
  [38]: characterReference,
  [92]: characterEscape
};
var text2 = {
  [-5]: lineEnding,
  [-4]: lineEnding,
  [-3]: lineEnding,
  [33]: labelStartImage,
  [38]: characterReference,
  [42]: attention,
  [60]: [autolink, htmlText],
  [91]: labelStartLink,
  [92]: [hardBreakEscape, characterEscape],
  [93]: labelEnd,
  [95]: attention,
  [96]: codeText
};
var insideSpan = {
  null: [attention, resolver]
};
var attentionMarkers = {
  null: [42, 95]
};
var disable = {
  null: []
};

// node_modules/.pnpm/micromark@3.2.0/node_modules/micromark/lib/parse.js
function parse(options) {
  const settings = options || {};
  const constructs3 = (
    /** @type {FullNormalizedExtension} */
    combineExtensions([constructs_exports, ...settings.extensions || []])
  );
  const parser = {
    defined: [],
    lazy: {},
    constructs: constructs3,
    content: create2(content),
    document: create2(document2),
    flow: create2(flow),
    string: create2(string),
    text: create2(text)
  };
  return parser;
  function create2(initial) {
    return creator;
    function creator(from) {
      return createTokenizer(parser, initial, from);
    }
  }
}

// node_modules/.pnpm/micromark@3.2.0/node_modules/micromark/lib/preprocess.js
var search = /[\0\t\n\r]/g;
function preprocess() {
  let column = 1;
  let buffer2 = "";
  let start = true;
  let atCarriageReturn;
  return preprocessor;
  function preprocessor(value, encoding, end) {
    const chunks = [];
    let match;
    let next;
    let startPosition;
    let endPosition;
    let code4;
    value = buffer2 + value.toString(encoding);
    startPosition = 0;
    buffer2 = "";
    if (start) {
      if (value.charCodeAt(0) === 65279) {
        startPosition++;
      }
      start = void 0;
    }
    while (startPosition < value.length) {
      search.lastIndex = startPosition;
      match = search.exec(value);
      endPosition = match && match.index !== void 0 ? match.index : value.length;
      code4 = value.charCodeAt(endPosition);
      if (!match) {
        buffer2 = value.slice(startPosition);
        break;
      }
      if (code4 === 10 && startPosition === endPosition && atCarriageReturn) {
        chunks.push(-3);
        atCarriageReturn = void 0;
      } else {
        if (atCarriageReturn) {
          chunks.push(-5);
          atCarriageReturn = void 0;
        }
        if (startPosition < endPosition) {
          chunks.push(value.slice(startPosition, endPosition));
          column += endPosition - startPosition;
        }
        switch (code4) {
          case 0: {
            chunks.push(65533);
            column++;
            break;
          }
          case 9: {
            next = Math.ceil(column / 4) * 4;
            chunks.push(-2);
            while (column++ < next)
              chunks.push(-1);
            break;
          }
          case 10: {
            chunks.push(-4);
            column = 1;
            break;
          }
          default: {
            atCarriageReturn = true;
            column = 1;
          }
        }
      }
      startPosition = endPosition + 1;
    }
    if (end) {
      if (atCarriageReturn)
        chunks.push(-5);
      if (buffer2)
        chunks.push(buffer2);
      chunks.push(null);
    }
    return chunks;
  }
}

// node_modules/.pnpm/micromark@3.2.0/node_modules/micromark/lib/postprocess.js
function postprocess(events) {
  while (!subtokenize(events)) {
  }
  return events;
}

// node_modules/.pnpm/micromark-util-decode-numeric-character-reference@1.1.0/node_modules/micromark-util-decode-numeric-character-reference/index.js
function decodeNumericCharacterReference(value, base2) {
  const code4 = Number.parseInt(value, base2);
  if (
    // C0 except for HT, LF, FF, CR, space.
    code4 < 9 || code4 === 11 || code4 > 13 && code4 < 32 || // Control character (DEL) of C0, and C1 controls.
    code4 > 126 && code4 < 160 || // Lone high surrogates and low surrogates.
    code4 > 55295 && code4 < 57344 || // Noncharacters.
    code4 > 64975 && code4 < 65008 || (code4 & 65535) === 65535 || (code4 & 65535) === 65534 || // Out of range
    code4 > 1114111
  ) {
    return "\uFFFD";
  }
  return String.fromCharCode(code4);
}

// node_modules/.pnpm/micromark-util-decode-string@1.1.0/node_modules/micromark-util-decode-string/index.js
var characterEscapeOrReference = /\\([!-/:-@[-`{-~])|&(#(?:\d{1,7}|x[\da-f]{1,6})|[\da-z]{1,31});/gi;
function decodeString(value) {
  return value.replace(characterEscapeOrReference, decode);
}
function decode($0, $1, $2) {
  if ($1) {
    return $1;
  }
  const head = $2.charCodeAt(0);
  if (head === 35) {
    const head2 = $2.charCodeAt(1);
    const hex = head2 === 120 || head2 === 88;
    return decodeNumericCharacterReference($2.slice(hex ? 2 : 1), hex ? 16 : 10);
  }
  return decodeNamedCharacterReference($2) || $0;
}

// node_modules/.pnpm/mdast-util-from-markdown@1.3.1/node_modules/mdast-util-from-markdown/lib/index.js
var own2 = {}.hasOwnProperty;
var fromMarkdown = (
  /**
   * @type {(
   *   ((value: Value, encoding: Encoding, options?: Options | null | undefined) => Root) &
   *   ((value: Value, options?: Options | null | undefined) => Root)
   * )}
   */
  /**
   * @param {Value} value
   * @param {Encoding | Options | null | undefined} [encoding]
   * @param {Options | null | undefined} [options]
   * @returns {Root}
   */
  function(value, encoding, options) {
    if (typeof encoding !== "string") {
      options = encoding;
      encoding = void 0;
    }
    return compiler(options)(
      postprocess(
        parse(options).document().write(preprocess()(value, encoding, true))
      )
    );
  }
);
function compiler(options) {
  const config = {
    transforms: [],
    canContainEols: ["emphasis", "fragment", "heading", "paragraph", "strong"],
    enter: {
      autolink: opener(link3),
      autolinkProtocol: onenterdata,
      autolinkEmail: onenterdata,
      atxHeading: opener(heading3),
      blockQuote: opener(blockQuote2),
      characterEscape: onenterdata,
      characterReference: onenterdata,
      codeFenced: opener(codeFlow),
      codeFencedFenceInfo: buffer2,
      codeFencedFenceMeta: buffer2,
      codeIndented: opener(codeFlow, buffer2),
      codeText: opener(codeText2, buffer2),
      codeTextData: onenterdata,
      data: onenterdata,
      codeFlowValue: onenterdata,
      definition: opener(definition3),
      definitionDestinationString: buffer2,
      definitionLabelString: buffer2,
      definitionTitleString: buffer2,
      emphasis: opener(emphasis3),
      hardBreakEscape: opener(hardBreak3),
      hardBreakTrailing: opener(hardBreak3),
      htmlFlow: opener(html5, buffer2),
      htmlFlowData: onenterdata,
      htmlText: opener(html5, buffer2),
      htmlTextData: onenterdata,
      image: opener(image3),
      label: buffer2,
      link: opener(link3),
      listItem: opener(listItem3),
      listItemValue: onenterlistitemvalue,
      listOrdered: opener(list4, onenterlistordered),
      listUnordered: opener(list4),
      paragraph: opener(paragraph3),
      reference: onenterreference,
      referenceString: buffer2,
      resourceDestinationString: buffer2,
      resourceTitleString: buffer2,
      setextHeading: opener(heading3),
      strong: opener(strong3),
      thematicBreak: opener(thematicBreak4)
    },
    exit: {
      atxHeading: closer(),
      atxHeadingSequence: onexitatxheadingsequence,
      autolink: closer(),
      autolinkEmail: onexitautolinkemail,
      autolinkProtocol: onexitautolinkprotocol,
      blockQuote: closer(),
      characterEscapeValue: onexitdata,
      characterReferenceMarkerHexadecimal: onexitcharacterreferencemarker,
      characterReferenceMarkerNumeric: onexitcharacterreferencemarker,
      characterReferenceValue: onexitcharacterreferencevalue,
      codeFenced: closer(onexitcodefenced),
      codeFencedFence: onexitcodefencedfence,
      codeFencedFenceInfo: onexitcodefencedfenceinfo,
      codeFencedFenceMeta: onexitcodefencedfencemeta,
      codeFlowValue: onexitdata,
      codeIndented: closer(onexitcodeindented),
      codeText: closer(onexitcodetext),
      codeTextData: onexitdata,
      data: onexitdata,
      definition: closer(),
      definitionDestinationString: onexitdefinitiondestinationstring,
      definitionLabelString: onexitdefinitionlabelstring,
      definitionTitleString: onexitdefinitiontitlestring,
      emphasis: closer(),
      hardBreakEscape: closer(onexithardbreak),
      hardBreakTrailing: closer(onexithardbreak),
      htmlFlow: closer(onexithtmlflow),
      htmlFlowData: onexitdata,
      htmlText: closer(onexithtmltext),
      htmlTextData: onexitdata,
      image: closer(onexitimage),
      label: onexitlabel,
      labelText: onexitlabeltext,
      lineEnding: onexitlineending,
      link: closer(onexitlink),
      listItem: closer(),
      listOrdered: closer(),
      listUnordered: closer(),
      paragraph: closer(),
      referenceString: onexitreferencestring,
      resourceDestinationString: onexitresourcedestinationstring,
      resourceTitleString: onexitresourcetitlestring,
      resource: onexitresource,
      setextHeading: closer(onexitsetextheading),
      setextHeadingLineSequence: onexitsetextheadinglinesequence,
      setextHeadingText: onexitsetextheadingtext,
      strong: closer(),
      thematicBreak: closer()
    }
  };
  configure(config, (options || {}).mdastExtensions || []);
  const data = {};
  return compile;
  function compile(events) {
    let tree = {
      type: "root",
      children: []
    };
    const context = {
      stack: [tree],
      tokenStack: [],
      config,
      enter,
      exit: exit3,
      buffer: buffer2,
      resume,
      setData,
      getData
    };
    const listStack = [];
    let index2 = -1;
    while (++index2 < events.length) {
      if (events[index2][1].type === "listOrdered" || events[index2][1].type === "listUnordered") {
        if (events[index2][0] === "enter") {
          listStack.push(index2);
        } else {
          const tail = listStack.pop();
          index2 = prepareList(events, tail, index2);
        }
      }
    }
    index2 = -1;
    while (++index2 < events.length) {
      const handler = config[events[index2][0]];
      if (own2.call(handler, events[index2][1].type)) {
        handler[events[index2][1].type].call(
          Object.assign(
            {
              sliceSerialize: events[index2][2].sliceSerialize
            },
            context
          ),
          events[index2][1]
        );
      }
    }
    if (context.tokenStack.length > 0) {
      const tail = context.tokenStack[context.tokenStack.length - 1];
      const handler = tail[1] || defaultOnError;
      handler.call(context, void 0, tail[0]);
    }
    tree.position = {
      start: point2(
        events.length > 0 ? events[0][1].start : {
          line: 1,
          column: 1,
          offset: 0
        }
      ),
      end: point2(
        events.length > 0 ? events[events.length - 2][1].end : {
          line: 1,
          column: 1,
          offset: 0
        }
      )
    };
    index2 = -1;
    while (++index2 < config.transforms.length) {
      tree = config.transforms[index2](tree) || tree;
    }
    return tree;
  }
  function prepareList(events, start, length) {
    let index2 = start - 1;
    let containerBalance = -1;
    let listSpread = false;
    let listItem4;
    let lineIndex;
    let firstBlankLineIndex;
    let atMarker;
    while (++index2 <= length) {
      const event = events[index2];
      if (event[1].type === "listUnordered" || event[1].type === "listOrdered" || event[1].type === "blockQuote") {
        if (event[0] === "enter") {
          containerBalance++;
        } else {
          containerBalance--;
        }
        atMarker = void 0;
      } else if (event[1].type === "lineEndingBlank") {
        if (event[0] === "enter") {
          if (listItem4 && !atMarker && !containerBalance && !firstBlankLineIndex) {
            firstBlankLineIndex = index2;
          }
          atMarker = void 0;
        }
      } else if (event[1].type === "linePrefix" || event[1].type === "listItemValue" || event[1].type === "listItemMarker" || event[1].type === "listItemPrefix" || event[1].type === "listItemPrefixWhitespace") {
      } else {
        atMarker = void 0;
      }
      if (!containerBalance && event[0] === "enter" && event[1].type === "listItemPrefix" || containerBalance === -1 && event[0] === "exit" && (event[1].type === "listUnordered" || event[1].type === "listOrdered")) {
        if (listItem4) {
          let tailIndex = index2;
          lineIndex = void 0;
          while (tailIndex--) {
            const tailEvent = events[tailIndex];
            if (tailEvent[1].type === "lineEnding" || tailEvent[1].type === "lineEndingBlank") {
              if (tailEvent[0] === "exit")
                continue;
              if (lineIndex) {
                events[lineIndex][1].type = "lineEndingBlank";
                listSpread = true;
              }
              tailEvent[1].type = "lineEnding";
              lineIndex = tailIndex;
            } else if (tailEvent[1].type === "linePrefix" || tailEvent[1].type === "blockQuotePrefix" || tailEvent[1].type === "blockQuotePrefixWhitespace" || tailEvent[1].type === "blockQuoteMarker" || tailEvent[1].type === "listItemIndent") {
            } else {
              break;
            }
          }
          if (firstBlankLineIndex && (!lineIndex || firstBlankLineIndex < lineIndex)) {
            listItem4._spread = true;
          }
          listItem4.end = Object.assign(
            {},
            lineIndex ? events[lineIndex][1].start : event[1].end
          );
          events.splice(lineIndex || index2, 0, ["exit", listItem4, event[2]]);
          index2++;
          length++;
        }
        if (event[1].type === "listItemPrefix") {
          listItem4 = {
            type: "listItem",
            _spread: false,
            start: Object.assign({}, event[1].start),
            // @ts-expect-error: we’ll add `end` in a second.
            end: void 0
          };
          events.splice(index2, 0, ["enter", listItem4, event[2]]);
          index2++;
          length++;
          firstBlankLineIndex = void 0;
          atMarker = true;
        }
      }
    }
    events[start][1]._spread = listSpread;
    return length;
  }
  function setData(key, value) {
    data[key] = value;
  }
  function getData(key) {
    return data[key];
  }
  function opener(create2, and) {
    return open;
    function open(token) {
      enter.call(this, create2(token), token);
      if (and)
        and.call(this, token);
    }
  }
  function buffer2() {
    this.stack.push({
      type: "fragment",
      children: []
    });
  }
  function enter(node3, token, errorHandler) {
    const parent = this.stack[this.stack.length - 1];
    parent.children.push(node3);
    this.stack.push(node3);
    this.tokenStack.push([token, errorHandler]);
    node3.position = {
      start: point2(token.start)
    };
    return node3;
  }
  function closer(and) {
    return close;
    function close(token) {
      if (and)
        and.call(this, token);
      exit3.call(this, token);
    }
  }
  function exit3(token, onExitError) {
    const node3 = this.stack.pop();
    const open = this.tokenStack.pop();
    if (!open) {
      throw new Error(
        "Cannot close `" + token.type + "` (" + stringifyPosition({
          start: token.start,
          end: token.end
        }) + "): it\u2019s not open"
      );
    } else if (open[0].type !== token.type) {
      if (onExitError) {
        onExitError.call(this, token, open[0]);
      } else {
        const handler = open[1] || defaultOnError;
        handler.call(this, token, open[0]);
      }
    }
    node3.position.end = point2(token.end);
    return node3;
  }
  function resume() {
    return toString(this.stack.pop());
  }
  function onenterlistordered() {
    setData("expectingFirstListItemValue", true);
  }
  function onenterlistitemvalue(token) {
    if (getData("expectingFirstListItemValue")) {
      const ancestor = this.stack[this.stack.length - 2];
      ancestor.start = Number.parseInt(this.sliceSerialize(token), 10);
      setData("expectingFirstListItemValue");
    }
  }
  function onexitcodefencedfenceinfo() {
    const data2 = this.resume();
    const node3 = this.stack[this.stack.length - 1];
    node3.lang = data2;
  }
  function onexitcodefencedfencemeta() {
    const data2 = this.resume();
    const node3 = this.stack[this.stack.length - 1];
    node3.meta = data2;
  }
  function onexitcodefencedfence() {
    if (getData("flowCodeInside"))
      return;
    this.buffer();
    setData("flowCodeInside", true);
  }
  function onexitcodefenced() {
    const data2 = this.resume();
    const node3 = this.stack[this.stack.length - 1];
    node3.value = data2.replace(/^(\r?\n|\r)|(\r?\n|\r)$/g, "");
    setData("flowCodeInside");
  }
  function onexitcodeindented() {
    const data2 = this.resume();
    const node3 = this.stack[this.stack.length - 1];
    node3.value = data2.replace(/(\r?\n|\r)$/g, "");
  }
  function onexitdefinitionlabelstring(token) {
    const label = this.resume();
    const node3 = this.stack[this.stack.length - 1];
    node3.label = label;
    node3.identifier = normalizeIdentifier(
      this.sliceSerialize(token)
    ).toLowerCase();
  }
  function onexitdefinitiontitlestring() {
    const data2 = this.resume();
    const node3 = this.stack[this.stack.length - 1];
    node3.title = data2;
  }
  function onexitdefinitiondestinationstring() {
    const data2 = this.resume();
    const node3 = this.stack[this.stack.length - 1];
    node3.url = data2;
  }
  function onexitatxheadingsequence(token) {
    const node3 = this.stack[this.stack.length - 1];
    if (!node3.depth) {
      const depth = this.sliceSerialize(token).length;
      node3.depth = depth;
    }
  }
  function onexitsetextheadingtext() {
    setData("setextHeadingSlurpLineEnding", true);
  }
  function onexitsetextheadinglinesequence(token) {
    const node3 = this.stack[this.stack.length - 1];
    node3.depth = this.sliceSerialize(token).charCodeAt(0) === 61 ? 1 : 2;
  }
  function onexitsetextheading() {
    setData("setextHeadingSlurpLineEnding");
  }
  function onenterdata(token) {
    const node3 = this.stack[this.stack.length - 1];
    let tail = node3.children[node3.children.length - 1];
    if (!tail || tail.type !== "text") {
      tail = text6();
      tail.position = {
        start: point2(token.start)
      };
      node3.children.push(tail);
    }
    this.stack.push(tail);
  }
  function onexitdata(token) {
    const tail = this.stack.pop();
    tail.value += this.sliceSerialize(token);
    tail.position.end = point2(token.end);
  }
  function onexitlineending(token) {
    const context = this.stack[this.stack.length - 1];
    if (getData("atHardBreak")) {
      const tail = context.children[context.children.length - 1];
      tail.position.end = point2(token.end);
      setData("atHardBreak");
      return;
    }
    if (!getData("setextHeadingSlurpLineEnding") && config.canContainEols.includes(context.type)) {
      onenterdata.call(this, token);
      onexitdata.call(this, token);
    }
  }
  function onexithardbreak() {
    setData("atHardBreak", true);
  }
  function onexithtmlflow() {
    const data2 = this.resume();
    const node3 = this.stack[this.stack.length - 1];
    node3.value = data2;
  }
  function onexithtmltext() {
    const data2 = this.resume();
    const node3 = this.stack[this.stack.length - 1];
    node3.value = data2;
  }
  function onexitcodetext() {
    const data2 = this.resume();
    const node3 = this.stack[this.stack.length - 1];
    node3.value = data2;
  }
  function onexitlink() {
    const node3 = this.stack[this.stack.length - 1];
    if (getData("inReference")) {
      const referenceType = getData("referenceType") || "shortcut";
      node3.type += "Reference";
      node3.referenceType = referenceType;
      delete node3.url;
      delete node3.title;
    } else {
      delete node3.identifier;
      delete node3.label;
    }
    setData("referenceType");
  }
  function onexitimage() {
    const node3 = this.stack[this.stack.length - 1];
    if (getData("inReference")) {
      const referenceType = getData("referenceType") || "shortcut";
      node3.type += "Reference";
      node3.referenceType = referenceType;
      delete node3.url;
      delete node3.title;
    } else {
      delete node3.identifier;
      delete node3.label;
    }
    setData("referenceType");
  }
  function onexitlabeltext(token) {
    const string3 = this.sliceSerialize(token);
    const ancestor = this.stack[this.stack.length - 2];
    ancestor.label = decodeString(string3);
    ancestor.identifier = normalizeIdentifier(string3).toLowerCase();
  }
  function onexitlabel() {
    const fragment = this.stack[this.stack.length - 1];
    const value = this.resume();
    const node3 = this.stack[this.stack.length - 1];
    setData("inReference", true);
    if (node3.type === "link") {
      const children = fragment.children;
      node3.children = children;
    } else {
      node3.alt = value;
    }
  }
  function onexitresourcedestinationstring() {
    const data2 = this.resume();
    const node3 = this.stack[this.stack.length - 1];
    node3.url = data2;
  }
  function onexitresourcetitlestring() {
    const data2 = this.resume();
    const node3 = this.stack[this.stack.length - 1];
    node3.title = data2;
  }
  function onexitresource() {
    setData("inReference");
  }
  function onenterreference() {
    setData("referenceType", "collapsed");
  }
  function onexitreferencestring(token) {
    const label = this.resume();
    const node3 = this.stack[this.stack.length - 1];
    node3.label = label;
    node3.identifier = normalizeIdentifier(
      this.sliceSerialize(token)
    ).toLowerCase();
    setData("referenceType", "full");
  }
  function onexitcharacterreferencemarker(token) {
    setData("characterReferenceType", token.type);
  }
  function onexitcharacterreferencevalue(token) {
    const data2 = this.sliceSerialize(token);
    const type = getData("characterReferenceType");
    let value;
    if (type) {
      value = decodeNumericCharacterReference(
        data2,
        type === "characterReferenceMarkerNumeric" ? 10 : 16
      );
      setData("characterReferenceType");
    } else {
      const result = decodeNamedCharacterReference(data2);
      value = result;
    }
    const tail = this.stack.pop();
    tail.value += value;
    tail.position.end = point2(token.end);
  }
  function onexitautolinkprotocol(token) {
    onexitdata.call(this, token);
    const node3 = this.stack[this.stack.length - 1];
    node3.url = this.sliceSerialize(token);
  }
  function onexitautolinkemail(token) {
    onexitdata.call(this, token);
    const node3 = this.stack[this.stack.length - 1];
    node3.url = "mailto:" + this.sliceSerialize(token);
  }
  function blockQuote2() {
    return {
      type: "blockquote",
      children: []
    };
  }
  function codeFlow() {
    return {
      type: "code",
      lang: null,
      meta: null,
      value: ""
    };
  }
  function codeText2() {
    return {
      type: "inlineCode",
      value: ""
    };
  }
  function definition3() {
    return {
      type: "definition",
      identifier: "",
      label: null,
      title: null,
      url: ""
    };
  }
  function emphasis3() {
    return {
      type: "emphasis",
      children: []
    };
  }
  function heading3() {
    return {
      type: "heading",
      depth: void 0,
      children: []
    };
  }
  function hardBreak3() {
    return {
      type: "break"
    };
  }
  function html5() {
    return {
      type: "html",
      value: ""
    };
  }
  function image3() {
    return {
      type: "image",
      title: null,
      url: "",
      alt: null
    };
  }
  function link3() {
    return {
      type: "link",
      title: null,
      url: "",
      children: []
    };
  }
  function list4(token) {
    return {
      type: "list",
      ordered: token.type === "listOrdered",
      start: null,
      spread: token._spread,
      children: []
    };
  }
  function listItem3(token) {
    return {
      type: "listItem",
      spread: token._spread,
      checked: null,
      children: []
    };
  }
  function paragraph3() {
    return {
      type: "paragraph",
      children: []
    };
  }
  function strong3() {
    return {
      type: "strong",
      children: []
    };
  }
  function text6() {
    return {
      type: "text",
      value: ""
    };
  }
  function thematicBreak4() {
    return {
      type: "thematicBreak"
    };
  }
}
function point2(d) {
  return {
    line: d.line,
    column: d.column,
    offset: d.offset
  };
}
function configure(combined, extensions) {
  let index2 = -1;
  while (++index2 < extensions.length) {
    const value = extensions[index2];
    if (Array.isArray(value)) {
      configure(combined, value);
    } else {
      extension(combined, value);
    }
  }
}
function extension(combined, extension2) {
  let key;
  for (key in extension2) {
    if (own2.call(extension2, key)) {
      if (key === "canContainEols") {
        const right = extension2[key];
        if (right) {
          combined[key].push(...right);
        }
      } else if (key === "transforms") {
        const right = extension2[key];
        if (right) {
          combined[key].push(...right);
        }
      } else if (key === "enter" || key === "exit") {
        const right = extension2[key];
        if (right) {
          Object.assign(combined[key], right);
        }
      }
    }
  }
}
function defaultOnError(left, right) {
  if (left) {
    throw new Error(
      "Cannot close `" + left.type + "` (" + stringifyPosition({
        start: left.start,
        end: left.end
      }) + "): a different token (`" + right.type + "`, " + stringifyPosition({
        start: right.start,
        end: right.end
      }) + ") is open"
    );
  } else {
    throw new Error(
      "Cannot close document, a token (`" + right.type + "`, " + stringifyPosition({
        start: right.start,
        end: right.end
      }) + ") is still open"
    );
  }
}

// node_modules/.pnpm/remark-parse@10.0.2/node_modules/remark-parse/lib/index.js
function remarkParse(options) {
  const parser = (doc) => {
    const settings = (
      /** @type {Options} */
      this.data("settings")
    );
    return fromMarkdown(
      doc,
      Object.assign({}, settings, options, {
        // Note: these options are not in the readme.
        // The goal is for them to be set by plugins on `data` instead of being
        // passed by users.
        extensions: this.data("micromarkExtensions") || [],
        mdastExtensions: this.data("fromMarkdownExtensions") || []
      })
    );
  };
  Object.assign(this, { Parser: parser });
}

// node_modules/.pnpm/mdast-util-to-hast@12.3.0/node_modules/mdast-util-to-hast/lib/handlers/blockquote.js
function blockquote(state, node3) {
  const result = {
    type: "element",
    tagName: "blockquote",
    properties: {},
    children: state.wrap(state.all(node3), true)
  };
  state.patch(node3, result);
  return state.applyData(node3, result);
}

// node_modules/.pnpm/mdast-util-to-hast@12.3.0/node_modules/mdast-util-to-hast/lib/handlers/break.js
function hardBreak(state, node3) {
  const result = { type: "element", tagName: "br", properties: {}, children: [] };
  state.patch(node3, result);
  return [state.applyData(node3, result), { type: "text", value: "\n" }];
}

// node_modules/.pnpm/mdast-util-to-hast@12.3.0/node_modules/mdast-util-to-hast/lib/handlers/code.js
function code(state, node3) {
  const value = node3.value ? node3.value + "\n" : "";
  const lang = node3.lang ? node3.lang.match(/^[^ \t]+(?=[ \t]|$)/) : null;
  const properties = {};
  if (lang) {
    properties.className = ["language-" + lang];
  }
  let result = {
    type: "element",
    tagName: "code",
    properties,
    children: [{ type: "text", value }]
  };
  if (node3.meta) {
    result.data = { meta: node3.meta };
  }
  state.patch(node3, result);
  result = state.applyData(node3, result);
  result = { type: "element", tagName: "pre", properties: {}, children: [result] };
  state.patch(node3, result);
  return result;
}

// node_modules/.pnpm/mdast-util-to-hast@12.3.0/node_modules/mdast-util-to-hast/lib/handlers/delete.js
function strikethrough(state, node3) {
  const result = {
    type: "element",
    tagName: "del",
    properties: {},
    children: state.all(node3)
  };
  state.patch(node3, result);
  return state.applyData(node3, result);
}

// node_modules/.pnpm/mdast-util-to-hast@12.3.0/node_modules/mdast-util-to-hast/lib/handlers/emphasis.js
function emphasis(state, node3) {
  const result = {
    type: "element",
    tagName: "em",
    properties: {},
    children: state.all(node3)
  };
  state.patch(node3, result);
  return state.applyData(node3, result);
}

// node_modules/.pnpm/micromark-util-sanitize-uri@1.2.0/node_modules/micromark-util-sanitize-uri/index.js
function normalizeUri(value) {
  const result = [];
  let index2 = -1;
  let start = 0;
  let skip = 0;
  while (++index2 < value.length) {
    const code4 = value.charCodeAt(index2);
    let replace2 = "";
    if (code4 === 37 && asciiAlphanumeric(value.charCodeAt(index2 + 1)) && asciiAlphanumeric(value.charCodeAt(index2 + 2))) {
      skip = 2;
    } else if (code4 < 128) {
      if (!/[!#$&-;=?-Z_a-z~]/.test(String.fromCharCode(code4))) {
        replace2 = String.fromCharCode(code4);
      }
    } else if (code4 > 55295 && code4 < 57344) {
      const next = value.charCodeAt(index2 + 1);
      if (code4 < 56320 && next > 56319 && next < 57344) {
        replace2 = String.fromCharCode(code4, next);
        skip = 1;
      } else {
        replace2 = "\uFFFD";
      }
    } else {
      replace2 = String.fromCharCode(code4);
    }
    if (replace2) {
      result.push(value.slice(start, index2), encodeURIComponent(replace2));
      start = index2 + skip + 1;
      replace2 = "";
    }
    if (skip) {
      index2 += skip;
      skip = 0;
    }
  }
  return result.join("") + value.slice(start);
}

// node_modules/.pnpm/mdast-util-to-hast@12.3.0/node_modules/mdast-util-to-hast/lib/handlers/footnote-reference.js
function footnoteReference(state, node3) {
  const id = String(node3.identifier).toUpperCase();
  const safeId = normalizeUri(id.toLowerCase());
  const index2 = state.footnoteOrder.indexOf(id);
  let counter;
  if (index2 === -1) {
    state.footnoteOrder.push(id);
    state.footnoteCounts[id] = 1;
    counter = state.footnoteOrder.length;
  } else {
    state.footnoteCounts[id]++;
    counter = index2 + 1;
  }
  const reuseCounter = state.footnoteCounts[id];
  const link3 = {
    type: "element",
    tagName: "a",
    properties: {
      href: "#" + state.clobberPrefix + "fn-" + safeId,
      id: state.clobberPrefix + "fnref-" + safeId + (reuseCounter > 1 ? "-" + reuseCounter : ""),
      dataFootnoteRef: true,
      ariaDescribedBy: ["footnote-label"]
    },
    children: [{ type: "text", value: String(counter) }]
  };
  state.patch(node3, link3);
  const sup = {
    type: "element",
    tagName: "sup",
    properties: {},
    children: [link3]
  };
  state.patch(node3, sup);
  return state.applyData(node3, sup);
}

// node_modules/.pnpm/mdast-util-to-hast@12.3.0/node_modules/mdast-util-to-hast/lib/handlers/footnote.js
function footnote(state, node3) {
  const footnoteById = state.footnoteById;
  let no = 1;
  while (no in footnoteById)
    no++;
  const identifier = String(no);
  footnoteById[identifier] = {
    type: "footnoteDefinition",
    identifier,
    children: [{ type: "paragraph", children: node3.children }],
    position: node3.position
  };
  return footnoteReference(state, {
    type: "footnoteReference",
    identifier,
    position: node3.position
  });
}

// node_modules/.pnpm/mdast-util-to-hast@12.3.0/node_modules/mdast-util-to-hast/lib/handlers/heading.js
function heading(state, node3) {
  const result = {
    type: "element",
    tagName: "h" + node3.depth,
    properties: {},
    children: state.all(node3)
  };
  state.patch(node3, result);
  return state.applyData(node3, result);
}

// node_modules/.pnpm/mdast-util-to-hast@12.3.0/node_modules/mdast-util-to-hast/lib/handlers/html.js
function html(state, node3) {
  if (state.dangerous) {
    const result = { type: "raw", value: node3.value };
    state.patch(node3, result);
    return state.applyData(node3, result);
  }
  return null;
}

// node_modules/.pnpm/mdast-util-to-hast@12.3.0/node_modules/mdast-util-to-hast/lib/revert.js
function revert(state, node3) {
  const subtype = node3.referenceType;
  let suffix = "]";
  if (subtype === "collapsed") {
    suffix += "[]";
  } else if (subtype === "full") {
    suffix += "[" + (node3.label || node3.identifier) + "]";
  }
  if (node3.type === "imageReference") {
    return { type: "text", value: "![" + node3.alt + suffix };
  }
  const contents = state.all(node3);
  const head = contents[0];
  if (head && head.type === "text") {
    head.value = "[" + head.value;
  } else {
    contents.unshift({ type: "text", value: "[" });
  }
  const tail = contents[contents.length - 1];
  if (tail && tail.type === "text") {
    tail.value += suffix;
  } else {
    contents.push({ type: "text", value: suffix });
  }
  return contents;
}

// node_modules/.pnpm/mdast-util-to-hast@12.3.0/node_modules/mdast-util-to-hast/lib/handlers/image-reference.js
function imageReference(state, node3) {
  const def = state.definition(node3.identifier);
  if (!def) {
    return revert(state, node3);
  }
  const properties = { src: normalizeUri(def.url || ""), alt: node3.alt };
  if (def.title !== null && def.title !== void 0) {
    properties.title = def.title;
  }
  const result = { type: "element", tagName: "img", properties, children: [] };
  state.patch(node3, result);
  return state.applyData(node3, result);
}

// node_modules/.pnpm/mdast-util-to-hast@12.3.0/node_modules/mdast-util-to-hast/lib/handlers/image.js
function image(state, node3) {
  const properties = { src: normalizeUri(node3.url) };
  if (node3.alt !== null && node3.alt !== void 0) {
    properties.alt = node3.alt;
  }
  if (node3.title !== null && node3.title !== void 0) {
    properties.title = node3.title;
  }
  const result = { type: "element", tagName: "img", properties, children: [] };
  state.patch(node3, result);
  return state.applyData(node3, result);
}

// node_modules/.pnpm/mdast-util-to-hast@12.3.0/node_modules/mdast-util-to-hast/lib/handlers/inline-code.js
function inlineCode(state, node3) {
  const text6 = { type: "text", value: node3.value.replace(/\r?\n|\r/g, " ") };
  state.patch(node3, text6);
  const result = {
    type: "element",
    tagName: "code",
    properties: {},
    children: [text6]
  };
  state.patch(node3, result);
  return state.applyData(node3, result);
}

// node_modules/.pnpm/mdast-util-to-hast@12.3.0/node_modules/mdast-util-to-hast/lib/handlers/link-reference.js
function linkReference(state, node3) {
  const def = state.definition(node3.identifier);
  if (!def) {
    return revert(state, node3);
  }
  const properties = { href: normalizeUri(def.url || "") };
  if (def.title !== null && def.title !== void 0) {
    properties.title = def.title;
  }
  const result = {
    type: "element",
    tagName: "a",
    properties,
    children: state.all(node3)
  };
  state.patch(node3, result);
  return state.applyData(node3, result);
}

// node_modules/.pnpm/mdast-util-to-hast@12.3.0/node_modules/mdast-util-to-hast/lib/handlers/link.js
function link(state, node3) {
  const properties = { href: normalizeUri(node3.url) };
  if (node3.title !== null && node3.title !== void 0) {
    properties.title = node3.title;
  }
  const result = {
    type: "element",
    tagName: "a",
    properties,
    children: state.all(node3)
  };
  state.patch(node3, result);
  return state.applyData(node3, result);
}

// node_modules/.pnpm/mdast-util-to-hast@12.3.0/node_modules/mdast-util-to-hast/lib/handlers/list-item.js
function listItem(state, node3, parent) {
  const results = state.all(node3);
  const loose = parent ? listLoose(parent) : listItemLoose(node3);
  const properties = {};
  const children = [];
  if (typeof node3.checked === "boolean") {
    const head = results[0];
    let paragraph3;
    if (head && head.type === "element" && head.tagName === "p") {
      paragraph3 = head;
    } else {
      paragraph3 = { type: "element", tagName: "p", properties: {}, children: [] };
      results.unshift(paragraph3);
    }
    if (paragraph3.children.length > 0) {
      paragraph3.children.unshift({ type: "text", value: " " });
    }
    paragraph3.children.unshift({
      type: "element",
      tagName: "input",
      properties: { type: "checkbox", checked: node3.checked, disabled: true },
      children: []
    });
    properties.className = ["task-list-item"];
  }
  let index2 = -1;
  while (++index2 < results.length) {
    const child = results[index2];
    if (loose || index2 !== 0 || child.type !== "element" || child.tagName !== "p") {
      children.push({ type: "text", value: "\n" });
    }
    if (child.type === "element" && child.tagName === "p" && !loose) {
      children.push(...child.children);
    } else {
      children.push(child);
    }
  }
  const tail = results[results.length - 1];
  if (tail && (loose || tail.type !== "element" || tail.tagName !== "p")) {
    children.push({ type: "text", value: "\n" });
  }
  const result = { type: "element", tagName: "li", properties, children };
  state.patch(node3, result);
  return state.applyData(node3, result);
}
function listLoose(node3) {
  let loose = false;
  if (node3.type === "list") {
    loose = node3.spread || false;
    const children = node3.children;
    let index2 = -1;
    while (!loose && ++index2 < children.length) {
      loose = listItemLoose(children[index2]);
    }
  }
  return loose;
}
function listItemLoose(node3) {
  const spread = node3.spread;
  return spread === void 0 || spread === null ? node3.children.length > 1 : spread;
}

// node_modules/.pnpm/mdast-util-to-hast@12.3.0/node_modules/mdast-util-to-hast/lib/handlers/list.js
function list2(state, node3) {
  const properties = {};
  const results = state.all(node3);
  let index2 = -1;
  if (typeof node3.start === "number" && node3.start !== 1) {
    properties.start = node3.start;
  }
  while (++index2 < results.length) {
    const child = results[index2];
    if (child.type === "element" && child.tagName === "li" && child.properties && Array.isArray(child.properties.className) && child.properties.className.includes("task-list-item")) {
      properties.className = ["contains-task-list"];
      break;
    }
  }
  const result = {
    type: "element",
    tagName: node3.ordered ? "ol" : "ul",
    properties,
    children: state.wrap(results, true)
  };
  state.patch(node3, result);
  return state.applyData(node3, result);
}

// node_modules/.pnpm/mdast-util-to-hast@12.3.0/node_modules/mdast-util-to-hast/lib/handlers/paragraph.js
function paragraph(state, node3) {
  const result = {
    type: "element",
    tagName: "p",
    properties: {},
    children: state.all(node3)
  };
  state.patch(node3, result);
  return state.applyData(node3, result);
}

// node_modules/.pnpm/mdast-util-to-hast@12.3.0/node_modules/mdast-util-to-hast/lib/handlers/root.js
function root(state, node3) {
  const result = { type: "root", children: state.wrap(state.all(node3)) };
  state.patch(node3, result);
  return state.applyData(node3, result);
}

// node_modules/.pnpm/mdast-util-to-hast@12.3.0/node_modules/mdast-util-to-hast/lib/handlers/strong.js
function strong(state, node3) {
  const result = {
    type: "element",
    tagName: "strong",
    properties: {},
    children: state.all(node3)
  };
  state.patch(node3, result);
  return state.applyData(node3, result);
}

// node_modules/.pnpm/unist-util-position@4.0.4/node_modules/unist-util-position/lib/index.js
var pointStart = point3("start");
var pointEnd = point3("end");
function position2(node3) {
  return { start: pointStart(node3), end: pointEnd(node3) };
}
function point3(type) {
  return point4;
  function point4(node3) {
    const point5 = node3 && node3.position && node3.position[type] || {};
    return {
      // @ts-expect-error: in practice, null is allowed.
      line: point5.line || null,
      // @ts-expect-error: in practice, null is allowed.
      column: point5.column || null,
      // @ts-expect-error: in practice, null is allowed.
      offset: point5.offset > -1 ? point5.offset : null
    };
  }
}

// node_modules/.pnpm/mdast-util-to-hast@12.3.0/node_modules/mdast-util-to-hast/lib/handlers/table.js
function table(state, node3) {
  const rows = state.all(node3);
  const firstRow = rows.shift();
  const tableContent = [];
  if (firstRow) {
    const head = {
      type: "element",
      tagName: "thead",
      properties: {},
      children: state.wrap([firstRow], true)
    };
    state.patch(node3.children[0], head);
    tableContent.push(head);
  }
  if (rows.length > 0) {
    const body = {
      type: "element",
      tagName: "tbody",
      properties: {},
      children: state.wrap(rows, true)
    };
    const start = pointStart(node3.children[1]);
    const end = pointEnd(node3.children[node3.children.length - 1]);
    if (start.line && end.line)
      body.position = { start, end };
    tableContent.push(body);
  }
  const result = {
    type: "element",
    tagName: "table",
    properties: {},
    children: state.wrap(tableContent, true)
  };
  state.patch(node3, result);
  return state.applyData(node3, result);
}

// node_modules/.pnpm/mdast-util-to-hast@12.3.0/node_modules/mdast-util-to-hast/lib/handlers/table-row.js
function tableRow(state, node3, parent) {
  const siblings = parent ? parent.children : void 0;
  const rowIndex = siblings ? siblings.indexOf(node3) : 1;
  const tagName = rowIndex === 0 ? "th" : "td";
  const align = parent && parent.type === "table" ? parent.align : void 0;
  const length = align ? align.length : node3.children.length;
  let cellIndex = -1;
  const cells = [];
  while (++cellIndex < length) {
    const cell = node3.children[cellIndex];
    const properties = {};
    const alignValue = align ? align[cellIndex] : void 0;
    if (alignValue) {
      properties.align = alignValue;
    }
    let result2 = { type: "element", tagName, properties, children: [] };
    if (cell) {
      result2.children = state.all(cell);
      state.patch(cell, result2);
      result2 = state.applyData(node3, result2);
    }
    cells.push(result2);
  }
  const result = {
    type: "element",
    tagName: "tr",
    properties: {},
    children: state.wrap(cells, true)
  };
  state.patch(node3, result);
  return state.applyData(node3, result);
}

// node_modules/.pnpm/mdast-util-to-hast@12.3.0/node_modules/mdast-util-to-hast/lib/handlers/table-cell.js
function tableCell(state, node3) {
  const result = {
    type: "element",
    tagName: "td",
    // Assume body cell.
    properties: {},
    children: state.all(node3)
  };
  state.patch(node3, result);
  return state.applyData(node3, result);
}

// node_modules/.pnpm/trim-lines@3.0.1/node_modules/trim-lines/index.js
var tab = 9;
var space = 32;
function trimLines(value) {
  const source = String(value);
  const search2 = /\r?\n|\r/g;
  let match = search2.exec(source);
  let last = 0;
  const lines = [];
  while (match) {
    lines.push(
      trimLine(source.slice(last, match.index), last > 0, true),
      match[0]
    );
    last = match.index + match[0].length;
    match = search2.exec(source);
  }
  lines.push(trimLine(source.slice(last), last > 0, false));
  return lines.join("");
}
function trimLine(value, start, end) {
  let startIndex = 0;
  let endIndex = value.length;
  if (start) {
    let code4 = value.codePointAt(startIndex);
    while (code4 === tab || code4 === space) {
      startIndex++;
      code4 = value.codePointAt(startIndex);
    }
  }
  if (end) {
    let code4 = value.codePointAt(endIndex - 1);
    while (code4 === tab || code4 === space) {
      endIndex--;
      code4 = value.codePointAt(endIndex - 1);
    }
  }
  return endIndex > startIndex ? value.slice(startIndex, endIndex) : "";
}

// node_modules/.pnpm/mdast-util-to-hast@12.3.0/node_modules/mdast-util-to-hast/lib/handlers/text.js
function text3(state, node3) {
  const result = { type: "text", value: trimLines(String(node3.value)) };
  state.patch(node3, result);
  return state.applyData(node3, result);
}

// node_modules/.pnpm/mdast-util-to-hast@12.3.0/node_modules/mdast-util-to-hast/lib/handlers/thematic-break.js
function thematicBreak2(state, node3) {
  const result = {
    type: "element",
    tagName: "hr",
    properties: {},
    children: []
  };
  state.patch(node3, result);
  return state.applyData(node3, result);
}

// node_modules/.pnpm/mdast-util-to-hast@12.3.0/node_modules/mdast-util-to-hast/lib/handlers/index.js
var handlers = {
  blockquote,
  break: hardBreak,
  code,
  delete: strikethrough,
  emphasis,
  footnoteReference,
  footnote,
  heading,
  html,
  imageReference,
  image,
  inlineCode,
  linkReference,
  link,
  listItem,
  list: list2,
  paragraph,
  root,
  strong,
  table,
  tableCell,
  tableRow,
  text: text3,
  thematicBreak: thematicBreak2,
  toml: ignore,
  yaml: ignore,
  definition: ignore,
  footnoteDefinition: ignore
};
function ignore() {
  return null;
}

// node_modules/.pnpm/unist-util-is@5.2.1/node_modules/unist-util-is/lib/index.js
var convert = (
  /**
   * @type {(
   *   (<Kind extends Node>(test: PredicateTest<Kind>) => AssertPredicate<Kind>) &
   *   ((test?: Test) => AssertAnything)
   * )}
   */
  /**
   * @param {Test} [test]
   * @returns {AssertAnything}
   */
  function(test) {
    if (test === void 0 || test === null) {
      return ok;
    }
    if (typeof test === "string") {
      return typeFactory(test);
    }
    if (typeof test === "object") {
      return Array.isArray(test) ? anyFactory(test) : propsFactory(test);
    }
    if (typeof test === "function") {
      return castFactory(test);
    }
    throw new Error("Expected function, string, or object as test");
  }
);
function anyFactory(tests) {
  const checks2 = [];
  let index2 = -1;
  while (++index2 < tests.length) {
    checks2[index2] = convert(tests[index2]);
  }
  return castFactory(any);
  function any(...parameters) {
    let index3 = -1;
    while (++index3 < checks2.length) {
      if (checks2[index3].call(this, ...parameters))
        return true;
    }
    return false;
  }
}
function propsFactory(check) {
  return castFactory(all4);
  function all4(node3) {
    let key;
    for (key in check) {
      if (node3[key] !== check[key])
        return false;
    }
    return true;
  }
}
function typeFactory(check) {
  return castFactory(type);
  function type(node3) {
    return node3 && node3.type === check;
  }
}
function castFactory(check) {
  return assertion;
  function assertion(node3, ...parameters) {
    return Boolean(
      node3 && typeof node3 === "object" && "type" in node3 && // @ts-expect-error: fine.
      Boolean(check.call(this, node3, ...parameters))
    );
  }
}
function ok() {
  return true;
}

// node_modules/.pnpm/unist-util-visit-parents@5.1.3/node_modules/unist-util-visit-parents/lib/color.browser.js
function color(d) {
  return d;
}

// node_modules/.pnpm/unist-util-visit-parents@5.1.3/node_modules/unist-util-visit-parents/lib/index.js
var CONTINUE = true;
var EXIT = false;
var SKIP = "skip";
var visitParents = (
  /**
   * @type {(
   *   (<Tree extends Node, Check extends Test>(tree: Tree, test: Check, visitor: BuildVisitor<Tree, Check>, reverse?: boolean | null | undefined) => void) &
   *   (<Tree extends Node>(tree: Tree, visitor: BuildVisitor<Tree>, reverse?: boolean | null | undefined) => void)
   * )}
   */
  /**
   * @param {Node} tree
   * @param {Test} test
   * @param {Visitor<Node>} visitor
   * @param {boolean | null | undefined} [reverse]
   * @returns {void}
   */
  function(tree, test, visitor, reverse) {
    if (typeof test === "function" && typeof visitor !== "function") {
      reverse = visitor;
      visitor = test;
      test = null;
    }
    const is3 = convert(test);
    const step = reverse ? -1 : 1;
    factory(tree, void 0, [])();
    function factory(node3, index2, parents) {
      const value = node3 && typeof node3 === "object" ? node3 : {};
      if (typeof value.type === "string") {
        const name = (
          // `hast`
          typeof value.tagName === "string" ? value.tagName : (
            // `xast`
            typeof value.name === "string" ? value.name : void 0
          )
        );
        Object.defineProperty(visit3, "name", {
          value: "node (" + color(node3.type + (name ? "<" + name + ">" : "")) + ")"
        });
      }
      return visit3;
      function visit3() {
        let result = [];
        let subresult;
        let offset;
        let grandparents;
        if (!test || is3(node3, index2, parents[parents.length - 1] || null)) {
          result = toResult(visitor(node3, parents));
          if (result[0] === EXIT) {
            return result;
          }
        }
        if (node3.children && result[0] !== SKIP) {
          offset = (reverse ? node3.children.length : -1) + step;
          grandparents = parents.concat(node3);
          while (offset > -1 && offset < node3.children.length) {
            subresult = factory(node3.children[offset], offset, grandparents)();
            if (subresult[0] === EXIT) {
              return subresult;
            }
            offset = typeof subresult[1] === "number" ? subresult[1] : offset + step;
          }
        }
        return result;
      }
    }
  }
);
function toResult(value) {
  if (Array.isArray(value)) {
    return value;
  }
  if (typeof value === "number") {
    return [CONTINUE, value];
  }
  return [value];
}

// node_modules/.pnpm/unist-util-visit@4.1.2/node_modules/unist-util-visit/lib/index.js
var visit = (
  /**
   * @type {(
   *   (<Tree extends Node, Check extends Test>(tree: Tree, test: Check, visitor: BuildVisitor<Tree, Check>, reverse?: boolean | null | undefined) => void) &
   *   (<Tree extends Node>(tree: Tree, visitor: BuildVisitor<Tree>, reverse?: boolean | null | undefined) => void)
   * )}
   */
  /**
   * @param {Node} tree
   * @param {Test} test
   * @param {Visitor} visitor
   * @param {boolean | null | undefined} [reverse]
   * @returns {void}
   */
  function(tree, test, visitor, reverse) {
    if (typeof test === "function" && typeof visitor !== "function") {
      reverse = visitor;
      visitor = test;
      test = null;
    }
    visitParents(tree, test, overload, reverse);
    function overload(node3, parents) {
      const parent = parents[parents.length - 1];
      return visitor(
        node3,
        parent ? parent.children.indexOf(node3) : null,
        parent
      );
    }
  }
);

// node_modules/.pnpm/unist-util-generated@2.0.1/node_modules/unist-util-generated/lib/index.js
function generated(node3) {
  return !node3 || !node3.position || !node3.position.start || !node3.position.start.line || !node3.position.start.column || !node3.position.end || !node3.position.end.line || !node3.position.end.column;
}

// node_modules/.pnpm/mdast-util-definitions@5.1.2/node_modules/mdast-util-definitions/lib/index.js
var own3 = {}.hasOwnProperty;
function definitions(tree) {
  const cache = /* @__PURE__ */ Object.create(null);
  if (!tree || !tree.type) {
    throw new Error("mdast-util-definitions expected node");
  }
  visit(tree, "definition", (definition4) => {
    const id = clean(definition4.identifier);
    if (id && !own3.call(cache, id)) {
      cache[id] = definition4;
    }
  });
  return definition3;
  function definition3(identifier) {
    const id = clean(identifier);
    return id && own3.call(cache, id) ? cache[id] : null;
  }
}
function clean(value) {
  return String(value || "").toUpperCase();
}

// node_modules/.pnpm/mdast-util-to-hast@12.3.0/node_modules/mdast-util-to-hast/lib/state.js
var own4 = {}.hasOwnProperty;
function createState(tree, options) {
  const settings = options || {};
  const dangerous = settings.allowDangerousHtml || false;
  const footnoteById = {};
  state.dangerous = dangerous;
  state.clobberPrefix = settings.clobberPrefix === void 0 || settings.clobberPrefix === null ? "user-content-" : settings.clobberPrefix;
  state.footnoteLabel = settings.footnoteLabel || "Footnotes";
  state.footnoteLabelTagName = settings.footnoteLabelTagName || "h2";
  state.footnoteLabelProperties = settings.footnoteLabelProperties || {
    className: ["sr-only"]
  };
  state.footnoteBackLabel = settings.footnoteBackLabel || "Back to content";
  state.unknownHandler = settings.unknownHandler;
  state.passThrough = settings.passThrough;
  state.handlers = { ...handlers, ...settings.handlers };
  state.definition = definitions(tree);
  state.footnoteById = footnoteById;
  state.footnoteOrder = [];
  state.footnoteCounts = {};
  state.patch = patch;
  state.applyData = applyData;
  state.one = oneBound;
  state.all = allBound;
  state.wrap = wrap2;
  state.augment = augment;
  visit(tree, "footnoteDefinition", (definition3) => {
    const id = String(definition3.identifier).toUpperCase();
    if (!own4.call(footnoteById, id)) {
      footnoteById[id] = definition3;
    }
  });
  return state;
  function augment(left, right) {
    if (left && "data" in left && left.data) {
      const data = left.data;
      if (data.hName) {
        if (right.type !== "element") {
          right = {
            type: "element",
            tagName: "",
            properties: {},
            children: []
          };
        }
        right.tagName = data.hName;
      }
      if (right.type === "element" && data.hProperties) {
        right.properties = { ...right.properties, ...data.hProperties };
      }
      if ("children" in right && right.children && data.hChildren) {
        right.children = data.hChildren;
      }
    }
    if (left) {
      const ctx = "type" in left ? left : { position: left };
      if (!generated(ctx)) {
        right.position = { start: pointStart(ctx), end: pointEnd(ctx) };
      }
    }
    return right;
  }
  function state(node3, tagName, props, children) {
    if (Array.isArray(props)) {
      children = props;
      props = {};
    }
    return augment(node3, {
      type: "element",
      tagName,
      properties: props || {},
      children: children || []
    });
  }
  function oneBound(node3, parent) {
    return one2(state, node3, parent);
  }
  function allBound(parent) {
    return all2(state, parent);
  }
}
function patch(from, to) {
  if (from.position)
    to.position = position2(from);
}
function applyData(from, to) {
  let result = to;
  if (from && from.data) {
    const hName = from.data.hName;
    const hChildren = from.data.hChildren;
    const hProperties = from.data.hProperties;
    if (typeof hName === "string") {
      if (result.type === "element") {
        result.tagName = hName;
      } else {
        result = {
          type: "element",
          tagName: hName,
          properties: {},
          children: []
        };
      }
    }
    if (result.type === "element" && hProperties) {
      result.properties = { ...result.properties, ...hProperties };
    }
    if ("children" in result && result.children && hChildren !== null && hChildren !== void 0) {
      result.children = hChildren;
    }
  }
  return result;
}
function one2(state, node3, parent) {
  const type = node3 && node3.type;
  if (!type) {
    throw new Error("Expected node, got `" + node3 + "`");
  }
  if (own4.call(state.handlers, type)) {
    return state.handlers[type](state, node3, parent);
  }
  if (state.passThrough && state.passThrough.includes(type)) {
    return "children" in node3 ? { ...node3, children: all2(state, node3) } : node3;
  }
  if (state.unknownHandler) {
    return state.unknownHandler(state, node3, parent);
  }
  return defaultUnknownHandler(state, node3);
}
function all2(state, parent) {
  const values = [];
  if ("children" in parent) {
    const nodes = parent.children;
    let index2 = -1;
    while (++index2 < nodes.length) {
      const result = one2(state, nodes[index2], parent);
      if (result) {
        if (index2 && nodes[index2 - 1].type === "break") {
          if (!Array.isArray(result) && result.type === "text") {
            result.value = result.value.replace(/^\s+/, "");
          }
          if (!Array.isArray(result) && result.type === "element") {
            const head = result.children[0];
            if (head && head.type === "text") {
              head.value = head.value.replace(/^\s+/, "");
            }
          }
        }
        if (Array.isArray(result)) {
          values.push(...result);
        } else {
          values.push(result);
        }
      }
    }
  }
  return values;
}
function defaultUnknownHandler(state, node3) {
  const data = node3.data || {};
  const result = "value" in node3 && !(own4.call(data, "hProperties") || own4.call(data, "hChildren")) ? { type: "text", value: node3.value } : {
    type: "element",
    tagName: "div",
    properties: {},
    children: all2(state, node3)
  };
  state.patch(node3, result);
  return state.applyData(node3, result);
}
function wrap2(nodes, loose) {
  const result = [];
  let index2 = -1;
  if (loose) {
    result.push({ type: "text", value: "\n" });
  }
  while (++index2 < nodes.length) {
    if (index2)
      result.push({ type: "text", value: "\n" });
    result.push(nodes[index2]);
  }
  if (loose && nodes.length > 0) {
    result.push({ type: "text", value: "\n" });
  }
  return result;
}

// node_modules/.pnpm/mdast-util-to-hast@12.3.0/node_modules/mdast-util-to-hast/lib/footer.js
function footer(state) {
  const listItems = [];
  let index2 = -1;
  while (++index2 < state.footnoteOrder.length) {
    const def = state.footnoteById[state.footnoteOrder[index2]];
    if (!def) {
      continue;
    }
    const content3 = state.all(def);
    const id = String(def.identifier).toUpperCase();
    const safeId = normalizeUri(id.toLowerCase());
    let referenceIndex = 0;
    const backReferences = [];
    while (++referenceIndex <= state.footnoteCounts[id]) {
      const backReference = {
        type: "element",
        tagName: "a",
        properties: {
          href: "#" + state.clobberPrefix + "fnref-" + safeId + (referenceIndex > 1 ? "-" + referenceIndex : ""),
          dataFootnoteBackref: true,
          className: ["data-footnote-backref"],
          ariaLabel: state.footnoteBackLabel
        },
        children: [{ type: "text", value: "\u21A9" }]
      };
      if (referenceIndex > 1) {
        backReference.children.push({
          type: "element",
          tagName: "sup",
          children: [{ type: "text", value: String(referenceIndex) }]
        });
      }
      if (backReferences.length > 0) {
        backReferences.push({ type: "text", value: " " });
      }
      backReferences.push(backReference);
    }
    const tail = content3[content3.length - 1];
    if (tail && tail.type === "element" && tail.tagName === "p") {
      const tailTail = tail.children[tail.children.length - 1];
      if (tailTail && tailTail.type === "text") {
        tailTail.value += " ";
      } else {
        tail.children.push({ type: "text", value: " " });
      }
      tail.children.push(...backReferences);
    } else {
      content3.push(...backReferences);
    }
    const listItem3 = {
      type: "element",
      tagName: "li",
      properties: { id: state.clobberPrefix + "fn-" + safeId },
      children: state.wrap(content3, true)
    };
    state.patch(def, listItem3);
    listItems.push(listItem3);
  }
  if (listItems.length === 0) {
    return;
  }
  return {
    type: "element",
    tagName: "section",
    properties: { dataFootnotes: true, className: ["footnotes"] },
    children: [
      {
        type: "element",
        tagName: state.footnoteLabelTagName,
        properties: {
          // To do: use structured clone.
          ...JSON.parse(JSON.stringify(state.footnoteLabelProperties)),
          id: "footnote-label"
        },
        children: [{ type: "text", value: state.footnoteLabel }]
      },
      { type: "text", value: "\n" },
      {
        type: "element",
        tagName: "ol",
        properties: {},
        children: state.wrap(listItems, true)
      },
      { type: "text", value: "\n" }
    ]
  };
}

// node_modules/.pnpm/mdast-util-to-hast@12.3.0/node_modules/mdast-util-to-hast/lib/index.js
function toHast(tree, options) {
  const state = createState(tree, options);
  const node3 = state.one(tree, null);
  const foot = footer(state);
  if (foot) {
    node3.children.push({ type: "text", value: "\n" }, foot);
  }
  return Array.isArray(node3) ? { type: "root", children: node3 } : node3;
}

// node_modules/.pnpm/remark-rehype@10.1.0/node_modules/remark-rehype/lib/index.js
var remarkRehype = (
  /** @type {(import('unified').Plugin<[Processor, Options?]|[null|undefined, Options?]|[Options]|[], MdastRoot>)} */
  function(destination, options) {
    return destination && "run" in destination ? bridge(destination, options) : mutate(destination || options);
  }
);
var lib_default = remarkRehype;
function bridge(destination, options) {
  return (node3, file, next) => {
    destination.run(toHast(node3, options), file, (error) => {
      next(error);
    });
  };
}
function mutate(options) {
  return (node3) => toHast(node3, options);
}

// node_modules/.pnpm/react-markdown@8.0.7_@types+react@18.3.18_react@18.3.1/node_modules/react-markdown/lib/react-markdown.js
var import_prop_types = __toESM(require_prop_types(), 1);

// node_modules/.pnpm/property-information@6.5.0/node_modules/property-information/lib/util/schema.js
var Schema = class {
  /**
   * @constructor
   * @param {Properties} property
   * @param {Normal} normal
   * @param {string} [space]
   */
  constructor(property, normal, space2) {
    this.property = property;
    this.normal = normal;
    if (space2) {
      this.space = space2;
    }
  }
};
Schema.prototype.property = {};
Schema.prototype.normal = {};
Schema.prototype.space = null;

// node_modules/.pnpm/property-information@6.5.0/node_modules/property-information/lib/util/merge.js
function merge(definitions2, space2) {
  const property = {};
  const normal = {};
  let index2 = -1;
  while (++index2 < definitions2.length) {
    Object.assign(property, definitions2[index2].property);
    Object.assign(normal, definitions2[index2].normal);
  }
  return new Schema(property, normal, space2);
}

// node_modules/.pnpm/property-information@6.5.0/node_modules/property-information/lib/normalize.js
function normalize2(value) {
  return value.toLowerCase();
}

// node_modules/.pnpm/property-information@6.5.0/node_modules/property-information/lib/util/info.js
var Info = class {
  /**
   * @constructor
   * @param {string} property
   * @param {string} attribute
   */
  constructor(property, attribute) {
    this.property = property;
    this.attribute = attribute;
  }
};
Info.prototype.space = null;
Info.prototype.boolean = false;
Info.prototype.booleanish = false;
Info.prototype.overloadedBoolean = false;
Info.prototype.number = false;
Info.prototype.commaSeparated = false;
Info.prototype.spaceSeparated = false;
Info.prototype.commaOrSpaceSeparated = false;
Info.prototype.mustUseProperty = false;
Info.prototype.defined = false;

// node_modules/.pnpm/property-information@6.5.0/node_modules/property-information/lib/util/types.js
var types_exports = {};
__export(types_exports, {
  boolean: () => boolean,
  booleanish: () => booleanish,
  commaOrSpaceSeparated: () => commaOrSpaceSeparated,
  commaSeparated: () => commaSeparated,
  number: () => number,
  overloadedBoolean: () => overloadedBoolean,
  spaceSeparated: () => spaceSeparated
});
var powers = 0;
var boolean = increment();
var booleanish = increment();
var overloadedBoolean = increment();
var number = increment();
var spaceSeparated = increment();
var commaSeparated = increment();
var commaOrSpaceSeparated = increment();
function increment() {
  return 2 ** ++powers;
}

// node_modules/.pnpm/property-information@6.5.0/node_modules/property-information/lib/util/defined-info.js
var checks = Object.keys(types_exports);
var DefinedInfo = class extends Info {
  /**
   * @constructor
   * @param {string} property
   * @param {string} attribute
   * @param {number|null} [mask]
   * @param {string} [space]
   */
  constructor(property, attribute, mask, space2) {
    let index2 = -1;
    super(property, attribute);
    mark(this, "space", space2);
    if (typeof mask === "number") {
      while (++index2 < checks.length) {
        const check = checks[index2];
        mark(this, checks[index2], (mask & types_exports[check]) === types_exports[check]);
      }
    }
  }
};
DefinedInfo.prototype.defined = true;
function mark(values, key, value) {
  if (value) {
    values[key] = value;
  }
}

// node_modules/.pnpm/property-information@6.5.0/node_modules/property-information/lib/util/create.js
var own5 = {}.hasOwnProperty;
function create(definition3) {
  const property = {};
  const normal = {};
  let prop;
  for (prop in definition3.properties) {
    if (own5.call(definition3.properties, prop)) {
      const value = definition3.properties[prop];
      const info = new DefinedInfo(
        prop,
        definition3.transform(definition3.attributes || {}, prop),
        value,
        definition3.space
      );
      if (definition3.mustUseProperty && definition3.mustUseProperty.includes(prop)) {
        info.mustUseProperty = true;
      }
      property[prop] = info;
      normal[normalize2(prop)] = prop;
      normal[normalize2(info.attribute)] = prop;
    }
  }
  return new Schema(property, normal, definition3.space);
}

// node_modules/.pnpm/property-information@6.5.0/node_modules/property-information/lib/xlink.js
var xlink = create({
  space: "xlink",
  transform(_, prop) {
    return "xlink:" + prop.slice(5).toLowerCase();
  },
  properties: {
    xLinkActuate: null,
    xLinkArcRole: null,
    xLinkHref: null,
    xLinkRole: null,
    xLinkShow: null,
    xLinkTitle: null,
    xLinkType: null
  }
});

// node_modules/.pnpm/property-information@6.5.0/node_modules/property-information/lib/xml.js
var xml = create({
  space: "xml",
  transform(_, prop) {
    return "xml:" + prop.slice(3).toLowerCase();
  },
  properties: { xmlLang: null, xmlBase: null, xmlSpace: null }
});

// node_modules/.pnpm/property-information@6.5.0/node_modules/property-information/lib/util/case-sensitive-transform.js
function caseSensitiveTransform(attributes, attribute) {
  return attribute in attributes ? attributes[attribute] : attribute;
}

// node_modules/.pnpm/property-information@6.5.0/node_modules/property-information/lib/util/case-insensitive-transform.js
function caseInsensitiveTransform(attributes, property) {
  return caseSensitiveTransform(attributes, property.toLowerCase());
}

// node_modules/.pnpm/property-information@6.5.0/node_modules/property-information/lib/xmlns.js
var xmlns = create({
  space: "xmlns",
  attributes: { xmlnsxlink: "xmlns:xlink" },
  transform: caseInsensitiveTransform,
  properties: { xmlns: null, xmlnsXLink: null }
});

// node_modules/.pnpm/property-information@6.5.0/node_modules/property-information/lib/aria.js
var aria = create({
  transform(_, prop) {
    return prop === "role" ? prop : "aria-" + prop.slice(4).toLowerCase();
  },
  properties: {
    ariaActiveDescendant: null,
    ariaAtomic: booleanish,
    ariaAutoComplete: null,
    ariaBusy: booleanish,
    ariaChecked: booleanish,
    ariaColCount: number,
    ariaColIndex: number,
    ariaColSpan: number,
    ariaControls: spaceSeparated,
    ariaCurrent: null,
    ariaDescribedBy: spaceSeparated,
    ariaDetails: null,
    ariaDisabled: booleanish,
    ariaDropEffect: spaceSeparated,
    ariaErrorMessage: null,
    ariaExpanded: booleanish,
    ariaFlowTo: spaceSeparated,
    ariaGrabbed: booleanish,
    ariaHasPopup: null,
    ariaHidden: booleanish,
    ariaInvalid: null,
    ariaKeyShortcuts: null,
    ariaLabel: null,
    ariaLabelledBy: spaceSeparated,
    ariaLevel: number,
    ariaLive: null,
    ariaModal: booleanish,
    ariaMultiLine: booleanish,
    ariaMultiSelectable: booleanish,
    ariaOrientation: null,
    ariaOwns: spaceSeparated,
    ariaPlaceholder: null,
    ariaPosInSet: number,
    ariaPressed: booleanish,
    ariaReadOnly: booleanish,
    ariaRelevant: null,
    ariaRequired: booleanish,
    ariaRoleDescription: spaceSeparated,
    ariaRowCount: number,
    ariaRowIndex: number,
    ariaRowSpan: number,
    ariaSelected: booleanish,
    ariaSetSize: number,
    ariaSort: null,
    ariaValueMax: number,
    ariaValueMin: number,
    ariaValueNow: number,
    ariaValueText: null,
    role: null
  }
});

// node_modules/.pnpm/property-information@6.5.0/node_modules/property-information/lib/html.js
var html2 = create({
  space: "html",
  attributes: {
    acceptcharset: "accept-charset",
    classname: "class",
    htmlfor: "for",
    httpequiv: "http-equiv"
  },
  transform: caseInsensitiveTransform,
  mustUseProperty: ["checked", "multiple", "muted", "selected"],
  properties: {
    // Standard Properties.
    abbr: null,
    accept: commaSeparated,
    acceptCharset: spaceSeparated,
    accessKey: spaceSeparated,
    action: null,
    allow: null,
    allowFullScreen: boolean,
    allowPaymentRequest: boolean,
    allowUserMedia: boolean,
    alt: null,
    as: null,
    async: boolean,
    autoCapitalize: null,
    autoComplete: spaceSeparated,
    autoFocus: boolean,
    autoPlay: boolean,
    blocking: spaceSeparated,
    capture: null,
    charSet: null,
    checked: boolean,
    cite: null,
    className: spaceSeparated,
    cols: number,
    colSpan: null,
    content: null,
    contentEditable: booleanish,
    controls: boolean,
    controlsList: spaceSeparated,
    coords: number | commaSeparated,
    crossOrigin: null,
    data: null,
    dateTime: null,
    decoding: null,
    default: boolean,
    defer: boolean,
    dir: null,
    dirName: null,
    disabled: boolean,
    download: overloadedBoolean,
    draggable: booleanish,
    encType: null,
    enterKeyHint: null,
    fetchPriority: null,
    form: null,
    formAction: null,
    formEncType: null,
    formMethod: null,
    formNoValidate: boolean,
    formTarget: null,
    headers: spaceSeparated,
    height: number,
    hidden: boolean,
    high: number,
    href: null,
    hrefLang: null,
    htmlFor: spaceSeparated,
    httpEquiv: spaceSeparated,
    id: null,
    imageSizes: null,
    imageSrcSet: null,
    inert: boolean,
    inputMode: null,
    integrity: null,
    is: null,
    isMap: boolean,
    itemId: null,
    itemProp: spaceSeparated,
    itemRef: spaceSeparated,
    itemScope: boolean,
    itemType: spaceSeparated,
    kind: null,
    label: null,
    lang: null,
    language: null,
    list: null,
    loading: null,
    loop: boolean,
    low: number,
    manifest: null,
    max: null,
    maxLength: number,
    media: null,
    method: null,
    min: null,
    minLength: number,
    multiple: boolean,
    muted: boolean,
    name: null,
    nonce: null,
    noModule: boolean,
    noValidate: boolean,
    onAbort: null,
    onAfterPrint: null,
    onAuxClick: null,
    onBeforeMatch: null,
    onBeforePrint: null,
    onBeforeToggle: null,
    onBeforeUnload: null,
    onBlur: null,
    onCancel: null,
    onCanPlay: null,
    onCanPlayThrough: null,
    onChange: null,
    onClick: null,
    onClose: null,
    onContextLost: null,
    onContextMenu: null,
    onContextRestored: null,
    onCopy: null,
    onCueChange: null,
    onCut: null,
    onDblClick: null,
    onDrag: null,
    onDragEnd: null,
    onDragEnter: null,
    onDragExit: null,
    onDragLeave: null,
    onDragOver: null,
    onDragStart: null,
    onDrop: null,
    onDurationChange: null,
    onEmptied: null,
    onEnded: null,
    onError: null,
    onFocus: null,
    onFormData: null,
    onHashChange: null,
    onInput: null,
    onInvalid: null,
    onKeyDown: null,
    onKeyPress: null,
    onKeyUp: null,
    onLanguageChange: null,
    onLoad: null,
    onLoadedData: null,
    onLoadedMetadata: null,
    onLoadEnd: null,
    onLoadStart: null,
    onMessage: null,
    onMessageError: null,
    onMouseDown: null,
    onMouseEnter: null,
    onMouseLeave: null,
    onMouseMove: null,
    onMouseOut: null,
    onMouseOver: null,
    onMouseUp: null,
    onOffline: null,
    onOnline: null,
    onPageHide: null,
    onPageShow: null,
    onPaste: null,
    onPause: null,
    onPlay: null,
    onPlaying: null,
    onPopState: null,
    onProgress: null,
    onRateChange: null,
    onRejectionHandled: null,
    onReset: null,
    onResize: null,
    onScroll: null,
    onScrollEnd: null,
    onSecurityPolicyViolation: null,
    onSeeked: null,
    onSeeking: null,
    onSelect: null,
    onSlotChange: null,
    onStalled: null,
    onStorage: null,
    onSubmit: null,
    onSuspend: null,
    onTimeUpdate: null,
    onToggle: null,
    onUnhandledRejection: null,
    onUnload: null,
    onVolumeChange: null,
    onWaiting: null,
    onWheel: null,
    open: boolean,
    optimum: number,
    pattern: null,
    ping: spaceSeparated,
    placeholder: null,
    playsInline: boolean,
    popover: null,
    popoverTarget: null,
    popoverTargetAction: null,
    poster: null,
    preload: null,
    readOnly: boolean,
    referrerPolicy: null,
    rel: spaceSeparated,
    required: boolean,
    reversed: boolean,
    rows: number,
    rowSpan: number,
    sandbox: spaceSeparated,
    scope: null,
    scoped: boolean,
    seamless: boolean,
    selected: boolean,
    shadowRootClonable: boolean,
    shadowRootDelegatesFocus: boolean,
    shadowRootMode: null,
    shape: null,
    size: number,
    sizes: null,
    slot: null,
    span: number,
    spellCheck: booleanish,
    src: null,
    srcDoc: null,
    srcLang: null,
    srcSet: null,
    start: number,
    step: null,
    style: null,
    tabIndex: number,
    target: null,
    title: null,
    translate: null,
    type: null,
    typeMustMatch: boolean,
    useMap: null,
    value: booleanish,
    width: number,
    wrap: null,
    writingSuggestions: null,
    // Legacy.
    // See: https://html.spec.whatwg.org/#other-elements,-attributes-and-apis
    align: null,
    // Several. Use CSS `text-align` instead,
    aLink: null,
    // `<body>`. Use CSS `a:active {color}` instead
    archive: spaceSeparated,
    // `<object>`. List of URIs to archives
    axis: null,
    // `<td>` and `<th>`. Use `scope` on `<th>`
    background: null,
    // `<body>`. Use CSS `background-image` instead
    bgColor: null,
    // `<body>` and table elements. Use CSS `background-color` instead
    border: number,
    // `<table>`. Use CSS `border-width` instead,
    borderColor: null,
    // `<table>`. Use CSS `border-color` instead,
    bottomMargin: number,
    // `<body>`
    cellPadding: null,
    // `<table>`
    cellSpacing: null,
    // `<table>`
    char: null,
    // Several table elements. When `align=char`, sets the character to align on
    charOff: null,
    // Several table elements. When `char`, offsets the alignment
    classId: null,
    // `<object>`
    clear: null,
    // `<br>`. Use CSS `clear` instead
    code: null,
    // `<object>`
    codeBase: null,
    // `<object>`
    codeType: null,
    // `<object>`
    color: null,
    // `<font>` and `<hr>`. Use CSS instead
    compact: boolean,
    // Lists. Use CSS to reduce space between items instead
    declare: boolean,
    // `<object>`
    event: null,
    // `<script>`
    face: null,
    // `<font>`. Use CSS instead
    frame: null,
    // `<table>`
    frameBorder: null,
    // `<iframe>`. Use CSS `border` instead
    hSpace: number,
    // `<img>` and `<object>`
    leftMargin: number,
    // `<body>`
    link: null,
    // `<body>`. Use CSS `a:link {color: *}` instead
    longDesc: null,
    // `<frame>`, `<iframe>`, and `<img>`. Use an `<a>`
    lowSrc: null,
    // `<img>`. Use a `<picture>`
    marginHeight: number,
    // `<body>`
    marginWidth: number,
    // `<body>`
    noResize: boolean,
    // `<frame>`
    noHref: boolean,
    // `<area>`. Use no href instead of an explicit `nohref`
    noShade: boolean,
    // `<hr>`. Use background-color and height instead of borders
    noWrap: boolean,
    // `<td>` and `<th>`
    object: null,
    // `<applet>`
    profile: null,
    // `<head>`
    prompt: null,
    // `<isindex>`
    rev: null,
    // `<link>`
    rightMargin: number,
    // `<body>`
    rules: null,
    // `<table>`
    scheme: null,
    // `<meta>`
    scrolling: booleanish,
    // `<frame>`. Use overflow in the child context
    standby: null,
    // `<object>`
    summary: null,
    // `<table>`
    text: null,
    // `<body>`. Use CSS `color` instead
    topMargin: number,
    // `<body>`
    valueType: null,
    // `<param>`
    version: null,
    // `<html>`. Use a doctype.
    vAlign: null,
    // Several. Use CSS `vertical-align` instead
    vLink: null,
    // `<body>`. Use CSS `a:visited {color}` instead
    vSpace: number,
    // `<img>` and `<object>`
    // Non-standard Properties.
    allowTransparency: null,
    autoCorrect: null,
    autoSave: null,
    disablePictureInPicture: boolean,
    disableRemotePlayback: boolean,
    prefix: null,
    property: null,
    results: number,
    security: null,
    unselectable: null
  }
});

// node_modules/.pnpm/property-information@6.5.0/node_modules/property-information/lib/svg.js
var svg = create({
  space: "svg",
  attributes: {
    accentHeight: "accent-height",
    alignmentBaseline: "alignment-baseline",
    arabicForm: "arabic-form",
    baselineShift: "baseline-shift",
    capHeight: "cap-height",
    className: "class",
    clipPath: "clip-path",
    clipRule: "clip-rule",
    colorInterpolation: "color-interpolation",
    colorInterpolationFilters: "color-interpolation-filters",
    colorProfile: "color-profile",
    colorRendering: "color-rendering",
    crossOrigin: "crossorigin",
    dataType: "datatype",
    dominantBaseline: "dominant-baseline",
    enableBackground: "enable-background",
    fillOpacity: "fill-opacity",
    fillRule: "fill-rule",
    floodColor: "flood-color",
    floodOpacity: "flood-opacity",
    fontFamily: "font-family",
    fontSize: "font-size",
    fontSizeAdjust: "font-size-adjust",
    fontStretch: "font-stretch",
    fontStyle: "font-style",
    fontVariant: "font-variant",
    fontWeight: "font-weight",
    glyphName: "glyph-name",
    glyphOrientationHorizontal: "glyph-orientation-horizontal",
    glyphOrientationVertical: "glyph-orientation-vertical",
    hrefLang: "hreflang",
    horizAdvX: "horiz-adv-x",
    horizOriginX: "horiz-origin-x",
    horizOriginY: "horiz-origin-y",
    imageRendering: "image-rendering",
    letterSpacing: "letter-spacing",
    lightingColor: "lighting-color",
    markerEnd: "marker-end",
    markerMid: "marker-mid",
    markerStart: "marker-start",
    navDown: "nav-down",
    navDownLeft: "nav-down-left",
    navDownRight: "nav-down-right",
    navLeft: "nav-left",
    navNext: "nav-next",
    navPrev: "nav-prev",
    navRight: "nav-right",
    navUp: "nav-up",
    navUpLeft: "nav-up-left",
    navUpRight: "nav-up-right",
    onAbort: "onabort",
    onActivate: "onactivate",
    onAfterPrint: "onafterprint",
    onBeforePrint: "onbeforeprint",
    onBegin: "onbegin",
    onCancel: "oncancel",
    onCanPlay: "oncanplay",
    onCanPlayThrough: "oncanplaythrough",
    onChange: "onchange",
    onClick: "onclick",
    onClose: "onclose",
    onCopy: "oncopy",
    onCueChange: "oncuechange",
    onCut: "oncut",
    onDblClick: "ondblclick",
    onDrag: "ondrag",
    onDragEnd: "ondragend",
    onDragEnter: "ondragenter",
    onDragExit: "ondragexit",
    onDragLeave: "ondragleave",
    onDragOver: "ondragover",
    onDragStart: "ondragstart",
    onDrop: "ondrop",
    onDurationChange: "ondurationchange",
    onEmptied: "onemptied",
    onEnd: "onend",
    onEnded: "onended",
    onError: "onerror",
    onFocus: "onfocus",
    onFocusIn: "onfocusin",
    onFocusOut: "onfocusout",
    onHashChange: "onhashchange",
    onInput: "oninput",
    onInvalid: "oninvalid",
    onKeyDown: "onkeydown",
    onKeyPress: "onkeypress",
    onKeyUp: "onkeyup",
    onLoad: "onload",
    onLoadedData: "onloadeddata",
    onLoadedMetadata: "onloadedmetadata",
    onLoadStart: "onloadstart",
    onMessage: "onmessage",
    onMouseDown: "onmousedown",
    onMouseEnter: "onmouseenter",
    onMouseLeave: "onmouseleave",
    onMouseMove: "onmousemove",
    onMouseOut: "onmouseout",
    onMouseOver: "onmouseover",
    onMouseUp: "onmouseup",
    onMouseWheel: "onmousewheel",
    onOffline: "onoffline",
    onOnline: "ononline",
    onPageHide: "onpagehide",
    onPageShow: "onpageshow",
    onPaste: "onpaste",
    onPause: "onpause",
    onPlay: "onplay",
    onPlaying: "onplaying",
    onPopState: "onpopstate",
    onProgress: "onprogress",
    onRateChange: "onratechange",
    onRepeat: "onrepeat",
    onReset: "onreset",
    onResize: "onresize",
    onScroll: "onscroll",
    onSeeked: "onseeked",
    onSeeking: "onseeking",
    onSelect: "onselect",
    onShow: "onshow",
    onStalled: "onstalled",
    onStorage: "onstorage",
    onSubmit: "onsubmit",
    onSuspend: "onsuspend",
    onTimeUpdate: "ontimeupdate",
    onToggle: "ontoggle",
    onUnload: "onunload",
    onVolumeChange: "onvolumechange",
    onWaiting: "onwaiting",
    onZoom: "onzoom",
    overlinePosition: "overline-position",
    overlineThickness: "overline-thickness",
    paintOrder: "paint-order",
    panose1: "panose-1",
    pointerEvents: "pointer-events",
    referrerPolicy: "referrerpolicy",
    renderingIntent: "rendering-intent",
    shapeRendering: "shape-rendering",
    stopColor: "stop-color",
    stopOpacity: "stop-opacity",
    strikethroughPosition: "strikethrough-position",
    strikethroughThickness: "strikethrough-thickness",
    strokeDashArray: "stroke-dasharray",
    strokeDashOffset: "stroke-dashoffset",
    strokeLineCap: "stroke-linecap",
    strokeLineJoin: "stroke-linejoin",
    strokeMiterLimit: "stroke-miterlimit",
    strokeOpacity: "stroke-opacity",
    strokeWidth: "stroke-width",
    tabIndex: "tabindex",
    textAnchor: "text-anchor",
    textDecoration: "text-decoration",
    textRendering: "text-rendering",
    transformOrigin: "transform-origin",
    typeOf: "typeof",
    underlinePosition: "underline-position",
    underlineThickness: "underline-thickness",
    unicodeBidi: "unicode-bidi",
    unicodeRange: "unicode-range",
    unitsPerEm: "units-per-em",
    vAlphabetic: "v-alphabetic",
    vHanging: "v-hanging",
    vIdeographic: "v-ideographic",
    vMathematical: "v-mathematical",
    vectorEffect: "vector-effect",
    vertAdvY: "vert-adv-y",
    vertOriginX: "vert-origin-x",
    vertOriginY: "vert-origin-y",
    wordSpacing: "word-spacing",
    writingMode: "writing-mode",
    xHeight: "x-height",
    // These were camelcased in Tiny. Now lowercased in SVG 2
    playbackOrder: "playbackorder",
    timelineBegin: "timelinebegin"
  },
  transform: caseSensitiveTransform,
  properties: {
    about: commaOrSpaceSeparated,
    accentHeight: number,
    accumulate: null,
    additive: null,
    alignmentBaseline: null,
    alphabetic: number,
    amplitude: number,
    arabicForm: null,
    ascent: number,
    attributeName: null,
    attributeType: null,
    azimuth: number,
    bandwidth: null,
    baselineShift: null,
    baseFrequency: null,
    baseProfile: null,
    bbox: null,
    begin: null,
    bias: number,
    by: null,
    calcMode: null,
    capHeight: number,
    className: spaceSeparated,
    clip: null,
    clipPath: null,
    clipPathUnits: null,
    clipRule: null,
    color: null,
    colorInterpolation: null,
    colorInterpolationFilters: null,
    colorProfile: null,
    colorRendering: null,
    content: null,
    contentScriptType: null,
    contentStyleType: null,
    crossOrigin: null,
    cursor: null,
    cx: null,
    cy: null,
    d: null,
    dataType: null,
    defaultAction: null,
    descent: number,
    diffuseConstant: number,
    direction: null,
    display: null,
    dur: null,
    divisor: number,
    dominantBaseline: null,
    download: boolean,
    dx: null,
    dy: null,
    edgeMode: null,
    editable: null,
    elevation: number,
    enableBackground: null,
    end: null,
    event: null,
    exponent: number,
    externalResourcesRequired: null,
    fill: null,
    fillOpacity: number,
    fillRule: null,
    filter: null,
    filterRes: null,
    filterUnits: null,
    floodColor: null,
    floodOpacity: null,
    focusable: null,
    focusHighlight: null,
    fontFamily: null,
    fontSize: null,
    fontSizeAdjust: null,
    fontStretch: null,
    fontStyle: null,
    fontVariant: null,
    fontWeight: null,
    format: null,
    fr: null,
    from: null,
    fx: null,
    fy: null,
    g1: commaSeparated,
    g2: commaSeparated,
    glyphName: commaSeparated,
    glyphOrientationHorizontal: null,
    glyphOrientationVertical: null,
    glyphRef: null,
    gradientTransform: null,
    gradientUnits: null,
    handler: null,
    hanging: number,
    hatchContentUnits: null,
    hatchUnits: null,
    height: null,
    href: null,
    hrefLang: null,
    horizAdvX: number,
    horizOriginX: number,
    horizOriginY: number,
    id: null,
    ideographic: number,
    imageRendering: null,
    initialVisibility: null,
    in: null,
    in2: null,
    intercept: number,
    k: number,
    k1: number,
    k2: number,
    k3: number,
    k4: number,
    kernelMatrix: commaOrSpaceSeparated,
    kernelUnitLength: null,
    keyPoints: null,
    // SEMI_COLON_SEPARATED
    keySplines: null,
    // SEMI_COLON_SEPARATED
    keyTimes: null,
    // SEMI_COLON_SEPARATED
    kerning: null,
    lang: null,
    lengthAdjust: null,
    letterSpacing: null,
    lightingColor: null,
    limitingConeAngle: number,
    local: null,
    markerEnd: null,
    markerMid: null,
    markerStart: null,
    markerHeight: null,
    markerUnits: null,
    markerWidth: null,
    mask: null,
    maskContentUnits: null,
    maskUnits: null,
    mathematical: null,
    max: null,
    media: null,
    mediaCharacterEncoding: null,
    mediaContentEncodings: null,
    mediaSize: number,
    mediaTime: null,
    method: null,
    min: null,
    mode: null,
    name: null,
    navDown: null,
    navDownLeft: null,
    navDownRight: null,
    navLeft: null,
    navNext: null,
    navPrev: null,
    navRight: null,
    navUp: null,
    navUpLeft: null,
    navUpRight: null,
    numOctaves: null,
    observer: null,
    offset: null,
    onAbort: null,
    onActivate: null,
    onAfterPrint: null,
    onBeforePrint: null,
    onBegin: null,
    onCancel: null,
    onCanPlay: null,
    onCanPlayThrough: null,
    onChange: null,
    onClick: null,
    onClose: null,
    onCopy: null,
    onCueChange: null,
    onCut: null,
    onDblClick: null,
    onDrag: null,
    onDragEnd: null,
    onDragEnter: null,
    onDragExit: null,
    onDragLeave: null,
    onDragOver: null,
    onDragStart: null,
    onDrop: null,
    onDurationChange: null,
    onEmptied: null,
    onEnd: null,
    onEnded: null,
    onError: null,
    onFocus: null,
    onFocusIn: null,
    onFocusOut: null,
    onHashChange: null,
    onInput: null,
    onInvalid: null,
    onKeyDown: null,
    onKeyPress: null,
    onKeyUp: null,
    onLoad: null,
    onLoadedData: null,
    onLoadedMetadata: null,
    onLoadStart: null,
    onMessage: null,
    onMouseDown: null,
    onMouseEnter: null,
    onMouseLeave: null,
    onMouseMove: null,
    onMouseOut: null,
    onMouseOver: null,
    onMouseUp: null,
    onMouseWheel: null,
    onOffline: null,
    onOnline: null,
    onPageHide: null,
    onPageShow: null,
    onPaste: null,
    onPause: null,
    onPlay: null,
    onPlaying: null,
    onPopState: null,
    onProgress: null,
    onRateChange: null,
    onRepeat: null,
    onReset: null,
    onResize: null,
    onScroll: null,
    onSeeked: null,
    onSeeking: null,
    onSelect: null,
    onShow: null,
    onStalled: null,
    onStorage: null,
    onSubmit: null,
    onSuspend: null,
    onTimeUpdate: null,
    onToggle: null,
    onUnload: null,
    onVolumeChange: null,
    onWaiting: null,
    onZoom: null,
    opacity: null,
    operator: null,
    order: null,
    orient: null,
    orientation: null,
    origin: null,
    overflow: null,
    overlay: null,
    overlinePosition: number,
    overlineThickness: number,
    paintOrder: null,
    panose1: null,
    path: null,
    pathLength: number,
    patternContentUnits: null,
    patternTransform: null,
    patternUnits: null,
    phase: null,
    ping: spaceSeparated,
    pitch: null,
    playbackOrder: null,
    pointerEvents: null,
    points: null,
    pointsAtX: number,
    pointsAtY: number,
    pointsAtZ: number,
    preserveAlpha: null,
    preserveAspectRatio: null,
    primitiveUnits: null,
    propagate: null,
    property: commaOrSpaceSeparated,
    r: null,
    radius: null,
    referrerPolicy: null,
    refX: null,
    refY: null,
    rel: commaOrSpaceSeparated,
    rev: commaOrSpaceSeparated,
    renderingIntent: null,
    repeatCount: null,
    repeatDur: null,
    requiredExtensions: commaOrSpaceSeparated,
    requiredFeatures: commaOrSpaceSeparated,
    requiredFonts: commaOrSpaceSeparated,
    requiredFormats: commaOrSpaceSeparated,
    resource: null,
    restart: null,
    result: null,
    rotate: null,
    rx: null,
    ry: null,
    scale: null,
    seed: null,
    shapeRendering: null,
    side: null,
    slope: null,
    snapshotTime: null,
    specularConstant: number,
    specularExponent: number,
    spreadMethod: null,
    spacing: null,
    startOffset: null,
    stdDeviation: null,
    stemh: null,
    stemv: null,
    stitchTiles: null,
    stopColor: null,
    stopOpacity: null,
    strikethroughPosition: number,
    strikethroughThickness: number,
    string: null,
    stroke: null,
    strokeDashArray: commaOrSpaceSeparated,
    strokeDashOffset: null,
    strokeLineCap: null,
    strokeLineJoin: null,
    strokeMiterLimit: number,
    strokeOpacity: number,
    strokeWidth: null,
    style: null,
    surfaceScale: number,
    syncBehavior: null,
    syncBehaviorDefault: null,
    syncMaster: null,
    syncTolerance: null,
    syncToleranceDefault: null,
    systemLanguage: commaOrSpaceSeparated,
    tabIndex: number,
    tableValues: null,
    target: null,
    targetX: number,
    targetY: number,
    textAnchor: null,
    textDecoration: null,
    textRendering: null,
    textLength: null,
    timelineBegin: null,
    title: null,
    transformBehavior: null,
    type: null,
    typeOf: commaOrSpaceSeparated,
    to: null,
    transform: null,
    transformOrigin: null,
    u1: null,
    u2: null,
    underlinePosition: number,
    underlineThickness: number,
    unicode: null,
    unicodeBidi: null,
    unicodeRange: null,
    unitsPerEm: number,
    values: null,
    vAlphabetic: number,
    vMathematical: number,
    vectorEffect: null,
    vHanging: number,
    vIdeographic: number,
    version: null,
    vertAdvY: number,
    vertOriginX: number,
    vertOriginY: number,
    viewBox: null,
    viewTarget: null,
    visibility: null,
    width: null,
    widths: null,
    wordSpacing: null,
    writingMode: null,
    x: null,
    x1: null,
    x2: null,
    xChannelSelector: null,
    xHeight: number,
    y: null,
    y1: null,
    y2: null,
    yChannelSelector: null,
    z: null,
    zoomAndPan: null
  }
});

// node_modules/.pnpm/property-information@6.5.0/node_modules/property-information/lib/find.js
var valid = /^data[-\w.:]+$/i;
var dash = /-[a-z]/g;
var cap = /[A-Z]/g;
function find(schema, value) {
  const normal = normalize2(value);
  let prop = value;
  let Type = Info;
  if (normal in schema.normal) {
    return schema.property[schema.normal[normal]];
  }
  if (normal.length > 4 && normal.slice(0, 4) === "data" && valid.test(value)) {
    if (value.charAt(4) === "-") {
      const rest = value.slice(5).replace(dash, camelcase);
      prop = "data" + rest.charAt(0).toUpperCase() + rest.slice(1);
    } else {
      const rest = value.slice(4);
      if (!dash.test(rest)) {
        let dashes = rest.replace(cap, kebab);
        if (dashes.charAt(0) !== "-") {
          dashes = "-" + dashes;
        }
        value = "data" + dashes;
      }
    }
    Type = DefinedInfo;
  }
  return new Type(prop, value);
}
function kebab($0) {
  return "-" + $0.toLowerCase();
}
function camelcase($0) {
  return $0.charAt(1).toUpperCase();
}

// node_modules/.pnpm/property-information@6.5.0/node_modules/property-information/lib/hast-to-react.js
var hastToReact = {
  classId: "classID",
  dataType: "datatype",
  itemId: "itemID",
  strokeDashArray: "strokeDasharray",
  strokeDashOffset: "strokeDashoffset",
  strokeLineCap: "strokeLinecap",
  strokeLineJoin: "strokeLinejoin",
  strokeMiterLimit: "strokeMiterlimit",
  typeOf: "typeof",
  xLinkActuate: "xlinkActuate",
  xLinkArcRole: "xlinkArcrole",
  xLinkHref: "xlinkHref",
  xLinkRole: "xlinkRole",
  xLinkShow: "xlinkShow",
  xLinkTitle: "xlinkTitle",
  xLinkType: "xlinkType",
  xmlnsXLink: "xmlnsXlink"
};

// node_modules/.pnpm/property-information@6.5.0/node_modules/property-information/index.js
var html3 = merge([xml, xlink, xmlns, aria, html2], "html");
var svg2 = merge([xml, xlink, xmlns, aria, svg], "svg");

// node_modules/.pnpm/react-markdown@8.0.7_@types+react@18.3.18_react@18.3.1/node_modules/react-markdown/lib/rehype-filter.js
function rehypeFilter(options) {
  if (options.allowedElements && options.disallowedElements) {
    throw new TypeError(
      "Only one of `allowedElements` and `disallowedElements` should be defined"
    );
  }
  if (options.allowedElements || options.disallowedElements || options.allowElement) {
    return (tree) => {
      visit(tree, "element", (node3, index2, parent_) => {
        const parent = (
          /** @type {Element|Root} */
          parent_
        );
        let remove;
        if (options.allowedElements) {
          remove = !options.allowedElements.includes(node3.tagName);
        } else if (options.disallowedElements) {
          remove = options.disallowedElements.includes(node3.tagName);
        }
        if (!remove && options.allowElement && typeof index2 === "number") {
          remove = !options.allowElement(node3, index2, parent);
        }
        if (remove && typeof index2 === "number") {
          if (options.unwrapDisallowed && node3.children) {
            parent.children.splice(index2, 1, ...node3.children);
          } else {
            parent.children.splice(index2, 1);
          }
          return index2;
        }
        return void 0;
      });
    };
  }
}

// node_modules/.pnpm/react-markdown@8.0.7_@types+react@18.3.18_react@18.3.1/node_modules/react-markdown/lib/ast-to-react.js
var import_react4 = __toESM(require_react(), 1);
var import_react_is = __toESM(require_react_is2(), 1);

// node_modules/.pnpm/hast-util-whitespace@2.0.1/node_modules/hast-util-whitespace/index.js
function whitespace(thing) {
  const value = (
    // @ts-expect-error looks like a node.
    thing && typeof thing === "object" && thing.type === "text" ? (
      // @ts-expect-error looks like a text.
      thing.value || ""
    ) : thing
  );
  return typeof value === "string" && value.replace(/[ \t\n\f\r]/g, "") === "";
}

// node_modules/.pnpm/space-separated-tokens@2.0.2/node_modules/space-separated-tokens/index.js
function stringify(values) {
  return values.join(" ").trim();
}

// node_modules/.pnpm/comma-separated-tokens@2.0.3/node_modules/comma-separated-tokens/index.js
function stringify2(values, options) {
  const settings = options || {};
  const input = values[values.length - 1] === "" ? [...values, ""] : values;
  return input.join(
    (settings.padRight ? " " : "") + "," + (settings.padLeft === false ? "" : " ")
  ).trim();
}

// node_modules/.pnpm/style-to-object@0.4.4/node_modules/style-to-object/index.mjs
var import_index = __toESM(require_style_to_object(), 1);
var style_to_object_default = import_index.default;

// node_modules/.pnpm/react-markdown@8.0.7_@types+react@18.3.18_react@18.3.1/node_modules/react-markdown/lib/ast-to-react.js
var own6 = {}.hasOwnProperty;
var tableElements = /* @__PURE__ */ new Set(["table", "thead", "tbody", "tfoot", "tr"]);
function childrenToReact(context, node3) {
  const children = [];
  let childIndex = -1;
  let child;
  while (++childIndex < node3.children.length) {
    child = node3.children[childIndex];
    if (child.type === "element") {
      children.push(toReact(context, child, childIndex, node3));
    } else if (child.type === "text") {
      if (node3.type !== "element" || !tableElements.has(node3.tagName) || !whitespace(child)) {
        children.push(child.value);
      }
    } else if (child.type === "raw" && !context.options.skipHtml) {
      children.push(child.value);
    }
  }
  return children;
}
function toReact(context, node3, index2, parent) {
  const options = context.options;
  const transform = options.transformLinkUri === void 0 ? uriTransformer : options.transformLinkUri;
  const parentSchema = context.schema;
  const name = node3.tagName;
  const properties = {};
  let schema = parentSchema;
  let property;
  if (parentSchema.space === "html" && name === "svg") {
    schema = svg2;
    context.schema = schema;
  }
  if (node3.properties) {
    for (property in node3.properties) {
      if (own6.call(node3.properties, property)) {
        addProperty(properties, property, node3.properties[property], context);
      }
    }
  }
  if (name === "ol" || name === "ul") {
    context.listDepth++;
  }
  const children = childrenToReact(context, node3);
  if (name === "ol" || name === "ul") {
    context.listDepth--;
  }
  context.schema = parentSchema;
  const position3 = node3.position || {
    start: { line: null, column: null, offset: null },
    end: { line: null, column: null, offset: null }
  };
  const component = options.components && own6.call(options.components, name) ? options.components[name] : name;
  const basic = typeof component === "string" || component === import_react4.default.Fragment;
  if (!import_react_is.default.isValidElementType(component)) {
    throw new TypeError(
      `Component for name \`${name}\` not defined or is not renderable`
    );
  }
  properties.key = index2;
  if (name === "a" && options.linkTarget) {
    properties.target = typeof options.linkTarget === "function" ? options.linkTarget(
      String(properties.href || ""),
      node3.children,
      typeof properties.title === "string" ? properties.title : null
    ) : options.linkTarget;
  }
  if (name === "a" && transform) {
    properties.href = transform(
      String(properties.href || ""),
      node3.children,
      typeof properties.title === "string" ? properties.title : null
    );
  }
  if (!basic && name === "code" && parent.type === "element" && parent.tagName !== "pre") {
    properties.inline = true;
  }
  if (!basic && (name === "h1" || name === "h2" || name === "h3" || name === "h4" || name === "h5" || name === "h6")) {
    properties.level = Number.parseInt(name.charAt(1), 10);
  }
  if (name === "img" && options.transformImageUri) {
    properties.src = options.transformImageUri(
      String(properties.src || ""),
      String(properties.alt || ""),
      typeof properties.title === "string" ? properties.title : null
    );
  }
  if (!basic && name === "li" && parent.type === "element") {
    const input = getInputElement(node3);
    properties.checked = input && input.properties ? Boolean(input.properties.checked) : null;
    properties.index = getElementsBeforeCount(parent, node3);
    properties.ordered = parent.tagName === "ol";
  }
  if (!basic && (name === "ol" || name === "ul")) {
    properties.ordered = name === "ol";
    properties.depth = context.listDepth;
  }
  if (name === "td" || name === "th") {
    if (properties.align) {
      if (!properties.style)
        properties.style = {};
      properties.style.textAlign = properties.align;
      delete properties.align;
    }
    if (!basic) {
      properties.isHeader = name === "th";
    }
  }
  if (!basic && name === "tr" && parent.type === "element") {
    properties.isHeader = Boolean(parent.tagName === "thead");
  }
  if (options.sourcePos) {
    properties["data-sourcepos"] = flattenPosition(position3);
  }
  if (!basic && options.rawSourcePos) {
    properties.sourcePosition = node3.position;
  }
  if (!basic && options.includeElementIndex) {
    properties.index = getElementsBeforeCount(parent, node3);
    properties.siblingCount = getElementsBeforeCount(parent);
  }
  if (!basic) {
    properties.node = node3;
  }
  return children.length > 0 ? import_react4.default.createElement(component, properties, children) : import_react4.default.createElement(component, properties);
}
function getInputElement(node3) {
  let index2 = -1;
  while (++index2 < node3.children.length) {
    const child = node3.children[index2];
    if (child.type === "element" && child.tagName === "input") {
      return child;
    }
  }
  return null;
}
function getElementsBeforeCount(parent, node3) {
  let index2 = -1;
  let count = 0;
  while (++index2 < parent.children.length) {
    if (parent.children[index2] === node3)
      break;
    if (parent.children[index2].type === "element")
      count++;
  }
  return count;
}
function addProperty(props, prop, value, ctx) {
  const info = find(ctx.schema, prop);
  let result = value;
  if (result === null || result === void 0 || result !== result) {
    return;
  }
  if (Array.isArray(result)) {
    result = info.commaSeparated ? stringify2(result) : stringify(result);
  }
  if (info.property === "style" && typeof result === "string") {
    result = parseStyle(result);
  }
  if (info.space && info.property) {
    props[own6.call(hastToReact, info.property) ? hastToReact[info.property] : info.property] = result;
  } else if (info.attribute) {
    props[info.attribute] = result;
  }
}
function parseStyle(value) {
  const result = {};
  try {
    style_to_object_default(value, iterator);
  } catch {
  }
  return result;
  function iterator(name, v) {
    const k = name.slice(0, 4) === "-ms-" ? `ms-${name.slice(4)}` : name;
    result[k.replace(/-([a-z])/g, styleReplacer)] = v;
  }
}
function styleReplacer(_, $1) {
  return $1.toUpperCase();
}
function flattenPosition(pos) {
  return [
    pos.start.line,
    ":",
    pos.start.column,
    "-",
    pos.end.line,
    ":",
    pos.end.column
  ].map(String).join("");
}

// node_modules/.pnpm/react-markdown@8.0.7_@types+react@18.3.18_react@18.3.1/node_modules/react-markdown/lib/react-markdown.js
var own7 = {}.hasOwnProperty;
var changelog = "https://github.com/remarkjs/react-markdown/blob/main/changelog.md";
var deprecated = {
  plugins: { to: "remarkPlugins", id: "change-plugins-to-remarkplugins" },
  renderers: { to: "components", id: "change-renderers-to-components" },
  astPlugins: { id: "remove-buggy-html-in-markdown-parser" },
  allowDangerousHtml: { id: "remove-buggy-html-in-markdown-parser" },
  escapeHtml: { id: "remove-buggy-html-in-markdown-parser" },
  source: { to: "children", id: "change-source-to-children" },
  allowNode: {
    to: "allowElement",
    id: "replace-allownode-allowedtypes-and-disallowedtypes"
  },
  allowedTypes: {
    to: "allowedElements",
    id: "replace-allownode-allowedtypes-and-disallowedtypes"
  },
  disallowedTypes: {
    to: "disallowedElements",
    id: "replace-allownode-allowedtypes-and-disallowedtypes"
  },
  includeNodeIndex: {
    to: "includeElementIndex",
    id: "change-includenodeindex-to-includeelementindex"
  }
};
function ReactMarkdown(options) {
  for (const key in deprecated) {
    if (own7.call(deprecated, key) && own7.call(options, key)) {
      const deprecation = deprecated[key];
      console.warn(
        `[react-markdown] Warning: please ${deprecation.to ? `use \`${deprecation.to}\` instead of` : "remove"} \`${key}\` (see <${changelog}#${deprecation.id}> for more info)`
      );
      delete deprecated[key];
    }
  }
  const processor = unified().use(remarkParse).use(options.remarkPlugins || []).use(lib_default, {
    ...options.remarkRehypeOptions,
    allowDangerousHtml: true
  }).use(options.rehypePlugins || []).use(rehypeFilter, options);
  const file = new VFile();
  if (typeof options.children === "string") {
    file.value = options.children;
  } else if (options.children !== void 0 && options.children !== null) {
    console.warn(
      `[react-markdown] Warning: please pass a string as \`children\` (not: \`${options.children}\`)`
    );
  }
  const hastNode = processor.runSync(processor.parse(file), file);
  if (hastNode.type !== "root") {
    throw new TypeError("Expected a `root` node");
  }
  let result = import_react5.default.createElement(
    import_react5.default.Fragment,
    {},
    childrenToReact({ options, schema: html3, listDepth: 0 }, hastNode)
  );
  if (options.className) {
    result = import_react5.default.createElement("div", { className: options.className }, result);
  }
  return result;
}
ReactMarkdown.propTypes = {
  // Core options:
  children: import_prop_types.default.string,
  // Layout options:
  className: import_prop_types.default.string,
  // Filter options:
  allowElement: import_prop_types.default.func,
  allowedElements: import_prop_types.default.arrayOf(import_prop_types.default.string),
  disallowedElements: import_prop_types.default.arrayOf(import_prop_types.default.string),
  unwrapDisallowed: import_prop_types.default.bool,
  // Plugin options:
  remarkPlugins: import_prop_types.default.arrayOf(
    import_prop_types.default.oneOfType([
      import_prop_types.default.object,
      import_prop_types.default.func,
      import_prop_types.default.arrayOf(
        import_prop_types.default.oneOfType([
          import_prop_types.default.bool,
          import_prop_types.default.string,
          import_prop_types.default.object,
          import_prop_types.default.func,
          import_prop_types.default.arrayOf(
            // prettier-ignore
            // type-coverage:ignore-next-line
            import_prop_types.default.any
          )
        ])
      )
    ])
  ),
  rehypePlugins: import_prop_types.default.arrayOf(
    import_prop_types.default.oneOfType([
      import_prop_types.default.object,
      import_prop_types.default.func,
      import_prop_types.default.arrayOf(
        import_prop_types.default.oneOfType([
          import_prop_types.default.bool,
          import_prop_types.default.string,
          import_prop_types.default.object,
          import_prop_types.default.func,
          import_prop_types.default.arrayOf(
            // prettier-ignore
            // type-coverage:ignore-next-line
            import_prop_types.default.any
          )
        ])
      )
    ])
  ),
  // Transform options:
  sourcePos: import_prop_types.default.bool,
  rawSourcePos: import_prop_types.default.bool,
  skipHtml: import_prop_types.default.bool,
  includeElementIndex: import_prop_types.default.bool,
  transformLinkUri: import_prop_types.default.oneOfType([import_prop_types.default.func, import_prop_types.default.bool]),
  linkTarget: import_prop_types.default.oneOfType([import_prop_types.default.func, import_prop_types.default.string]),
  transformImageUri: import_prop_types.default.func,
  components: import_prop_types.default.object
};

// node_modules/.pnpm/ccount@2.0.1/node_modules/ccount/index.js
function ccount(value, character) {
  const source = String(value);
  if (typeof character !== "string") {
    throw new TypeError("Expected character");
  }
  let count = 0;
  let index2 = source.indexOf(character);
  while (index2 !== -1) {
    count++;
    index2 = source.indexOf(character, index2 + character.length);
  }
  return count;
}

// node_modules/.pnpm/devlop@1.1.0/node_modules/devlop/lib/default.js
function ok2() {
}

// node_modules/.pnpm/micromark-util-character@2.1.1/node_modules/micromark-util-character/index.js
var asciiAlpha2 = regexCheck2(/[A-Za-z]/);
var asciiAlphanumeric2 = regexCheck2(/[\dA-Za-z]/);
var asciiAtext2 = regexCheck2(/[#-'*+\--9=?A-Z^-~]/);
function asciiControl2(code4) {
  return (
    // Special whitespace codes (which have negative values), C0 and Control
    // character DEL
    code4 !== null && (code4 < 32 || code4 === 127)
  );
}
var asciiDigit2 = regexCheck2(/\d/);
var asciiHexDigit2 = regexCheck2(/[\dA-Fa-f]/);
var asciiPunctuation2 = regexCheck2(/[!-/:-@[-`{-~]/);
function markdownLineEnding2(code4) {
  return code4 !== null && code4 < -2;
}
function markdownLineEndingOrSpace2(code4) {
  return code4 !== null && (code4 < 0 || code4 === 32);
}
function markdownSpace2(code4) {
  return code4 === -2 || code4 === -1 || code4 === 32;
}
var unicodePunctuation2 = regexCheck2(/\p{P}|\p{S}/u);
var unicodeWhitespace2 = regexCheck2(/\s/);
function regexCheck2(regex) {
  return check;
  function check(code4) {
    return code4 !== null && code4 > -1 && regex.test(String.fromCharCode(code4));
  }
}

// node_modules/.pnpm/escape-string-regexp@5.0.0/node_modules/escape-string-regexp/index.js
function escapeStringRegexp(string3) {
  if (typeof string3 !== "string") {
    throw new TypeError("Expected a string");
  }
  return string3.replace(/[|\\{}()[\]^$+*?.]/g, "\\$&").replace(/-/g, "\\x2d");
}

// node_modules/.pnpm/unist-util-is@6.0.0/node_modules/unist-util-is/lib/index.js
var convert2 = (
  // Note: overloads in JSDoc can’t yet use different `@template`s.
  /**
   * @type {(
   *   (<Condition extends string>(test: Condition) => (node: unknown, index?: number | null | undefined, parent?: Parent | null | undefined, context?: unknown) => node is Node & {type: Condition}) &
   *   (<Condition extends Props>(test: Condition) => (node: unknown, index?: number | null | undefined, parent?: Parent | null | undefined, context?: unknown) => node is Node & Condition) &
   *   (<Condition extends TestFunction>(test: Condition) => (node: unknown, index?: number | null | undefined, parent?: Parent | null | undefined, context?: unknown) => node is Node & Predicate<Condition, Node>) &
   *   ((test?: null | undefined) => (node?: unknown, index?: number | null | undefined, parent?: Parent | null | undefined, context?: unknown) => node is Node) &
   *   ((test?: Test) => Check)
   * )}
   */
  /**
   * @param {Test} [test]
   * @returns {Check}
   */
  function(test) {
    if (test === null || test === void 0) {
      return ok3;
    }
    if (typeof test === "function") {
      return castFactory2(test);
    }
    if (typeof test === "object") {
      return Array.isArray(test) ? anyFactory2(test) : propsFactory2(test);
    }
    if (typeof test === "string") {
      return typeFactory2(test);
    }
    throw new Error("Expected function, string, or object as test");
  }
);
function anyFactory2(tests) {
  const checks2 = [];
  let index2 = -1;
  while (++index2 < tests.length) {
    checks2[index2] = convert2(tests[index2]);
  }
  return castFactory2(any);
  function any(...parameters) {
    let index3 = -1;
    while (++index3 < checks2.length) {
      if (checks2[index3].apply(this, parameters))
        return true;
    }
    return false;
  }
}
function propsFactory2(check) {
  const checkAsRecord = (
    /** @type {Record<string, unknown>} */
    check
  );
  return castFactory2(all4);
  function all4(node3) {
    const nodeAsRecord = (
      /** @type {Record<string, unknown>} */
      /** @type {unknown} */
      node3
    );
    let key;
    for (key in check) {
      if (nodeAsRecord[key] !== checkAsRecord[key])
        return false;
    }
    return true;
  }
}
function typeFactory2(check) {
  return castFactory2(type);
  function type(node3) {
    return node3 && node3.type === check;
  }
}
function castFactory2(testFunction) {
  return check;
  function check(value, index2, parent) {
    return Boolean(
      looksLikeANode(value) && testFunction.call(
        this,
        value,
        typeof index2 === "number" ? index2 : void 0,
        parent || void 0
      )
    );
  }
}
function ok3() {
  return true;
}
function looksLikeANode(value) {
  return value !== null && typeof value === "object" && "type" in value;
}

// node_modules/.pnpm/unist-util-visit-parents@6.0.1/node_modules/unist-util-visit-parents/lib/color.js
function color2(d) {
  return d;
}

// node_modules/.pnpm/unist-util-visit-parents@6.0.1/node_modules/unist-util-visit-parents/lib/index.js
var empty = [];
var CONTINUE2 = true;
var EXIT2 = false;
var SKIP2 = "skip";
function visitParents2(tree, test, visitor, reverse) {
  let check;
  if (typeof test === "function" && typeof visitor !== "function") {
    reverse = visitor;
    visitor = test;
  } else {
    check = test;
  }
  const is3 = convert2(check);
  const step = reverse ? -1 : 1;
  factory(tree, void 0, [])();
  function factory(node3, index2, parents) {
    const value = (
      /** @type {Record<string, unknown>} */
      node3 && typeof node3 === "object" ? node3 : {}
    );
    if (typeof value.type === "string") {
      const name = (
        // `hast`
        typeof value.tagName === "string" ? value.tagName : (
          // `xast`
          typeof value.name === "string" ? value.name : void 0
        )
      );
      Object.defineProperty(visit3, "name", {
        value: "node (" + color2(node3.type + (name ? "<" + name + ">" : "")) + ")"
      });
    }
    return visit3;
    function visit3() {
      let result = empty;
      let subresult;
      let offset;
      let grandparents;
      if (!test || is3(node3, index2, parents[parents.length - 1] || void 0)) {
        result = toResult2(visitor(node3, parents));
        if (result[0] === EXIT2) {
          return result;
        }
      }
      if ("children" in node3 && node3.children) {
        const nodeAsParent = (
          /** @type {UnistParent} */
          node3
        );
        if (nodeAsParent.children && result[0] !== SKIP2) {
          offset = (reverse ? nodeAsParent.children.length : -1) + step;
          grandparents = parents.concat(nodeAsParent);
          while (offset > -1 && offset < nodeAsParent.children.length) {
            const child = nodeAsParent.children[offset];
            subresult = factory(child, offset, grandparents)();
            if (subresult[0] === EXIT2) {
              return subresult;
            }
            offset = typeof subresult[1] === "number" ? subresult[1] : offset + step;
          }
        }
      }
      return result;
    }
  }
}
function toResult2(value) {
  if (Array.isArray(value)) {
    return value;
  }
  if (typeof value === "number") {
    return [CONTINUE2, value];
  }
  return value === null || value === void 0 ? empty : [value];
}

// node_modules/.pnpm/mdast-util-find-and-replace@3.0.2/node_modules/mdast-util-find-and-replace/lib/index.js
function findAndReplace(tree, list4, options) {
  const settings = options || {};
  const ignored = convert2(settings.ignore || []);
  const pairs = toPairs(list4);
  let pairIndex = -1;
  while (++pairIndex < pairs.length) {
    visitParents2(tree, "text", visitor);
  }
  function visitor(node3, parents) {
    let index2 = -1;
    let grandparent;
    while (++index2 < parents.length) {
      const parent = parents[index2];
      const siblings = grandparent ? grandparent.children : void 0;
      if (ignored(
        parent,
        siblings ? siblings.indexOf(parent) : void 0,
        grandparent
      )) {
        return;
      }
      grandparent = parent;
    }
    if (grandparent) {
      return handler(node3, parents);
    }
  }
  function handler(node3, parents) {
    const parent = parents[parents.length - 1];
    const find2 = pairs[pairIndex][0];
    const replace2 = pairs[pairIndex][1];
    let start = 0;
    const siblings = parent.children;
    const index2 = siblings.indexOf(node3);
    let change = false;
    let nodes = [];
    find2.lastIndex = 0;
    let match = find2.exec(node3.value);
    while (match) {
      const position3 = match.index;
      const matchObject = {
        index: match.index,
        input: match.input,
        stack: [...parents, node3]
      };
      let value = replace2(...match, matchObject);
      if (typeof value === "string") {
        value = value.length > 0 ? { type: "text", value } : void 0;
      }
      if (value === false) {
        find2.lastIndex = position3 + 1;
      } else {
        if (start !== position3) {
          nodes.push({
            type: "text",
            value: node3.value.slice(start, position3)
          });
        }
        if (Array.isArray(value)) {
          nodes.push(...value);
        } else if (value) {
          nodes.push(value);
        }
        start = position3 + match[0].length;
        change = true;
      }
      if (!find2.global) {
        break;
      }
      match = find2.exec(node3.value);
    }
    if (change) {
      if (start < node3.value.length) {
        nodes.push({ type: "text", value: node3.value.slice(start) });
      }
      parent.children.splice(index2, 1, ...nodes);
    } else {
      nodes = [node3];
    }
    return index2 + nodes.length;
  }
}
function toPairs(tupleOrList) {
  const result = [];
  if (!Array.isArray(tupleOrList)) {
    throw new TypeError("Expected find and replace tuple or list of tuples");
  }
  const list4 = !tupleOrList[0] || Array.isArray(tupleOrList[0]) ? tupleOrList : [tupleOrList];
  let index2 = -1;
  while (++index2 < list4.length) {
    const tuple = list4[index2];
    result.push([toExpression(tuple[0]), toFunction(tuple[1])]);
  }
  return result;
}
function toExpression(find2) {
  return typeof find2 === "string" ? new RegExp(escapeStringRegexp(find2), "g") : find2;
}
function toFunction(replace2) {
  return typeof replace2 === "function" ? replace2 : function() {
    return replace2;
  };
}

// node_modules/.pnpm/mdast-util-gfm-autolink-literal@2.0.1/node_modules/mdast-util-gfm-autolink-literal/lib/index.js
var inConstruct = "phrasing";
var notInConstruct = ["autolink", "link", "image", "label"];
function gfmAutolinkLiteralFromMarkdown() {
  return {
    transforms: [transformGfmAutolinkLiterals],
    enter: {
      literalAutolink: enterLiteralAutolink,
      literalAutolinkEmail: enterLiteralAutolinkValue,
      literalAutolinkHttp: enterLiteralAutolinkValue,
      literalAutolinkWww: enterLiteralAutolinkValue
    },
    exit: {
      literalAutolink: exitLiteralAutolink,
      literalAutolinkEmail: exitLiteralAutolinkEmail,
      literalAutolinkHttp: exitLiteralAutolinkHttp,
      literalAutolinkWww: exitLiteralAutolinkWww
    }
  };
}
function gfmAutolinkLiteralToMarkdown() {
  return {
    unsafe: [
      {
        character: "@",
        before: "[+\\-.\\w]",
        after: "[\\-.\\w]",
        inConstruct,
        notInConstruct
      },
      {
        character: ".",
        before: "[Ww]",
        after: "[\\-.\\w]",
        inConstruct,
        notInConstruct
      },
      {
        character: ":",
        before: "[ps]",
        after: "\\/",
        inConstruct,
        notInConstruct
      }
    ]
  };
}
function enterLiteralAutolink(token) {
  this.enter({ type: "link", title: null, url: "", children: [] }, token);
}
function enterLiteralAutolinkValue(token) {
  this.config.enter.autolinkProtocol.call(this, token);
}
function exitLiteralAutolinkHttp(token) {
  this.config.exit.autolinkProtocol.call(this, token);
}
function exitLiteralAutolinkWww(token) {
  this.config.exit.data.call(this, token);
  const node3 = this.stack[this.stack.length - 1];
  ok2(node3.type === "link");
  node3.url = "http://" + this.sliceSerialize(token);
}
function exitLiteralAutolinkEmail(token) {
  this.config.exit.autolinkEmail.call(this, token);
}
function exitLiteralAutolink(token) {
  this.exit(token);
}
function transformGfmAutolinkLiterals(tree) {
  findAndReplace(
    tree,
    [
      [/(https?:\/\/|www(?=\.))([-.\w]+)([^ \t\r\n]*)/gi, findUrl],
      [/(?<=^|\s|\p{P}|\p{S})([-.\w+]+)@([-\w]+(?:\.[-\w]+)+)/gu, findEmail]
    ],
    { ignore: ["link", "linkReference"] }
  );
}
function findUrl(_, protocol, domain2, path3, match) {
  let prefix = "";
  if (!previous2(match)) {
    return false;
  }
  if (/^w/i.test(protocol)) {
    domain2 = protocol + domain2;
    protocol = "";
    prefix = "http://";
  }
  if (!isCorrectDomain(domain2)) {
    return false;
  }
  const parts = splitUrl(domain2 + path3);
  if (!parts[0])
    return false;
  const result = {
    type: "link",
    title: null,
    url: prefix + protocol + parts[0],
    children: [{ type: "text", value: protocol + parts[0] }]
  };
  if (parts[1]) {
    return [result, { type: "text", value: parts[1] }];
  }
  return result;
}
function findEmail(_, atext, label, match) {
  if (
    // Not an expected previous character.
    !previous2(match, true) || // Label ends in not allowed character.
    /[-\d_]$/.test(label)
  ) {
    return false;
  }
  return {
    type: "link",
    title: null,
    url: "mailto:" + atext + "@" + label,
    children: [{ type: "text", value: atext + "@" + label }]
  };
}
function isCorrectDomain(domain2) {
  const parts = domain2.split(".");
  if (parts.length < 2 || parts[parts.length - 1] && (/_/.test(parts[parts.length - 1]) || !/[a-zA-Z\d]/.test(parts[parts.length - 1])) || parts[parts.length - 2] && (/_/.test(parts[parts.length - 2]) || !/[a-zA-Z\d]/.test(parts[parts.length - 2]))) {
    return false;
  }
  return true;
}
function splitUrl(url) {
  const trailExec = /[!"&'),.:;<>?\]}]+$/.exec(url);
  if (!trailExec) {
    return [url, void 0];
  }
  url = url.slice(0, trailExec.index);
  let trail2 = trailExec[0];
  let closingParenIndex = trail2.indexOf(")");
  const openingParens = ccount(url, "(");
  let closingParens = ccount(url, ")");
  while (closingParenIndex !== -1 && openingParens > closingParens) {
    url += trail2.slice(0, closingParenIndex + 1);
    trail2 = trail2.slice(closingParenIndex + 1);
    closingParenIndex = trail2.indexOf(")");
    closingParens++;
  }
  return [url, trail2];
}
function previous2(match, email) {
  const code4 = match.input.charCodeAt(match.index - 1);
  return (match.index === 0 || unicodeWhitespace2(code4) || unicodePunctuation2(code4)) && // If it’s an email, the previous character should not be a slash.
  (!email || code4 !== 47);
}

// node_modules/.pnpm/micromark-util-normalize-identifier@2.0.1/node_modules/micromark-util-normalize-identifier/index.js
function normalizeIdentifier2(value) {
  return value.replace(/[\t\n\r ]+/g, " ").replace(/^ | $/g, "").toLowerCase().toUpperCase();
}

// node_modules/.pnpm/mdast-util-gfm-footnote@2.0.0/node_modules/mdast-util-gfm-footnote/lib/index.js
footnoteReference2.peek = footnoteReferencePeek;
function gfmFootnoteFromMarkdown() {
  return {
    enter: {
      gfmFootnoteDefinition: enterFootnoteDefinition,
      gfmFootnoteDefinitionLabelString: enterFootnoteDefinitionLabelString,
      gfmFootnoteCall: enterFootnoteCall,
      gfmFootnoteCallString: enterFootnoteCallString
    },
    exit: {
      gfmFootnoteDefinition: exitFootnoteDefinition,
      gfmFootnoteDefinitionLabelString: exitFootnoteDefinitionLabelString,
      gfmFootnoteCall: exitFootnoteCall,
      gfmFootnoteCallString: exitFootnoteCallString
    }
  };
}
function gfmFootnoteToMarkdown() {
  return {
    // This is on by default already.
    unsafe: [{ character: "[", inConstruct: ["phrasing", "label", "reference"] }],
    handlers: { footnoteDefinition, footnoteReference: footnoteReference2 }
  };
}
function enterFootnoteDefinition(token) {
  this.enter(
    { type: "footnoteDefinition", identifier: "", label: "", children: [] },
    token
  );
}
function enterFootnoteDefinitionLabelString() {
  this.buffer();
}
function exitFootnoteDefinitionLabelString(token) {
  const label = this.resume();
  const node3 = this.stack[this.stack.length - 1];
  ok2(node3.type === "footnoteDefinition");
  node3.label = label;
  node3.identifier = normalizeIdentifier2(
    this.sliceSerialize(token)
  ).toLowerCase();
}
function exitFootnoteDefinition(token) {
  this.exit(token);
}
function enterFootnoteCall(token) {
  this.enter({ type: "footnoteReference", identifier: "", label: "" }, token);
}
function enterFootnoteCallString() {
  this.buffer();
}
function exitFootnoteCallString(token) {
  const label = this.resume();
  const node3 = this.stack[this.stack.length - 1];
  ok2(node3.type === "footnoteReference");
  node3.label = label;
  node3.identifier = normalizeIdentifier2(
    this.sliceSerialize(token)
  ).toLowerCase();
}
function exitFootnoteCall(token) {
  this.exit(token);
}
function footnoteReference2(node3, _, state, info) {
  const tracker = state.createTracker(info);
  let value = tracker.move("[^");
  const exit3 = state.enter("footnoteReference");
  const subexit = state.enter("reference");
  value += tracker.move(
    state.safe(state.associationId(node3), {
      ...tracker.current(),
      before: value,
      after: "]"
    })
  );
  subexit();
  exit3();
  value += tracker.move("]");
  return value;
}
function footnoteReferencePeek() {
  return "[";
}
function footnoteDefinition(node3, _, state, info) {
  const tracker = state.createTracker(info);
  let value = tracker.move("[^");
  const exit3 = state.enter("footnoteDefinition");
  const subexit = state.enter("label");
  value += tracker.move(
    state.safe(state.associationId(node3), {
      ...tracker.current(),
      before: value,
      after: "]"
    })
  );
  subexit();
  value += tracker.move(
    "]:" + (node3.children && node3.children.length > 0 ? " " : "")
  );
  tracker.shift(4);
  value += tracker.move(
    state.indentLines(state.containerFlow(node3, tracker.current()), map)
  );
  exit3();
  return value;
}
function map(line, index2, blank) {
  if (index2 === 0) {
    return line;
  }
  return (blank ? "" : "    ") + line;
}

// node_modules/.pnpm/mdast-util-gfm-strikethrough@2.0.0/node_modules/mdast-util-gfm-strikethrough/lib/index.js
var constructsWithoutStrikethrough = [
  "autolink",
  "destinationLiteral",
  "destinationRaw",
  "reference",
  "titleQuote",
  "titleApostrophe"
];
handleDelete.peek = peekDelete;
function gfmStrikethroughFromMarkdown() {
  return {
    canContainEols: ["delete"],
    enter: { strikethrough: enterStrikethrough },
    exit: { strikethrough: exitStrikethrough }
  };
}
function gfmStrikethroughToMarkdown() {
  return {
    unsafe: [
      {
        character: "~",
        inConstruct: "phrasing",
        notInConstruct: constructsWithoutStrikethrough
      }
    ],
    handlers: { delete: handleDelete }
  };
}
function enterStrikethrough(token) {
  this.enter({ type: "delete", children: [] }, token);
}
function exitStrikethrough(token) {
  this.exit(token);
}
function handleDelete(node3, _, state, info) {
  const tracker = state.createTracker(info);
  const exit3 = state.enter("strikethrough");
  let value = tracker.move("~~");
  value += state.containerPhrasing(node3, {
    ...tracker.current(),
    before: value,
    after: "~"
  });
  value += tracker.move("~~");
  exit3();
  return value;
}
function peekDelete() {
  return "~";
}

// node_modules/.pnpm/markdown-table@3.0.4/node_modules/markdown-table/index.js
function defaultStringLength(value) {
  return value.length;
}
function markdownTable(table2, options) {
  const settings = options || {};
  const align = (settings.align || []).concat();
  const stringLength = settings.stringLength || defaultStringLength;
  const alignments = [];
  const cellMatrix = [];
  const sizeMatrix = [];
  const longestCellByColumn = [];
  let mostCellsPerRow = 0;
  let rowIndex = -1;
  while (++rowIndex < table2.length) {
    const row2 = [];
    const sizes2 = [];
    let columnIndex2 = -1;
    if (table2[rowIndex].length > mostCellsPerRow) {
      mostCellsPerRow = table2[rowIndex].length;
    }
    while (++columnIndex2 < table2[rowIndex].length) {
      const cell = serialize(table2[rowIndex][columnIndex2]);
      if (settings.alignDelimiters !== false) {
        const size = stringLength(cell);
        sizes2[columnIndex2] = size;
        if (longestCellByColumn[columnIndex2] === void 0 || size > longestCellByColumn[columnIndex2]) {
          longestCellByColumn[columnIndex2] = size;
        }
      }
      row2.push(cell);
    }
    cellMatrix[rowIndex] = row2;
    sizeMatrix[rowIndex] = sizes2;
  }
  let columnIndex = -1;
  if (typeof align === "object" && "length" in align) {
    while (++columnIndex < mostCellsPerRow) {
      alignments[columnIndex] = toAlignment(align[columnIndex]);
    }
  } else {
    const code4 = toAlignment(align);
    while (++columnIndex < mostCellsPerRow) {
      alignments[columnIndex] = code4;
    }
  }
  columnIndex = -1;
  const row = [];
  const sizes = [];
  while (++columnIndex < mostCellsPerRow) {
    const code4 = alignments[columnIndex];
    let before = "";
    let after = "";
    if (code4 === 99) {
      before = ":";
      after = ":";
    } else if (code4 === 108) {
      before = ":";
    } else if (code4 === 114) {
      after = ":";
    }
    let size = settings.alignDelimiters === false ? 1 : Math.max(
      1,
      longestCellByColumn[columnIndex] - before.length - after.length
    );
    const cell = before + "-".repeat(size) + after;
    if (settings.alignDelimiters !== false) {
      size = before.length + size + after.length;
      if (size > longestCellByColumn[columnIndex]) {
        longestCellByColumn[columnIndex] = size;
      }
      sizes[columnIndex] = size;
    }
    row[columnIndex] = cell;
  }
  cellMatrix.splice(1, 0, row);
  sizeMatrix.splice(1, 0, sizes);
  rowIndex = -1;
  const lines = [];
  while (++rowIndex < cellMatrix.length) {
    const row2 = cellMatrix[rowIndex];
    const sizes2 = sizeMatrix[rowIndex];
    columnIndex = -1;
    const line = [];
    while (++columnIndex < mostCellsPerRow) {
      const cell = row2[columnIndex] || "";
      let before = "";
      let after = "";
      if (settings.alignDelimiters !== false) {
        const size = longestCellByColumn[columnIndex] - (sizes2[columnIndex] || 0);
        const code4 = alignments[columnIndex];
        if (code4 === 114) {
          before = " ".repeat(size);
        } else if (code4 === 99) {
          if (size % 2) {
            before = " ".repeat(size / 2 + 0.5);
            after = " ".repeat(size / 2 - 0.5);
          } else {
            before = " ".repeat(size / 2);
            after = before;
          }
        } else {
          after = " ".repeat(size);
        }
      }
      if (settings.delimiterStart !== false && !columnIndex) {
        line.push("|");
      }
      if (settings.padding !== false && // Don’t add the opening space if we’re not aligning and the cell is
      // empty: there will be a closing space.
      !(settings.alignDelimiters === false && cell === "") && (settings.delimiterStart !== false || columnIndex)) {
        line.push(" ");
      }
      if (settings.alignDelimiters !== false) {
        line.push(before);
      }
      line.push(cell);
      if (settings.alignDelimiters !== false) {
        line.push(after);
      }
      if (settings.padding !== false) {
        line.push(" ");
      }
      if (settings.delimiterEnd !== false || columnIndex !== mostCellsPerRow - 1) {
        line.push("|");
      }
    }
    lines.push(
      settings.delimiterEnd === false ? line.join("").replace(/ +$/, "") : line.join("")
    );
  }
  return lines.join("\n");
}
function serialize(value) {
  return value === null || value === void 0 ? "" : String(value);
}
function toAlignment(value) {
  const code4 = typeof value === "string" ? value.codePointAt(0) : 0;
  return code4 === 67 || code4 === 99 ? 99 : code4 === 76 || code4 === 108 ? 108 : code4 === 82 || code4 === 114 ? 114 : 0;
}

// node_modules/.pnpm/mdast-util-to-markdown@2.1.2/node_modules/mdast-util-to-markdown/lib/handle/blockquote.js
function blockquote2(node3, _, state, info) {
  const exit3 = state.enter("blockquote");
  const tracker = state.createTracker(info);
  tracker.move("> ");
  tracker.shift(2);
  const value = state.indentLines(
    state.containerFlow(node3, tracker.current()),
    map2
  );
  exit3();
  return value;
}
function map2(line, _, blank) {
  return ">" + (blank ? "" : " ") + line;
}

// node_modules/.pnpm/mdast-util-to-markdown@2.1.2/node_modules/mdast-util-to-markdown/lib/util/pattern-in-scope.js
function patternInScope(stack, pattern) {
  return listInScope(stack, pattern.inConstruct, true) && !listInScope(stack, pattern.notInConstruct, false);
}
function listInScope(stack, list4, none) {
  if (typeof list4 === "string") {
    list4 = [list4];
  }
  if (!list4 || list4.length === 0) {
    return none;
  }
  let index2 = -1;
  while (++index2 < list4.length) {
    if (stack.includes(list4[index2])) {
      return true;
    }
  }
  return false;
}

// node_modules/.pnpm/mdast-util-to-markdown@2.1.2/node_modules/mdast-util-to-markdown/lib/handle/break.js
function hardBreak2(_, _1, state, info) {
  let index2 = -1;
  while (++index2 < state.unsafe.length) {
    if (state.unsafe[index2].character === "\n" && patternInScope(state.stack, state.unsafe[index2])) {
      return /[ \t]/.test(info.before) ? "" : " ";
    }
  }
  return "\\\n";
}

// node_modules/.pnpm/longest-streak@3.1.0/node_modules/longest-streak/index.js
function longestStreak(value, substring) {
  const source = String(value);
  let index2 = source.indexOf(substring);
  let expected = index2;
  let count = 0;
  let max = 0;
  if (typeof substring !== "string") {
    throw new TypeError("Expected substring");
  }
  while (index2 !== -1) {
    if (index2 === expected) {
      if (++count > max) {
        max = count;
      }
    } else {
      count = 1;
    }
    expected = index2 + substring.length;
    index2 = source.indexOf(substring, expected);
  }
  return max;
}

// node_modules/.pnpm/mdast-util-to-markdown@2.1.2/node_modules/mdast-util-to-markdown/lib/util/format-code-as-indented.js
function formatCodeAsIndented(node3, state) {
  return Boolean(
    state.options.fences === false && node3.value && // If there’s no info…
    !node3.lang && // And there’s a non-whitespace character…
    /[^ \r\n]/.test(node3.value) && // And the value doesn’t start or end in a blank…
    !/^[\t ]*(?:[\r\n]|$)|(?:^|[\r\n])[\t ]*$/.test(node3.value)
  );
}

// node_modules/.pnpm/mdast-util-to-markdown@2.1.2/node_modules/mdast-util-to-markdown/lib/util/check-fence.js
function checkFence(state) {
  const marker = state.options.fence || "`";
  if (marker !== "`" && marker !== "~") {
    throw new Error(
      "Cannot serialize code with `" + marker + "` for `options.fence`, expected `` ` `` or `~`"
    );
  }
  return marker;
}

// node_modules/.pnpm/mdast-util-to-markdown@2.1.2/node_modules/mdast-util-to-markdown/lib/handle/code.js
function code2(node3, _, state, info) {
  const marker = checkFence(state);
  const raw = node3.value || "";
  const suffix = marker === "`" ? "GraveAccent" : "Tilde";
  if (formatCodeAsIndented(node3, state)) {
    const exit4 = state.enter("codeIndented");
    const value2 = state.indentLines(raw, map3);
    exit4();
    return value2;
  }
  const tracker = state.createTracker(info);
  const sequence = marker.repeat(Math.max(longestStreak(raw, marker) + 1, 3));
  const exit3 = state.enter("codeFenced");
  let value = tracker.move(sequence);
  if (node3.lang) {
    const subexit = state.enter(`codeFencedLang${suffix}`);
    value += tracker.move(
      state.safe(node3.lang, {
        before: value,
        after: " ",
        encode: ["`"],
        ...tracker.current()
      })
    );
    subexit();
  }
  if (node3.lang && node3.meta) {
    const subexit = state.enter(`codeFencedMeta${suffix}`);
    value += tracker.move(" ");
    value += tracker.move(
      state.safe(node3.meta, {
        before: value,
        after: "\n",
        encode: ["`"],
        ...tracker.current()
      })
    );
    subexit();
  }
  value += tracker.move("\n");
  if (raw) {
    value += tracker.move(raw + "\n");
  }
  value += tracker.move(sequence);
  exit3();
  return value;
}
function map3(line, _, blank) {
  return (blank ? "" : "    ") + line;
}

// node_modules/.pnpm/mdast-util-to-markdown@2.1.2/node_modules/mdast-util-to-markdown/lib/util/check-quote.js
function checkQuote(state) {
  const marker = state.options.quote || '"';
  if (marker !== '"' && marker !== "'") {
    throw new Error(
      "Cannot serialize title with `" + marker + "` for `options.quote`, expected `\"`, or `'`"
    );
  }
  return marker;
}

// node_modules/.pnpm/mdast-util-to-markdown@2.1.2/node_modules/mdast-util-to-markdown/lib/handle/definition.js
function definition2(node3, _, state, info) {
  const quote = checkQuote(state);
  const suffix = quote === '"' ? "Quote" : "Apostrophe";
  const exit3 = state.enter("definition");
  let subexit = state.enter("label");
  const tracker = state.createTracker(info);
  let value = tracker.move("[");
  value += tracker.move(
    state.safe(state.associationId(node3), {
      before: value,
      after: "]",
      ...tracker.current()
    })
  );
  value += tracker.move("]: ");
  subexit();
  if (
    // If there’s no url, or…
    !node3.url || // If there are control characters or whitespace.
    /[\0- \u007F]/.test(node3.url)
  ) {
    subexit = state.enter("destinationLiteral");
    value += tracker.move("<");
    value += tracker.move(
      state.safe(node3.url, { before: value, after: ">", ...tracker.current() })
    );
    value += tracker.move(">");
  } else {
    subexit = state.enter("destinationRaw");
    value += tracker.move(
      state.safe(node3.url, {
        before: value,
        after: node3.title ? " " : "\n",
        ...tracker.current()
      })
    );
  }
  subexit();
  if (node3.title) {
    subexit = state.enter(`title${suffix}`);
    value += tracker.move(" " + quote);
    value += tracker.move(
      state.safe(node3.title, {
        before: value,
        after: quote,
        ...tracker.current()
      })
    );
    value += tracker.move(quote);
    subexit();
  }
  exit3();
  return value;
}

// node_modules/.pnpm/mdast-util-to-markdown@2.1.2/node_modules/mdast-util-to-markdown/lib/util/check-emphasis.js
function checkEmphasis(state) {
  const marker = state.options.emphasis || "*";
  if (marker !== "*" && marker !== "_") {
    throw new Error(
      "Cannot serialize emphasis with `" + marker + "` for `options.emphasis`, expected `*`, or `_`"
    );
  }
  return marker;
}

// node_modules/.pnpm/mdast-util-to-markdown@2.1.2/node_modules/mdast-util-to-markdown/lib/util/encode-character-reference.js
function encodeCharacterReference(code4) {
  return "&#x" + code4.toString(16).toUpperCase() + ";";
}

// node_modules/.pnpm/micromark-util-classify-character@2.0.1/node_modules/micromark-util-classify-character/index.js
function classifyCharacter2(code4) {
  if (code4 === null || markdownLineEndingOrSpace2(code4) || unicodeWhitespace2(code4)) {
    return 1;
  }
  if (unicodePunctuation2(code4)) {
    return 2;
  }
}

// node_modules/.pnpm/mdast-util-to-markdown@2.1.2/node_modules/mdast-util-to-markdown/lib/util/encode-info.js
function encodeInfo(outside, inside, marker) {
  const outsideKind = classifyCharacter2(outside);
  const insideKind = classifyCharacter2(inside);
  if (outsideKind === void 0) {
    return insideKind === void 0 ? (
      // Letter inside:
      // we have to encode *both* letters for `_` as it is looser.
      // it already forms for `*` (and GFMs `~`).
      marker === "_" ? { inside: true, outside: true } : { inside: false, outside: false }
    ) : insideKind === 1 ? (
      // Whitespace inside: encode both (letter, whitespace).
      { inside: true, outside: true }
    ) : (
      // Punctuation inside: encode outer (letter)
      { inside: false, outside: true }
    );
  }
  if (outsideKind === 1) {
    return insideKind === void 0 ? (
      // Letter inside: already forms.
      { inside: false, outside: false }
    ) : insideKind === 1 ? (
      // Whitespace inside: encode both (whitespace).
      { inside: true, outside: true }
    ) : (
      // Punctuation inside: already forms.
      { inside: false, outside: false }
    );
  }
  return insideKind === void 0 ? (
    // Letter inside: already forms.
    { inside: false, outside: false }
  ) : insideKind === 1 ? (
    // Whitespace inside: encode inner (whitespace).
    { inside: true, outside: false }
  ) : (
    // Punctuation inside: already forms.
    { inside: false, outside: false }
  );
}

// node_modules/.pnpm/mdast-util-to-markdown@2.1.2/node_modules/mdast-util-to-markdown/lib/handle/emphasis.js
emphasis2.peek = emphasisPeek;
function emphasis2(node3, _, state, info) {
  const marker = checkEmphasis(state);
  const exit3 = state.enter("emphasis");
  const tracker = state.createTracker(info);
  const before = tracker.move(marker);
  let between = tracker.move(
    state.containerPhrasing(node3, {
      after: marker,
      before,
      ...tracker.current()
    })
  );
  const betweenHead = between.charCodeAt(0);
  const open = encodeInfo(
    info.before.charCodeAt(info.before.length - 1),
    betweenHead,
    marker
  );
  if (open.inside) {
    between = encodeCharacterReference(betweenHead) + between.slice(1);
  }
  const betweenTail = between.charCodeAt(between.length - 1);
  const close = encodeInfo(info.after.charCodeAt(0), betweenTail, marker);
  if (close.inside) {
    between = between.slice(0, -1) + encodeCharacterReference(betweenTail);
  }
  const after = tracker.move(marker);
  exit3();
  state.attentionEncodeSurroundingInfo = {
    after: close.outside,
    before: open.outside
  };
  return before + between + after;
}
function emphasisPeek(_, _1, state) {
  return state.options.emphasis || "*";
}

// node_modules/.pnpm/unist-util-visit@5.0.0/node_modules/unist-util-visit/lib/index.js
function visit2(tree, testOrVisitor, visitorOrReverse, maybeReverse) {
  let reverse;
  let test;
  let visitor;
  if (typeof testOrVisitor === "function" && typeof visitorOrReverse !== "function") {
    test = void 0;
    visitor = testOrVisitor;
    reverse = visitorOrReverse;
  } else {
    test = testOrVisitor;
    visitor = visitorOrReverse;
    reverse = maybeReverse;
  }
  visitParents2(tree, test, overload, reverse);
  function overload(node3, parents) {
    const parent = parents[parents.length - 1];
    const index2 = parent ? parent.children.indexOf(node3) : void 0;
    return visitor(node3, index2, parent);
  }
}

// node_modules/.pnpm/mdast-util-to-string@4.0.0/node_modules/mdast-util-to-string/lib/index.js
var emptyOptions2 = {};
function toString2(value, options) {
  const settings = options || emptyOptions2;
  const includeImageAlt = typeof settings.includeImageAlt === "boolean" ? settings.includeImageAlt : true;
  const includeHtml = typeof settings.includeHtml === "boolean" ? settings.includeHtml : true;
  return one3(value, includeImageAlt, includeHtml);
}
function one3(value, includeImageAlt, includeHtml) {
  if (node2(value)) {
    if ("value" in value) {
      return value.type === "html" && !includeHtml ? "" : value.value;
    }
    if (includeImageAlt && "alt" in value && value.alt) {
      return value.alt;
    }
    if ("children" in value) {
      return all3(value.children, includeImageAlt, includeHtml);
    }
  }
  if (Array.isArray(value)) {
    return all3(value, includeImageAlt, includeHtml);
  }
  return "";
}
function all3(values, includeImageAlt, includeHtml) {
  const result = [];
  let index2 = -1;
  while (++index2 < values.length) {
    result[index2] = one3(values[index2], includeImageAlt, includeHtml);
  }
  return result.join("");
}
function node2(value) {
  return Boolean(value && typeof value === "object");
}

// node_modules/.pnpm/mdast-util-to-markdown@2.1.2/node_modules/mdast-util-to-markdown/lib/util/format-heading-as-setext.js
function formatHeadingAsSetext(node3, state) {
  let literalWithBreak = false;
  visit2(node3, function(node4) {
    if ("value" in node4 && /\r?\n|\r/.test(node4.value) || node4.type === "break") {
      literalWithBreak = true;
      return EXIT2;
    }
  });
  return Boolean(
    (!node3.depth || node3.depth < 3) && toString2(node3) && (state.options.setext || literalWithBreak)
  );
}

// node_modules/.pnpm/mdast-util-to-markdown@2.1.2/node_modules/mdast-util-to-markdown/lib/handle/heading.js
function heading2(node3, _, state, info) {
  const rank = Math.max(Math.min(6, node3.depth || 1), 1);
  const tracker = state.createTracker(info);
  if (formatHeadingAsSetext(node3, state)) {
    const exit4 = state.enter("headingSetext");
    const subexit2 = state.enter("phrasing");
    const value2 = state.containerPhrasing(node3, {
      ...tracker.current(),
      before: "\n",
      after: "\n"
    });
    subexit2();
    exit4();
    return value2 + "\n" + (rank === 1 ? "=" : "-").repeat(
      // The whole size…
      value2.length - // Minus the position of the character after the last EOL (or
      // 0 if there is none)…
      (Math.max(value2.lastIndexOf("\r"), value2.lastIndexOf("\n")) + 1)
    );
  }
  const sequence = "#".repeat(rank);
  const exit3 = state.enter("headingAtx");
  const subexit = state.enter("phrasing");
  tracker.move(sequence + " ");
  let value = state.containerPhrasing(node3, {
    before: "# ",
    after: "\n",
    ...tracker.current()
  });
  if (/^[\t ]/.test(value)) {
    value = encodeCharacterReference(value.charCodeAt(0)) + value.slice(1);
  }
  value = value ? sequence + " " + value : sequence;
  if (state.options.closeAtx) {
    value += " " + sequence;
  }
  subexit();
  exit3();
  return value;
}

// node_modules/.pnpm/mdast-util-to-markdown@2.1.2/node_modules/mdast-util-to-markdown/lib/handle/html.js
html4.peek = htmlPeek;
function html4(node3) {
  return node3.value || "";
}
function htmlPeek() {
  return "<";
}

// node_modules/.pnpm/mdast-util-to-markdown@2.1.2/node_modules/mdast-util-to-markdown/lib/handle/image.js
image2.peek = imagePeek;
function image2(node3, _, state, info) {
  const quote = checkQuote(state);
  const suffix = quote === '"' ? "Quote" : "Apostrophe";
  const exit3 = state.enter("image");
  let subexit = state.enter("label");
  const tracker = state.createTracker(info);
  let value = tracker.move("![");
  value += tracker.move(
    state.safe(node3.alt, { before: value, after: "]", ...tracker.current() })
  );
  value += tracker.move("](");
  subexit();
  if (
    // If there’s no url but there is a title…
    !node3.url && node3.title || // If there are control characters or whitespace.
    /[\0- \u007F]/.test(node3.url)
  ) {
    subexit = state.enter("destinationLiteral");
    value += tracker.move("<");
    value += tracker.move(
      state.safe(node3.url, { before: value, after: ">", ...tracker.current() })
    );
    value += tracker.move(">");
  } else {
    subexit = state.enter("destinationRaw");
    value += tracker.move(
      state.safe(node3.url, {
        before: value,
        after: node3.title ? " " : ")",
        ...tracker.current()
      })
    );
  }
  subexit();
  if (node3.title) {
    subexit = state.enter(`title${suffix}`);
    value += tracker.move(" " + quote);
    value += tracker.move(
      state.safe(node3.title, {
        before: value,
        after: quote,
        ...tracker.current()
      })
    );
    value += tracker.move(quote);
    subexit();
  }
  value += tracker.move(")");
  exit3();
  return value;
}
function imagePeek() {
  return "!";
}

// node_modules/.pnpm/mdast-util-to-markdown@2.1.2/node_modules/mdast-util-to-markdown/lib/handle/image-reference.js
imageReference2.peek = imageReferencePeek;
function imageReference2(node3, _, state, info) {
  const type = node3.referenceType;
  const exit3 = state.enter("imageReference");
  let subexit = state.enter("label");
  const tracker = state.createTracker(info);
  let value = tracker.move("![");
  const alt = state.safe(node3.alt, {
    before: value,
    after: "]",
    ...tracker.current()
  });
  value += tracker.move(alt + "][");
  subexit();
  const stack = state.stack;
  state.stack = [];
  subexit = state.enter("reference");
  const reference = state.safe(state.associationId(node3), {
    before: value,
    after: "]",
    ...tracker.current()
  });
  subexit();
  state.stack = stack;
  exit3();
  if (type === "full" || !alt || alt !== reference) {
    value += tracker.move(reference + "]");
  } else if (type === "shortcut") {
    value = value.slice(0, -1);
  } else {
    value += tracker.move("]");
  }
  return value;
}
function imageReferencePeek() {
  return "!";
}

// node_modules/.pnpm/mdast-util-to-markdown@2.1.2/node_modules/mdast-util-to-markdown/lib/handle/inline-code.js
inlineCode2.peek = inlineCodePeek;
function inlineCode2(node3, _, state) {
  let value = node3.value || "";
  let sequence = "`";
  let index2 = -1;
  while (new RegExp("(^|[^`])" + sequence + "([^`]|$)").test(value)) {
    sequence += "`";
  }
  if (/[^ \r\n]/.test(value) && (/^[ \r\n]/.test(value) && /[ \r\n]$/.test(value) || /^`|`$/.test(value))) {
    value = " " + value + " ";
  }
  while (++index2 < state.unsafe.length) {
    const pattern = state.unsafe[index2];
    const expression = state.compilePattern(pattern);
    let match;
    if (!pattern.atBreak)
      continue;
    while (match = expression.exec(value)) {
      let position3 = match.index;
      if (value.charCodeAt(position3) === 10 && value.charCodeAt(position3 - 1) === 13) {
        position3--;
      }
      value = value.slice(0, position3) + " " + value.slice(match.index + 1);
    }
  }
  return sequence + value + sequence;
}
function inlineCodePeek() {
  return "`";
}

// node_modules/.pnpm/mdast-util-to-markdown@2.1.2/node_modules/mdast-util-to-markdown/lib/util/format-link-as-autolink.js
function formatLinkAsAutolink(node3, state) {
  const raw = toString2(node3);
  return Boolean(
    !state.options.resourceLink && // If there’s a url…
    node3.url && // And there’s a no title…
    !node3.title && // And the content of `node` is a single text node…
    node3.children && node3.children.length === 1 && node3.children[0].type === "text" && // And if the url is the same as the content…
    (raw === node3.url || "mailto:" + raw === node3.url) && // And that starts w/ a protocol…
    /^[a-z][a-z+.-]+:/i.test(node3.url) && // And that doesn’t contain ASCII control codes (character escapes and
    // references don’t work), space, or angle brackets…
    !/[\0- <>\u007F]/.test(node3.url)
  );
}

// node_modules/.pnpm/mdast-util-to-markdown@2.1.2/node_modules/mdast-util-to-markdown/lib/handle/link.js
link2.peek = linkPeek;
function link2(node3, _, state, info) {
  const quote = checkQuote(state);
  const suffix = quote === '"' ? "Quote" : "Apostrophe";
  const tracker = state.createTracker(info);
  let exit3;
  let subexit;
  if (formatLinkAsAutolink(node3, state)) {
    const stack = state.stack;
    state.stack = [];
    exit3 = state.enter("autolink");
    let value2 = tracker.move("<");
    value2 += tracker.move(
      state.containerPhrasing(node3, {
        before: value2,
        after: ">",
        ...tracker.current()
      })
    );
    value2 += tracker.move(">");
    exit3();
    state.stack = stack;
    return value2;
  }
  exit3 = state.enter("link");
  subexit = state.enter("label");
  let value = tracker.move("[");
  value += tracker.move(
    state.containerPhrasing(node3, {
      before: value,
      after: "](",
      ...tracker.current()
    })
  );
  value += tracker.move("](");
  subexit();
  if (
    // If there’s no url but there is a title…
    !node3.url && node3.title || // If there are control characters or whitespace.
    /[\0- \u007F]/.test(node3.url)
  ) {
    subexit = state.enter("destinationLiteral");
    value += tracker.move("<");
    value += tracker.move(
      state.safe(node3.url, { before: value, after: ">", ...tracker.current() })
    );
    value += tracker.move(">");
  } else {
    subexit = state.enter("destinationRaw");
    value += tracker.move(
      state.safe(node3.url, {
        before: value,
        after: node3.title ? " " : ")",
        ...tracker.current()
      })
    );
  }
  subexit();
  if (node3.title) {
    subexit = state.enter(`title${suffix}`);
    value += tracker.move(" " + quote);
    value += tracker.move(
      state.safe(node3.title, {
        before: value,
        after: quote,
        ...tracker.current()
      })
    );
    value += tracker.move(quote);
    subexit();
  }
  value += tracker.move(")");
  exit3();
  return value;
}
function linkPeek(node3, _, state) {
  return formatLinkAsAutolink(node3, state) ? "<" : "[";
}

// node_modules/.pnpm/mdast-util-to-markdown@2.1.2/node_modules/mdast-util-to-markdown/lib/handle/link-reference.js
linkReference2.peek = linkReferencePeek;
function linkReference2(node3, _, state, info) {
  const type = node3.referenceType;
  const exit3 = state.enter("linkReference");
  let subexit = state.enter("label");
  const tracker = state.createTracker(info);
  let value = tracker.move("[");
  const text6 = state.containerPhrasing(node3, {
    before: value,
    after: "]",
    ...tracker.current()
  });
  value += tracker.move(text6 + "][");
  subexit();
  const stack = state.stack;
  state.stack = [];
  subexit = state.enter("reference");
  const reference = state.safe(state.associationId(node3), {
    before: value,
    after: "]",
    ...tracker.current()
  });
  subexit();
  state.stack = stack;
  exit3();
  if (type === "full" || !text6 || text6 !== reference) {
    value += tracker.move(reference + "]");
  } else if (type === "shortcut") {
    value = value.slice(0, -1);
  } else {
    value += tracker.move("]");
  }
  return value;
}
function linkReferencePeek() {
  return "[";
}

// node_modules/.pnpm/mdast-util-to-markdown@2.1.2/node_modules/mdast-util-to-markdown/lib/util/check-bullet.js
function checkBullet(state) {
  const marker = state.options.bullet || "*";
  if (marker !== "*" && marker !== "+" && marker !== "-") {
    throw new Error(
      "Cannot serialize items with `" + marker + "` for `options.bullet`, expected `*`, `+`, or `-`"
    );
  }
  return marker;
}

// node_modules/.pnpm/mdast-util-to-markdown@2.1.2/node_modules/mdast-util-to-markdown/lib/util/check-bullet-other.js
function checkBulletOther(state) {
  const bullet = checkBullet(state);
  const bulletOther = state.options.bulletOther;
  if (!bulletOther) {
    return bullet === "*" ? "-" : "*";
  }
  if (bulletOther !== "*" && bulletOther !== "+" && bulletOther !== "-") {
    throw new Error(
      "Cannot serialize items with `" + bulletOther + "` for `options.bulletOther`, expected `*`, `+`, or `-`"
    );
  }
  if (bulletOther === bullet) {
    throw new Error(
      "Expected `bullet` (`" + bullet + "`) and `bulletOther` (`" + bulletOther + "`) to be different"
    );
  }
  return bulletOther;
}

// node_modules/.pnpm/mdast-util-to-markdown@2.1.2/node_modules/mdast-util-to-markdown/lib/util/check-bullet-ordered.js
function checkBulletOrdered(state) {
  const marker = state.options.bulletOrdered || ".";
  if (marker !== "." && marker !== ")") {
    throw new Error(
      "Cannot serialize items with `" + marker + "` for `options.bulletOrdered`, expected `.` or `)`"
    );
  }
  return marker;
}

// node_modules/.pnpm/mdast-util-to-markdown@2.1.2/node_modules/mdast-util-to-markdown/lib/util/check-rule.js
function checkRule(state) {
  const marker = state.options.rule || "*";
  if (marker !== "*" && marker !== "-" && marker !== "_") {
    throw new Error(
      "Cannot serialize rules with `" + marker + "` for `options.rule`, expected `*`, `-`, or `_`"
    );
  }
  return marker;
}

// node_modules/.pnpm/mdast-util-to-markdown@2.1.2/node_modules/mdast-util-to-markdown/lib/handle/list.js
function list3(node3, parent, state, info) {
  const exit3 = state.enter("list");
  const bulletCurrent = state.bulletCurrent;
  let bullet = node3.ordered ? checkBulletOrdered(state) : checkBullet(state);
  const bulletOther = node3.ordered ? bullet === "." ? ")" : "." : checkBulletOther(state);
  let useDifferentMarker = parent && state.bulletLastUsed ? bullet === state.bulletLastUsed : false;
  if (!node3.ordered) {
    const firstListItem = node3.children ? node3.children[0] : void 0;
    if (
      // Bullet could be used as a thematic break marker:
      (bullet === "*" || bullet === "-") && // Empty first list item:
      firstListItem && (!firstListItem.children || !firstListItem.children[0]) && // Directly in two other list items:
      state.stack[state.stack.length - 1] === "list" && state.stack[state.stack.length - 2] === "listItem" && state.stack[state.stack.length - 3] === "list" && state.stack[state.stack.length - 4] === "listItem" && // That are each the first child.
      state.indexStack[state.indexStack.length - 1] === 0 && state.indexStack[state.indexStack.length - 2] === 0 && state.indexStack[state.indexStack.length - 3] === 0
    ) {
      useDifferentMarker = true;
    }
    if (checkRule(state) === bullet && firstListItem) {
      let index2 = -1;
      while (++index2 < node3.children.length) {
        const item = node3.children[index2];
        if (item && item.type === "listItem" && item.children && item.children[0] && item.children[0].type === "thematicBreak") {
          useDifferentMarker = true;
          break;
        }
      }
    }
  }
  if (useDifferentMarker) {
    bullet = bulletOther;
  }
  state.bulletCurrent = bullet;
  const value = state.containerFlow(node3, info);
  state.bulletLastUsed = bullet;
  state.bulletCurrent = bulletCurrent;
  exit3();
  return value;
}

// node_modules/.pnpm/mdast-util-to-markdown@2.1.2/node_modules/mdast-util-to-markdown/lib/util/check-list-item-indent.js
function checkListItemIndent(state) {
  const style = state.options.listItemIndent || "one";
  if (style !== "tab" && style !== "one" && style !== "mixed") {
    throw new Error(
      "Cannot serialize items with `" + style + "` for `options.listItemIndent`, expected `tab`, `one`, or `mixed`"
    );
  }
  return style;
}

// node_modules/.pnpm/mdast-util-to-markdown@2.1.2/node_modules/mdast-util-to-markdown/lib/handle/list-item.js
function listItem2(node3, parent, state, info) {
  const listItemIndent = checkListItemIndent(state);
  let bullet = state.bulletCurrent || checkBullet(state);
  if (parent && parent.type === "list" && parent.ordered) {
    bullet = (typeof parent.start === "number" && parent.start > -1 ? parent.start : 1) + (state.options.incrementListMarker === false ? 0 : parent.children.indexOf(node3)) + bullet;
  }
  let size = bullet.length + 1;
  if (listItemIndent === "tab" || listItemIndent === "mixed" && (parent && parent.type === "list" && parent.spread || node3.spread)) {
    size = Math.ceil(size / 4) * 4;
  }
  const tracker = state.createTracker(info);
  tracker.move(bullet + " ".repeat(size - bullet.length));
  tracker.shift(size);
  const exit3 = state.enter("listItem");
  const value = state.indentLines(
    state.containerFlow(node3, tracker.current()),
    map4
  );
  exit3();
  return value;
  function map4(line, index2, blank) {
    if (index2) {
      return (blank ? "" : " ".repeat(size)) + line;
    }
    return (blank ? bullet : bullet + " ".repeat(size - bullet.length)) + line;
  }
}

// node_modules/.pnpm/mdast-util-to-markdown@2.1.2/node_modules/mdast-util-to-markdown/lib/handle/paragraph.js
function paragraph2(node3, _, state, info) {
  const exit3 = state.enter("paragraph");
  const subexit = state.enter("phrasing");
  const value = state.containerPhrasing(node3, info);
  subexit();
  exit3();
  return value;
}

// node_modules/.pnpm/mdast-util-phrasing@4.1.0/node_modules/mdast-util-phrasing/lib/index.js
var phrasing = (
  /** @type {(node?: unknown) => node is Exclude<PhrasingContent, Html>} */
  convert2([
    "break",
    "delete",
    "emphasis",
    // To do: next major: removed since footnotes were added to GFM.
    "footnote",
    "footnoteReference",
    "image",
    "imageReference",
    "inlineCode",
    // Enabled by `mdast-util-math`:
    "inlineMath",
    "link",
    "linkReference",
    // Enabled by `mdast-util-mdx`:
    "mdxJsxTextElement",
    // Enabled by `mdast-util-mdx`:
    "mdxTextExpression",
    "strong",
    "text",
    // Enabled by `mdast-util-directive`:
    "textDirective"
  ])
);

// node_modules/.pnpm/mdast-util-to-markdown@2.1.2/node_modules/mdast-util-to-markdown/lib/handle/root.js
function root2(node3, _, state, info) {
  const hasPhrasing = node3.children.some(function(d) {
    return phrasing(d);
  });
  const container = hasPhrasing ? state.containerPhrasing : state.containerFlow;
  return container.call(state, node3, info);
}

// node_modules/.pnpm/mdast-util-to-markdown@2.1.2/node_modules/mdast-util-to-markdown/lib/util/check-strong.js
function checkStrong(state) {
  const marker = state.options.strong || "*";
  if (marker !== "*" && marker !== "_") {
    throw new Error(
      "Cannot serialize strong with `" + marker + "` for `options.strong`, expected `*`, or `_`"
    );
  }
  return marker;
}

// node_modules/.pnpm/mdast-util-to-markdown@2.1.2/node_modules/mdast-util-to-markdown/lib/handle/strong.js
strong2.peek = strongPeek;
function strong2(node3, _, state, info) {
  const marker = checkStrong(state);
  const exit3 = state.enter("strong");
  const tracker = state.createTracker(info);
  const before = tracker.move(marker + marker);
  let between = tracker.move(
    state.containerPhrasing(node3, {
      after: marker,
      before,
      ...tracker.current()
    })
  );
  const betweenHead = between.charCodeAt(0);
  const open = encodeInfo(
    info.before.charCodeAt(info.before.length - 1),
    betweenHead,
    marker
  );
  if (open.inside) {
    between = encodeCharacterReference(betweenHead) + between.slice(1);
  }
  const betweenTail = between.charCodeAt(between.length - 1);
  const close = encodeInfo(info.after.charCodeAt(0), betweenTail, marker);
  if (close.inside) {
    between = between.slice(0, -1) + encodeCharacterReference(betweenTail);
  }
  const after = tracker.move(marker + marker);
  exit3();
  state.attentionEncodeSurroundingInfo = {
    after: close.outside,
    before: open.outside
  };
  return before + between + after;
}
function strongPeek(_, _1, state) {
  return state.options.strong || "*";
}

// node_modules/.pnpm/mdast-util-to-markdown@2.1.2/node_modules/mdast-util-to-markdown/lib/handle/text.js
function text4(node3, _, state, info) {
  return state.safe(node3.value, info);
}

// node_modules/.pnpm/mdast-util-to-markdown@2.1.2/node_modules/mdast-util-to-markdown/lib/util/check-rule-repetition.js
function checkRuleRepetition(state) {
  const repetition = state.options.ruleRepetition || 3;
  if (repetition < 3) {
    throw new Error(
      "Cannot serialize rules with repetition `" + repetition + "` for `options.ruleRepetition`, expected `3` or more"
    );
  }
  return repetition;
}

// node_modules/.pnpm/mdast-util-to-markdown@2.1.2/node_modules/mdast-util-to-markdown/lib/handle/thematic-break.js
function thematicBreak3(_, _1, state) {
  const value = (checkRule(state) + (state.options.ruleSpaces ? " " : "")).repeat(checkRuleRepetition(state));
  return state.options.ruleSpaces ? value.slice(0, -1) : value;
}

// node_modules/.pnpm/mdast-util-to-markdown@2.1.2/node_modules/mdast-util-to-markdown/lib/handle/index.js
var handle = {
  blockquote: blockquote2,
  break: hardBreak2,
  code: code2,
  definition: definition2,
  emphasis: emphasis2,
  hardBreak: hardBreak2,
  heading: heading2,
  html: html4,
  image: image2,
  imageReference: imageReference2,
  inlineCode: inlineCode2,
  link: link2,
  linkReference: linkReference2,
  list: list3,
  listItem: listItem2,
  paragraph: paragraph2,
  root: root2,
  strong: strong2,
  text: text4,
  thematicBreak: thematicBreak3
};

// node_modules/.pnpm/mdast-util-gfm-table@2.0.0/node_modules/mdast-util-gfm-table/lib/index.js
function gfmTableFromMarkdown() {
  return {
    enter: {
      table: enterTable,
      tableData: enterCell,
      tableHeader: enterCell,
      tableRow: enterRow
    },
    exit: {
      codeText: exitCodeText,
      table: exitTable,
      tableData: exit2,
      tableHeader: exit2,
      tableRow: exit2
    }
  };
}
function enterTable(token) {
  const align = token._align;
  ok2(align, "expected `_align` on table");
  this.enter(
    {
      type: "table",
      align: align.map(function(d) {
        return d === "none" ? null : d;
      }),
      children: []
    },
    token
  );
  this.data.inTable = true;
}
function exitTable(token) {
  this.exit(token);
  this.data.inTable = void 0;
}
function enterRow(token) {
  this.enter({ type: "tableRow", children: [] }, token);
}
function exit2(token) {
  this.exit(token);
}
function enterCell(token) {
  this.enter({ type: "tableCell", children: [] }, token);
}
function exitCodeText(token) {
  let value = this.resume();
  if (this.data.inTable) {
    value = value.replace(/\\([\\|])/g, replace);
  }
  const node3 = this.stack[this.stack.length - 1];
  ok2(node3.type === "inlineCode");
  node3.value = value;
  this.exit(token);
}
function replace($0, $1) {
  return $1 === "|" ? $1 : $0;
}
function gfmTableToMarkdown(options) {
  const settings = options || {};
  const padding = settings.tableCellPadding;
  const alignDelimiters = settings.tablePipeAlign;
  const stringLength = settings.stringLength;
  const around = padding ? " " : "|";
  return {
    unsafe: [
      { character: "\r", inConstruct: "tableCell" },
      { character: "\n", inConstruct: "tableCell" },
      // A pipe, when followed by a tab or space (padding), or a dash or colon
      // (unpadded delimiter row), could result in a table.
      { atBreak: true, character: "|", after: "[	 :-]" },
      // A pipe in a cell must be encoded.
      { character: "|", inConstruct: "tableCell" },
      // A colon must be followed by a dash, in which case it could start a
      // delimiter row.
      { atBreak: true, character: ":", after: "-" },
      // A delimiter row can also start with a dash, when followed by more
      // dashes, a colon, or a pipe.
      // This is a stricter version than the built in check for lists, thematic
      // breaks, and setex heading underlines though:
      // <https://github.com/syntax-tree/mdast-util-to-markdown/blob/51a2038/lib/unsafe.js#L57>
      { atBreak: true, character: "-", after: "[:|-]" }
    ],
    handlers: {
      inlineCode: inlineCodeWithTable,
      table: handleTable,
      tableCell: handleTableCell,
      tableRow: handleTableRow
    }
  };
  function handleTable(node3, _, state, info) {
    return serializeData(handleTableAsData(node3, state, info), node3.align);
  }
  function handleTableRow(node3, _, state, info) {
    const row = handleTableRowAsData(node3, state, info);
    const value = serializeData([row]);
    return value.slice(0, value.indexOf("\n"));
  }
  function handleTableCell(node3, _, state, info) {
    const exit3 = state.enter("tableCell");
    const subexit = state.enter("phrasing");
    const value = state.containerPhrasing(node3, {
      ...info,
      before: around,
      after: around
    });
    subexit();
    exit3();
    return value;
  }
  function serializeData(matrix, align) {
    return markdownTable(matrix, {
      align,
      // @ts-expect-error: `markdown-table` types should support `null`.
      alignDelimiters,
      // @ts-expect-error: `markdown-table` types should support `null`.
      padding,
      // @ts-expect-error: `markdown-table` types should support `null`.
      stringLength
    });
  }
  function handleTableAsData(node3, state, info) {
    const children = node3.children;
    let index2 = -1;
    const result = [];
    const subexit = state.enter("table");
    while (++index2 < children.length) {
      result[index2] = handleTableRowAsData(children[index2], state, info);
    }
    subexit();
    return result;
  }
  function handleTableRowAsData(node3, state, info) {
    const children = node3.children;
    let index2 = -1;
    const result = [];
    const subexit = state.enter("tableRow");
    while (++index2 < children.length) {
      result[index2] = handleTableCell(children[index2], node3, state, info);
    }
    subexit();
    return result;
  }
  function inlineCodeWithTable(node3, parent, state) {
    let value = handle.inlineCode(node3, parent, state);
    if (state.stack.includes("tableCell")) {
      value = value.replace(/\|/g, "\\$&");
    }
    return value;
  }
}

// node_modules/.pnpm/mdast-util-gfm-task-list-item@2.0.0/node_modules/mdast-util-gfm-task-list-item/lib/index.js
function gfmTaskListItemFromMarkdown() {
  return {
    exit: {
      taskListCheckValueChecked: exitCheck,
      taskListCheckValueUnchecked: exitCheck,
      paragraph: exitParagraphWithTaskListItem
    }
  };
}
function gfmTaskListItemToMarkdown() {
  return {
    unsafe: [{ atBreak: true, character: "-", after: "[:|-]" }],
    handlers: { listItem: listItemWithTaskListItem }
  };
}
function exitCheck(token) {
  const node3 = this.stack[this.stack.length - 2];
  ok2(node3.type === "listItem");
  node3.checked = token.type === "taskListCheckValueChecked";
}
function exitParagraphWithTaskListItem(token) {
  const parent = this.stack[this.stack.length - 2];
  if (parent && parent.type === "listItem" && typeof parent.checked === "boolean") {
    const node3 = this.stack[this.stack.length - 1];
    ok2(node3.type === "paragraph");
    const head = node3.children[0];
    if (head && head.type === "text") {
      const siblings = parent.children;
      let index2 = -1;
      let firstParaghraph;
      while (++index2 < siblings.length) {
        const sibling = siblings[index2];
        if (sibling.type === "paragraph") {
          firstParaghraph = sibling;
          break;
        }
      }
      if (firstParaghraph === node3) {
        head.value = head.value.slice(1);
        if (head.value.length === 0) {
          node3.children.shift();
        } else if (node3.position && head.position && typeof head.position.start.offset === "number") {
          head.position.start.column++;
          head.position.start.offset++;
          node3.position.start = Object.assign({}, head.position.start);
        }
      }
    }
  }
  this.exit(token);
}
function listItemWithTaskListItem(node3, parent, state, info) {
  const head = node3.children[0];
  const checkable = typeof node3.checked === "boolean" && head && head.type === "paragraph";
  const checkbox = "[" + (node3.checked ? "x" : " ") + "] ";
  const tracker = state.createTracker(info);
  if (checkable) {
    tracker.move(checkbox);
  }
  let value = handle.listItem(node3, parent, state, {
    ...info,
    ...tracker.current()
  });
  if (checkable) {
    value = value.replace(/^(?:[*+-]|\d+\.)([\r\n]| {1,3})/, check);
  }
  return value;
  function check($0) {
    return $0 + checkbox;
  }
}

// node_modules/.pnpm/mdast-util-gfm@3.0.0/node_modules/mdast-util-gfm/lib/index.js
function gfmFromMarkdown() {
  return [
    gfmAutolinkLiteralFromMarkdown(),
    gfmFootnoteFromMarkdown(),
    gfmStrikethroughFromMarkdown(),
    gfmTableFromMarkdown(),
    gfmTaskListItemFromMarkdown()
  ];
}
function gfmToMarkdown(options) {
  return {
    extensions: [
      gfmAutolinkLiteralToMarkdown(),
      gfmFootnoteToMarkdown(),
      gfmStrikethroughToMarkdown(),
      gfmTableToMarkdown(options),
      gfmTaskListItemToMarkdown()
    ]
  };
}

// node_modules/.pnpm/micromark-util-chunked@2.0.1/node_modules/micromark-util-chunked/index.js
function splice2(list4, start, remove, items) {
  const end = list4.length;
  let chunkStart = 0;
  let parameters;
  if (start < 0) {
    start = -start > end ? 0 : end + start;
  } else {
    start = start > end ? end : start;
  }
  remove = remove > 0 ? remove : 0;
  if (items.length < 1e4) {
    parameters = Array.from(items);
    parameters.unshift(start, remove);
    list4.splice(...parameters);
  } else {
    if (remove)
      list4.splice(start, remove);
    while (chunkStart < items.length) {
      parameters = items.slice(chunkStart, chunkStart + 1e4);
      parameters.unshift(start, 0);
      list4.splice(...parameters);
      chunkStart += 1e4;
      start += 1e4;
    }
  }
}

// node_modules/.pnpm/micromark-util-combine-extensions@2.0.1/node_modules/micromark-util-combine-extensions/index.js
var hasOwnProperty2 = {}.hasOwnProperty;
function combineExtensions2(extensions) {
  const all4 = {};
  let index2 = -1;
  while (++index2 < extensions.length) {
    syntaxExtension2(all4, extensions[index2]);
  }
  return all4;
}
function syntaxExtension2(all4, extension2) {
  let hook;
  for (hook in extension2) {
    const maybe = hasOwnProperty2.call(all4, hook) ? all4[hook] : void 0;
    const left = maybe || (all4[hook] = {});
    const right = extension2[hook];
    let code4;
    if (right) {
      for (code4 in right) {
        if (!hasOwnProperty2.call(left, code4))
          left[code4] = [];
        const value = right[code4];
        constructs2(
          // @ts-expect-error Looks like a list.
          left[code4],
          Array.isArray(value) ? value : value ? [value] : []
        );
      }
    }
  }
}
function constructs2(existing, list4) {
  let index2 = -1;
  const before = [];
  while (++index2 < list4.length) {
    ;
    (list4[index2].add === "after" ? existing : before).push(list4[index2]);
  }
  splice2(existing, 0, 0, before);
}

// node_modules/.pnpm/micromark-extension-gfm-autolink-literal@2.1.0/node_modules/micromark-extension-gfm-autolink-literal/lib/syntax.js
var wwwPrefix = {
  tokenize: tokenizeWwwPrefix,
  partial: true
};
var domain = {
  tokenize: tokenizeDomain,
  partial: true
};
var path2 = {
  tokenize: tokenizePath,
  partial: true
};
var trail = {
  tokenize: tokenizeTrail,
  partial: true
};
var emailDomainDotTrail = {
  tokenize: tokenizeEmailDomainDotTrail,
  partial: true
};
var wwwAutolink = {
  name: "wwwAutolink",
  tokenize: tokenizeWwwAutolink,
  previous: previousWww
};
var protocolAutolink = {
  name: "protocolAutolink",
  tokenize: tokenizeProtocolAutolink,
  previous: previousProtocol
};
var emailAutolink = {
  name: "emailAutolink",
  tokenize: tokenizeEmailAutolink,
  previous: previousEmail
};
var text5 = {};
function gfmAutolinkLiteral() {
  return {
    text: text5
  };
}
var code3 = 48;
while (code3 < 123) {
  text5[code3] = emailAutolink;
  code3++;
  if (code3 === 58)
    code3 = 65;
  else if (code3 === 91)
    code3 = 97;
}
text5[43] = emailAutolink;
text5[45] = emailAutolink;
text5[46] = emailAutolink;
text5[95] = emailAutolink;
text5[72] = [emailAutolink, protocolAutolink];
text5[104] = [emailAutolink, protocolAutolink];
text5[87] = [emailAutolink, wwwAutolink];
text5[119] = [emailAutolink, wwwAutolink];
function tokenizeEmailAutolink(effects, ok4, nok) {
  const self = this;
  let dot;
  let data;
  return start;
  function start(code4) {
    if (!gfmAtext(code4) || !previousEmail.call(self, self.previous) || previousUnbalanced(self.events)) {
      return nok(code4);
    }
    effects.enter("literalAutolink");
    effects.enter("literalAutolinkEmail");
    return atext(code4);
  }
  function atext(code4) {
    if (gfmAtext(code4)) {
      effects.consume(code4);
      return atext;
    }
    if (code4 === 64) {
      effects.consume(code4);
      return emailDomain;
    }
    return nok(code4);
  }
  function emailDomain(code4) {
    if (code4 === 46) {
      return effects.check(emailDomainDotTrail, emailDomainAfter, emailDomainDot)(code4);
    }
    if (code4 === 45 || code4 === 95 || asciiAlphanumeric2(code4)) {
      data = true;
      effects.consume(code4);
      return emailDomain;
    }
    return emailDomainAfter(code4);
  }
  function emailDomainDot(code4) {
    effects.consume(code4);
    dot = true;
    return emailDomain;
  }
  function emailDomainAfter(code4) {
    if (data && dot && asciiAlpha2(self.previous)) {
      effects.exit("literalAutolinkEmail");
      effects.exit("literalAutolink");
      return ok4(code4);
    }
    return nok(code4);
  }
}
function tokenizeWwwAutolink(effects, ok4, nok) {
  const self = this;
  return wwwStart;
  function wwwStart(code4) {
    if (code4 !== 87 && code4 !== 119 || !previousWww.call(self, self.previous) || previousUnbalanced(self.events)) {
      return nok(code4);
    }
    effects.enter("literalAutolink");
    effects.enter("literalAutolinkWww");
    return effects.check(wwwPrefix, effects.attempt(domain, effects.attempt(path2, wwwAfter), nok), nok)(code4);
  }
  function wwwAfter(code4) {
    effects.exit("literalAutolinkWww");
    effects.exit("literalAutolink");
    return ok4(code4);
  }
}
function tokenizeProtocolAutolink(effects, ok4, nok) {
  const self = this;
  let buffer2 = "";
  let seen = false;
  return protocolStart;
  function protocolStart(code4) {
    if ((code4 === 72 || code4 === 104) && previousProtocol.call(self, self.previous) && !previousUnbalanced(self.events)) {
      effects.enter("literalAutolink");
      effects.enter("literalAutolinkHttp");
      buffer2 += String.fromCodePoint(code4);
      effects.consume(code4);
      return protocolPrefixInside;
    }
    return nok(code4);
  }
  function protocolPrefixInside(code4) {
    if (asciiAlpha2(code4) && buffer2.length < 5) {
      buffer2 += String.fromCodePoint(code4);
      effects.consume(code4);
      return protocolPrefixInside;
    }
    if (code4 === 58) {
      const protocol = buffer2.toLowerCase();
      if (protocol === "http" || protocol === "https") {
        effects.consume(code4);
        return protocolSlashesInside;
      }
    }
    return nok(code4);
  }
  function protocolSlashesInside(code4) {
    if (code4 === 47) {
      effects.consume(code4);
      if (seen) {
        return afterProtocol;
      }
      seen = true;
      return protocolSlashesInside;
    }
    return nok(code4);
  }
  function afterProtocol(code4) {
    return code4 === null || asciiControl2(code4) || markdownLineEndingOrSpace2(code4) || unicodeWhitespace2(code4) || unicodePunctuation2(code4) ? nok(code4) : effects.attempt(domain, effects.attempt(path2, protocolAfter), nok)(code4);
  }
  function protocolAfter(code4) {
    effects.exit("literalAutolinkHttp");
    effects.exit("literalAutolink");
    return ok4(code4);
  }
}
function tokenizeWwwPrefix(effects, ok4, nok) {
  let size = 0;
  return wwwPrefixInside;
  function wwwPrefixInside(code4) {
    if ((code4 === 87 || code4 === 119) && size < 3) {
      size++;
      effects.consume(code4);
      return wwwPrefixInside;
    }
    if (code4 === 46 && size === 3) {
      effects.consume(code4);
      return wwwPrefixAfter;
    }
    return nok(code4);
  }
  function wwwPrefixAfter(code4) {
    return code4 === null ? nok(code4) : ok4(code4);
  }
}
function tokenizeDomain(effects, ok4, nok) {
  let underscoreInLastSegment;
  let underscoreInLastLastSegment;
  let seen;
  return domainInside;
  function domainInside(code4) {
    if (code4 === 46 || code4 === 95) {
      return effects.check(trail, domainAfter, domainAtPunctuation)(code4);
    }
    if (code4 === null || markdownLineEndingOrSpace2(code4) || unicodeWhitespace2(code4) || code4 !== 45 && unicodePunctuation2(code4)) {
      return domainAfter(code4);
    }
    seen = true;
    effects.consume(code4);
    return domainInside;
  }
  function domainAtPunctuation(code4) {
    if (code4 === 95) {
      underscoreInLastSegment = true;
    } else {
      underscoreInLastLastSegment = underscoreInLastSegment;
      underscoreInLastSegment = void 0;
    }
    effects.consume(code4);
    return domainInside;
  }
  function domainAfter(code4) {
    if (underscoreInLastLastSegment || underscoreInLastSegment || !seen) {
      return nok(code4);
    }
    return ok4(code4);
  }
}
function tokenizePath(effects, ok4) {
  let sizeOpen = 0;
  let sizeClose = 0;
  return pathInside;
  function pathInside(code4) {
    if (code4 === 40) {
      sizeOpen++;
      effects.consume(code4);
      return pathInside;
    }
    if (code4 === 41 && sizeClose < sizeOpen) {
      return pathAtPunctuation(code4);
    }
    if (code4 === 33 || code4 === 34 || code4 === 38 || code4 === 39 || code4 === 41 || code4 === 42 || code4 === 44 || code4 === 46 || code4 === 58 || code4 === 59 || code4 === 60 || code4 === 63 || code4 === 93 || code4 === 95 || code4 === 126) {
      return effects.check(trail, ok4, pathAtPunctuation)(code4);
    }
    if (code4 === null || markdownLineEndingOrSpace2(code4) || unicodeWhitespace2(code4)) {
      return ok4(code4);
    }
    effects.consume(code4);
    return pathInside;
  }
  function pathAtPunctuation(code4) {
    if (code4 === 41) {
      sizeClose++;
    }
    effects.consume(code4);
    return pathInside;
  }
}
function tokenizeTrail(effects, ok4, nok) {
  return trail2;
  function trail2(code4) {
    if (code4 === 33 || code4 === 34 || code4 === 39 || code4 === 41 || code4 === 42 || code4 === 44 || code4 === 46 || code4 === 58 || code4 === 59 || code4 === 63 || code4 === 95 || code4 === 126) {
      effects.consume(code4);
      return trail2;
    }
    if (code4 === 38) {
      effects.consume(code4);
      return trailCharacterReferenceStart;
    }
    if (code4 === 93) {
      effects.consume(code4);
      return trailBracketAfter;
    }
    if (
      // `<` is an end.
      code4 === 60 || // So is whitespace.
      code4 === null || markdownLineEndingOrSpace2(code4) || unicodeWhitespace2(code4)
    ) {
      return ok4(code4);
    }
    return nok(code4);
  }
  function trailBracketAfter(code4) {
    if (code4 === null || code4 === 40 || code4 === 91 || markdownLineEndingOrSpace2(code4) || unicodeWhitespace2(code4)) {
      return ok4(code4);
    }
    return trail2(code4);
  }
  function trailCharacterReferenceStart(code4) {
    return asciiAlpha2(code4) ? trailCharacterReferenceInside(code4) : nok(code4);
  }
  function trailCharacterReferenceInside(code4) {
    if (code4 === 59) {
      effects.consume(code4);
      return trail2;
    }
    if (asciiAlpha2(code4)) {
      effects.consume(code4);
      return trailCharacterReferenceInside;
    }
    return nok(code4);
  }
}
function tokenizeEmailDomainDotTrail(effects, ok4, nok) {
  return start;
  function start(code4) {
    effects.consume(code4);
    return after;
  }
  function after(code4) {
    return asciiAlphanumeric2(code4) ? nok(code4) : ok4(code4);
  }
}
function previousWww(code4) {
  return code4 === null || code4 === 40 || code4 === 42 || code4 === 95 || code4 === 91 || code4 === 93 || code4 === 126 || markdownLineEndingOrSpace2(code4);
}
function previousProtocol(code4) {
  return !asciiAlpha2(code4);
}
function previousEmail(code4) {
  return !(code4 === 47 || gfmAtext(code4));
}
function gfmAtext(code4) {
  return code4 === 43 || code4 === 45 || code4 === 46 || code4 === 95 || asciiAlphanumeric2(code4);
}
function previousUnbalanced(events) {
  let index2 = events.length;
  let result = false;
  while (index2--) {
    const token = events[index2][1];
    if ((token.type === "labelLink" || token.type === "labelImage") && !token._balanced) {
      result = true;
      break;
    }
    if (token._gfmAutolinkLiteralWalkedInto) {
      result = false;
      break;
    }
  }
  if (events.length > 0 && !result) {
    events[events.length - 1][1]._gfmAutolinkLiteralWalkedInto = true;
  }
  return result;
}

// node_modules/.pnpm/micromark-util-resolve-all@2.0.1/node_modules/micromark-util-resolve-all/index.js
function resolveAll2(constructs3, events, context) {
  const called = [];
  let index2 = -1;
  while (++index2 < constructs3.length) {
    const resolve = constructs3[index2].resolveAll;
    if (resolve && !called.includes(resolve)) {
      events = resolve(events, context);
      called.push(resolve);
    }
  }
  return events;
}

// node_modules/.pnpm/micromark-factory-space@2.0.1/node_modules/micromark-factory-space/index.js
function factorySpace2(effects, ok4, type, max) {
  const limit = max ? max - 1 : Number.POSITIVE_INFINITY;
  let size = 0;
  return start;
  function start(code4) {
    if (markdownSpace2(code4)) {
      effects.enter(type);
      return prefix(code4);
    }
    return ok4(code4);
  }
  function prefix(code4) {
    if (markdownSpace2(code4) && size++ < limit) {
      effects.consume(code4);
      return prefix;
    }
    effects.exit(type);
    return ok4(code4);
  }
}

// node_modules/.pnpm/micromark-core-commonmark@2.0.2/node_modules/micromark-core-commonmark/lib/blank-line.js
var blankLine2 = {
  partial: true,
  tokenize: tokenizeBlankLine2
};
function tokenizeBlankLine2(effects, ok4, nok) {
  return start;
  function start(code4) {
    return markdownSpace2(code4) ? factorySpace2(effects, after, "linePrefix")(code4) : after(code4);
  }
  function after(code4) {
    return code4 === null || markdownLineEnding2(code4) ? ok4(code4) : nok(code4);
  }
}

// node_modules/.pnpm/micromark-extension-gfm-footnote@2.1.0/node_modules/micromark-extension-gfm-footnote/lib/syntax.js
var indent = {
  tokenize: tokenizeIndent2,
  partial: true
};
function gfmFootnote() {
  return {
    document: {
      [91]: {
        name: "gfmFootnoteDefinition",
        tokenize: tokenizeDefinitionStart,
        continuation: {
          tokenize: tokenizeDefinitionContinuation
        },
        exit: gfmFootnoteDefinitionEnd
      }
    },
    text: {
      [91]: {
        name: "gfmFootnoteCall",
        tokenize: tokenizeGfmFootnoteCall
      },
      [93]: {
        name: "gfmPotentialFootnoteCall",
        add: "after",
        tokenize: tokenizePotentialGfmFootnoteCall,
        resolveTo: resolveToPotentialGfmFootnoteCall
      }
    }
  };
}
function tokenizePotentialGfmFootnoteCall(effects, ok4, nok) {
  const self = this;
  let index2 = self.events.length;
  const defined = self.parser.gfmFootnotes || (self.parser.gfmFootnotes = []);
  let labelStart;
  while (index2--) {
    const token = self.events[index2][1];
    if (token.type === "labelImage") {
      labelStart = token;
      break;
    }
    if (token.type === "gfmFootnoteCall" || token.type === "labelLink" || token.type === "label" || token.type === "image" || token.type === "link") {
      break;
    }
  }
  return start;
  function start(code4) {
    if (!labelStart || !labelStart._balanced) {
      return nok(code4);
    }
    const id = normalizeIdentifier2(self.sliceSerialize({
      start: labelStart.end,
      end: self.now()
    }));
    if (id.codePointAt(0) !== 94 || !defined.includes(id.slice(1))) {
      return nok(code4);
    }
    effects.enter("gfmFootnoteCallLabelMarker");
    effects.consume(code4);
    effects.exit("gfmFootnoteCallLabelMarker");
    return ok4(code4);
  }
}
function resolveToPotentialGfmFootnoteCall(events, context) {
  let index2 = events.length;
  let labelStart;
  while (index2--) {
    if (events[index2][1].type === "labelImage" && events[index2][0] === "enter") {
      labelStart = events[index2][1];
      break;
    }
  }
  events[index2 + 1][1].type = "data";
  events[index2 + 3][1].type = "gfmFootnoteCallLabelMarker";
  const call = {
    type: "gfmFootnoteCall",
    start: Object.assign({}, events[index2 + 3][1].start),
    end: Object.assign({}, events[events.length - 1][1].end)
  };
  const marker = {
    type: "gfmFootnoteCallMarker",
    start: Object.assign({}, events[index2 + 3][1].end),
    end: Object.assign({}, events[index2 + 3][1].end)
  };
  marker.end.column++;
  marker.end.offset++;
  marker.end._bufferIndex++;
  const string3 = {
    type: "gfmFootnoteCallString",
    start: Object.assign({}, marker.end),
    end: Object.assign({}, events[events.length - 1][1].start)
  };
  const chunk = {
    type: "chunkString",
    contentType: "string",
    start: Object.assign({}, string3.start),
    end: Object.assign({}, string3.end)
  };
  const replacement = [
    // Take the `labelImageMarker` (now `data`, the `!`)
    events[index2 + 1],
    events[index2 + 2],
    ["enter", call, context],
    // The `[`
    events[index2 + 3],
    events[index2 + 4],
    // The `^`.
    ["enter", marker, context],
    ["exit", marker, context],
    // Everything in between.
    ["enter", string3, context],
    ["enter", chunk, context],
    ["exit", chunk, context],
    ["exit", string3, context],
    // The ending (`]`, properly parsed and labelled).
    events[events.length - 2],
    events[events.length - 1],
    ["exit", call, context]
  ];
  events.splice(index2, events.length - index2 + 1, ...replacement);
  return events;
}
function tokenizeGfmFootnoteCall(effects, ok4, nok) {
  const self = this;
  const defined = self.parser.gfmFootnotes || (self.parser.gfmFootnotes = []);
  let size = 0;
  let data;
  return start;
  function start(code4) {
    effects.enter("gfmFootnoteCall");
    effects.enter("gfmFootnoteCallLabelMarker");
    effects.consume(code4);
    effects.exit("gfmFootnoteCallLabelMarker");
    return callStart;
  }
  function callStart(code4) {
    if (code4 !== 94)
      return nok(code4);
    effects.enter("gfmFootnoteCallMarker");
    effects.consume(code4);
    effects.exit("gfmFootnoteCallMarker");
    effects.enter("gfmFootnoteCallString");
    effects.enter("chunkString").contentType = "string";
    return callData;
  }
  function callData(code4) {
    if (
      // Too long.
      size > 999 || // Closing brace with nothing.
      code4 === 93 && !data || // Space or tab is not supported by GFM for some reason.
      // `\n` and `[` not being supported makes sense.
      code4 === null || code4 === 91 || markdownLineEndingOrSpace2(code4)
    ) {
      return nok(code4);
    }
    if (code4 === 93) {
      effects.exit("chunkString");
      const token = effects.exit("gfmFootnoteCallString");
      if (!defined.includes(normalizeIdentifier2(self.sliceSerialize(token)))) {
        return nok(code4);
      }
      effects.enter("gfmFootnoteCallLabelMarker");
      effects.consume(code4);
      effects.exit("gfmFootnoteCallLabelMarker");
      effects.exit("gfmFootnoteCall");
      return ok4;
    }
    if (!markdownLineEndingOrSpace2(code4)) {
      data = true;
    }
    size++;
    effects.consume(code4);
    return code4 === 92 ? callEscape : callData;
  }
  function callEscape(code4) {
    if (code4 === 91 || code4 === 92 || code4 === 93) {
      effects.consume(code4);
      size++;
      return callData;
    }
    return callData(code4);
  }
}
function tokenizeDefinitionStart(effects, ok4, nok) {
  const self = this;
  const defined = self.parser.gfmFootnotes || (self.parser.gfmFootnotes = []);
  let identifier;
  let size = 0;
  let data;
  return start;
  function start(code4) {
    effects.enter("gfmFootnoteDefinition")._container = true;
    effects.enter("gfmFootnoteDefinitionLabel");
    effects.enter("gfmFootnoteDefinitionLabelMarker");
    effects.consume(code4);
    effects.exit("gfmFootnoteDefinitionLabelMarker");
    return labelAtMarker;
  }
  function labelAtMarker(code4) {
    if (code4 === 94) {
      effects.enter("gfmFootnoteDefinitionMarker");
      effects.consume(code4);
      effects.exit("gfmFootnoteDefinitionMarker");
      effects.enter("gfmFootnoteDefinitionLabelString");
      effects.enter("chunkString").contentType = "string";
      return labelInside;
    }
    return nok(code4);
  }
  function labelInside(code4) {
    if (
      // Too long.
      size > 999 || // Closing brace with nothing.
      code4 === 93 && !data || // Space or tab is not supported by GFM for some reason.
      // `\n` and `[` not being supported makes sense.
      code4 === null || code4 === 91 || markdownLineEndingOrSpace2(code4)
    ) {
      return nok(code4);
    }
    if (code4 === 93) {
      effects.exit("chunkString");
      const token = effects.exit("gfmFootnoteDefinitionLabelString");
      identifier = normalizeIdentifier2(self.sliceSerialize(token));
      effects.enter("gfmFootnoteDefinitionLabelMarker");
      effects.consume(code4);
      effects.exit("gfmFootnoteDefinitionLabelMarker");
      effects.exit("gfmFootnoteDefinitionLabel");
      return labelAfter;
    }
    if (!markdownLineEndingOrSpace2(code4)) {
      data = true;
    }
    size++;
    effects.consume(code4);
    return code4 === 92 ? labelEscape : labelInside;
  }
  function labelEscape(code4) {
    if (code4 === 91 || code4 === 92 || code4 === 93) {
      effects.consume(code4);
      size++;
      return labelInside;
    }
    return labelInside(code4);
  }
  function labelAfter(code4) {
    if (code4 === 58) {
      effects.enter("definitionMarker");
      effects.consume(code4);
      effects.exit("definitionMarker");
      if (!defined.includes(identifier)) {
        defined.push(identifier);
      }
      return factorySpace2(effects, whitespaceAfter, "gfmFootnoteDefinitionWhitespace");
    }
    return nok(code4);
  }
  function whitespaceAfter(code4) {
    return ok4(code4);
  }
}
function tokenizeDefinitionContinuation(effects, ok4, nok) {
  return effects.check(blankLine2, ok4, effects.attempt(indent, ok4, nok));
}
function gfmFootnoteDefinitionEnd(effects) {
  effects.exit("gfmFootnoteDefinition");
}
function tokenizeIndent2(effects, ok4, nok) {
  const self = this;
  return factorySpace2(effects, afterPrefix, "gfmFootnoteDefinitionIndent", 4 + 1);
  function afterPrefix(code4) {
    const tail = self.events[self.events.length - 1];
    return tail && tail[1].type === "gfmFootnoteDefinitionIndent" && tail[2].sliceSerialize(tail[1], true).length === 4 ? ok4(code4) : nok(code4);
  }
}

// node_modules/.pnpm/micromark-extension-gfm-strikethrough@2.1.0/node_modules/micromark-extension-gfm-strikethrough/lib/syntax.js
function gfmStrikethrough(options) {
  const options_ = options || {};
  let single = options_.singleTilde;
  const tokenizer = {
    name: "strikethrough",
    tokenize: tokenizeStrikethrough,
    resolveAll: resolveAllStrikethrough
  };
  if (single === null || single === void 0) {
    single = true;
  }
  return {
    text: {
      [126]: tokenizer
    },
    insideSpan: {
      null: [tokenizer]
    },
    attentionMarkers: {
      null: [126]
    }
  };
  function resolveAllStrikethrough(events, context) {
    let index2 = -1;
    while (++index2 < events.length) {
      if (events[index2][0] === "enter" && events[index2][1].type === "strikethroughSequenceTemporary" && events[index2][1]._close) {
        let open = index2;
        while (open--) {
          if (events[open][0] === "exit" && events[open][1].type === "strikethroughSequenceTemporary" && events[open][1]._open && // If the sizes are the same:
          events[index2][1].end.offset - events[index2][1].start.offset === events[open][1].end.offset - events[open][1].start.offset) {
            events[index2][1].type = "strikethroughSequence";
            events[open][1].type = "strikethroughSequence";
            const strikethrough2 = {
              type: "strikethrough",
              start: Object.assign({}, events[open][1].start),
              end: Object.assign({}, events[index2][1].end)
            };
            const text6 = {
              type: "strikethroughText",
              start: Object.assign({}, events[open][1].end),
              end: Object.assign({}, events[index2][1].start)
            };
            const nextEvents = [["enter", strikethrough2, context], ["enter", events[open][1], context], ["exit", events[open][1], context], ["enter", text6, context]];
            const insideSpan2 = context.parser.constructs.insideSpan.null;
            if (insideSpan2) {
              splice2(nextEvents, nextEvents.length, 0, resolveAll2(insideSpan2, events.slice(open + 1, index2), context));
            }
            splice2(nextEvents, nextEvents.length, 0, [["exit", text6, context], ["enter", events[index2][1], context], ["exit", events[index2][1], context], ["exit", strikethrough2, context]]);
            splice2(events, open - 1, index2 - open + 3, nextEvents);
            index2 = open + nextEvents.length - 2;
            break;
          }
        }
      }
    }
    index2 = -1;
    while (++index2 < events.length) {
      if (events[index2][1].type === "strikethroughSequenceTemporary") {
        events[index2][1].type = "data";
      }
    }
    return events;
  }
  function tokenizeStrikethrough(effects, ok4, nok) {
    const previous3 = this.previous;
    const events = this.events;
    let size = 0;
    return start;
    function start(code4) {
      if (previous3 === 126 && events[events.length - 1][1].type !== "characterEscape") {
        return nok(code4);
      }
      effects.enter("strikethroughSequenceTemporary");
      return more(code4);
    }
    function more(code4) {
      const before = classifyCharacter2(previous3);
      if (code4 === 126) {
        if (size > 1)
          return nok(code4);
        effects.consume(code4);
        size++;
        return more;
      }
      if (size < 2 && !single)
        return nok(code4);
      const token = effects.exit("strikethroughSequenceTemporary");
      const after = classifyCharacter2(code4);
      token._open = !after || after === 2 && Boolean(before);
      token._close = !before || before === 2 && Boolean(after);
      return ok4(code4);
    }
  }
}

// node_modules/.pnpm/micromark-extension-gfm-table@2.1.1/node_modules/micromark-extension-gfm-table/lib/edit-map.js
var EditMap = class {
  /**
   * Create a new edit map.
   */
  constructor() {
    this.map = [];
  }
  /**
   * Create an edit: a remove and/or add at a certain place.
   *
   * @param {number} index
   * @param {number} remove
   * @param {Array<Event>} add
   * @returns {undefined}
   */
  add(index2, remove, add) {
    addImplementation(this, index2, remove, add);
  }
  // To do: add this when moving to `micromark`.
  // /**
  //  * Create an edit: but insert `add` before existing additions.
  //  *
  //  * @param {number} index
  //  * @param {number} remove
  //  * @param {Array<Event>} add
  //  * @returns {undefined}
  //  */
  // addBefore(index, remove, add) {
  //   addImplementation(this, index, remove, add, true)
  // }
  /**
   * Done, change the events.
   *
   * @param {Array<Event>} events
   * @returns {undefined}
   */
  consume(events) {
    this.map.sort(function(a, b) {
      return a[0] - b[0];
    });
    if (this.map.length === 0) {
      return;
    }
    let index2 = this.map.length;
    const vecs = [];
    while (index2 > 0) {
      index2 -= 1;
      vecs.push(events.slice(this.map[index2][0] + this.map[index2][1]), this.map[index2][2]);
      events.length = this.map[index2][0];
    }
    vecs.push(events.slice());
    events.length = 0;
    let slice = vecs.pop();
    while (slice) {
      for (const element2 of slice) {
        events.push(element2);
      }
      slice = vecs.pop();
    }
    this.map.length = 0;
  }
};
function addImplementation(editMap, at, remove, add) {
  let index2 = 0;
  if (remove === 0 && add.length === 0) {
    return;
  }
  while (index2 < editMap.map.length) {
    if (editMap.map[index2][0] === at) {
      editMap.map[index2][1] += remove;
      editMap.map[index2][2].push(...add);
      return;
    }
    index2 += 1;
  }
  editMap.map.push([at, remove, add]);
}

// node_modules/.pnpm/micromark-extension-gfm-table@2.1.1/node_modules/micromark-extension-gfm-table/lib/infer.js
function gfmTableAlign(events, index2) {
  let inDelimiterRow = false;
  const align = [];
  while (index2 < events.length) {
    const event = events[index2];
    if (inDelimiterRow) {
      if (event[0] === "enter") {
        if (event[1].type === "tableContent") {
          align.push(events[index2 + 1][1].type === "tableDelimiterMarker" ? "left" : "none");
        }
      } else if (event[1].type === "tableContent") {
        if (events[index2 - 1][1].type === "tableDelimiterMarker") {
          const alignIndex = align.length - 1;
          align[alignIndex] = align[alignIndex] === "left" ? "center" : "right";
        }
      } else if (event[1].type === "tableDelimiterRow") {
        break;
      }
    } else if (event[0] === "enter" && event[1].type === "tableDelimiterRow") {
      inDelimiterRow = true;
    }
    index2 += 1;
  }
  return align;
}

// node_modules/.pnpm/micromark-extension-gfm-table@2.1.1/node_modules/micromark-extension-gfm-table/lib/syntax.js
function gfmTable() {
  return {
    flow: {
      null: {
        name: "table",
        tokenize: tokenizeTable,
        resolveAll: resolveTable
      }
    }
  };
}
function tokenizeTable(effects, ok4, nok) {
  const self = this;
  let size = 0;
  let sizeB = 0;
  let seen;
  return start;
  function start(code4) {
    let index2 = self.events.length - 1;
    while (index2 > -1) {
      const type = self.events[index2][1].type;
      if (type === "lineEnding" || // Note: markdown-rs uses `whitespace` instead of `linePrefix`
      type === "linePrefix")
        index2--;
      else
        break;
    }
    const tail = index2 > -1 ? self.events[index2][1].type : null;
    const next = tail === "tableHead" || tail === "tableRow" ? bodyRowStart : headRowBefore;
    if (next === bodyRowStart && self.parser.lazy[self.now().line]) {
      return nok(code4);
    }
    return next(code4);
  }
  function headRowBefore(code4) {
    effects.enter("tableHead");
    effects.enter("tableRow");
    return headRowStart(code4);
  }
  function headRowStart(code4) {
    if (code4 === 124) {
      return headRowBreak(code4);
    }
    seen = true;
    sizeB += 1;
    return headRowBreak(code4);
  }
  function headRowBreak(code4) {
    if (code4 === null) {
      return nok(code4);
    }
    if (markdownLineEnding2(code4)) {
      if (sizeB > 1) {
        sizeB = 0;
        self.interrupt = true;
        effects.exit("tableRow");
        effects.enter("lineEnding");
        effects.consume(code4);
        effects.exit("lineEnding");
        return headDelimiterStart;
      }
      return nok(code4);
    }
    if (markdownSpace2(code4)) {
      return factorySpace2(effects, headRowBreak, "whitespace")(code4);
    }
    sizeB += 1;
    if (seen) {
      seen = false;
      size += 1;
    }
    if (code4 === 124) {
      effects.enter("tableCellDivider");
      effects.consume(code4);
      effects.exit("tableCellDivider");
      seen = true;
      return headRowBreak;
    }
    effects.enter("data");
    return headRowData(code4);
  }
  function headRowData(code4) {
    if (code4 === null || code4 === 124 || markdownLineEndingOrSpace2(code4)) {
      effects.exit("data");
      return headRowBreak(code4);
    }
    effects.consume(code4);
    return code4 === 92 ? headRowEscape : headRowData;
  }
  function headRowEscape(code4) {
    if (code4 === 92 || code4 === 124) {
      effects.consume(code4);
      return headRowData;
    }
    return headRowData(code4);
  }
  function headDelimiterStart(code4) {
    self.interrupt = false;
    if (self.parser.lazy[self.now().line]) {
      return nok(code4);
    }
    effects.enter("tableDelimiterRow");
    seen = false;
    if (markdownSpace2(code4)) {
      return factorySpace2(effects, headDelimiterBefore, "linePrefix", self.parser.constructs.disable.null.includes("codeIndented") ? void 0 : 4)(code4);
    }
    return headDelimiterBefore(code4);
  }
  function headDelimiterBefore(code4) {
    if (code4 === 45 || code4 === 58) {
      return headDelimiterValueBefore(code4);
    }
    if (code4 === 124) {
      seen = true;
      effects.enter("tableCellDivider");
      effects.consume(code4);
      effects.exit("tableCellDivider");
      return headDelimiterCellBefore;
    }
    return headDelimiterNok(code4);
  }
  function headDelimiterCellBefore(code4) {
    if (markdownSpace2(code4)) {
      return factorySpace2(effects, headDelimiterValueBefore, "whitespace")(code4);
    }
    return headDelimiterValueBefore(code4);
  }
  function headDelimiterValueBefore(code4) {
    if (code4 === 58) {
      sizeB += 1;
      seen = true;
      effects.enter("tableDelimiterMarker");
      effects.consume(code4);
      effects.exit("tableDelimiterMarker");
      return headDelimiterLeftAlignmentAfter;
    }
    if (code4 === 45) {
      sizeB += 1;
      return headDelimiterLeftAlignmentAfter(code4);
    }
    if (code4 === null || markdownLineEnding2(code4)) {
      return headDelimiterCellAfter(code4);
    }
    return headDelimiterNok(code4);
  }
  function headDelimiterLeftAlignmentAfter(code4) {
    if (code4 === 45) {
      effects.enter("tableDelimiterFiller");
      return headDelimiterFiller(code4);
    }
    return headDelimiterNok(code4);
  }
  function headDelimiterFiller(code4) {
    if (code4 === 45) {
      effects.consume(code4);
      return headDelimiterFiller;
    }
    if (code4 === 58) {
      seen = true;
      effects.exit("tableDelimiterFiller");
      effects.enter("tableDelimiterMarker");
      effects.consume(code4);
      effects.exit("tableDelimiterMarker");
      return headDelimiterRightAlignmentAfter;
    }
    effects.exit("tableDelimiterFiller");
    return headDelimiterRightAlignmentAfter(code4);
  }
  function headDelimiterRightAlignmentAfter(code4) {
    if (markdownSpace2(code4)) {
      return factorySpace2(effects, headDelimiterCellAfter, "whitespace")(code4);
    }
    return headDelimiterCellAfter(code4);
  }
  function headDelimiterCellAfter(code4) {
    if (code4 === 124) {
      return headDelimiterBefore(code4);
    }
    if (code4 === null || markdownLineEnding2(code4)) {
      if (!seen || size !== sizeB) {
        return headDelimiterNok(code4);
      }
      effects.exit("tableDelimiterRow");
      effects.exit("tableHead");
      return ok4(code4);
    }
    return headDelimiterNok(code4);
  }
  function headDelimiterNok(code4) {
    return nok(code4);
  }
  function bodyRowStart(code4) {
    effects.enter("tableRow");
    return bodyRowBreak(code4);
  }
  function bodyRowBreak(code4) {
    if (code4 === 124) {
      effects.enter("tableCellDivider");
      effects.consume(code4);
      effects.exit("tableCellDivider");
      return bodyRowBreak;
    }
    if (code4 === null || markdownLineEnding2(code4)) {
      effects.exit("tableRow");
      return ok4(code4);
    }
    if (markdownSpace2(code4)) {
      return factorySpace2(effects, bodyRowBreak, "whitespace")(code4);
    }
    effects.enter("data");
    return bodyRowData(code4);
  }
  function bodyRowData(code4) {
    if (code4 === null || code4 === 124 || markdownLineEndingOrSpace2(code4)) {
      effects.exit("data");
      return bodyRowBreak(code4);
    }
    effects.consume(code4);
    return code4 === 92 ? bodyRowEscape : bodyRowData;
  }
  function bodyRowEscape(code4) {
    if (code4 === 92 || code4 === 124) {
      effects.consume(code4);
      return bodyRowData;
    }
    return bodyRowData(code4);
  }
}
function resolveTable(events, context) {
  let index2 = -1;
  let inFirstCellAwaitingPipe = true;
  let rowKind = 0;
  let lastCell = [0, 0, 0, 0];
  let cell = [0, 0, 0, 0];
  let afterHeadAwaitingFirstBodyRow = false;
  let lastTableEnd = 0;
  let currentTable;
  let currentBody;
  let currentCell;
  const map4 = new EditMap();
  while (++index2 < events.length) {
    const event = events[index2];
    const token = event[1];
    if (event[0] === "enter") {
      if (token.type === "tableHead") {
        afterHeadAwaitingFirstBodyRow = false;
        if (lastTableEnd !== 0) {
          flushTableEnd(map4, context, lastTableEnd, currentTable, currentBody);
          currentBody = void 0;
          lastTableEnd = 0;
        }
        currentTable = {
          type: "table",
          start: Object.assign({}, token.start),
          // Note: correct end is set later.
          end: Object.assign({}, token.end)
        };
        map4.add(index2, 0, [["enter", currentTable, context]]);
      } else if (token.type === "tableRow" || token.type === "tableDelimiterRow") {
        inFirstCellAwaitingPipe = true;
        currentCell = void 0;
        lastCell = [0, 0, 0, 0];
        cell = [0, index2 + 1, 0, 0];
        if (afterHeadAwaitingFirstBodyRow) {
          afterHeadAwaitingFirstBodyRow = false;
          currentBody = {
            type: "tableBody",
            start: Object.assign({}, token.start),
            // Note: correct end is set later.
            end: Object.assign({}, token.end)
          };
          map4.add(index2, 0, [["enter", currentBody, context]]);
        }
        rowKind = token.type === "tableDelimiterRow" ? 2 : currentBody ? 3 : 1;
      } else if (rowKind && (token.type === "data" || token.type === "tableDelimiterMarker" || token.type === "tableDelimiterFiller")) {
        inFirstCellAwaitingPipe = false;
        if (cell[2] === 0) {
          if (lastCell[1] !== 0) {
            cell[0] = cell[1];
            currentCell = flushCell(map4, context, lastCell, rowKind, void 0, currentCell);
            lastCell = [0, 0, 0, 0];
          }
          cell[2] = index2;
        }
      } else if (token.type === "tableCellDivider") {
        if (inFirstCellAwaitingPipe) {
          inFirstCellAwaitingPipe = false;
        } else {
          if (lastCell[1] !== 0) {
            cell[0] = cell[1];
            currentCell = flushCell(map4, context, lastCell, rowKind, void 0, currentCell);
          }
          lastCell = cell;
          cell = [lastCell[1], index2, 0, 0];
        }
      }
    } else if (token.type === "tableHead") {
      afterHeadAwaitingFirstBodyRow = true;
      lastTableEnd = index2;
    } else if (token.type === "tableRow" || token.type === "tableDelimiterRow") {
      lastTableEnd = index2;
      if (lastCell[1] !== 0) {
        cell[0] = cell[1];
        currentCell = flushCell(map4, context, lastCell, rowKind, index2, currentCell);
      } else if (cell[1] !== 0) {
        currentCell = flushCell(map4, context, cell, rowKind, index2, currentCell);
      }
      rowKind = 0;
    } else if (rowKind && (token.type === "data" || token.type === "tableDelimiterMarker" || token.type === "tableDelimiterFiller")) {
      cell[3] = index2;
    }
  }
  if (lastTableEnd !== 0) {
    flushTableEnd(map4, context, lastTableEnd, currentTable, currentBody);
  }
  map4.consume(context.events);
  index2 = -1;
  while (++index2 < context.events.length) {
    const event = context.events[index2];
    if (event[0] === "enter" && event[1].type === "table") {
      event[1]._align = gfmTableAlign(context.events, index2);
    }
  }
  return events;
}
function flushCell(map4, context, range, rowKind, rowEnd, previousCell) {
  const groupName = rowKind === 1 ? "tableHeader" : rowKind === 2 ? "tableDelimiter" : "tableData";
  const valueName = "tableContent";
  if (range[0] !== 0) {
    previousCell.end = Object.assign({}, getPoint(context.events, range[0]));
    map4.add(range[0], 0, [["exit", previousCell, context]]);
  }
  const now = getPoint(context.events, range[1]);
  previousCell = {
    type: groupName,
    start: Object.assign({}, now),
    // Note: correct end is set later.
    end: Object.assign({}, now)
  };
  map4.add(range[1], 0, [["enter", previousCell, context]]);
  if (range[2] !== 0) {
    const relatedStart = getPoint(context.events, range[2]);
    const relatedEnd = getPoint(context.events, range[3]);
    const valueToken = {
      type: valueName,
      start: Object.assign({}, relatedStart),
      end: Object.assign({}, relatedEnd)
    };
    map4.add(range[2], 0, [["enter", valueToken, context]]);
    if (rowKind !== 2) {
      const start = context.events[range[2]];
      const end = context.events[range[3]];
      start[1].end = Object.assign({}, end[1].end);
      start[1].type = "chunkText";
      start[1].contentType = "text";
      if (range[3] > range[2] + 1) {
        const a = range[2] + 1;
        const b = range[3] - range[2] - 1;
        map4.add(a, b, []);
      }
    }
    map4.add(range[3] + 1, 0, [["exit", valueToken, context]]);
  }
  if (rowEnd !== void 0) {
    previousCell.end = Object.assign({}, getPoint(context.events, rowEnd));
    map4.add(rowEnd, 0, [["exit", previousCell, context]]);
    previousCell = void 0;
  }
  return previousCell;
}
function flushTableEnd(map4, context, index2, table2, tableBody) {
  const exits = [];
  const related = getPoint(context.events, index2);
  if (tableBody) {
    tableBody.end = Object.assign({}, related);
    exits.push(["exit", tableBody, context]);
  }
  table2.end = Object.assign({}, related);
  exits.push(["exit", table2, context]);
  map4.add(index2 + 1, 0, exits);
}
function getPoint(events, index2) {
  const event = events[index2];
  const side = event[0] === "enter" ? "start" : "end";
  return event[1][side];
}

// node_modules/.pnpm/micromark-extension-gfm-task-list-item@2.1.0/node_modules/micromark-extension-gfm-task-list-item/lib/syntax.js
var tasklistCheck = {
  name: "tasklistCheck",
  tokenize: tokenizeTasklistCheck
};
function gfmTaskListItem() {
  return {
    text: {
      [91]: tasklistCheck
    }
  };
}
function tokenizeTasklistCheck(effects, ok4, nok) {
  const self = this;
  return open;
  function open(code4) {
    if (
      // Exit if there’s stuff before.
      self.previous !== null || // Exit if not in the first content that is the first child of a list
      // item.
      !self._gfmTasklistFirstContentOfListItem
    ) {
      return nok(code4);
    }
    effects.enter("taskListCheck");
    effects.enter("taskListCheckMarker");
    effects.consume(code4);
    effects.exit("taskListCheckMarker");
    return inside;
  }
  function inside(code4) {
    if (markdownLineEndingOrSpace2(code4)) {
      effects.enter("taskListCheckValueUnchecked");
      effects.consume(code4);
      effects.exit("taskListCheckValueUnchecked");
      return close;
    }
    if (code4 === 88 || code4 === 120) {
      effects.enter("taskListCheckValueChecked");
      effects.consume(code4);
      effects.exit("taskListCheckValueChecked");
      return close;
    }
    return nok(code4);
  }
  function close(code4) {
    if (code4 === 93) {
      effects.enter("taskListCheckMarker");
      effects.consume(code4);
      effects.exit("taskListCheckMarker");
      effects.exit("taskListCheck");
      return after;
    }
    return nok(code4);
  }
  function after(code4) {
    if (markdownLineEnding2(code4)) {
      return ok4(code4);
    }
    if (markdownSpace2(code4)) {
      return effects.check({
        tokenize: spaceThenNonSpace
      }, ok4, nok)(code4);
    }
    return nok(code4);
  }
}
function spaceThenNonSpace(effects, ok4, nok) {
  return factorySpace2(effects, after, "whitespace");
  function after(code4) {
    return code4 === null ? nok(code4) : ok4(code4);
  }
}

// node_modules/.pnpm/micromark-extension-gfm@3.0.0/node_modules/micromark-extension-gfm/index.js
function gfm(options) {
  return combineExtensions2([
    gfmAutolinkLiteral(),
    gfmFootnote(),
    gfmStrikethrough(options),
    gfmTable(),
    gfmTaskListItem()
  ]);
}

// node_modules/.pnpm/remark-gfm@4.0.0/node_modules/remark-gfm/lib/index.js
var emptyOptions3 = {};
function remarkGfm(options) {
  const self = (
    /** @type {Processor} */
    this
  );
  const settings = options || emptyOptions3;
  const data = self.data();
  const micromarkExtensions = data.micromarkExtensions || (data.micromarkExtensions = []);
  const fromMarkdownExtensions = data.fromMarkdownExtensions || (data.fromMarkdownExtensions = []);
  const toMarkdownExtensions = data.toMarkdownExtensions || (data.toMarkdownExtensions = []);
  micromarkExtensions.push(gfm(settings));
  fromMarkdownExtensions.push(gfmFromMarkdown());
  toMarkdownExtensions.push(gfmToMarkdown(settings));
}

// app/components/layout/markdown.tsx
var import_jsx_dev_runtime5 = __toESM(require_jsx_dev_runtime(), 1);
if (!window.$RefreshReg$ || !window.$RefreshSig$ || !window.$RefreshRuntime$) {
  console.warn("remix:hmr: React Fast Refresh only works when the Remix compiler is running in development mode.");
} else {
  prevRefreshReg = window.$RefreshReg$;
  prevRefreshSig = window.$RefreshSig$;
  window.$RefreshReg$ = (type, id) => {
    window.$RefreshRuntime$.register(type, '"app/components/layout/markdown.tsx"' + id);
  };
  window.$RefreshSig$ = window.$RefreshRuntime$.createSignatureFunctionForTransform;
}
var prevRefreshReg;
var prevRefreshSig;
if (import.meta) {
  import.meta.hot = createHotContext(
    //@ts-expect-error
    "app/components/layout/markdown.tsx"
  );
  import.meta.hot.lastModified = "1738670497174.5989";
}
function Markdown({
  content: content3,
  className
}) {
  return /* @__PURE__ */ (0, import_jsx_dev_runtime5.jsxDEV)(ErrorBoundary, { fallback: /* @__PURE__ */ (0, import_jsx_dev_runtime5.jsxDEV)("div", { className: "text-destructive", children: "Error rendering markdown" }, void 0, false, {
    fileName: "app/components/layout/markdown.tsx",
    lineNumber: 29,
    columnNumber: 35
  }, this), children: /* @__PURE__ */ (0, import_jsx_dev_runtime5.jsxDEV)("div", { className: cn("prose dark:prose-invert max-w-none", className), children: /* @__PURE__ */ (0, import_jsx_dev_runtime5.jsxDEV)(ReactMarkdown, { remarkPlugins: [remarkGfm], components: {
    code({
      className: className2,
      children,
      ...props
    }) {
      const match = /language-(\w+)/.exec(className2 || "");
      return /* @__PURE__ */ (0, import_jsx_dev_runtime5.jsxDEV)("code", { className: cn("bg-muted px-[0.4em] py-[0.2em] rounded font-mono text-sm", match ? "block overflow-x-auto p-4" : "inline-block", className2), ...props, children }, void 0, false, {
        fileName: "app/components/layout/markdown.tsx",
        lineNumber: 38,
        columnNumber: 18
      }, this);
    }
  }, children: content3 }, void 0, false, {
    fileName: "app/components/layout/markdown.tsx",
    lineNumber: 31,
    columnNumber: 9
  }, this) }, void 0, false, {
    fileName: "app/components/layout/markdown.tsx",
    lineNumber: 30,
    columnNumber: 7
  }, this) }, void 0, false, {
    fileName: "app/components/layout/markdown.tsx",
    lineNumber: 29,
    columnNumber: 10
  }, this);
}
_c5 = Markdown;
var ErrorBoundary = class extends React6.Component {
  constructor(props) {
    super(props);
    this.state = {
      hasError: false
    };
  }
  static getDerivedStateFromError() {
    return {
      hasError: true
    };
  }
  componentDidCatch(error) {
    console.error("Markdown rendering error:", error);
  }
  render() {
    if (this.state.hasError) {
      return this.props.fallback;
    }
    return this.props.children;
  }
};
var _c5;
$RefreshReg$(_c5, "Markdown");
window.$RefreshReg$ = prevRefreshReg;
window.$RefreshSig$ = prevRefreshSig;

// app/components/ui/avatar.tsx
var React8 = __toESM(require_react(), 1);

// node_modules/.pnpm/@radix-ui+react-avatar@1.1.2_@types+react-dom@18.3.5_@types+react@18.3.18__@types+react_c40a5ed558d7580c48534837bdd11506/node_modules/@radix-ui/react-avatar/dist/index.mjs
var React7 = __toESM(require_react(), 1);
var import_jsx_runtime2 = __toESM(require_jsx_runtime(), 1);
"use client";
var AVATAR_NAME = "Avatar";
var [createAvatarContext, createAvatarScope] = createContextScope(AVATAR_NAME);
var [AvatarProvider, useAvatarContext] = createAvatarContext(AVATAR_NAME);
var Avatar = React7.forwardRef(
  (props, forwardedRef) => {
    const { __scopeAvatar, ...avatarProps } = props;
    const [imageLoadingStatus, setImageLoadingStatus] = React7.useState("idle");
    return /* @__PURE__ */ (0, import_jsx_runtime2.jsx)(
      AvatarProvider,
      {
        scope: __scopeAvatar,
        imageLoadingStatus,
        onImageLoadingStatusChange: setImageLoadingStatus,
        children: /* @__PURE__ */ (0, import_jsx_runtime2.jsx)(Primitive.span, { ...avatarProps, ref: forwardedRef })
      }
    );
  }
);
Avatar.displayName = AVATAR_NAME;
var IMAGE_NAME = "AvatarImage";
var AvatarImage = React7.forwardRef(
  (props, forwardedRef) => {
    const { __scopeAvatar, src, onLoadingStatusChange = () => {
    }, ...imageProps } = props;
    const context = useAvatarContext(IMAGE_NAME, __scopeAvatar);
    const imageLoadingStatus = useImageLoadingStatus(src, imageProps.referrerPolicy);
    const handleLoadingStatusChange = useCallbackRef((status) => {
      onLoadingStatusChange(status);
      context.onImageLoadingStatusChange(status);
    });
    useLayoutEffect2(() => {
      if (imageLoadingStatus !== "idle") {
        handleLoadingStatusChange(imageLoadingStatus);
      }
    }, [imageLoadingStatus, handleLoadingStatusChange]);
    return imageLoadingStatus === "loaded" ? /* @__PURE__ */ (0, import_jsx_runtime2.jsx)(Primitive.img, { ...imageProps, ref: forwardedRef, src }) : null;
  }
);
AvatarImage.displayName = IMAGE_NAME;
var FALLBACK_NAME = "AvatarFallback";
var AvatarFallback = React7.forwardRef(
  (props, forwardedRef) => {
    const { __scopeAvatar, delayMs, ...fallbackProps } = props;
    const context = useAvatarContext(FALLBACK_NAME, __scopeAvatar);
    const [canRender, setCanRender] = React7.useState(delayMs === void 0);
    React7.useEffect(() => {
      if (delayMs !== void 0) {
        const timerId = window.setTimeout(() => setCanRender(true), delayMs);
        return () => window.clearTimeout(timerId);
      }
    }, [delayMs]);
    return canRender && context.imageLoadingStatus !== "loaded" ? /* @__PURE__ */ (0, import_jsx_runtime2.jsx)(Primitive.span, { ...fallbackProps, ref: forwardedRef }) : null;
  }
);
AvatarFallback.displayName = FALLBACK_NAME;
function useImageLoadingStatus(src, referrerPolicy) {
  const [loadingStatus, setLoadingStatus] = React7.useState("idle");
  useLayoutEffect2(() => {
    if (!src) {
      setLoadingStatus("error");
      return;
    }
    let isMounted = true;
    const image3 = new window.Image();
    const updateStatus = (status) => () => {
      if (!isMounted)
        return;
      setLoadingStatus(status);
    };
    setLoadingStatus("loading");
    image3.onload = updateStatus("loaded");
    image3.onerror = updateStatus("error");
    image3.src = src;
    if (referrerPolicy) {
      image3.referrerPolicy = referrerPolicy;
    }
    return () => {
      isMounted = false;
    };
  }, [src, referrerPolicy]);
  return loadingStatus;
}
var Root2 = Avatar;
var Image = AvatarImage;
var Fallback = AvatarFallback;

// app/components/ui/avatar.tsx
var import_jsx_dev_runtime6 = __toESM(require_jsx_dev_runtime(), 1);
if (!window.$RefreshReg$ || !window.$RefreshSig$ || !window.$RefreshRuntime$) {
  console.warn("remix:hmr: React Fast Refresh only works when the Remix compiler is running in development mode.");
} else {
  prevRefreshReg = window.$RefreshReg$;
  prevRefreshSig = window.$RefreshSig$;
  window.$RefreshReg$ = (type, id) => {
    window.$RefreshRuntime$.register(type, '"app/components/ui/avatar.tsx"' + id);
  };
  window.$RefreshSig$ = window.$RefreshRuntime$.createSignatureFunctionForTransform;
}
var prevRefreshReg;
var prevRefreshSig;
if (import.meta) {
  import.meta.hot = createHotContext(
    //@ts-expect-error
    "app/components/ui/avatar.tsx"
  );
  import.meta.hot.lastModified = "1738662837907.6753";
}
var Avatar2 = React8.forwardRef(_c6 = ({
  className,
  ...props
}, ref) => /* @__PURE__ */ (0, import_jsx_dev_runtime6.jsxDEV)(Root2, { ref, className: cn("relative flex h-10 w-10 shrink-0 overflow-hidden rounded-full", className), ...props }, void 0, false, {
  fileName: "app/components/ui/avatar.tsx",
  lineNumber: 27,
  columnNumber: 12
}, this));
_c23 = Avatar2;
Avatar2.displayName = Root2.displayName;
var AvatarImage2 = React8.forwardRef(_c32 = ({
  className,
  ...props
}, ref) => /* @__PURE__ */ (0, import_jsx_dev_runtime6.jsxDEV)(Image, { ref, className: cn("aspect-square h-full w-full", className), ...props }, void 0, false, {
  fileName: "app/components/ui/avatar.tsx",
  lineNumber: 33,
  columnNumber: 12
}, this));
_c42 = AvatarImage2;
AvatarImage2.displayName = Image.displayName;
var AvatarFallback2 = React8.forwardRef(_c52 = ({
  className,
  ...props
}, ref) => /* @__PURE__ */ (0, import_jsx_dev_runtime6.jsxDEV)(Fallback, { ref, className: cn("flex h-full w-full items-center justify-center rounded-full bg-muted", className), ...props }, void 0, false, {
  fileName: "app/components/ui/avatar.tsx",
  lineNumber: 39,
  columnNumber: 12
}, this));
_c62 = AvatarFallback2;
AvatarFallback2.displayName = Fallback.displayName;
var _c6;
var _c23;
var _c32;
var _c42;
var _c52;
var _c62;
$RefreshReg$(_c6, "Avatar$React.forwardRef");
$RefreshReg$(_c23, "Avatar");
$RefreshReg$(_c32, "AvatarImage$React.forwardRef");
$RefreshReg$(_c42, "AvatarImage");
$RefreshReg$(_c52, "AvatarFallback$React.forwardRef");
$RefreshReg$(_c62, "AvatarFallback");
window.$RefreshReg$ = prevRefreshReg;
window.$RefreshSig$ = prevRefreshSig;

// app/components/chat/chat-message.tsx
var import_jsx_dev_runtime7 = __toESM(require_jsx_dev_runtime(), 1);
if (!window.$RefreshReg$ || !window.$RefreshSig$ || !window.$RefreshRuntime$) {
  console.warn("remix:hmr: React Fast Refresh only works when the Remix compiler is running in development mode.");
} else {
  prevRefreshReg = window.$RefreshReg$;
  prevRefreshSig = window.$RefreshSig$;
  window.$RefreshReg$ = (type, id) => {
    window.$RefreshRuntime$.register(type, '"app/components/chat/chat-message.tsx"' + id);
  };
  window.$RefreshSig$ = window.$RefreshRuntime$.createSignatureFunctionForTransform;
}
var prevRefreshReg;
var prevRefreshSig;
if (import.meta) {
  import.meta.hot = createHotContext(
    //@ts-expect-error
    "app/components/chat/chat-message.tsx"
  );
  import.meta.hot.lastModified = "1738670497174.5989";
}
function ChatMessage({
  message,
  isLoading,
  className
}) {
  const isUser = message.role === "USER";
  return /* @__PURE__ */ (0, import_jsx_dev_runtime7.jsxDEV)("div", { className: cn("flex gap-4 p-4", isUser && "flex-row-reverse", className), children: [
    /* @__PURE__ */ (0, import_jsx_dev_runtime7.jsxDEV)(Avatar2, { className: cn("h-8 w-8 shrink-0", isUser ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"), children: /* @__PURE__ */ (0, import_jsx_dev_runtime7.jsxDEV)(AvatarFallback2, { children: isUser ? "U" : "A" }, void 0, false, {
      fileName: "app/components/chat/chat-message.tsx",
      lineNumber: 35,
      columnNumber: 9
    }, this) }, void 0, false, {
      fileName: "app/components/chat/chat-message.tsx",
      lineNumber: 34,
      columnNumber: 7
    }, this),
    /* @__PURE__ */ (0, import_jsx_dev_runtime7.jsxDEV)(Card, { className: cn("flex-1 p-4", isUser ? "bg-primary/5" : "bg-background", "border shadow-sm"), children: isLoading ? /* @__PURE__ */ (0, import_jsx_dev_runtime7.jsxDEV)("div", { className: "flex items-center gap-2 text-muted-foreground animate-pulse", children: [
      /* @__PURE__ */ (0, import_jsx_dev_runtime7.jsxDEV)("span", { children: "Agent Smith is thinking" }, void 0, false, {
        fileName: "app/components/chat/chat-message.tsx",
        lineNumber: 40,
        columnNumber: 13
      }, this),
      /* @__PURE__ */ (0, import_jsx_dev_runtime7.jsxDEV)(Loader2, { className: "h-4 w-4 animate-spin" }, void 0, false, {
        fileName: "app/components/chat/chat-message.tsx",
        lineNumber: 41,
        columnNumber: 13
      }, this)
    ] }, void 0, true, {
      fileName: "app/components/chat/chat-message.tsx",
      lineNumber: 39,
      columnNumber: 22
    }, this) : /* @__PURE__ */ (0, import_jsx_dev_runtime7.jsxDEV)("div", { className: cn("prose dark:prose-invert max-w-none", "prose-p:leading-relaxed prose-pre:p-0", "prose-code:bg-muted prose-code:text-foreground", "prose-headings:text-foreground prose-a:text-primary"), children: /* @__PURE__ */ (0, import_jsx_dev_runtime7.jsxDEV)(Markdown, { content: message.content }, void 0, false, {
      fileName: "app/components/chat/chat-message.tsx",
      lineNumber: 43,
      columnNumber: 13
    }, this) }, void 0, false, {
      fileName: "app/components/chat/chat-message.tsx",
      lineNumber: 42,
      columnNumber: 20
    }, this) }, void 0, false, {
      fileName: "app/components/chat/chat-message.tsx",
      lineNumber: 38,
      columnNumber: 7
    }, this)
  ] }, void 0, true, {
    fileName: "app/components/chat/chat-message.tsx",
    lineNumber: 33,
    columnNumber: 10
  }, this);
}
_c7 = ChatMessage;
var _c7;
$RefreshReg$(_c7, "ChatMessage");
window.$RefreshReg$ = prevRefreshReg;
window.$RefreshSig$ = prevRefreshSig;

// app/components/chat/new-chat-dialog.tsx
var import_react6 = __toESM(require_react(), 1);
var import_jsx_dev_runtime8 = __toESM(require_jsx_dev_runtime(), 1);
if (!window.$RefreshReg$ || !window.$RefreshSig$ || !window.$RefreshRuntime$) {
  console.warn("remix:hmr: React Fast Refresh only works when the Remix compiler is running in development mode.");
} else {
  prevRefreshReg = window.$RefreshReg$;
  prevRefreshSig = window.$RefreshSig$;
  window.$RefreshReg$ = (type, id) => {
    window.$RefreshRuntime$.register(type, '"app/components/chat/new-chat-dialog.tsx"' + id);
  };
  window.$RefreshSig$ = window.$RefreshRuntime$.createSignatureFunctionForTransform;
}
var prevRefreshReg;
var prevRefreshSig;
var _s4 = $RefreshSig$();
if (import.meta) {
  import.meta.hot = createHotContext(
    //@ts-expect-error
    "app/components/chat/new-chat-dialog.tsx"
  );
  import.meta.hot.lastModified = "1738662837906.6753";
}
function NewChatDialog({
  isOpen,
  onClose,
  onCreateChat
}) {
  _s4();
  const [title, setTitle] = (0, import_react6.useState)("");
  const [isCreating, setIsCreating] = (0, import_react6.useState)(false);
  const handleCreate = async () => {
    if (!title.trim() || isCreating)
      return;
    try {
      setIsCreating(true);
      await onCreateChat(title);
      setTitle("");
      onClose();
    } catch (error) {
      console.error("Failed to create chat:", error);
    } finally {
      setIsCreating(false);
    }
  };
  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleCreate();
    }
  };
  return /* @__PURE__ */ (0, import_jsx_dev_runtime8.jsxDEV)(Dialog, { open: isOpen, onOpenChange: onClose, children: /* @__PURE__ */ (0, import_jsx_dev_runtime8.jsxDEV)(DialogContent, { children: [
    /* @__PURE__ */ (0, import_jsx_dev_runtime8.jsxDEV)(DialogHeader, { children: [
      /* @__PURE__ */ (0, import_jsx_dev_runtime8.jsxDEV)(DialogTitle, { className: "flex items-center gap-2", children: [
        /* @__PURE__ */ (0, import_jsx_dev_runtime8.jsxDEV)(MessageSquarePlus, { className: "h-5 w-5" }, void 0, false, {
          fileName: "app/components/chat/new-chat-dialog.tsx",
          lineNumber: 59,
          columnNumber: 13
        }, this),
        "New Chat"
      ] }, void 0, true, {
        fileName: "app/components/chat/new-chat-dialog.tsx",
        lineNumber: 58,
        columnNumber: 11
      }, this),
      /* @__PURE__ */ (0, import_jsx_dev_runtime8.jsxDEV)(DialogDescription, { children: "Create a new chat session. Give it a descriptive title." }, void 0, false, {
        fileName: "app/components/chat/new-chat-dialog.tsx",
        lineNumber: 62,
        columnNumber: 11
      }, this)
    ] }, void 0, true, {
      fileName: "app/components/chat/new-chat-dialog.tsx",
      lineNumber: 57,
      columnNumber: 9
    }, this),
    /* @__PURE__ */ (0, import_jsx_dev_runtime8.jsxDEV)(Input, { value: title, onChange: (e) => setTitle(e.target.value), onKeyDown: handleKeyDown, placeholder: "Enter chat title...", disabled: isCreating, autoFocus: true }, void 0, false, {
      fileName: "app/components/chat/new-chat-dialog.tsx",
      lineNumber: 66,
      columnNumber: 9
    }, this),
    /* @__PURE__ */ (0, import_jsx_dev_runtime8.jsxDEV)(DialogFooter, { children: [
      /* @__PURE__ */ (0, import_jsx_dev_runtime8.jsxDEV)(Button, { variant: "outline", onClick: onClose, disabled: isCreating, children: "Cancel" }, void 0, false, {
        fileName: "app/components/chat/new-chat-dialog.tsx",
        lineNumber: 68,
        columnNumber: 11
      }, this),
      /* @__PURE__ */ (0, import_jsx_dev_runtime8.jsxDEV)(Button, { onClick: handleCreate, disabled: !title.trim() || isCreating, children: isCreating ? /* @__PURE__ */ (0, import_jsx_dev_runtime8.jsxDEV)(import_jsx_dev_runtime8.Fragment, { children: [
        /* @__PURE__ */ (0, import_jsx_dev_runtime8.jsxDEV)(Loader2, { className: "mr-2 h-4 w-4 animate-spin" }, void 0, false, {
          fileName: "app/components/chat/new-chat-dialog.tsx",
          lineNumber: 73,
          columnNumber: 17
        }, this),
        "Creating..."
      ] }, void 0, true, {
        fileName: "app/components/chat/new-chat-dialog.tsx",
        lineNumber: 72,
        columnNumber: 27
      }, this) : "Create" }, void 0, false, {
        fileName: "app/components/chat/new-chat-dialog.tsx",
        lineNumber: 71,
        columnNumber: 11
      }, this)
    ] }, void 0, true, {
      fileName: "app/components/chat/new-chat-dialog.tsx",
      lineNumber: 67,
      columnNumber: 9
    }, this)
  ] }, void 0, true, {
    fileName: "app/components/chat/new-chat-dialog.tsx",
    lineNumber: 56,
    columnNumber: 7
  }, this) }, void 0, false, {
    fileName: "app/components/chat/new-chat-dialog.tsx",
    lineNumber: 55,
    columnNumber: 10
  }, this);
}
_s4(NewChatDialog, "R9pi7/TB4KKAqRMIkNQhXEXe7rM=");
_c8 = NewChatDialog;
var _c8;
$RefreshReg$(_c8, "NewChatDialog");
window.$RefreshReg$ = prevRefreshReg;
window.$RefreshSig$ = prevRefreshSig;

// app/components/ui/alert.tsx
var React9 = __toESM(require_react(), 1);
var import_jsx_dev_runtime9 = __toESM(require_jsx_dev_runtime(), 1);
if (!window.$RefreshReg$ || !window.$RefreshSig$ || !window.$RefreshRuntime$) {
  console.warn("remix:hmr: React Fast Refresh only works when the Remix compiler is running in development mode.");
} else {
  prevRefreshReg = window.$RefreshReg$;
  prevRefreshSig = window.$RefreshSig$;
  window.$RefreshReg$ = (type, id) => {
    window.$RefreshRuntime$.register(type, '"app/components/ui/alert.tsx"' + id);
  };
  window.$RefreshSig$ = window.$RefreshRuntime$.createSignatureFunctionForTransform;
}
var prevRefreshReg;
var prevRefreshSig;
if (import.meta) {
  import.meta.hot = createHotContext(
    //@ts-expect-error
    "app/components/ui/alert.tsx"
  );
  import.meta.hot.lastModified = "1738662837907.6753";
}
var alertVariants = cva("relative w-full rounded-lg border px-4 py-3 text-sm [&>svg+div]:translate-y-[-3px] [&>svg]:absolute [&>svg]:left-4 [&>svg]:top-4 [&>svg]:text-foreground [&>svg~*]:pl-7", {
  variants: {
    variant: {
      default: "bg-background text-foreground",
      destructive: "border-destructive/50 text-destructive dark:border-destructive [&>svg]:text-destructive"
    }
  },
  defaultVariants: {
    variant: "default"
  }
});
var Alert = React9.forwardRef(_c9 = ({
  className,
  variant,
  ...props
}, ref) => /* @__PURE__ */ (0, import_jsx_dev_runtime9.jsxDEV)("div", { ref, role: "alert", className: cn(alertVariants({
  variant
}), className), ...props }, void 0, false, {
  fileName: "app/components/ui/alert.tsx",
  lineNumber: 39,
  columnNumber: 12
}, this));
_c24 = Alert;
Alert.displayName = "Alert";
var AlertTitle = React9.forwardRef(_c33 = ({
  className,
  ...props
}, ref) => /* @__PURE__ */ (0, import_jsx_dev_runtime9.jsxDEV)("h5", { ref, className: cn("mb-1 font-medium leading-none tracking-tight", className), ...props }, void 0, false, {
  fileName: "app/components/ui/alert.tsx",
  lineNumber: 47,
  columnNumber: 12
}, this));
_c43 = AlertTitle;
AlertTitle.displayName = "AlertTitle";
var AlertDescription = React9.forwardRef(_c53 = ({
  className,
  ...props
}, ref) => /* @__PURE__ */ (0, import_jsx_dev_runtime9.jsxDEV)("div", { ref, className: cn("text-sm [&_p]:leading-relaxed", className), ...props }, void 0, false, {
  fileName: "app/components/ui/alert.tsx",
  lineNumber: 53,
  columnNumber: 12
}, this));
_c63 = AlertDescription;
AlertDescription.displayName = "AlertDescription";
var _c9;
var _c24;
var _c33;
var _c43;
var _c53;
var _c63;
$RefreshReg$(_c9, "Alert$React.forwardRef");
$RefreshReg$(_c24, "Alert");
$RefreshReg$(_c33, "AlertTitle$React.forwardRef");
$RefreshReg$(_c43, "AlertTitle");
$RefreshReg$(_c53, "AlertDescription$React.forwardRef");
$RefreshReg$(_c63, "AlertDescription");
window.$RefreshReg$ = prevRefreshReg;
window.$RefreshSig$ = prevRefreshSig;

// app/routes/chat.tsx
var import_session = __toESM(require_session(), 1);

// app/components/ui/scroll-area.tsx
var React11 = __toESM(require_react(), 1);

// node_modules/.pnpm/@radix-ui+react-scroll-area@1.2.2_@types+react-dom@18.3.5_@types+react@18.3.18__@types+_6025139b77993bb6e71939ac2a0c4457/node_modules/@radix-ui/react-scroll-area/dist/index.mjs
var React22 = __toESM(require_react(), 1);

// node_modules/.pnpm/@radix-ui+number@1.1.0/node_modules/@radix-ui/number/dist/index.mjs
function clamp(value, [min, max]) {
  return Math.min(max, Math.max(min, value));
}

// node_modules/.pnpm/@radix-ui+react-scroll-area@1.2.2_@types+react-dom@18.3.5_@types+react@18.3.18__@types+_6025139b77993bb6e71939ac2a0c4457/node_modules/@radix-ui/react-scroll-area/dist/index.mjs
var React10 = __toESM(require_react(), 1);
var import_jsx_runtime3 = __toESM(require_jsx_runtime(), 1);
"use client";
function useStateMachine(initialState, machine) {
  return React10.useReducer((state, event) => {
    const nextState = machine[state][event];
    return nextState ?? state;
  }, initialState);
}
var SCROLL_AREA_NAME = "ScrollArea";
var [createScrollAreaContext, createScrollAreaScope] = createContextScope(SCROLL_AREA_NAME);
var [ScrollAreaProvider, useScrollAreaContext] = createScrollAreaContext(SCROLL_AREA_NAME);
var ScrollArea = React22.forwardRef(
  (props, forwardedRef) => {
    const {
      __scopeScrollArea,
      type = "hover",
      dir,
      scrollHideDelay = 600,
      ...scrollAreaProps
    } = props;
    const [scrollArea, setScrollArea] = React22.useState(null);
    const [viewport, setViewport] = React22.useState(null);
    const [content3, setContent] = React22.useState(null);
    const [scrollbarX, setScrollbarX] = React22.useState(null);
    const [scrollbarY, setScrollbarY] = React22.useState(null);
    const [cornerWidth, setCornerWidth] = React22.useState(0);
    const [cornerHeight, setCornerHeight] = React22.useState(0);
    const [scrollbarXEnabled, setScrollbarXEnabled] = React22.useState(false);
    const [scrollbarYEnabled, setScrollbarYEnabled] = React22.useState(false);
    const composedRefs = useComposedRefs(forwardedRef, (node3) => setScrollArea(node3));
    const direction = useDirection(dir);
    return /* @__PURE__ */ (0, import_jsx_runtime3.jsx)(
      ScrollAreaProvider,
      {
        scope: __scopeScrollArea,
        type,
        dir: direction,
        scrollHideDelay,
        scrollArea,
        viewport,
        onViewportChange: setViewport,
        content: content3,
        onContentChange: setContent,
        scrollbarX,
        onScrollbarXChange: setScrollbarX,
        scrollbarXEnabled,
        onScrollbarXEnabledChange: setScrollbarXEnabled,
        scrollbarY,
        onScrollbarYChange: setScrollbarY,
        scrollbarYEnabled,
        onScrollbarYEnabledChange: setScrollbarYEnabled,
        onCornerWidthChange: setCornerWidth,
        onCornerHeightChange: setCornerHeight,
        children: /* @__PURE__ */ (0, import_jsx_runtime3.jsx)(
          Primitive.div,
          {
            dir: direction,
            ...scrollAreaProps,
            ref: composedRefs,
            style: {
              position: "relative",
              // Pass corner sizes as CSS vars to reduce re-renders of context consumers
              ["--radix-scroll-area-corner-width"]: cornerWidth + "px",
              ["--radix-scroll-area-corner-height"]: cornerHeight + "px",
              ...props.style
            }
          }
        )
      }
    );
  }
);
ScrollArea.displayName = SCROLL_AREA_NAME;
var VIEWPORT_NAME = "ScrollAreaViewport";
var ScrollAreaViewport = React22.forwardRef(
  (props, forwardedRef) => {
    const { __scopeScrollArea, children, nonce, ...viewportProps } = props;
    const context = useScrollAreaContext(VIEWPORT_NAME, __scopeScrollArea);
    const ref = React22.useRef(null);
    const composedRefs = useComposedRefs(forwardedRef, ref, context.onViewportChange);
    return /* @__PURE__ */ (0, import_jsx_runtime3.jsxs)(import_jsx_runtime3.Fragment, { children: [
      /* @__PURE__ */ (0, import_jsx_runtime3.jsx)(
        "style",
        {
          dangerouslySetInnerHTML: {
            __html: `[data-radix-scroll-area-viewport]{scrollbar-width:none;-ms-overflow-style:none;-webkit-overflow-scrolling:touch;}[data-radix-scroll-area-viewport]::-webkit-scrollbar{display:none}`
          },
          nonce
        }
      ),
      /* @__PURE__ */ (0, import_jsx_runtime3.jsx)(
        Primitive.div,
        {
          "data-radix-scroll-area-viewport": "",
          ...viewportProps,
          ref: composedRefs,
          style: {
            /**
             * We don't support `visible` because the intention is to have at least one scrollbar
             * if this component is used and `visible` will behave like `auto` in that case
             * https://developer.mozilla.org/en-US/docs/Web/CSS/overflow#description
             *
             * We don't handle `auto` because the intention is for the native implementation
             * to be hidden if using this component. We just want to ensure the node is scrollable
             * so could have used either `scroll` or `auto` here. We picked `scroll` to prevent
             * the browser from having to work out whether to render native scrollbars or not,
             * we tell it to with the intention of hiding them in CSS.
             */
            overflowX: context.scrollbarXEnabled ? "scroll" : "hidden",
            overflowY: context.scrollbarYEnabled ? "scroll" : "hidden",
            ...props.style
          },
          children: /* @__PURE__ */ (0, import_jsx_runtime3.jsx)("div", { ref: context.onContentChange, style: { minWidth: "100%", display: "table" }, children })
        }
      )
    ] });
  }
);
ScrollAreaViewport.displayName = VIEWPORT_NAME;
var SCROLLBAR_NAME = "ScrollAreaScrollbar";
var ScrollAreaScrollbar = React22.forwardRef(
  (props, forwardedRef) => {
    const { forceMount, ...scrollbarProps } = props;
    const context = useScrollAreaContext(SCROLLBAR_NAME, props.__scopeScrollArea);
    const { onScrollbarXEnabledChange, onScrollbarYEnabledChange } = context;
    const isHorizontal = props.orientation === "horizontal";
    React22.useEffect(() => {
      isHorizontal ? onScrollbarXEnabledChange(true) : onScrollbarYEnabledChange(true);
      return () => {
        isHorizontal ? onScrollbarXEnabledChange(false) : onScrollbarYEnabledChange(false);
      };
    }, [isHorizontal, onScrollbarXEnabledChange, onScrollbarYEnabledChange]);
    return context.type === "hover" ? /* @__PURE__ */ (0, import_jsx_runtime3.jsx)(ScrollAreaScrollbarHover, { ...scrollbarProps, ref: forwardedRef, forceMount }) : context.type === "scroll" ? /* @__PURE__ */ (0, import_jsx_runtime3.jsx)(ScrollAreaScrollbarScroll, { ...scrollbarProps, ref: forwardedRef, forceMount }) : context.type === "auto" ? /* @__PURE__ */ (0, import_jsx_runtime3.jsx)(ScrollAreaScrollbarAuto, { ...scrollbarProps, ref: forwardedRef, forceMount }) : context.type === "always" ? /* @__PURE__ */ (0, import_jsx_runtime3.jsx)(ScrollAreaScrollbarVisible, { ...scrollbarProps, ref: forwardedRef }) : null;
  }
);
ScrollAreaScrollbar.displayName = SCROLLBAR_NAME;
var ScrollAreaScrollbarHover = React22.forwardRef((props, forwardedRef) => {
  const { forceMount, ...scrollbarProps } = props;
  const context = useScrollAreaContext(SCROLLBAR_NAME, props.__scopeScrollArea);
  const [visible, setVisible] = React22.useState(false);
  React22.useEffect(() => {
    const scrollArea = context.scrollArea;
    let hideTimer = 0;
    if (scrollArea) {
      const handlePointerEnter = () => {
        window.clearTimeout(hideTimer);
        setVisible(true);
      };
      const handlePointerLeave = () => {
        hideTimer = window.setTimeout(() => setVisible(false), context.scrollHideDelay);
      };
      scrollArea.addEventListener("pointerenter", handlePointerEnter);
      scrollArea.addEventListener("pointerleave", handlePointerLeave);
      return () => {
        window.clearTimeout(hideTimer);
        scrollArea.removeEventListener("pointerenter", handlePointerEnter);
        scrollArea.removeEventListener("pointerleave", handlePointerLeave);
      };
    }
  }, [context.scrollArea, context.scrollHideDelay]);
  return /* @__PURE__ */ (0, import_jsx_runtime3.jsx)(Presence, { present: forceMount || visible, children: /* @__PURE__ */ (0, import_jsx_runtime3.jsx)(
    ScrollAreaScrollbarAuto,
    {
      "data-state": visible ? "visible" : "hidden",
      ...scrollbarProps,
      ref: forwardedRef
    }
  ) });
});
var ScrollAreaScrollbarScroll = React22.forwardRef((props, forwardedRef) => {
  const { forceMount, ...scrollbarProps } = props;
  const context = useScrollAreaContext(SCROLLBAR_NAME, props.__scopeScrollArea);
  const isHorizontal = props.orientation === "horizontal";
  const debounceScrollEnd = useDebounceCallback(() => send("SCROLL_END"), 100);
  const [state, send] = useStateMachine("hidden", {
    hidden: {
      SCROLL: "scrolling"
    },
    scrolling: {
      SCROLL_END: "idle",
      POINTER_ENTER: "interacting"
    },
    interacting: {
      SCROLL: "interacting",
      POINTER_LEAVE: "idle"
    },
    idle: {
      HIDE: "hidden",
      SCROLL: "scrolling",
      POINTER_ENTER: "interacting"
    }
  });
  React22.useEffect(() => {
    if (state === "idle") {
      const hideTimer = window.setTimeout(() => send("HIDE"), context.scrollHideDelay);
      return () => window.clearTimeout(hideTimer);
    }
  }, [state, context.scrollHideDelay, send]);
  React22.useEffect(() => {
    const viewport = context.viewport;
    const scrollDirection = isHorizontal ? "scrollLeft" : "scrollTop";
    if (viewport) {
      let prevScrollPos = viewport[scrollDirection];
      const handleScroll = () => {
        const scrollPos = viewport[scrollDirection];
        const hasScrollInDirectionChanged = prevScrollPos !== scrollPos;
        if (hasScrollInDirectionChanged) {
          send("SCROLL");
          debounceScrollEnd();
        }
        prevScrollPos = scrollPos;
      };
      viewport.addEventListener("scroll", handleScroll);
      return () => viewport.removeEventListener("scroll", handleScroll);
    }
  }, [context.viewport, isHorizontal, send, debounceScrollEnd]);
  return /* @__PURE__ */ (0, import_jsx_runtime3.jsx)(Presence, { present: forceMount || state !== "hidden", children: /* @__PURE__ */ (0, import_jsx_runtime3.jsx)(
    ScrollAreaScrollbarVisible,
    {
      "data-state": state === "hidden" ? "hidden" : "visible",
      ...scrollbarProps,
      ref: forwardedRef,
      onPointerEnter: composeEventHandlers(props.onPointerEnter, () => send("POINTER_ENTER")),
      onPointerLeave: composeEventHandlers(props.onPointerLeave, () => send("POINTER_LEAVE"))
    }
  ) });
});
var ScrollAreaScrollbarAuto = React22.forwardRef((props, forwardedRef) => {
  const context = useScrollAreaContext(SCROLLBAR_NAME, props.__scopeScrollArea);
  const { forceMount, ...scrollbarProps } = props;
  const [visible, setVisible] = React22.useState(false);
  const isHorizontal = props.orientation === "horizontal";
  const handleResize = useDebounceCallback(() => {
    if (context.viewport) {
      const isOverflowX = context.viewport.offsetWidth < context.viewport.scrollWidth;
      const isOverflowY = context.viewport.offsetHeight < context.viewport.scrollHeight;
      setVisible(isHorizontal ? isOverflowX : isOverflowY);
    }
  }, 10);
  useResizeObserver(context.viewport, handleResize);
  useResizeObserver(context.content, handleResize);
  return /* @__PURE__ */ (0, import_jsx_runtime3.jsx)(Presence, { present: forceMount || visible, children: /* @__PURE__ */ (0, import_jsx_runtime3.jsx)(
    ScrollAreaScrollbarVisible,
    {
      "data-state": visible ? "visible" : "hidden",
      ...scrollbarProps,
      ref: forwardedRef
    }
  ) });
});
var ScrollAreaScrollbarVisible = React22.forwardRef((props, forwardedRef) => {
  const { orientation = "vertical", ...scrollbarProps } = props;
  const context = useScrollAreaContext(SCROLLBAR_NAME, props.__scopeScrollArea);
  const thumbRef = React22.useRef(null);
  const pointerOffsetRef = React22.useRef(0);
  const [sizes, setSizes] = React22.useState({
    content: 0,
    viewport: 0,
    scrollbar: { size: 0, paddingStart: 0, paddingEnd: 0 }
  });
  const thumbRatio = getThumbRatio(sizes.viewport, sizes.content);
  const commonProps = {
    ...scrollbarProps,
    sizes,
    onSizesChange: setSizes,
    hasThumb: Boolean(thumbRatio > 0 && thumbRatio < 1),
    onThumbChange: (thumb) => thumbRef.current = thumb,
    onThumbPointerUp: () => pointerOffsetRef.current = 0,
    onThumbPointerDown: (pointerPos) => pointerOffsetRef.current = pointerPos
  };
  function getScrollPosition(pointerPos, dir) {
    return getScrollPositionFromPointer(pointerPos, pointerOffsetRef.current, sizes, dir);
  }
  if (orientation === "horizontal") {
    return /* @__PURE__ */ (0, import_jsx_runtime3.jsx)(
      ScrollAreaScrollbarX,
      {
        ...commonProps,
        ref: forwardedRef,
        onThumbPositionChange: () => {
          if (context.viewport && thumbRef.current) {
            const scrollPos = context.viewport.scrollLeft;
            const offset = getThumbOffsetFromScroll(scrollPos, sizes, context.dir);
            thumbRef.current.style.transform = `translate3d(${offset}px, 0, 0)`;
          }
        },
        onWheelScroll: (scrollPos) => {
          if (context.viewport)
            context.viewport.scrollLeft = scrollPos;
        },
        onDragScroll: (pointerPos) => {
          if (context.viewport) {
            context.viewport.scrollLeft = getScrollPosition(pointerPos, context.dir);
          }
        }
      }
    );
  }
  if (orientation === "vertical") {
    return /* @__PURE__ */ (0, import_jsx_runtime3.jsx)(
      ScrollAreaScrollbarY,
      {
        ...commonProps,
        ref: forwardedRef,
        onThumbPositionChange: () => {
          if (context.viewport && thumbRef.current) {
            const scrollPos = context.viewport.scrollTop;
            const offset = getThumbOffsetFromScroll(scrollPos, sizes);
            thumbRef.current.style.transform = `translate3d(0, ${offset}px, 0)`;
          }
        },
        onWheelScroll: (scrollPos) => {
          if (context.viewport)
            context.viewport.scrollTop = scrollPos;
        },
        onDragScroll: (pointerPos) => {
          if (context.viewport)
            context.viewport.scrollTop = getScrollPosition(pointerPos);
        }
      }
    );
  }
  return null;
});
var ScrollAreaScrollbarX = React22.forwardRef((props, forwardedRef) => {
  const { sizes, onSizesChange, ...scrollbarProps } = props;
  const context = useScrollAreaContext(SCROLLBAR_NAME, props.__scopeScrollArea);
  const [computedStyle, setComputedStyle] = React22.useState();
  const ref = React22.useRef(null);
  const composeRefs = useComposedRefs(forwardedRef, ref, context.onScrollbarXChange);
  React22.useEffect(() => {
    if (ref.current)
      setComputedStyle(getComputedStyle(ref.current));
  }, [ref]);
  return /* @__PURE__ */ (0, import_jsx_runtime3.jsx)(
    ScrollAreaScrollbarImpl,
    {
      "data-orientation": "horizontal",
      ...scrollbarProps,
      ref: composeRefs,
      sizes,
      style: {
        bottom: 0,
        left: context.dir === "rtl" ? "var(--radix-scroll-area-corner-width)" : 0,
        right: context.dir === "ltr" ? "var(--radix-scroll-area-corner-width)" : 0,
        ["--radix-scroll-area-thumb-width"]: getThumbSize(sizes) + "px",
        ...props.style
      },
      onThumbPointerDown: (pointerPos) => props.onThumbPointerDown(pointerPos.x),
      onDragScroll: (pointerPos) => props.onDragScroll(pointerPos.x),
      onWheelScroll: (event, maxScrollPos) => {
        if (context.viewport) {
          const scrollPos = context.viewport.scrollLeft + event.deltaX;
          props.onWheelScroll(scrollPos);
          if (isScrollingWithinScrollbarBounds(scrollPos, maxScrollPos)) {
            event.preventDefault();
          }
        }
      },
      onResize: () => {
        if (ref.current && context.viewport && computedStyle) {
          onSizesChange({
            content: context.viewport.scrollWidth,
            viewport: context.viewport.offsetWidth,
            scrollbar: {
              size: ref.current.clientWidth,
              paddingStart: toInt(computedStyle.paddingLeft),
              paddingEnd: toInt(computedStyle.paddingRight)
            }
          });
        }
      }
    }
  );
});
var ScrollAreaScrollbarY = React22.forwardRef((props, forwardedRef) => {
  const { sizes, onSizesChange, ...scrollbarProps } = props;
  const context = useScrollAreaContext(SCROLLBAR_NAME, props.__scopeScrollArea);
  const [computedStyle, setComputedStyle] = React22.useState();
  const ref = React22.useRef(null);
  const composeRefs = useComposedRefs(forwardedRef, ref, context.onScrollbarYChange);
  React22.useEffect(() => {
    if (ref.current)
      setComputedStyle(getComputedStyle(ref.current));
  }, [ref]);
  return /* @__PURE__ */ (0, import_jsx_runtime3.jsx)(
    ScrollAreaScrollbarImpl,
    {
      "data-orientation": "vertical",
      ...scrollbarProps,
      ref: composeRefs,
      sizes,
      style: {
        top: 0,
        right: context.dir === "ltr" ? 0 : void 0,
        left: context.dir === "rtl" ? 0 : void 0,
        bottom: "var(--radix-scroll-area-corner-height)",
        ["--radix-scroll-area-thumb-height"]: getThumbSize(sizes) + "px",
        ...props.style
      },
      onThumbPointerDown: (pointerPos) => props.onThumbPointerDown(pointerPos.y),
      onDragScroll: (pointerPos) => props.onDragScroll(pointerPos.y),
      onWheelScroll: (event, maxScrollPos) => {
        if (context.viewport) {
          const scrollPos = context.viewport.scrollTop + event.deltaY;
          props.onWheelScroll(scrollPos);
          if (isScrollingWithinScrollbarBounds(scrollPos, maxScrollPos)) {
            event.preventDefault();
          }
        }
      },
      onResize: () => {
        if (ref.current && context.viewport && computedStyle) {
          onSizesChange({
            content: context.viewport.scrollHeight,
            viewport: context.viewport.offsetHeight,
            scrollbar: {
              size: ref.current.clientHeight,
              paddingStart: toInt(computedStyle.paddingTop),
              paddingEnd: toInt(computedStyle.paddingBottom)
            }
          });
        }
      }
    }
  );
});
var [ScrollbarProvider, useScrollbarContext] = createScrollAreaContext(SCROLLBAR_NAME);
var ScrollAreaScrollbarImpl = React22.forwardRef((props, forwardedRef) => {
  const {
    __scopeScrollArea,
    sizes,
    hasThumb,
    onThumbChange,
    onThumbPointerUp,
    onThumbPointerDown,
    onThumbPositionChange,
    onDragScroll,
    onWheelScroll,
    onResize,
    ...scrollbarProps
  } = props;
  const context = useScrollAreaContext(SCROLLBAR_NAME, __scopeScrollArea);
  const [scrollbar, setScrollbar] = React22.useState(null);
  const composeRefs = useComposedRefs(forwardedRef, (node3) => setScrollbar(node3));
  const rectRef = React22.useRef(null);
  const prevWebkitUserSelectRef = React22.useRef("");
  const viewport = context.viewport;
  const maxScrollPos = sizes.content - sizes.viewport;
  const handleWheelScroll = useCallbackRef(onWheelScroll);
  const handleThumbPositionChange = useCallbackRef(onThumbPositionChange);
  const handleResize = useDebounceCallback(onResize, 10);
  function handleDragScroll(event) {
    if (rectRef.current) {
      const x = event.clientX - rectRef.current.left;
      const y = event.clientY - rectRef.current.top;
      onDragScroll({ x, y });
    }
  }
  React22.useEffect(() => {
    const handleWheel = (event) => {
      const element2 = event.target;
      const isScrollbarWheel = scrollbar?.contains(element2);
      if (isScrollbarWheel)
        handleWheelScroll(event, maxScrollPos);
    };
    document.addEventListener("wheel", handleWheel, { passive: false });
    return () => document.removeEventListener("wheel", handleWheel, { passive: false });
  }, [viewport, scrollbar, maxScrollPos, handleWheelScroll]);
  React22.useEffect(handleThumbPositionChange, [sizes, handleThumbPositionChange]);
  useResizeObserver(scrollbar, handleResize);
  useResizeObserver(context.content, handleResize);
  return /* @__PURE__ */ (0, import_jsx_runtime3.jsx)(
    ScrollbarProvider,
    {
      scope: __scopeScrollArea,
      scrollbar,
      hasThumb,
      onThumbChange: useCallbackRef(onThumbChange),
      onThumbPointerUp: useCallbackRef(onThumbPointerUp),
      onThumbPositionChange: handleThumbPositionChange,
      onThumbPointerDown: useCallbackRef(onThumbPointerDown),
      children: /* @__PURE__ */ (0, import_jsx_runtime3.jsx)(
        Primitive.div,
        {
          ...scrollbarProps,
          ref: composeRefs,
          style: { position: "absolute", ...scrollbarProps.style },
          onPointerDown: composeEventHandlers(props.onPointerDown, (event) => {
            const mainPointer = 0;
            if (event.button === mainPointer) {
              const element2 = event.target;
              element2.setPointerCapture(event.pointerId);
              rectRef.current = scrollbar.getBoundingClientRect();
              prevWebkitUserSelectRef.current = document.body.style.webkitUserSelect;
              document.body.style.webkitUserSelect = "none";
              if (context.viewport)
                context.viewport.style.scrollBehavior = "auto";
              handleDragScroll(event);
            }
          }),
          onPointerMove: composeEventHandlers(props.onPointerMove, handleDragScroll),
          onPointerUp: composeEventHandlers(props.onPointerUp, (event) => {
            const element2 = event.target;
            if (element2.hasPointerCapture(event.pointerId)) {
              element2.releasePointerCapture(event.pointerId);
            }
            document.body.style.webkitUserSelect = prevWebkitUserSelectRef.current;
            if (context.viewport)
              context.viewport.style.scrollBehavior = "";
            rectRef.current = null;
          })
        }
      )
    }
  );
});
var THUMB_NAME = "ScrollAreaThumb";
var ScrollAreaThumb = React22.forwardRef(
  (props, forwardedRef) => {
    const { forceMount, ...thumbProps } = props;
    const scrollbarContext = useScrollbarContext(THUMB_NAME, props.__scopeScrollArea);
    return /* @__PURE__ */ (0, import_jsx_runtime3.jsx)(Presence, { present: forceMount || scrollbarContext.hasThumb, children: /* @__PURE__ */ (0, import_jsx_runtime3.jsx)(ScrollAreaThumbImpl, { ref: forwardedRef, ...thumbProps }) });
  }
);
var ScrollAreaThumbImpl = React22.forwardRef(
  (props, forwardedRef) => {
    const { __scopeScrollArea, style, ...thumbProps } = props;
    const scrollAreaContext = useScrollAreaContext(THUMB_NAME, __scopeScrollArea);
    const scrollbarContext = useScrollbarContext(THUMB_NAME, __scopeScrollArea);
    const { onThumbPositionChange } = scrollbarContext;
    const composedRef = useComposedRefs(
      forwardedRef,
      (node3) => scrollbarContext.onThumbChange(node3)
    );
    const removeUnlinkedScrollListenerRef = React22.useRef(void 0);
    const debounceScrollEnd = useDebounceCallback(() => {
      if (removeUnlinkedScrollListenerRef.current) {
        removeUnlinkedScrollListenerRef.current();
        removeUnlinkedScrollListenerRef.current = void 0;
      }
    }, 100);
    React22.useEffect(() => {
      const viewport = scrollAreaContext.viewport;
      if (viewport) {
        const handleScroll = () => {
          debounceScrollEnd();
          if (!removeUnlinkedScrollListenerRef.current) {
            const listener = addUnlinkedScrollListener(viewport, onThumbPositionChange);
            removeUnlinkedScrollListenerRef.current = listener;
            onThumbPositionChange();
          }
        };
        onThumbPositionChange();
        viewport.addEventListener("scroll", handleScroll);
        return () => viewport.removeEventListener("scroll", handleScroll);
      }
    }, [scrollAreaContext.viewport, debounceScrollEnd, onThumbPositionChange]);
    return /* @__PURE__ */ (0, import_jsx_runtime3.jsx)(
      Primitive.div,
      {
        "data-state": scrollbarContext.hasThumb ? "visible" : "hidden",
        ...thumbProps,
        ref: composedRef,
        style: {
          width: "var(--radix-scroll-area-thumb-width)",
          height: "var(--radix-scroll-area-thumb-height)",
          ...style
        },
        onPointerDownCapture: composeEventHandlers(props.onPointerDownCapture, (event) => {
          const thumb = event.target;
          const thumbRect = thumb.getBoundingClientRect();
          const x = event.clientX - thumbRect.left;
          const y = event.clientY - thumbRect.top;
          scrollbarContext.onThumbPointerDown({ x, y });
        }),
        onPointerUp: composeEventHandlers(props.onPointerUp, scrollbarContext.onThumbPointerUp)
      }
    );
  }
);
ScrollAreaThumb.displayName = THUMB_NAME;
var CORNER_NAME = "ScrollAreaCorner";
var ScrollAreaCorner = React22.forwardRef(
  (props, forwardedRef) => {
    const context = useScrollAreaContext(CORNER_NAME, props.__scopeScrollArea);
    const hasBothScrollbarsVisible = Boolean(context.scrollbarX && context.scrollbarY);
    const hasCorner = context.type !== "scroll" && hasBothScrollbarsVisible;
    return hasCorner ? /* @__PURE__ */ (0, import_jsx_runtime3.jsx)(ScrollAreaCornerImpl, { ...props, ref: forwardedRef }) : null;
  }
);
ScrollAreaCorner.displayName = CORNER_NAME;
var ScrollAreaCornerImpl = React22.forwardRef((props, forwardedRef) => {
  const { __scopeScrollArea, ...cornerProps } = props;
  const context = useScrollAreaContext(CORNER_NAME, __scopeScrollArea);
  const [width, setWidth] = React22.useState(0);
  const [height, setHeight] = React22.useState(0);
  const hasSize = Boolean(width && height);
  useResizeObserver(context.scrollbarX, () => {
    const height2 = context.scrollbarX?.offsetHeight || 0;
    context.onCornerHeightChange(height2);
    setHeight(height2);
  });
  useResizeObserver(context.scrollbarY, () => {
    const width2 = context.scrollbarY?.offsetWidth || 0;
    context.onCornerWidthChange(width2);
    setWidth(width2);
  });
  return hasSize ? /* @__PURE__ */ (0, import_jsx_runtime3.jsx)(
    Primitive.div,
    {
      ...cornerProps,
      ref: forwardedRef,
      style: {
        width,
        height,
        position: "absolute",
        right: context.dir === "ltr" ? 0 : void 0,
        left: context.dir === "rtl" ? 0 : void 0,
        bottom: 0,
        ...props.style
      }
    }
  ) : null;
});
function toInt(value) {
  return value ? parseInt(value, 10) : 0;
}
function getThumbRatio(viewportSize, contentSize) {
  const ratio = viewportSize / contentSize;
  return isNaN(ratio) ? 0 : ratio;
}
function getThumbSize(sizes) {
  const ratio = getThumbRatio(sizes.viewport, sizes.content);
  const scrollbarPadding = sizes.scrollbar.paddingStart + sizes.scrollbar.paddingEnd;
  const thumbSize = (sizes.scrollbar.size - scrollbarPadding) * ratio;
  return Math.max(thumbSize, 18);
}
function getScrollPositionFromPointer(pointerPos, pointerOffset, sizes, dir = "ltr") {
  const thumbSizePx = getThumbSize(sizes);
  const thumbCenter = thumbSizePx / 2;
  const offset = pointerOffset || thumbCenter;
  const thumbOffsetFromEnd = thumbSizePx - offset;
  const minPointerPos = sizes.scrollbar.paddingStart + offset;
  const maxPointerPos = sizes.scrollbar.size - sizes.scrollbar.paddingEnd - thumbOffsetFromEnd;
  const maxScrollPos = sizes.content - sizes.viewport;
  const scrollRange = dir === "ltr" ? [0, maxScrollPos] : [maxScrollPos * -1, 0];
  const interpolate = linearScale([minPointerPos, maxPointerPos], scrollRange);
  return interpolate(pointerPos);
}
function getThumbOffsetFromScroll(scrollPos, sizes, dir = "ltr") {
  const thumbSizePx = getThumbSize(sizes);
  const scrollbarPadding = sizes.scrollbar.paddingStart + sizes.scrollbar.paddingEnd;
  const scrollbar = sizes.scrollbar.size - scrollbarPadding;
  const maxScrollPos = sizes.content - sizes.viewport;
  const maxThumbPos = scrollbar - thumbSizePx;
  const scrollClampRange = dir === "ltr" ? [0, maxScrollPos] : [maxScrollPos * -1, 0];
  const scrollWithoutMomentum = clamp(scrollPos, scrollClampRange);
  const interpolate = linearScale([0, maxScrollPos], [0, maxThumbPos]);
  return interpolate(scrollWithoutMomentum);
}
function linearScale(input, output) {
  return (value) => {
    if (input[0] === input[1] || output[0] === output[1])
      return output[0];
    const ratio = (output[1] - output[0]) / (input[1] - input[0]);
    return output[0] + ratio * (value - input[0]);
  };
}
function isScrollingWithinScrollbarBounds(scrollPos, maxScrollPos) {
  return scrollPos > 0 && scrollPos < maxScrollPos;
}
var addUnlinkedScrollListener = (node3, handler = () => {
}) => {
  let prevPosition = { left: node3.scrollLeft, top: node3.scrollTop };
  let rAF = 0;
  (function loop() {
    const position3 = { left: node3.scrollLeft, top: node3.scrollTop };
    const isHorizontalScroll = prevPosition.left !== position3.left;
    const isVerticalScroll = prevPosition.top !== position3.top;
    if (isHorizontalScroll || isVerticalScroll)
      handler();
    prevPosition = position3;
    rAF = window.requestAnimationFrame(loop);
  })();
  return () => window.cancelAnimationFrame(rAF);
};
function useDebounceCallback(callback, delay) {
  const handleCallback = useCallbackRef(callback);
  const debounceTimerRef = React22.useRef(0);
  React22.useEffect(() => () => window.clearTimeout(debounceTimerRef.current), []);
  return React22.useCallback(() => {
    window.clearTimeout(debounceTimerRef.current);
    debounceTimerRef.current = window.setTimeout(handleCallback, delay);
  }, [handleCallback, delay]);
}
function useResizeObserver(element2, onResize) {
  const handleResize = useCallbackRef(onResize);
  useLayoutEffect2(() => {
    let rAF = 0;
    if (element2) {
      const resizeObserver = new ResizeObserver(() => {
        cancelAnimationFrame(rAF);
        rAF = window.requestAnimationFrame(handleResize);
      });
      resizeObserver.observe(element2);
      return () => {
        window.cancelAnimationFrame(rAF);
        resizeObserver.unobserve(element2);
      };
    }
  }, [element2, handleResize]);
}
var Root3 = ScrollArea;
var Viewport = ScrollAreaViewport;
var Corner = ScrollAreaCorner;

// app/components/ui/scroll-area.tsx
var import_jsx_dev_runtime10 = __toESM(require_jsx_dev_runtime(), 1);
if (!window.$RefreshReg$ || !window.$RefreshSig$ || !window.$RefreshRuntime$) {
  console.warn("remix:hmr: React Fast Refresh only works when the Remix compiler is running in development mode.");
} else {
  prevRefreshReg = window.$RefreshReg$;
  prevRefreshSig = window.$RefreshSig$;
  window.$RefreshReg$ = (type, id) => {
    window.$RefreshRuntime$.register(type, '"app/components/ui/scroll-area.tsx"' + id);
  };
  window.$RefreshSig$ = window.$RefreshRuntime$.createSignatureFunctionForTransform;
}
var prevRefreshReg;
var prevRefreshSig;
if (import.meta) {
  import.meta.hot = createHotContext(
    //@ts-expect-error
    "app/components/ui/scroll-area.tsx"
  );
  import.meta.hot.lastModified = "1738662837907.6753";
}
var ScrollArea2 = React11.forwardRef(_c10 = ({
  className,
  children,
  ...props
}, ref) => /* @__PURE__ */ (0, import_jsx_dev_runtime10.jsxDEV)(Root3, { ref, className: cn("relative overflow-hidden", className), ...props, children: [
  /* @__PURE__ */ (0, import_jsx_dev_runtime10.jsxDEV)(Viewport, { className: "h-full w-full rounded-[inherit]", children }, void 0, false, {
    fileName: "app/components/ui/scroll-area.tsx",
    lineNumber: 29,
    columnNumber: 5
  }, this),
  /* @__PURE__ */ (0, import_jsx_dev_runtime10.jsxDEV)(ScrollBar, {}, void 0, false, {
    fileName: "app/components/ui/scroll-area.tsx",
    lineNumber: 32,
    columnNumber: 5
  }, this),
  /* @__PURE__ */ (0, import_jsx_dev_runtime10.jsxDEV)(Corner, {}, void 0, false, {
    fileName: "app/components/ui/scroll-area.tsx",
    lineNumber: 33,
    columnNumber: 5
  }, this)
] }, void 0, true, {
  fileName: "app/components/ui/scroll-area.tsx",
  lineNumber: 28,
  columnNumber: 12
}, this));
_c25 = ScrollArea2;
ScrollArea2.displayName = Root3.displayName;
var ScrollBar = React11.forwardRef(_c34 = ({
  className,
  orientation = "vertical",
  ...props
}, ref) => /* @__PURE__ */ (0, import_jsx_dev_runtime10.jsxDEV)(ScrollAreaScrollbar, { ref, orientation, className: cn("flex touch-none select-none transition-colors", orientation === "vertical" && "h-full w-2.5 border-l border-l-transparent p-[1px]", orientation === "horizontal" && "h-2.5 flex-col border-t border-t-transparent p-[1px]", className), ...props, children: /* @__PURE__ */ (0, import_jsx_dev_runtime10.jsxDEV)(ScrollAreaThumb, { className: "relative flex-1 rounded-full bg-border" }, void 0, false, {
  fileName: "app/components/ui/scroll-area.tsx",
  lineNumber: 42,
  columnNumber: 5
}, this) }, void 0, false, {
  fileName: "app/components/ui/scroll-area.tsx",
  lineNumber: 41,
  columnNumber: 12
}, this));
_c44 = ScrollBar;
ScrollBar.displayName = ScrollAreaScrollbar.displayName;
var _c10;
var _c25;
var _c34;
var _c44;
$RefreshReg$(_c10, "ScrollArea$React.forwardRef");
$RefreshReg$(_c25, "ScrollArea");
$RefreshReg$(_c34, "ScrollBar$React.forwardRef");
$RefreshReg$(_c44, "ScrollBar");
window.$RefreshReg$ = prevRefreshReg;
window.$RefreshSig$ = prevRefreshSig;

// app/components/layout/session-timeout-warning.tsx
var import_react7 = __toESM(require_react(), 1);
var import_jsx_dev_runtime11 = __toESM(require_jsx_dev_runtime(), 1);
if (!window.$RefreshReg$ || !window.$RefreshSig$ || !window.$RefreshRuntime$) {
  console.warn("remix:hmr: React Fast Refresh only works when the Remix compiler is running in development mode.");
} else {
  prevRefreshReg = window.$RefreshReg$;
  prevRefreshSig = window.$RefreshSig$;
  window.$RefreshReg$ = (type, id) => {
    window.$RefreshRuntime$.register(type, '"app/components/layout/session-timeout-warning.tsx"' + id);
  };
  window.$RefreshSig$ = window.$RefreshRuntime$.createSignatureFunctionForTransform;
}
var prevRefreshReg;
var prevRefreshSig;
var _s5 = $RefreshSig$();
if (import.meta) {
  import.meta.hot = createHotContext(
    //@ts-expect-error
    "app/components/layout/session-timeout-warning.tsx"
  );
  import.meta.hot.lastModified = "1738670458389.6924";
}
function SessionTimeoutWarning({
  timeoutMinutes,
  onTimeout
}) {
  _s5();
  const [remainingTime, setRemainingTime] = (0, import_react7.useState)(timeoutMinutes * 60);
  const [showWarning, setShowWarning] = (0, import_react7.useState)(false);
  const resetTimer = () => {
    setRemainingTime(timeoutMinutes * 60);
    setShowWarning(false);
  };
  (0, import_react7.useEffect)(() => {
    let timer;
    const warningTime = 60;
    const updateTimer = () => {
      setRemainingTime((prev) => {
        const newTime = prev - 1;
        if (newTime <= 0) {
          onTimeout();
          return 0;
        }
        if (newTime <= warningTime) {
          setShowWarning(true);
        }
        return newTime;
      });
    };
    timer = setInterval(updateTimer, 1e3);
    return () => clearInterval(timer);
  }, [timeoutMinutes, onTimeout]);
  if (!showWarning)
    return null;
  const seconds = remainingTime % 60;
  return /* @__PURE__ */ (0, import_jsx_dev_runtime11.jsxDEV)(Alert, { className: "fixed bottom-4 right-4 max-w-md bg-yellow-50 border-yellow-200 dark:bg-yellow-900/10 dark:border-yellow-900/20", children: /* @__PURE__ */ (0, import_jsx_dev_runtime11.jsxDEV)(AlertDescription, { className: "flex flex-col gap-3", children: [
    /* @__PURE__ */ (0, import_jsx_dev_runtime11.jsxDEV)("p", { children: [
      "Your session will expire in ",
      seconds,
      " seconds."
    ] }, void 0, true, {
      fileName: "app/components/layout/session-timeout-warning.tsx",
      lineNumber: 63,
      columnNumber: 9
    }, this),
    /* @__PURE__ */ (0, import_jsx_dev_runtime11.jsxDEV)("div", { className: "flex justify-end gap-2", children: [
      /* @__PURE__ */ (0, import_jsx_dev_runtime11.jsxDEV)(Button, { variant: "outline", onClick: resetTimer, children: "Continue Session" }, void 0, false, {
        fileName: "app/components/layout/session-timeout-warning.tsx",
        lineNumber: 65,
        columnNumber: 11
      }, this),
      /* @__PURE__ */ (0, import_jsx_dev_runtime11.jsxDEV)(Button, { variant: "destructive", onClick: onTimeout, children: "Log Off" }, void 0, false, {
        fileName: "app/components/layout/session-timeout-warning.tsx",
        lineNumber: 68,
        columnNumber: 11
      }, this)
    ] }, void 0, true, {
      fileName: "app/components/layout/session-timeout-warning.tsx",
      lineNumber: 64,
      columnNumber: 9
    }, this)
  ] }, void 0, true, {
    fileName: "app/components/layout/session-timeout-warning.tsx",
    lineNumber: 62,
    columnNumber: 7
  }, this) }, void 0, false, {
    fileName: "app/components/layout/session-timeout-warning.tsx",
    lineNumber: 61,
    columnNumber: 10
  }, this);
}
_s5(SessionTimeoutWarning, "rI6RN4dkN4h+0dmmk6/bPk1L+Jk=");
_c11 = SessionTimeoutWarning;
var _c11;
$RefreshReg$(_c11, "SessionTimeoutWarning");
window.$RefreshReg$ = prevRefreshReg;
window.$RefreshSig$ = prevRefreshSig;

// app/routes/chat.tsx
var import_session2 = __toESM(require_session(), 1);
var import_jsx_dev_runtime12 = __toESM(require_jsx_dev_runtime(), 1);
if (!window.$RefreshReg$ || !window.$RefreshSig$ || !window.$RefreshRuntime$) {
  console.warn("remix:hmr: React Fast Refresh only works when the Remix compiler is running in development mode.");
} else {
  prevRefreshReg = window.$RefreshReg$;
  prevRefreshSig = window.$RefreshSig$;
  window.$RefreshReg$ = (type, id) => {
    window.$RefreshRuntime$.register(type, '"app/routes/chat.tsx"' + id);
  };
  window.$RefreshSig$ = window.$RefreshRuntime$.createSignatureFunctionForTransform;
}
var prevRefreshReg;
var prevRefreshSig;
var _s6 = $RefreshSig$();
if (import.meta) {
  import.meta.hot = createHotContext(
    //@ts-expect-error
    "app/routes/chat.tsx"
  );
  import.meta.hot.lastModified = "1738670458389.6924";
}
function Chat() {
  _s6();
  const {
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
  } = useChat();
  const [isNewChatOpen, setIsNewChatOpen] = (0, import_react8.useState)(false);
  const scrollAreaRef = (0, import_react8.useRef)(null);
  const isAutoScrollEnabled = (0, import_react8.useRef)(true);
  const lastMessageRef = (0, import_react8.useRef)(null);
  const navigate = useNavigate();
  const {
    sessionTimeoutMinutes
  } = useLoaderData();
  (0, import_react8.useEffect)(() => {
    if (scrollAreaRef.current && isAutoScrollEnabled.current) {
      const scrollContainer = scrollAreaRef.current.querySelector("[data-radix-scroll-area-viewport]");
      if (scrollContainer) {
        scrollContainer.scrollTop = scrollContainer.scrollHeight;
      }
    }
  }, [messages, isLoading]);
  (0, import_react8.useEffect)(() => {
    const scrollContainer = scrollAreaRef.current?.querySelector("[data-radix-scroll-area-viewport]");
    if (!scrollContainer)
      return;
    const handleScroll = () => {
      const {
        scrollTop,
        scrollHeight,
        clientHeight
      } = scrollContainer;
      const isNearBottom = scrollHeight - (scrollTop + clientHeight) < 100;
      isAutoScrollEnabled.current = isNearBottom;
    };
    scrollContainer.addEventListener("scroll", handleScroll);
    return () => scrollContainer.removeEventListener("scroll", handleScroll);
  }, []);
  const handleNewChat = async (title) => {
    await startNewChat(title);
    setIsNewChatOpen(false);
  };
  const handleTimeout = () => {
    document.getElementById("logoutForm")?.submit();
  };
  return /* @__PURE__ */ (0, import_jsx_dev_runtime12.jsxDEV)("div", { className: "container py-8 mx-auto", children: [
    /* @__PURE__ */ (0, import_jsx_dev_runtime12.jsxDEV)(Card, { className: "h-[calc(100vh-16rem)] flex flex-col border-0", children: [
      /* @__PURE__ */ (0, import_jsx_dev_runtime12.jsxDEV)(ChatHeader, { isLoading, onNewChat: () => setIsNewChatOpen(true), onSelectChat: selectChat, onClearChat: deleteChat, sessions, currentSession, progress }, void 0, false, {
        fileName: "app/routes/chat.tsx",
        lineNumber: 117,
        columnNumber: 9
      }, this),
      /* @__PURE__ */ (0, import_jsx_dev_runtime12.jsxDEV)(ScrollArea2, { ref: scrollAreaRef, className: "flex-1 p-4", children: [
        messages.map((message, index2) => /* @__PURE__ */ (0, import_jsx_dev_runtime12.jsxDEV)("div", { ref: index2 === messages.length - 1 ? lastMessageRef : null, children: /* @__PURE__ */ (0, import_jsx_dev_runtime12.jsxDEV)(ChatMessage, { message, isLoading: isLoading && index2 === messages.length - 1 }, void 0, false, {
          fileName: "app/routes/chat.tsx",
          lineNumber: 120,
          columnNumber: 15
        }, this) }, index2, false, {
          fileName: "app/routes/chat.tsx",
          lineNumber: 119,
          columnNumber: 45
        }, this)),
        error && /* @__PURE__ */ (0, import_jsx_dev_runtime12.jsxDEV)(Alert, { variant: "destructive", className: "mt-4", children: /* @__PURE__ */ (0, import_jsx_dev_runtime12.jsxDEV)(AlertDescription, { children: error }, void 0, false, {
          fileName: "app/routes/chat.tsx",
          lineNumber: 123,
          columnNumber: 15
        }, this) }, void 0, false, {
          fileName: "app/routes/chat.tsx",
          lineNumber: 122,
          columnNumber: 21
        }, this)
      ] }, void 0, true, {
        fileName: "app/routes/chat.tsx",
        lineNumber: 118,
        columnNumber: 9
      }, this),
      /* @__PURE__ */ (0, import_jsx_dev_runtime12.jsxDEV)("div", { className: "p-4 border-t", children: /* @__PURE__ */ (0, import_jsx_dev_runtime12.jsxDEV)(ChatInput, { input, handleInputChange, handleSubmit, isLoading, hasActiveSession: !!currentSession }, void 0, false, {
        fileName: "app/routes/chat.tsx",
        lineNumber: 127,
        columnNumber: 11
      }, this) }, void 0, false, {
        fileName: "app/routes/chat.tsx",
        lineNumber: 126,
        columnNumber: 9
      }, this)
    ] }, void 0, true, {
      fileName: "app/routes/chat.tsx",
      lineNumber: 116,
      columnNumber: 7
    }, this),
    /* @__PURE__ */ (0, import_jsx_dev_runtime12.jsxDEV)(NewChatDialog, { isOpen: isNewChatOpen, onClose: () => setIsNewChatOpen(false), onCreateChat: handleNewChat }, void 0, false, {
      fileName: "app/routes/chat.tsx",
      lineNumber: 130,
      columnNumber: 7
    }, this),
    /* @__PURE__ */ (0, import_jsx_dev_runtime12.jsxDEV)(Form, { method: "post", id: "logoutForm", className: "hidden" }, void 0, false, {
      fileName: "app/routes/chat.tsx",
      lineNumber: 131,
      columnNumber: 7
    }, this),
    /* @__PURE__ */ (0, import_jsx_dev_runtime12.jsxDEV)(SessionTimeoutWarning, { timeoutMinutes: sessionTimeoutMinutes, onTimeout: handleTimeout }, void 0, false, {
      fileName: "app/routes/chat.tsx",
      lineNumber: 132,
      columnNumber: 7
    }, this)
  ] }, void 0, true, {
    fileName: "app/routes/chat.tsx",
    lineNumber: 115,
    columnNumber: 10
  }, this);
}
_s6(Chat, "b50ZIGP1k9chNbnAbsfxJN7A6yo=", false, function() {
  return [useChat, useNavigate, useLoaderData];
});
_c12 = Chat;
var _c12;
$RefreshReg$(_c12, "Chat");
window.$RefreshReg$ = prevRefreshReg;
window.$RefreshSig$ = prevRefreshSig;
export {
  Chat as default
};
/*! Bundled license information:

is-buffer/index.js:
  (*!
   * Determine if an object is a Buffer
   *
   * @author   Feross Aboukhadijeh <https://feross.org>
   * @license  MIT
   *)

react-is/cjs/react-is.development.js:
  (** @license React v16.13.1
   * react-is.development.js
   *
   * Copyright (c) Facebook, Inc. and its affiliates.
   *
   * This source code is licensed under the MIT license found in the
   * LICENSE file in the root directory of this source tree.
   *)

object-assign/index.js:
  (*
  object-assign
  (c) Sindre Sorhus
  @license MIT
  *)

react-is/cjs/react-is.development.js:
  (**
   * @license React
   * react-is.development.js
   *
   * Copyright (c) Facebook, Inc. and its affiliates.
   *
   * This source code is licensed under the MIT license found in the
   * LICENSE file in the root directory of this source tree.
   *)
*/
//# sourceMappingURL=/build/routes/chat-FPLFVKHX.js.map
