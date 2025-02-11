import {
  require_react
} from "/build/_shared/chunk-QPVUD6NO.js";
import {
  __toESM
} from "/build/_shared/chunk-PZDJHGND.js";

// node_modules/.pnpm/markdown-to-jsx@7.7.3_react@18.3.1/node_modules/markdown-to-jsx/dist/index.modern.js
var e = __toESM(require_react(), 1);
function t() {
  return t = Object.assign ? Object.assign.bind() : function(e2) {
    for (var t2 = 1; t2 < arguments.length; t2++) {
      var n2 = arguments[t2];
      for (var r2 in n2)
        Object.prototype.hasOwnProperty.call(n2, r2) && (e2[r2] = n2[r2]);
    }
    return e2;
  }, t.apply(this, arguments);
}
var n = ["children", "options"];
var r = { blockQuote: "0", breakLine: "1", breakThematic: "2", codeBlock: "3", codeFenced: "4", codeInline: "5", footnote: "6", footnoteReference: "7", gfmTask: "8", heading: "9", headingSetext: "10", htmlBlock: "11", htmlComment: "12", htmlSelfClosing: "13", image: "14", link: "15", linkAngleBraceStyleDetector: "16", linkBareUrlDetector: "17", linkMailtoDetector: "18", newlineCoalescer: "19", orderedList: "20", paragraph: "21", ref: "22", refImage: "23", refLink: "24", table: "25", tableSeparator: "26", text: "27", textBolded: "28", textEmphasized: "29", textEscaped: "30", textMarked: "31", textStrikethroughed: "32", unorderedList: "33" };
var i;
!function(e2) {
  e2[e2.MAX = 0] = "MAX", e2[e2.HIGH = 1] = "HIGH", e2[e2.MED = 2] = "MED", e2[e2.LOW = 3] = "LOW", e2[e2.MIN = 4] = "MIN";
}(i || (i = {}));
var l = ["allowFullScreen", "allowTransparency", "autoComplete", "autoFocus", "autoPlay", "cellPadding", "cellSpacing", "charSet", "classId", "colSpan", "contentEditable", "contextMenu", "crossOrigin", "encType", "formAction", "formEncType", "formMethod", "formNoValidate", "formTarget", "frameBorder", "hrefLang", "inputMode", "keyParams", "keyType", "marginHeight", "marginWidth", "maxLength", "mediaGroup", "minLength", "noValidate", "radioGroup", "readOnly", "rowSpan", "spellCheck", "srcDoc", "srcLang", "srcSet", "tabIndex", "useMap"].reduce((e2, t2) => (e2[t2.toLowerCase()] = t2, e2), { class: "className", for: "htmlFor" });
var a = { amp: "&", apos: "'", gt: ">", lt: "<", nbsp: "\xA0", quot: "\u201C" };
var o = ["style", "script"];
var c = /([-A-Z0-9_:]+)(?:\s*=\s*(?:(?:"((?:\\.|[^"])*)")|(?:'((?:\\.|[^'])*)')|(?:\{((?:\\.|{[^}]*?}|[^}])*)\})))?/gi;
var s = /mailto:/i;
var d = /\n{2,}$/;
var u = /^(\s*>[\s\S]*?)(?=\n\n|$)/;
var p = /^ *> ?/gm;
var f = /^(?:\[!([^\]]*)\]\n)?([\s\S]*)/;
var h = /^ {2,}\n/;
var m = /^(?:( *[-*_])){3,} *(?:\n *)+\n/;
var g = /^(?: {1,3})?(`{3,}|~{3,}) *(\S+)? *([^\n]*?)?\n([\s\S]*?)(?:\1\n?|$)/;
var y = /^(?: {4}[^\n]+\n*)+(?:\n *)+\n?/;
var k = /^(`+)\s*([\s\S]*?[^`])\s*\1(?!`)/;
var x = /^(?:\n *)*\n/;
var b = /\r\n?/g;
var v = /^\[\^([^\]]+)](:(.*)((\n+ {4,}.*)|(\n(?!\[\^).+))*)/;
var C = /^\[\^([^\]]+)]/;
var $ = /\f/g;
var S = /^---[ \t]*\n(.|\n)*\n---[ \t]*\n/;
var w = /^\s*?\[(x|\s)\]/;
var E = /^ *(#{1,6}) *([^\n]+?)(?: +#*)?(?:\n *)*(?:\n|$)/;
var z = /^ *(#{1,6}) +([^\n]+?)(?: +#*)?(?:\n *)*(?:\n|$)/;
var L = /^([^\n]+)\n *(=|-){3,} *(?:\n *)+\n/;
var A = /^ *(?!<[a-z][^ >/]* ?\/>)<([a-z][^ >/]*) ?((?:[^>]*[^/])?)>\n?(\s*(?:<\1[^>]*?>[\s\S]*?<\/\1>|(?!<\1\b)[\s\S])*?)<\/\1>(?!<\/\1>)\n*/i;
var T = /&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-fA-F]{1,6});/gi;
var B = /^<!--[\s\S]*?(?:-->)/;
var O = /^(data|aria|x)-[a-z_][a-z\d_.-]*$/;
var M = /^ *<([a-z][a-z0-9:]*)(?:\s+((?:<.*?>|[^>])*))?\/?>(?!<\/\1>)(\s*\n)?/i;
var R = /^\{.*\}$/;
var I = /^(https?:\/\/[^\s<]+[^<.,:;"')\]\s])/;
var U = /^<([^ >]+@[^ >]+)>/;
var D = /^<([^ >]+:\/[^ >]+)>/;
var N = /-([a-z])?/gi;
var j = /^(\|.*)\n(?: *(\|? *[-:]+ *\|[-| :]*)\n((?:.*\|.*\n)*))?\n?/;
var H = /^\[([^\]]*)\]:\s+<?([^\s>]+)>?\s*("([^"]*)")?/;
var P = /^!\[([^\]]*)\] ?\[([^\]]*)\]/;
var F = /^\[([^\]]*)\] ?\[([^\]]*)\]/;
var _ = /(\n|^[-*]\s|^#|^ {2,}|^-{2,}|^>\s)/;
var G = /\t/g;
var W = /(^ *\||\| *$)/g;
var Z = /^ *:-+: *$/;
var q = /^ *:-+ *$/;
var Q = /^ *-+: *$/;
var V = "((?:\\[.*?\\][([].*?[)\\]]|<.*?>(?:.*?<.*?>)?|`.*?`|~~.*?~~|==.*?==|.|\\n)*?)";
var X = new RegExp(`^([*_])\\1${V}\\1\\1(?!\\1)`);
var J = new RegExp(`^([*_])${V}\\1(?!\\1|\\w)`);
var K = new RegExp(`^==${V}==`);
var Y = new RegExp(`^~~${V}~~`);
var ee = /^\\([^0-9A-Za-z\s])/;
var te = /^[\s\S]+?(?=[^0-9A-Z\s\u00c0-\uffff&#;.()'"]|\d+\.|\n\n| {2,}\n|\w+:\S|$)/i;
var ne = /^\n+/;
var re = /^([ \t]*)/;
var ie = /\\([^\\])/g;
var le = / *\n+$/;
var ae = /(?:^|\n)( *)$/;
var oe = "(?:\\d+\\.)";
var ce = "(?:[*+-])";
function se(e2) {
  return "( *)(" + (1 === e2 ? oe : ce) + ") +";
}
var de = se(1);
var ue = se(2);
function pe(e2) {
  return new RegExp("^" + (1 === e2 ? de : ue));
}
var fe = pe(1);
var he = pe(2);
function me(e2) {
  return new RegExp("^" + (1 === e2 ? de : ue) + "[^\\n]*(?:\\n(?!\\1" + (1 === e2 ? oe : ce) + " )[^\\n]*)*(\\n|$)", "gm");
}
var ge = me(1);
var ye = me(2);
function ke(e2) {
  const t2 = 1 === e2 ? oe : ce;
  return new RegExp("^( *)(" + t2 + ") [\\s\\S]+?(?:\\n{2,}(?! )(?!\\1" + t2 + " (?!" + t2 + " ))\\n*|\\s*\\n*$)");
}
var xe = ke(1);
var be = ke(2);
function ve(e2, t2) {
  const n2 = 1 === t2, i2 = n2 ? xe : be, l2 = n2 ? ge : ye, a2 = n2 ? fe : he;
  return { match(e3, t3) {
    const n3 = ae.exec(t3.prevCapture);
    return n3 && (t3.list || !t3.inline && !t3.simple) ? i2.exec(e3 = n3[1] + e3) : null;
  }, order: 1, parse(e3, t3, r2) {
    const i3 = n2 ? +e3[2] : void 0, o2 = e3[0].replace(d, "\n").match(l2);
    let c2 = false;
    return { items: o2.map(function(e4, n3) {
      const i4 = a2.exec(e4)[0].length, l3 = new RegExp("^ {1," + i4 + "}", "gm"), s2 = e4.replace(l3, "").replace(a2, ""), d2 = n3 === o2.length - 1, u2 = -1 !== s2.indexOf("\n\n") || d2 && c2;
      c2 = u2;
      const p2 = r2.inline, f2 = r2.list;
      let h2;
      r2.list = true, u2 ? (r2.inline = false, h2 = s2.replace(le, "\n\n")) : (r2.inline = true, h2 = s2.replace(le, ""));
      const m2 = t3(h2, r2);
      return r2.inline = p2, r2.list = f2, m2;
    }), ordered: n2, start: i3 };
  }, render: (t3, n3, i3) => e2(t3.ordered ? "ol" : "ul", { key: i3.key, start: t3.type === r.orderedList ? t3.start : void 0 }, t3.items.map(function(t4, r2) {
    return e2("li", { key: r2 }, n3(t4, i3));
  })) };
}
var Ce = new RegExp(`^\\[((?:\\[[^\\]]*\\]|[^\\[\\]]|\\](?=[^\\[]*\\]))*)\\]\\(\\s*<?((?:\\([^)]*\\)|[^\\s\\\\]|\\\\.)*?)>?(?:\\s+['"]([\\s\\S]*?)['"])?\\s*\\)`);
var $e = /^!\[(.*?)\]\( *((?:\([^)]*\)|[^() ])*) *"?([^)"]*)?"?\)/;
var Se = [u, g, y, E, L, z, B, j, ge, xe, ye, be];
var we = [...Se, /^[^\n]+(?:  \n|\n{2,})/, A, M];
function Ee(e2) {
  return e2.replace(/[ÀÁÂÃÄÅàáâãäåæÆ]/g, "a").replace(/[çÇ]/g, "c").replace(/[ðÐ]/g, "d").replace(/[ÈÉÊËéèêë]/g, "e").replace(/[ÏïÎîÍíÌì]/g, "i").replace(/[Ññ]/g, "n").replace(/[øØœŒÕõÔôÓóÒò]/g, "o").replace(/[ÜüÛûÚúÙù]/g, "u").replace(/[ŸÿÝý]/g, "y").replace(/[^a-z0-9- ]/gi, "").replace(/ /gi, "-").toLowerCase();
}
function ze(e2) {
  return Q.test(e2) ? "right" : Z.test(e2) ? "center" : q.test(e2) ? "left" : null;
}
function Le(e2, t2, n2, r2) {
  const i2 = n2.inTable;
  n2.inTable = true;
  let l2 = [[]], a2 = "";
  function o2() {
    if (!a2)
      return;
    const e3 = l2[l2.length - 1];
    e3.push.apply(e3, t2(a2, n2)), a2 = "";
  }
  return e2.trim().split(/(`[^`]*`|\\\||\|)/).filter(Boolean).forEach((e3, t3, n3) => {
    "|" === e3.trim() && (o2(), r2) ? 0 !== t3 && t3 !== n3.length - 1 && l2.push([]) : a2 += e3;
  }), o2(), n2.inTable = i2, l2;
}
function Ae(e2, t2, n2) {
  n2.inline = true;
  const i2 = e2[2] ? e2[2].replace(W, "").split("|").map(ze) : [], l2 = e2[3] ? function(e3, t3, n3) {
    return e3.trim().split("\n").map(function(e4) {
      return Le(e4, t3, n3, true);
    });
  }(e2[3], t2, n2) : [], a2 = Le(e2[1], t2, n2, !!l2.length);
  return n2.inline = false, l2.length ? { align: i2, cells: l2, header: a2, type: r.table } : { children: a2, type: r.paragraph };
}
function Te(e2, t2) {
  return null == e2.align[t2] ? {} : { textAlign: e2.align[t2] };
}
function Be(e2) {
  return function(t2, n2) {
    return n2.inline ? e2.exec(t2) : null;
  };
}
function Oe(e2) {
  return function(t2, n2) {
    return n2.inline || n2.simple ? e2.exec(t2) : null;
  };
}
function Me(e2) {
  return function(t2, n2) {
    return n2.inline || n2.simple ? null : e2.exec(t2);
  };
}
function Re(e2) {
  return function(t2) {
    return e2.exec(t2);
  };
}
function Ie(e2, t2) {
  if (t2.inline || t2.simple)
    return null;
  let n2 = "";
  e2.split("\n").every((e3) => (e3 += "\n", !Se.some((t3) => t3.test(e3)) && (n2 += e3, !!e3.trim())));
  const r2 = n2.trimEnd();
  return "" == r2 ? null : [n2, r2];
}
function Ue(e2) {
  try {
    if (decodeURIComponent(e2).replace(/[^A-Za-z0-9/:]/g, "").match(/^\s*(javascript|vbscript|data(?!:image)):/i))
      return null;
  } catch (e3) {
    return null;
  }
  return e2;
}
function De(e2) {
  return e2.replace(ie, "$1");
}
function Ne(e2, t2, n2) {
  const r2 = n2.inline || false, i2 = n2.simple || false;
  n2.inline = true, n2.simple = true;
  const l2 = e2(t2, n2);
  return n2.inline = r2, n2.simple = i2, l2;
}
function je(e2, t2, n2) {
  const r2 = n2.inline || false, i2 = n2.simple || false;
  n2.inline = false, n2.simple = true;
  const l2 = e2(t2, n2);
  return n2.inline = r2, n2.simple = i2, l2;
}
function He(e2, t2, n2) {
  const r2 = n2.inline || false;
  n2.inline = false;
  const i2 = e2(t2, n2);
  return n2.inline = r2, i2;
}
var Pe = (e2, t2, n2) => ({ children: Ne(t2, e2[1], n2) });
function Fe() {
  return {};
}
function _e() {
  return null;
}
function Ge(...e2) {
  return e2.filter(Boolean).join(" ");
}
function We(e2, t2, n2) {
  let r2 = e2;
  const i2 = t2.split(".");
  for (; i2.length && (r2 = r2[i2[0]], void 0 !== r2); )
    i2.shift();
  return r2 || n2;
}
function Ze(n2 = "", i2 = {}) {
  function d2(e2, n3, ...r2) {
    const l2 = We(i2.overrides, `${e2}.props`, {});
    return i2.createElement(function(e3, t2) {
      const n4 = We(t2, e3);
      return n4 ? "function" == typeof n4 || "object" == typeof n4 && "render" in n4 ? n4 : We(t2, `${e3}.component`, e3) : e3;
    }(e2, i2.overrides), t({}, n3, l2, { className: Ge(null == n3 ? void 0 : n3.className, l2.className) || void 0 }), ...r2);
  }
  function W2(e2) {
    e2 = e2.replace(S, "");
    let t2 = false;
    i2.forceInline ? t2 = true : i2.forceBlock || (t2 = false === _.test(e2));
    const n3 = le2(ie2(t2 ? e2 : `${e2.trimEnd().replace(ne, "")}

`, { inline: t2 }));
    for (; "string" == typeof n3[n3.length - 1] && !n3[n3.length - 1].trim(); )
      n3.pop();
    if (null === i2.wrapper)
      return n3;
    const r2 = i2.wrapper || (t2 ? "span" : "div");
    let l2;
    if (n3.length > 1 || i2.forceWrapper)
      l2 = n3;
    else {
      if (1 === n3.length)
        return l2 = n3[0], "string" == typeof l2 ? d2("span", { key: "outer" }, l2) : l2;
      l2 = null;
    }
    return i2.createElement(r2, { key: "outer" }, l2);
  }
  function Z2(e2, t2) {
    const n3 = t2.match(c);
    return n3 ? n3.reduce(function(t3, n4) {
      const r2 = n4.indexOf("=");
      if (-1 !== r2) {
        const a2 = function(e3) {
          return -1 !== e3.indexOf("-") && null === e3.match(O) && (e3 = e3.replace(N, function(e4, t4) {
            return t4.toUpperCase();
          })), e3;
        }(n4.slice(0, r2)).trim(), o2 = function(e3) {
          const t4 = e3[0];
          return ('"' === t4 || "'" === t4) && e3.length >= 2 && e3[e3.length - 1] === t4 ? e3.slice(1, -1) : e3;
        }(n4.slice(r2 + 1).trim()), c2 = l[a2] || a2;
        if ("ref" === c2)
          return t3;
        const s2 = t3[c2] = function(e3, t4, n5, r3) {
          return "style" === t4 ? n5.split(/;\s?/).reduce(function(e4, t5) {
            const n6 = t5.slice(0, t5.indexOf(":"));
            return e4[n6.trim().replace(/(-[a-z])/g, (e5) => e5[1].toUpperCase())] = t5.slice(n6.length + 1).trim(), e4;
          }, {}) : "href" === t4 || "src" === t4 ? r3(n5, e3, t4) : (n5.match(R) && (n5 = n5.slice(1, n5.length - 1)), "true" === n5 || "false" !== n5 && n5);
        }(e2, a2, o2, i2.sanitizer);
        "string" == typeof s2 && (A.test(s2) || M.test(s2)) && (t3[c2] = W2(s2.trim()));
      } else
        "style" !== n4 && (t3[l[n4] || n4] = true);
      return t3;
    }, {}) : null;
  }
  i2.overrides = i2.overrides || {}, i2.sanitizer = i2.sanitizer || Ue, i2.slugify = i2.slugify || Ee, i2.namedCodesToUnicode = i2.namedCodesToUnicode ? t({}, a, i2.namedCodesToUnicode) : a, i2.createElement = i2.createElement || e.createElement;
  const q2 = [], Q2 = {}, V2 = { [r.blockQuote]: { match: Me(u), order: 1, parse(e2, t2, n3) {
    const [, r2, i3] = e2[0].replace(p, "").match(f);
    return { alert: r2, children: t2(i3, n3) };
  }, render(e2, t2, n3) {
    const l2 = { key: n3.key };
    return e2.alert && (l2.className = "markdown-alert-" + i2.slugify(e2.alert.toLowerCase(), Ee), e2.children.unshift({ attrs: {}, children: [{ type: r.text, text: e2.alert }], noInnerParse: true, type: r.htmlBlock, tag: "header" })), d2("blockquote", l2, t2(e2.children, n3));
  } }, [r.breakLine]: { match: Re(h), order: 1, parse: Fe, render: (e2, t2, n3) => d2("br", { key: n3.key }) }, [r.breakThematic]: { match: Me(m), order: 1, parse: Fe, render: (e2, t2, n3) => d2("hr", { key: n3.key }) }, [r.codeBlock]: { match: Me(y), order: 0, parse: (e2) => ({ lang: void 0, text: e2[0].replace(/^ {4}/gm, "").replace(/\n+$/, "") }), render: (e2, n3, r2) => d2("pre", { key: r2.key }, d2("code", t({}, e2.attrs, { className: e2.lang ? `lang-${e2.lang}` : "" }), e2.text)) }, [r.codeFenced]: { match: Me(g), order: 0, parse: (e2) => ({ attrs: Z2("code", e2[3] || ""), lang: e2[2] || void 0, text: e2[4], type: r.codeBlock }) }, [r.codeInline]: { match: Oe(k), order: 3, parse: (e2) => ({ text: e2[2] }), render: (e2, t2, n3) => d2("code", { key: n3.key }, e2.text) }, [r.footnote]: { match: Me(v), order: 0, parse: (e2) => (q2.push({ footnote: e2[2], identifier: e2[1] }), {}), render: _e }, [r.footnoteReference]: { match: Be(C), order: 1, parse: (e2) => ({ target: `#${i2.slugify(e2[1], Ee)}`, text: e2[1] }), render: (e2, t2, n3) => d2("a", { key: n3.key, href: i2.sanitizer(e2.target, "a", "href") }, d2("sup", { key: n3.key }, e2.text)) }, [r.gfmTask]: { match: Be(w), order: 1, parse: (e2) => ({ completed: "x" === e2[1].toLowerCase() }), render: (e2, t2, n3) => d2("input", { checked: e2.completed, key: n3.key, readOnly: true, type: "checkbox" }) }, [r.heading]: { match: Me(i2.enforceAtxHeadings ? z : E), order: 1, parse: (e2, t2, n3) => ({ children: Ne(t2, e2[2], n3), id: i2.slugify(e2[2], Ee), level: e2[1].length }), render: (e2, t2, n3) => d2(`h${e2.level}`, { id: e2.id, key: n3.key }, t2(e2.children, n3)) }, [r.headingSetext]: { match: Me(L), order: 0, parse: (e2, t2, n3) => ({ children: Ne(t2, e2[1], n3), level: "=" === e2[2] ? 1 : 2, type: r.heading }) }, [r.htmlBlock]: { match: Re(A), order: 1, parse(e2, t2, n3) {
    const [, r2] = e2[3].match(re), i3 = new RegExp(`^${r2}`, "gm"), l2 = e2[3].replace(i3, ""), a2 = (c2 = l2, we.some((e3) => e3.test(c2)) ? He : Ne);
    var c2;
    const s2 = e2[1].toLowerCase(), d3 = -1 !== o.indexOf(s2), u2 = (d3 ? s2 : e2[1]).trim(), p2 = { attrs: Z2(u2, e2[2]), noInnerParse: d3, tag: u2 };
    return n3.inAnchor = n3.inAnchor || "a" === s2, d3 ? p2.text = e2[3] : p2.children = a2(t2, l2, n3), n3.inAnchor = false, p2;
  }, render: (e2, n3, r2) => d2(e2.tag, t({ key: r2.key }, e2.attrs), e2.text || (e2.children ? n3(e2.children, r2) : "")) }, [r.htmlSelfClosing]: { match: Re(M), order: 1, parse(e2) {
    const t2 = e2[1].trim();
    return { attrs: Z2(t2, e2[2] || ""), tag: t2 };
  }, render: (e2, n3, r2) => d2(e2.tag, t({}, e2.attrs, { key: r2.key })) }, [r.htmlComment]: { match: Re(B), order: 1, parse: () => ({}), render: _e }, [r.image]: { match: Oe($e), order: 1, parse: (e2) => ({ alt: e2[1], target: De(e2[2]), title: e2[3] }), render: (e2, t2, n3) => d2("img", { key: n3.key, alt: e2.alt || void 0, title: e2.title || void 0, src: i2.sanitizer(e2.target, "img", "src") }) }, [r.link]: { match: Be(Ce), order: 3, parse: (e2, t2, n3) => ({ children: je(t2, e2[1], n3), target: De(e2[2]), title: e2[3] }), render: (e2, t2, n3) => d2("a", { key: n3.key, href: i2.sanitizer(e2.target, "a", "href"), title: e2.title }, t2(e2.children, n3)) }, [r.linkAngleBraceStyleDetector]: { match: Be(D), order: 0, parse: (e2) => ({ children: [{ text: e2[1], type: r.text }], target: e2[1], type: r.link }) }, [r.linkBareUrlDetector]: { match: (e2, t2) => t2.inAnchor || i2.disableAutoLink ? null : Be(I)(e2, t2), order: 0, parse: (e2) => ({ children: [{ text: e2[1], type: r.text }], target: e2[1], title: void 0, type: r.link }) }, [r.linkMailtoDetector]: { match: Be(U), order: 0, parse(e2) {
    let t2 = e2[1], n3 = e2[1];
    return s.test(n3) || (n3 = "mailto:" + n3), { children: [{ text: t2.replace("mailto:", ""), type: r.text }], target: n3, type: r.link };
  } }, [r.orderedList]: ve(d2, 1), [r.unorderedList]: ve(d2, 2), [r.newlineCoalescer]: { match: Me(x), order: 3, parse: Fe, render: () => "\n" }, [r.paragraph]: { match: Ie, order: 3, parse: Pe, render: (e2, t2, n3) => d2("p", { key: n3.key }, t2(e2.children, n3)) }, [r.ref]: { match: Be(H), order: 0, parse: (e2) => (Q2[e2[1]] = { target: e2[2], title: e2[4] }, {}), render: _e }, [r.refImage]: { match: Oe(P), order: 0, parse: (e2) => ({ alt: e2[1] || void 0, ref: e2[2] }), render: (e2, t2, n3) => Q2[e2.ref] ? d2("img", { key: n3.key, alt: e2.alt, src: i2.sanitizer(Q2[e2.ref].target, "img", "src"), title: Q2[e2.ref].title }) : null }, [r.refLink]: { match: Be(F), order: 0, parse: (e2, t2, n3) => ({ children: t2(e2[1], n3), fallbackChildren: e2[0], ref: e2[2] }), render: (e2, t2, n3) => Q2[e2.ref] ? d2("a", { key: n3.key, href: i2.sanitizer(Q2[e2.ref].target, "a", "href"), title: Q2[e2.ref].title }, t2(e2.children, n3)) : d2("span", { key: n3.key }, e2.fallbackChildren) }, [r.table]: { match: Me(j), order: 1, parse: Ae, render(e2, t2, n3) {
    const r2 = e2;
    return d2("table", { key: n3.key }, d2("thead", null, d2("tr", null, r2.header.map(function(e3, i3) {
      return d2("th", { key: i3, style: Te(r2, i3) }, t2(e3, n3));
    }))), d2("tbody", null, r2.cells.map(function(e3, i3) {
      return d2("tr", { key: i3 }, e3.map(function(e4, i4) {
        return d2("td", { key: i4, style: Te(r2, i4) }, t2(e4, n3));
      }));
    })));
  } }, [r.text]: { match: Re(te), order: 4, parse: (e2) => ({ text: e2[0].replace(T, (e3, t2) => i2.namedCodesToUnicode[t2] ? i2.namedCodesToUnicode[t2] : e3) }), render: (e2) => e2.text }, [r.textBolded]: { match: Oe(X), order: 2, parse: (e2, t2, n3) => ({ children: t2(e2[2], n3) }), render: (e2, t2, n3) => d2("strong", { key: n3.key }, t2(e2.children, n3)) }, [r.textEmphasized]: { match: Oe(J), order: 3, parse: (e2, t2, n3) => ({ children: t2(e2[2], n3) }), render: (e2, t2, n3) => d2("em", { key: n3.key }, t2(e2.children, n3)) }, [r.textEscaped]: { match: Oe(ee), order: 1, parse: (e2) => ({ text: e2[1], type: r.text }) }, [r.textMarked]: { match: Oe(K), order: 3, parse: Pe, render: (e2, t2, n3) => d2("mark", { key: n3.key }, t2(e2.children, n3)) }, [r.textStrikethroughed]: { match: Oe(Y), order: 3, parse: Pe, render: (e2, t2, n3) => d2("del", { key: n3.key }, t2(e2.children, n3)) } };
  true === i2.disableParsingRawHTML && (delete V2[r.htmlBlock], delete V2[r.htmlSelfClosing]);
  const ie2 = function(e2) {
    let t2 = Object.keys(e2);
    function n3(r2, i3) {
      let l2 = [];
      for (i3.prevCapture = i3.prevCapture || ""; r2; ) {
        let a2 = 0;
        for (; a2 < t2.length; ) {
          const o2 = t2[a2], c2 = e2[o2], s2 = c2.match(r2, i3);
          if (s2) {
            const e3 = s2[0];
            i3.prevCapture += e3, r2 = r2.substring(e3.length);
            const t3 = c2.parse(s2, n3, i3);
            null == t3.type && (t3.type = o2), l2.push(t3);
            break;
          }
          a2++;
        }
      }
      return i3.prevCapture = "", l2;
    }
    return t2.sort(function(t3, n4) {
      let r2 = e2[t3].order, i3 = e2[n4].order;
      return r2 !== i3 ? r2 - i3 : t3 < n4 ? -1 : 1;
    }), function(e3, t3) {
      return n3(function(e4) {
        return e4.replace(b, "\n").replace($, "").replace(G, "    ");
      }(e3), t3);
    };
  }(V2), le2 = (ae2 = function(e2, t2) {
    return function(n3, r2, i3) {
      const l2 = e2[n3.type].render;
      return t2 ? t2(() => l2(n3, r2, i3), n3, r2, i3) : l2(n3, r2, i3);
    };
  }(V2, i2.renderRule), function e2(t2, n3 = {}) {
    if (Array.isArray(t2)) {
      const r2 = n3.key, i3 = [];
      let l2 = false;
      for (let r3 = 0; r3 < t2.length; r3++) {
        n3.key = r3;
        const a2 = e2(t2[r3], n3), o2 = "string" == typeof a2;
        o2 && l2 ? i3[i3.length - 1] += a2 : null !== a2 && i3.push(a2), l2 = o2;
      }
      return n3.key = r2, i3;
    }
    return ae2(t2, e2, n3);
  });
  var ae2;
  const oe2 = W2(n2);
  return q2.length ? d2("div", null, oe2, d2("footer", { key: "footer" }, q2.map(function(e2) {
    return d2("div", { id: i2.slugify(e2.identifier, Ee), key: e2.identifier }, e2.identifier, le2(ie2(e2.footnote, { inline: true })));
  }))) : oe2;
}
var index_modern_default = (t2) => {
  let { children: r2 = "", options: i2 } = t2, l2 = function(e2, t3) {
    if (null == e2)
      return {};
    var n2, r3, i3 = {}, l3 = Object.keys(e2);
    for (r3 = 0; r3 < l3.length; r3++)
      t3.indexOf(n2 = l3[r3]) >= 0 || (i3[n2] = e2[n2]);
    return i3;
  }(t2, n);
  return e.cloneElement(Ze(r2, i2), l2);
};

export {
  index_modern_default
};
//# sourceMappingURL=/build/_shared/chunk-DIGYRLJS.js.map
