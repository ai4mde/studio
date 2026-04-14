"""
Agent nodes for the JSON-to-Django UI pipeline.

Each node receives the full PipelineState and returns a dict with the
keys it wants to update.  LangGraph merges the returned dict into state.
"""
import json
import logging
import os
import random
import re
from typing import List
from urllib.request import Request, urlopen

from generator.agents.state import PipelineState, ScreenInfo
from llm.handler import call_openai

logger = logging.getLogger(__name__)


def _parse_json_response(raw: str) -> dict:
    """Parse an LLM response as JSON, stripping markdown code fences if present."""
    raw = raw.strip()
    if raw.startswith("```"):
        lines = raw.split("\n")
        # Remove opening fence line (e.g. ```json) and any trailing ``` lines
        start = 1
        end = len(lines)
        while end > start and lines[end - 1].strip() in ("", "```"):
            end -= 1
        raw = "\n".join(lines[start:end])
    return json.loads(raw)


# ─────────────────────────────────────────────────────────────────────────────
# Live design-library discovery
# Dynamically discovers component pages at runtime from docs index pages.
# This avoids hardcoding individual component URLs.
# ─────────────────────────────────────────────────────────────────────────────

_DESIGN_LIBRARY_INDEXES: list[tuple[str, str]] = [
    ("https://flowbite.com/docs/components/", "Flowbite"),
    ("https://flowbite.com/docs/forms/", "Flowbite"),
    ("https://daisyui.com/components/", "DaisyUI"),
    ("https://merakiui.com/components/application-ui", "MerakiUI"),
]


def _get_design_library_indexes() -> list[tuple[str, str]]:
    """Get design index sources from env, falling back to defaults.

    Env format:
      DESIGN_SOURCE_INDEXES="Flowbite|https://flowbite.com/docs/components/,DaisyUI|https://daisyui.com/components/"
    """
    raw = os.getenv("DESIGN_SOURCE_INDEXES", "").strip()
    if not raw:
        return _DESIGN_LIBRARY_INDEXES

    parsed: list[tuple[str, str]] = []
    for item in raw.split(","):
        part = item.strip()
        if not part:
            continue
        if "|" in part:
            label, url = part.split("|", 1)
            label = label.strip() or "Source"
            url = url.strip()
        else:
            label = "Source"
            url = part
        if url.startswith("http://") or url.startswith("https://"):
            parsed.append((url, label))

    return parsed or _DESIGN_LIBRARY_INDEXES


def _extract_palette_tokens(html: str, limit: int = 16) -> list[str]:
    """Extract Tailwind color-like tokens from fetched HTML snippets."""
    matches = re.findall(
        r"\b(?:bg|text|border|ring|from|to|via)-(?:slate|gray|zinc|neutral|stone|red|orange|amber|yellow|lime|green|emerald|teal|cyan|sky|blue|indigo|violet|purple|fuchsia|pink|rose)-\d{2,3}\b",
        html,
    )
    uniq: list[str] = []
    for token in matches:
        t = token.lower()
        if t not in uniq:
            uniq.append(t)
        if len(uniq) >= limit:
            break
    return uniq


def _extract_layout_tokens(html: str, limit: int = 16) -> list[str]:
    """Extract Tailwind layout-like utility tokens from fetched HTML snippets."""
    matches = re.findall(
        r"\b(?:flex|grid|block|inline-block|w-full|max-w-[\w-]+|gap-\d+|space-[xy]-\d+|items-(?:start|center|end|baseline|stretch)|justify-(?:start|center|end|between|around|evenly)|col-span-\d+|grid-cols-\d+|grid-rows-\d+|p[trblxy]?-[\d.]+|m[trblxy]?-[\d.]+|rounded(?:-[a-z]+)?|shadow(?:-[a-z]+)?)\b",
        html,
    )
    uniq: list[str] = []
    for token in matches:
        t = token.lower()
        if t not in uniq:
            uniq.append(t)
        if len(uniq) >= limit:
            break
    return uniq


def _extract_typography_tokens(html: str, limit: int = 16) -> list[str]:
    """Extract Tailwind typography-like utility tokens from fetched HTML snippets."""
    matches = re.findall(
        r"\b(?:font-(?:sans|serif|mono|thin|extralight|light|normal|medium|semibold|bold|extrabold|black)|text-(?:xs|sm|base|lg|xl|\dxl|[a-z]+-\d{2,3})|tracking-(?:tighter|tight|normal|wide|wider|widest)|leading-(?:none|tight|snug|normal|relaxed|loose|\d+))\b",
        html,
    )
    uniq: list[str] = []
    for token in matches:
        t = token.lower()
        if t not in uniq:
            uniq.append(t)
        if len(uniq) >= limit:
            break
    return uniq


def _fetch_html(url: str, timeout: int = 5) -> str | None:
    """Fetch HTML and strip heavy script/style blocks."""
    try:
        req = Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; DesignBot/1.0)"})
        with urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="ignore")
    except Exception:
        return None
    body = re.sub(r"<script[^>]*>.*?</script>", "", body, flags=re.DOTALL | re.IGNORECASE)
    body = re.sub(r"<style[^>]*>.*?</style>", "", body, flags=re.DOTALL | re.IGNORECASE)
    return body


def _normalize_abs_url(base_url: str, href: str) -> str | None:
    """Normalize anchor href to absolute URL on supported docs hosts."""
    href = (href or "").strip()
    if not href or href.startswith("#") or href.startswith("javascript:"):
        return None
    if href.startswith("http://") or href.startswith("https://"):
        return href
    if href.startswith("//"):
        return f"https:{href}"

    m = re.match(r"^(https?://[^/]+)", base_url)
    if not m:
        return None
    origin = m.group(1)
    if href.startswith("/"):
        return origin + href

    base = base_url if base_url.endswith("/") else base_url + "/"
    return base + href


def _discover_design_urls(max_per_index: int = 12) -> list[tuple[str, str]]:
    """Discover candidate component URLs from design library index pages."""
    discovered: list[tuple[str, str]] = []
    seen: set[str] = set()

    for index_url, source in _get_design_library_indexes():
        html = _fetch_html(index_url)
        if not html:
            continue

        hrefs = re.findall(r'<a[^>]+href=["\']([^"\']+)["\']', html, re.IGNORECASE)
        base_origin = re.match(r"^(https?://[^/]+)", index_url)
        if not base_origin:
            continue
        origin = base_origin.group(1)

        scored_candidates: list[tuple[int, str]] = []
        added = 0
        for href in hrefs:
            abs_url = _normalize_abs_url(index_url, href)
            if not abs_url:
                continue
            low = abs_url.lower()
            if not low.startswith(origin.lower()):
                continue
            if abs_url in seen:
                continue
            if "#" in abs_url or "?" in abs_url:
                continue

            path = abs_url[len(origin):].strip("/")
            segments = [s for s in path.split("/") if s]
            if not segments:
                continue
            slug = segments[-1]
            if not re.search(r"[a-zA-Z]", slug):
                continue

            # Prefer deeper, descriptive paths over root/utility links.
            alpha_len = len(re.sub(r"[^a-zA-Z]", "", slug))
            score = len(segments) * 4 + min(alpha_len, 24)
            scored_candidates.append((score, abs_url))

        for _score, abs_url in sorted(scored_candidates, key=lambda x: x[0], reverse=True):
            if abs_url in seen:
                continue

            slug = abs_url.rstrip("/").split("/")[-1] or "component"
            label = f"{source} · {slug.replace('-', ' ').title()}"
            discovered.append((abs_url, label))
            seen.add(abs_url)
            added += 1
            if added >= max_per_index:
                break

    return discovered


def _structure_only_html(html: str, max_len: int = 700) -> str:
    """Convert raw fetched HTML into structure-only skeleton.

    Removes style-heavy attributes so prompt references encode layout composition
    (nesting/order/sections) instead of copied visual tokens.
    """
    cleaned = html
    cleaned = re.sub(r"\sclass=(\"[^\"]*\"|'[^']*')", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\sstyle=(\"[^\"]*\"|'[^']*')", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\sid=(\"[^\"]*\"|'[^']*')", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\sdata-[\w-]+=(\"[^\"]*\"|'[^']*')", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\saria-[\w-]+=(\"[^\"]*\"|'[^']*')", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned[:max_len]


def _fetch_design_snippet(url: str, source_name: str, timeout: int = 5) -> str | None:
    """Fetch one design-library page and extract a representative HTML snippet.

    Tries two strategies in order:
    1. Find a <code> block whose text contains nav/sidebar class patterns.
    2. Fall back to the first raw <nav> or <aside> block in the page.

    Returns a labelled string ready to embed in the LLM prompt, or None on failure.
    """
    body = _fetch_html(url, timeout=timeout)
    if not body:
        return None

    # Strategy 1: code blocks that look like nav/sidebar HTML
    for block in re.findall(r"<code[^>]*>(.*?)</code>", body, re.DOTALL | re.IGNORECASE):
        plain = re.sub(r"<[^>]+>", "", block).strip()
        if any(kw in plain for kw in ("<nav", "<aside", "<header", "bg-", "flex ", "sidebar")):
            snippet = _structure_only_html(plain, max_len=700)
            if len(snippet) > 80:
                palette = _extract_palette_tokens(plain)
                layout = _extract_layout_tokens(plain)
                typo = _extract_typography_tokens(plain)
                palette_line = f"PALETTE_HINTS: {', '.join(palette)}" if palette else "PALETTE_HINTS: (none)"
                layout_line = f"LAYOUT_HINTS: {', '.join(layout)}" if layout else "LAYOUT_HINTS: (none)"
                typo_line = f"TYPOGRAPHY_HINTS: {', '.join(typo)}" if typo else "TYPOGRAPHY_HINTS: (none)"
                return f"[{source_name}]\n{palette_line}\n{layout_line}\n{typo_line}\n{snippet}"

    # Strategy 2: first structural block in raw HTML
    for pat in (r"<nav\b", r"<aside\b", r"<header\b"):
        m = re.search(pat, body, re.IGNORECASE)
        if m:
            raw_block = body[m.start(): m.start() + 800]
            palette = _extract_palette_tokens(raw_block)
            layout = _extract_layout_tokens(raw_block)
            typo = _extract_typography_tokens(raw_block)
            palette_line = f"PALETTE_HINTS: {', '.join(palette)}" if palette else "PALETTE_HINTS: (none)"
            layout_line = f"LAYOUT_HINTS: {', '.join(layout)}" if layout else "LAYOUT_HINTS: (none)"
            typo_line = f"TYPOGRAPHY_HINTS: {', '.join(typo)}" if typo else "TYPOGRAPHY_HINTS: (none)"
            return f"[{source_name}]\n{palette_line}\n{layout_line}\n{typo_line}\n{_structure_only_html(raw_block, max_len=700)}"

    return None


def _build_design_references(n: int = 5) -> str:
    """Fetch n live design-library pages and compile real HTML snippets.

    URLs are sampled randomly each run so successive pipelines get
    different inspiration — no hardcoded style descriptions.
    """
    all_urls = _discover_design_urls(max_per_index=14)
    sampled = random.sample(all_urls, min(n, len(all_urls))) if all_urls else []
    chunks: list[str] = [
        "LIVE DESIGN LIBRARY SNIPPETS (fetched at pipeline runtime):",
        "Use these for structure/placement and palette hints (topbar/sidebar/section composition + colors).",
        "PALETTE_HINTS and LAYOUT_HINTS are extracted from fetched snippets and should influence each option style.",
        "",
    ]
    found = 0
    for url, name in sampled:
        snippet = _fetch_design_snippet(url, name)
        if snippet:
            chunks.append(f"── SNIPPET {found + 1} ──")
            chunks.append(snippet)
            chunks.append("")
            found += 1
    if found == 0:
        chunks.append(
            "(All live fetches timed out. Generate 5 richly distinct layouts "
            "from your own knowledge of modern SaaS UI patterns.)"
        )
    return "\n".join(chunks)


def _discover_html_blocks(
    html: str,
    *,
    max_blocks: int,
    min_text_len: int = 24,
) -> list[tuple[str, str]]:
    """Discover representative HTML blocks directly from fetched markup.

    Returns ordered (tag, block_html) tuples without relying on hardcoded tag maps.
    """
    seen_tags: set[str] = set()
    candidates: list[str] = []
    for m in re.finditer(r"<([a-z][a-z0-9]*)\b[^>]*>", html, flags=re.IGNORECASE):
        tag = m.group(1).lower()
        if tag not in seen_tags:
            seen_tags.add(tag)
            candidates.append(tag)

    blocks: list[tuple[str, str]] = []
    for tag in candidates:
        if len(blocks) >= max_blocks:
            break

        paired = re.search(rf"<{tag}\b[^>]*>.*?</{tag}>", html, flags=re.DOTALL | re.IGNORECASE)
        if paired:
            block = paired.group(0)
        else:
            single = re.search(rf"<{tag}\b[^>]*>", html, flags=re.IGNORECASE)
            if not single:
                continue
            block = single.group(0)

        text = re.sub(r"<[^>]+>", " ", block)
        plain_text_len = len(" ".join(text.split()))
        tag_count = len(re.findall(r"<[a-z][a-z0-9]*\b", block, flags=re.IGNORECASE))
        attr_count = len(re.findall(r"\s[a-zA-Z_:][-a-zA-Z0-9_:.]*=", block))
        if plain_text_len < min_text_len and tag_count < 6 and attr_count < 4:
            continue
        blocks.append((tag, block))

    return blocks


def _block_structure_signature(tag: str, block: str) -> dict[str, int]:
    """Build structure metrics from a fetched HTML block."""
    opening_tags = re.findall(r"<([a-z][a-z0-9]*)\b", block, flags=re.IGNORECASE)
    tag_freq: dict[str, int] = {}
    for t in opening_tags:
        low = t.lower()
        tag_freq[low] = tag_freq.get(low, 0) + 1

    return {
        "total_nodes": len(opening_tags),
        "distinct_tags": len(tag_freq),
        "interactive_nodes": sum(
            v for k, v in tag_freq.items() if k in {"form", "input", "select", "textarea", "button", "label", "fieldset", "option"}
        ),
        "list_nodes": sum(
            v for k, v in tag_freq.items() if k in {"table", "thead", "tbody", "tr", "th", "td", "ul", "ol", "li", "dl", "dt", "dd"}
        ),
        "chrome_nodes": sum(
            v for k, v in tag_freq.items() if k in {"nav", "aside", "header", "footer", "menu"}
        ),
        "heading_nodes": sum(v for k, v in tag_freq.items() if re.fullmatch(r"h[1-6]", k)),
        "container_nodes": sum(
            v for k, v in tag_freq.items() if k in {"main", "section", "article", "div"}
        ),
        "is_form_tag": 1 if tag == "form" else 0,
        "is_table_tag": 1 if tag == "table" else 0,
        "is_nav_tag": 1 if tag in {"nav", "aside", "header", "footer"} else 0,
    }


def _layout_block_score(tag: str, block: str) -> int:
    """Heuristic score to prefer structurally useful fetched blocks."""
    sig = _block_structure_signature(tag, block)
    score = 0

    # Prefer blocks that carry structural/layout information.
    score += len(_extract_layout_tokens(block, limit=24)) * 3
    score += len(_extract_palette_tokens(block, limit=24))
    score += len(_extract_typography_tokens(block, limit=24))
    score += min(sig["total_nodes"], 30)
    score += min(sig["distinct_tags"], 10) * 2
    score += sig["interactive_nodes"] * 2
    score += sig["list_nodes"] * 2
    score += sig["chrome_nodes"] * 2
    score += sig["heading_nodes"]
    score += sig["container_nodes"]
    score += sig["is_form_tag"] * 8
    score += sig["is_table_tag"] * 6
    score += sig["is_nav_tag"] * 4

    return score


def _infer_region_hint(tag: str, block: str) -> str:
    """Infer a region hint from fetched block semantics."""
    sig = _block_structure_signature(tag, block)
    if sig["is_form_tag"] or sig["interactive_nodes"] >= max(3, sig["total_nodes"] // 5):
        return "form"
    if sig["is_table_tag"] or sig["list_nodes"] >= max(3, sig["total_nodes"] // 4):
        return "list"
    if sig["is_nav_tag"] or sig["chrome_nodes"] >= max(2, sig["total_nodes"] // 6):
        return "layout_chrome"
    if sig["container_nodes"] > 0 and sig["heading_nodes"] > 0:
        return "dashboard"
    return "detail"


def _infer_component_name(tag: str, block: str) -> str:
    """Infer a component name from discovered block semantics."""
    if tag not in {"div", "section", "article", "main"}:
        return tag

    opening_tags = re.findall(r"<([a-z][a-z0-9]*)\b", block, flags=re.IGNORECASE)
    freq: dict[str, int] = {}
    for t in opening_tags:
        low = t.lower()
        if low in {"div", "section", "article", "main"}:
            continue
        freq[low] = freq.get(low, 0) + 1

    if not freq:
        return tag
    return max(freq.items(), key=lambda kv: kv[1])[0]


def _build_ui_layout_references(n: int = 5, blocks_per_page: int = 6) -> str:
    """Fetch full pages and extract region-typed blocks for ui_designer guidance.

    This provides region/component assignment hints beyond chrome-only snippets.
    """
    all_urls = _discover_design_urls(max_per_index=18)
    sampled = random.sample(all_urls, min(n, len(all_urls))) if all_urls else []
    chunks: list[str] = [
        "FULL PAGE LAYOUT REFERENCES (fetched live at runtime):",
        "Use these to assign page_ir actions into suitable regions/components (form/list/dashboard/action_panel/detail).",
        "Each block includes REGION_HINT + PALETTE_HINTS + LAYOUT_HINTS + TYPOGRAPHY_HINTS extracted from fetched pages.",
        "Blocks are discovered dynamically from fetched HTML structure (no fixed block template list).",
        "",
    ]

    found = 0
    for url, source_name in sampled:
        html = _fetch_html(url)
        if not html:
            continue
        page_palette = _extract_palette_tokens(html, limit=20)
        page_layout = _extract_layout_tokens(html, limit=20)
        page_typo = _extract_typography_tokens(html, limit=20)
        chunks.append(f"=== PAGE: {source_name} ===")
        if page_palette:
            chunks.append(f"PAGE_PALETTE_HINTS: {', '.join(page_palette)}")
        if page_layout:
            chunks.append(f"PAGE_LAYOUT_HINTS: {', '.join(page_layout)}")
        if page_typo:
            chunks.append(f"PAGE_TYPOGRAPHY_HINTS: {', '.join(page_typo)}")

        discovered = _discover_html_blocks(html, max_blocks=max(18, blocks_per_page * 3), min_text_len=24)
        discovered = sorted(discovered, key=lambda tb: _layout_block_score(tb[0], tb[1]), reverse=True)[:blocks_per_page]
        for tag_name, block in discovered:
            region_hint = _infer_region_hint(tag_name, block)
            palette = _extract_palette_tokens(block, limit=10)
            layout = _extract_layout_tokens(block, limit=10)
            typo = _extract_typography_tokens(block, limit=10)
            chunks.append(f"- REGION_HINT: {region_hint} | TAG: {tag_name}")
            chunks.append(f"  PALETTE_HINTS: {', '.join(palette) if palette else '(none)'}")
            chunks.append(f"  LAYOUT_HINTS: {', '.join(layout) if layout else '(none)'}")
            chunks.append(f"  TYPOGRAPHY_HINTS: {', '.join(typo) if typo else '(none)'}")
            chunks.append(f"  HTML_SKELETON: {_structure_only_html(block, max_len=600)}")
            found += 1
        chunks.append("")

    if found == 0:
        chunks.append("(All page fetches timed out. Use strong SaaS region composition best practices.)")

    return "\n".join(chunks)


def _build_component_style_references(n: int = 4, max_per_component: int = 4) -> str:
    """Fetch component-level style snippets for token generation.

    This augments region/page references with direct examples for frequently styled
    controls so element/component tokens can follow fetched visual language.
    """
    all_urls = _discover_design_urls(max_per_index=16)
    sampled = random.sample(all_urls, min(n, len(all_urls))) if all_urls else []

    collected: dict[str, list[str]] = {}

    for url, _source_name in sampled:
        html = _fetch_html(url)
        if not html:
            continue

        for tag_name, snippet in _discover_html_blocks(html, max_blocks=24, min_text_len=10):
            name = _infer_component_name(tag_name, snippet)
            bucket = collected.setdefault(name, [])
            if len(bucket) >= max_per_component:
                continue
            cleaned = _structure_only_html(snippet, max_len=420)
            if cleaned and cleaned not in bucket:
                bucket.append(cleaned)

    chunks: list[str] = [
        "COMPONENT STYLE REFERENCES (fetched live at runtime):",
        "Use these for component-level token styling across discovered component families.",
        "Components are inferred dynamically from fetched HTML (no fixed component pattern list).",
        "",
    ]

    for name in sorted(collected.keys()):
        chunks.append(f"== COMPONENT: {name} ==")
        if not collected[name]:
            chunks.append("(no fetched snippet)")
            chunks.append("")
            continue

        for idx, snippet in enumerate(collected[name], 1):
            palette = _extract_palette_tokens(snippet, limit=8)
            layout = _extract_layout_tokens(snippet, limit=8)
            typo = _extract_typography_tokens(snippet, limit=8)
            chunks.append(f"- SAMPLE {idx}")
            chunks.append(f"  PALETTE_HINTS: {', '.join(palette) if palette else '(none)'}")
            chunks.append(f"  LAYOUT_HINTS: {', '.join(layout) if layout else '(none)'}")
            chunks.append(f"  TYPOGRAPHY_HINTS: {', '.join(typo) if typo else '(none)'}")
            chunks.append(f"  HTML_SKELETON: {snippet}")
        chunks.append("")

    return "\n".join(chunks)


def _extract_layout_hints_from_references(ref_text: str) -> set[str]:
    """Extract layout utility hints from reference text blocks."""
    hints: set[str] = set()
    for line in ref_text.splitlines():
        if "LAYOUT_HINTS:" not in line:
            continue
        _, raw = line.split("LAYOUT_HINTS:", 1)
        for token in raw.split(","):
            t = token.strip()
            if t and t != "(none)":
                hints.add(t)
    return hints


def _extract_ui_ast_class_tokens(obj: object) -> set[str]:
    """Collect all attrs.class tokens from generated ui_ir AST."""
    tokens: set[str] = set()
    if isinstance(obj, dict):
        attrs = obj.get("attrs")
        if isinstance(attrs, dict):
            cls = attrs.get("class")
            if isinstance(cls, str):
                for part in cls.split():
                    part = part.strip()
                    if part:
                        tokens.add(part)
        for v in obj.values():
            tokens.update(_extract_ui_ast_class_tokens(v))
    elif isinstance(obj, list):
        for item in obj:
            tokens.update(_extract_ui_ast_class_tokens(item))
    return tokens


def _layout_alignment_ratio(ui_design: dict, ui_layout_references: str) -> float:
    """Return overlap ratio between fetched layout hints and generated AST classes."""
    hints = _extract_layout_hints_from_references(ui_layout_references)
    if not hints:
        return 1.0
    used = _extract_ui_ast_class_tokens(ui_design)
    if not used:
        return 0.0
    overlap = len(hints & used)
    return overlap / max(1, len(hints))


# ─────────────────────────────────────────────────────────────────────────────
# 1. Parser Node
#    Reads the raw metadata JSON and extracts per-page summary info.
# ─────────────────────────────────────────────────────────────────────────────

def _extract_diagrams(metadata: dict) -> dict:
    """Extract structured summaries from all UML diagrams in the metadata.

    Returns a dict with three keys:
      usecase  — list of { name, actors, usecases, relations }
                 - usecases: [{name, precondition, postcondition, trigger, scenarios}]
                 - relations: [{type: include|extend|interaction, source, target}]
      activity — list of { name, actors, steps: [{name, actor, automatic, body, precondition, postcondition}] }
      classes  — list of { name, classes: [{name, attributes: [{name, type}]}] }

    Only fields that are non-empty are included to keep the payload lean.
    """
    usecase_diagrams: list[dict] = []
    activity_diagrams: list[dict] = []
    class_diagrams: list[dict] = []

    for diagram in metadata.get("diagrams", []):
        dtype = diagram.get("type", "")
        dname = diagram.get("name", "")
        nodes = diagram.get("nodes", [])
        edges = diagram.get("edges", [])

        if dtype == "usecase":
            # Build a node-id → name map so we can resolve relation endpoints
            node_name_map: dict[str, str] = {}
            usecases = []
            actors = []
            for node in nodes:
                node_id = str(node.get("id", "") or node.get("cls_ptr", ""))
                cls_data = node.get("cls", {})
                ntype = cls_data.get("type", "")
                node_name = cls_data.get("name", "")
                if node_id:
                    node_name_map[node_id] = node_name
                if ntype == "actor":
                    actors.append(node_name)
                elif ntype == "usecase":
                    uc: dict = {"name": node_name}
                    if cls_data.get("precondition"):
                        uc["precondition"] = cls_data["precondition"]
                    if cls_data.get("postcondition"):
                        uc["postcondition"] = cls_data["postcondition"]
                    if cls_data.get("trigger"):
                        uc["trigger"] = cls_data["trigger"]
                    if cls_data.get("scenarios"):
                        uc["scenarios"] = cls_data["scenarios"]
                    usecases.append(uc)

            # Extract Include / Extend / Interaction relations
            relations: list[dict] = []
            for edge in edges:
                rel_data = edge.get("rel", {})
                rtype = rel_data.get("type", "interaction")
                src_id = str(edge.get("source_ptr", "") or edge.get("source", ""))
                tgt_id = str(edge.get("target_ptr", "") or edge.get("target", ""))
                src_name = node_name_map.get(src_id, src_id)
                tgt_name = node_name_map.get(tgt_id, tgt_id)
                if src_name and tgt_name:
                    relations.append({"type": rtype, "source": src_name, "target": tgt_name})

            if usecases or actors:
                entry: dict = {
                    "name": dname,
                    "actors": actors,
                    "usecases": usecases,
                }
                if relations:
                    entry["relations"] = relations
                usecase_diagrams.append(entry)

        elif dtype == "activity":
            steps = []
            actors_in_diagram: list[str] = []
            for node in nodes:
                cls_data = node.get("cls", {})
                ntype = cls_data.get("type", "")
                if ntype == "action":
                    step: dict = {"name": cls_data.get("name", "")}
                    if cls_data.get("actorNodeName"):
                        step["actor"] = cls_data["actorNodeName"]
                        if cls_data["actorNodeName"] not in actors_in_diagram:
                            actors_in_diagram.append(cls_data["actorNodeName"])
                    if cls_data.get("isAutomatic"):
                        step["automatic"] = True
                    if cls_data.get("body"):
                        step["body"] = cls_data["body"]
                    if cls_data.get("localPrecondition"):
                        step["precondition"] = cls_data["localPrecondition"]
                    if cls_data.get("localPostcondition"):
                        step["postcondition"] = cls_data["localPostcondition"]
                    steps.append(step)
                elif ntype == "swimlane":
                    actor_name = cls_data.get("actorNodeName", "")
                    if actor_name and actor_name not in actors_in_diagram:
                        actors_in_diagram.append(actor_name)
            if steps:
                activity_diagrams.append({
                    "name": dname,
                    "actors": actors_in_diagram,
                    "steps": steps,
                })

        elif dtype == "classes":
            classes = []
            for node in nodes:
                cls_data = node.get("cls", {})
                if cls_data.get("type") == "class":
                    entry: dict = {"name": cls_data.get("name", "")}
                    attrs = [
                        {"name": a.get("name", ""), "type": a.get("type", "")}
                        for a in cls_data.get("attributes", [])
                        if a.get("name")
                    ]
                    if attrs:
                        entry["attributes"] = attrs
                    classes.append(entry)
            if classes:
                class_diagrams.append({"name": dname, "classes": classes})

    return {
        "usecase": usecase_diagrams,
        "activity": activity_diagrams,
        "classes": class_diagrams,
    }


# ─────────────────────────────────────────────────────────────────────────────
# New-format (classifiers + relations) parser helpers
# ─────────────────────────────────────────────────────────────────────────────

def _build_diagram_summary(classifiers: list, relations: list) -> dict:
    """Build diagram_summary from flat classifiers + relations metadata format.

    Produces the same DiagramSummary structure as _extract_diagrams, but from
    the newer flat representation where every UML node is a classifier and every
    edge is a relation.
    """
    clf_by_id: dict[str, dict] = {c["id"]: c for c in classifiers}

    def _name(clf_id: str) -> str:
        return clf_by_id.get(clf_id, {}).get("data", {}).get("name", clf_id)

    # ── Use Case diagram ──────────────────────────────────────────────────────
    actors: list[str] = [
        c["data"]["name"] for c in classifiers if c["data"].get("type") == "actor"
    ]
    usecases: list[dict] = []
    for c in classifiers:
        d = c["data"]
        if d.get("type") != "usecase":
            continue
        uc: dict = {"name": d["name"]}
        if d.get("precondition"):
            uc["precondition"] = d["precondition"]
        if d.get("postcondition"):
            uc["postcondition"] = d["postcondition"]
        if d.get("trigger"):
            uc["trigger"] = d["trigger"]
        if d.get("scenarios"):
            uc["scenarios"] = d["scenarios"]
        usecases.append(uc)

    uc_relations: list[dict] = [
        {"type": r["data"]["type"], "source": _name(r["source"]), "target": _name(r["target"])}
        for r in relations
        if r["data"]["type"] in ("interaction", "inclusion", "extension")
    ]

    # ── Activity diagram ──────────────────────────────────────────────────────
    activity_actors: list[str] = []
    for c in classifiers:
        if c["data"].get("type") == "swimlanegroup":
            for lane in c["data"].get("swimlanes", []):
                actor_name = lane.get("actorNodeName", "")
                if actor_name and actor_name not in activity_actors:
                    activity_actors.append(actor_name)

    steps: list[dict] = []
    for c in classifiers:
        d = c["data"]
        if d.get("type") != "action":
            continue
        step: dict = {"name": d["name"]}
        if d.get("actorNodeName"):
            step["actor"] = d["actorNodeName"]
        if d.get("isAutomatic"):
            step["automatic"] = True
        if d.get("localPrecondition"):
            step["precondition"] = d["localPrecondition"]
        if d.get("localPostcondition"):
            step["postcondition"] = d["localPostcondition"]
        steps.append(step)

    # ── Class diagram ─────────────────────────────────────────────────────────
    classes: list[dict] = []
    for c in classifiers:
        d = c["data"]
        if d.get("type") != "class":
            continue
        entry: dict = {"name": d["name"]}
        attrs = [
            {"name": a["name"], "type": a["type"]}
            for a in d.get("attributes", [])
            if a.get("name")
        ]
        if attrs:
            entry["attributes"] = attrs
        classes.append(entry)

    return {
        "usecase": [{"name": "Use Case Diagram", "actors": actors, "usecases": usecases, "relations": uc_relations}] if (actors or usecases) else [],
        "activity": [{"name": "Activity Diagram", "actors": activity_actors, "steps": steps}] if steps else [],
        "classes": [{"name": "Class Diagram", "classes": classes}] if classes else [],
    }


_CREATE_KEYWORDS = frozenset({"fill", "submit", "create", "add", "register", "new", "open", "upload", "enter", "apply"})
_UPDATE_KEYWORDS = frozenset({"edit", "update", "modify", "assess", "analyze", "analyse", "review", "decide", "final", "provide", "check", "approve", "perform"})
_DELETE_KEYWORDS = frozenset({"delete", "remove", "cancel", "reject", "deny"})


def _norm_state(label: str) -> str:
    """Normalise state labels into stable snake_case IDs."""
    if not label:
        return ""
    return "_".join(label.strip().lower().replace("-", " ").split())


def _build_parser_dsl(classifiers: list, relations: list, diagrams: list | None = None) -> dict:
    """Build the canonical Parser DSL from classifiers + relations.

    Output:
      domain      — {name}
      actors      — [{id, name}]
      entities    — [{id, name, fields}]  (domain classes)
      actions     — [{id, name, actor, input?: [entity_ids], auto?: true,
                      entity_flow, step_order, upstream_actions, downstream_actions,
                      control_flow, actor_name}]
      workflow    — {nodes: [action_id, ...], edges: [[from, to] or [from, to, condition]]}
    """
    clf_by_id: dict[str, dict] = {c["id"]: c for c in classifiers}
    class_by_id: dict[str, dict] = {c["id"]: c for c in classifiers if c["data"].get("type") == "class"}

    _CONTROL_TYPES = frozenset({"decision", "merge", "fork", "join", "initial", "final", "object", "signal", "event"})

    # Build adjacency list for controlflow edges (used by BFS)
    edges_by_source: dict[str, list] = {}
    for r in relations:
        if r.get("data", {}).get("type") == "controlflow":
            edges_by_source.setdefault(r["source"], []).append(r)

    # Build bidirectional adjacency for entity-field lookup
    adjacent_nodes: dict[str, list] = {}
    for r in relations:
        if r.get("data", {}).get("type") in ("controlflow", "objectflow"):
            adjacent_nodes.setdefault(r["source"], []).append(r["target"])
            adjacent_nodes.setdefault(r["target"], []).append(r["source"])

    def _input_entities_for(action_id: str) -> list[str]:
        """Return entity (class) IDs reachable from an action via BFS through control nodes."""
        entity_ids: list[str] = []
        seen_entities: set[str] = set()
        visited: set[str] = {action_id}
        queue: list[str] = list(adjacent_nodes.get(action_id, []))
        while queue:
            nid = queue.pop(0)
            if nid in visited:
                continue
            visited.add(nid)
            ndata = clf_by_id.get(nid, {}).get("data", {})
            ntype = ndata.get("type", "")
            if ntype == "object":
                cls_id = ndata.get("cls", "")
                if cls_id and cls_id not in seen_entities:
                    seen_entities.add(cls_id)
                    entity_ids.append(cls_id)
            elif ntype in _CONTROL_TYPES:
                for neighbor in adjacent_nodes.get(nid, []):
                    if neighbor not in visited:
                        queue.append(neighbor)
        return entity_ids

    def _find_action_successors(node_id: str, visited: frozenset) -> list[dict]:
        """BFS through non-action control nodes to find the next action(s)."""
        results = []
        source_type = clf_by_id.get(node_id, {}).get("data", {}).get("type", "")
        for edge_idx, edge in enumerate(edges_by_source.get(node_id, [])):
            target_id = edge["target"]
            if target_id in visited:
                continue
            visited = visited | {target_id}
            target_data = clf_by_id.get(target_id, {}).get("data", {})
            t_type = target_data.get("type", "")
            if t_type == "action":
                trans: dict = {"to": target_id}
                cond = edge.get("data", {}).get("condition") or {}
                guard = edge.get("data", {}).get("guard") or ""
                if cond and not cond.get("isElse") and cond.get("target_attribute"):
                    trans["condition"] = f"{cond['target_attribute']} == {cond['threshold']}"
                elif cond and cond.get("isElse"):
                    trans["condition"] = "else"
                elif guard:
                    trans["condition"] = guard
                elif source_type == "decision":
                    trans["condition"] = f"branch_{edge_idx + 1}"
                results.append(trans)
            elif t_type in _CONTROL_TYPES:
                sub = _find_action_successors(target_id, visited)
                if source_type == "decision":
                    for s in sub:
                        if "condition" not in s:
                            s["condition"] = f"branch_{edge_idx + 1}"
                results.extend(sub)
        return results

    # domain name (from system_name on classifiers)
    domain_name = next((c.get("system_name", "") for c in classifiers if c.get("system_name")), "")

    # actors
    actors = [
        {"id": c["id"], "name": c["data"]["name"]}
        for c in classifiers if c["data"].get("type") == "actor"
    ]

    # Also index by swimlane actorNode IDs (actions use these, not classifier IDs)
    _swimlane_id_to_name: dict[str, str] = {}
    for c in classifiers:
        d = c.get("data", {})
        if d.get("type") == "swimlanegroup":
            for lane in d.get("swimlanes", []):
                node_id = lane.get("actorNode")
                name = lane.get("actorNodeName")
                if node_id and name:
                    _swimlane_id_to_name[node_id] = name
    # Add swimlane actor nodes deduplicated by id
    existing_ids = {a["id"] for a in actors}
    for node_id, name in _swimlane_id_to_name.items():
        if node_id not in existing_ids:
            actors.append({"id": node_id, "name": name})
            existing_ids.add(node_id)

    # entities (domain classes)
    entities = [
        {
            "id": c["id"],
            "name": c["data"]["name"],
            "fields": [a["name"] for a in c["data"].get("attributes", []) if a.get("name")],
        }
        for c in classifiers if c["data"].get("type") == "class"
    ]

    # Entity field types lookup (passed to LLM as context for field_mode reasoning)
    _entity_field_types: dict[str, dict[str, str]] = {}
    for c in classifiers:
        d = c.get("data", {})
        if d.get("type") == "class":
            ename = d.get("name", "")
            if ename:
                _entity_field_types[ename] = {
                    a["name"]: a.get("type", "str")
                    for a in d.get("attributes", []) if a.get("name")
                }

    # actions (all action nodes)
    actions = []
    for c in classifiers:
        d = c["data"]
        if d.get("type") != "action":
            continue
        is_auto = bool(d.get("isAutomatic"))
        action: dict = {
            "id": c["id"],
            "name": d["name"],
        }
        if d.get("actorNode"):
            action["actor"] = d["actorNode"]
        if is_auto:
            action["auto"] = True
        input_entities = _input_entities_for(c["id"])
        if input_entities:
            action["input"] = input_entities
        actions.append(action)

    # workflow — nodes list + edges [[from, to] or [from, to, condition]]
    wf_nodes = [c["id"] for c in classifiers if c["data"].get("type") == "action"]
    wf_edges: list[list] = []
    for c in classifiers:
        if c["data"].get("type") != "action":
            continue
        for succ in _find_action_successors(c["id"], frozenset({c["id"]})):
            edge: list = [c["id"], succ["to"]]
            if "condition" in succ:
                edge.append(succ["condition"])
            wf_edges.append(edge)

    # ── Enrich actions with UML workflow position & entity flow ────────────
    # Directed adjacency for entity flow direction
    _fwd: dict[str, list[str]] = {}
    _rev: dict[str, list[str]] = {}
    for r in relations:
        if r.get("data", {}).get("type") == "controlflow":
            _fwd.setdefault(r["source"], []).append(r["target"])
            _rev.setdefault(r["target"], []).append(r["source"])

    def _directed_bfs(start: str, adj: dict[str, list[str]]) -> set[str]:
        """BFS from *start* through control nodes; return entity class names found at object nodes."""
        found: set[str] = set()
        visited: set[str] = {start}
        queue = list(adj.get(start, []))
        while queue:
            nid = queue.pop(0)
            if nid in visited:
                continue
            visited.add(nid)
            nd = clf_by_id.get(nid, {}).get("data", {})
            nt = nd.get("type", "")
            if nt == "object":
                cls_id = nd.get("cls", "")
                cname = class_by_id.get(cls_id, {}).get("data", {}).get("name", "")
                if cname:
                    found.add(cname)
            elif nt in _CONTROL_TYPES:
                for nb in adj.get(nid, []):
                    if nb not in visited:
                        queue.append(nb)
        return found

    # Activity diagram y-positions → step ordering
    _action_y: dict[str, int] = {}
    for diag in (diagrams or []):
        if diag.get("type") == "activity":
            for dn in diag.get("nodes", []):
                cid = dn.get("cls", "")
                y = dn.get("data", {}).get("position", {}).get("y")
                if cid and y is not None:
                    _action_y[cid] = y

    _sorted_aids = sorted(
        [a["id"] for a in actions],
        key=lambda aid: _action_y.get(aid, 9999),
    )
    _step_map = {aid: idx + 1 for idx, aid in enumerate(_sorted_aids)}

    # Action-to-action successor / predecessor names
    _act_ids = {a["id"] for a in actions}
    _act_name = {a["id"]: a["name"] for a in actions}
    _successors: dict[str, list[str]] = {}
    _predecessors: dict[str, list[str]] = {}
    for edge in wf_edges:
        if len(edge) >= 2 and edge[0] in _act_ids and edge[1] in _act_ids:
            _successors.setdefault(edge[0], []).append(_act_name[edge[1]])
            _predecessors.setdefault(edge[1], []).append(_act_name[edge[0]])

    # Control-flow pattern tags (fork / join / decision / merge neighbours)
    def _cf_patterns(action_id: str) -> list[str]:
        pats: list[str] = []
        for pid in _rev.get(action_id, []):
            pt = clf_by_id.get(pid, {}).get("data", {}).get("type", "")
            if pt == "fork":
                pats.append("after_fork(parallel)")
            elif pt == "decision":
                guard = ""
                for r in relations:
                    rd = r.get("data", {})
                    if rd.get("type") == "controlflow" and r["source"] == pid and r["target"] == action_id:
                        guard = rd.get("guard", "")
                        break
                pats.append(f"after_decision(condition={guard})" if guard else "after_decision")
            elif pt == "merge":
                pats.append("after_merge(convergence)")
            elif pt == "join":
                pats.append("after_join(sync)")
        for sid in _fwd.get(action_id, []):
            st = clf_by_id.get(sid, {}).get("data", {}).get("type", "")
            if st == "fork":
                pats.append("before_fork(splits)")
            elif st == "decision":
                pats.append("before_decision(branching)")
            elif st == "join":
                pats.append("before_join(sync)")
            elif st == "merge":
                pats.append("before_merge")
        return pats

    for action in actions:
        aid = action["id"]
        produced = _directed_bfs(aid, _fwd)
        consumed = _directed_bfs(aid, _rev)
        ef: dict[str, str] = {}
        for en in produced | consumed:
            if en in produced and en in consumed:
                ef[en] = "read_write"
            elif en in produced:
                ef[en] = "produces"
            else:
                ef[en] = "consumes"
        action["entity_flow"] = ef
        action["step_order"] = _step_map.get(aid, 0)
        action["upstream_actions"] = _predecessors.get(aid, [])
        action["downstream_actions"] = _successors.get(aid, [])
        action["control_flow"] = _cf_patterns(aid)
        action["actor_name"] = _swimlane_id_to_name.get(action.get("actor", ""), "")

    # ── State transitions: which entity states each action consumes/produces ─
    # BFS forward/backward from each action through control nodes to find
    # connected object nodes with their state labels.
    _action_ids_set = {a["id"] for a in actions}

    def _state_bfs(start: str, adj: dict[str, list[str]]) -> dict[str, list[str]]:
        """BFS from *start*; return {entity_name: [state_labels]} from object nodes.

        Traverses through control nodes AND other action nodes (not *start*)
        so that states separated by intermediate actions are still reachable.
        e.g. Final decision ← decision ← Assess completeness ← … ← [Analyzed]
        """
        result: dict[str, list[str]] = {}
        visited: set[str] = {start}
        queue = list(adj.get(start, []))
        while queue:
            nid = queue.pop(0)
            if nid in visited:
                continue
            visited.add(nid)
            nd = clf_by_id.get(nid, {}).get("data", {})
            nt = nd.get("type", "")
            if nt == "object":
                cls_id = nd.get("cls", "")
                cname = class_by_id.get(cls_id, {}).get("data", {}).get("name", "")
                state = nd.get("state", "")
                if cname and state:
                    result.setdefault(cname, []).append(state)
            elif nt in _CONTROL_TYPES or nid in _action_ids_set:
                # Also traverse through other action nodes so we can reach
                # object-state nodes separated by intermediate actions.
                for nb in adj.get(nid, []):
                    if nb not in visited:
                        queue.append(nb)
        return result

    for action in actions:
        aid = action["id"]
        fwd_states = _state_bfs(aid, _fwd)   # states this action produces
        rev_states = _state_bfs(aid, _rev)    # states this action consumes
        st: dict[str, dict[str, list[str]]] = {}
        for ename in set(list(fwd_states.keys()) + list(rev_states.keys())):
            st[ename] = {}
            if ename in rev_states:
                st[ename]["from_states"] = sorted(set(rev_states[ename]))
            if ename in fwd_states:
                st[ename]["to_states"] = sorted(set(fwd_states[ename]))
        if st:
            action["state_transitions"] = st

    # ── Field context: structured metadata for LLM field_mode reasoning ─────
    # 1. Collect "decision fields" — fields referenced in decision node conditions.
    #    These fields belong to the actor whose action feeds the decision.
    _decision_fields: dict[str, set[str]] = {}  # entity_name → {field_names}
    _decision_field_actor: dict[str, str] = {}    # field_name → actor_id that decides it
    _decision_field_actor_name: dict[str, str] = {}  # field_name → actor_name
    for r in relations:
        rd = r.get("data", {})
        if rd.get("type") != "controlflow":
            continue
        cond = rd.get("condition") or {}
        attr = cond.get("target_attribute", "")
        cls_name = cond.get("target_class_name", "")
        if attr and cls_name:
            _decision_fields.setdefault(cls_name, set()).add(attr)
            src_data = clf_by_id.get(r.get("source", ""), {}).get("data", {})
            if src_data.get("type") == "decision":
                for prev_r in relations:
                    if prev_r.get("data", {}).get("type") == "controlflow" and prev_r["target"] == r["source"]:
                        prev_data = clf_by_id.get(prev_r["source"], {}).get("data", {})
                        if prev_data.get("type") == "action":
                            prev_actor = prev_data.get("actorNode", "")
                            if prev_actor:
                                _decision_field_actor[attr] = prev_actor
                                _decision_field_actor_name[attr] = _swimlane_id_to_name.get(prev_actor, prev_actor)

    # 2. Track first producer per entity.
    _entity_first_producer: dict[str, str] = {}  # entity_name → actor_id
    _entity_first_producer_name: dict[str, str] = {}
    for a in sorted(actions, key=lambda x: x.get("step_order", 9999)):
        for ename, flow in a.get("entity_flow", {}).items():
            if flow == "produces" and ename not in _entity_first_producer:
                _entity_first_producer[ename] = a.get("actor", "")
                _entity_first_producer_name[ename] = a.get("actor_name", "")

    # 3. Build per-entity field_context: LLM-facing structured hints.
    _entity_field_context: dict[str, list[dict]] = {}  # entity_name → [{field, type, decision_info}]
    for e in entities:
        ename = e.get("name", "")
        fields = e.get("fields", []) or []
        ftypes = _entity_field_types.get(ename, {})
        ctx_list: list[dict] = []
        for f in fields:
            entry: dict = {
                "field": f,
                "type": ftypes.get(f, "str"),
            }
            if f in _decision_fields.get(ename, set()):
                entry["decision_condition"] = True
                owner_name = _decision_field_actor_name.get(f, "")
                if owner_name:
                    entry["decided_by_actor"] = owner_name
            if ename in _entity_first_producer_name:
                entry["first_produced_by"] = _entity_first_producer_name[ename]
            ctx_list.append(entry)
        if ctx_list:
            _entity_field_context[ename] = ctx_list

    return {
        "domain": {"name": domain_name},
        "actors": actors,
        "entities": entities,
        "actions": actions,
        "workflow": {
            "nodes": wf_nodes,
            "edges": wf_edges,
        },
        "field_context": _entity_field_context,
    }


def _build_flow_graph(classifiers: list, relations: list, parser_dsl: dict) -> dict:
    """Build a normalised flow graph used by state-driven page mapping.

    This is the intermediate layer between parser and UI synthesis:
      - states: canonical workflow states
      - transitions: actor-bound actions moving entity state from -> to
    """
    actors = {a["id"]: a for a in parser_dsl.get("actors", []) or []}
    actions = {a["id"]: a for a in parser_dsl.get("actions", []) or []}
    workflow_edges = parser_dsl.get("workflow", {}).get("edges", []) or []

    clf_by_id = {c["id"]: c for c in classifiers}
    object_nodes = {
        c["id"]: c for c in classifiers
        if c.get("data", {}).get("type") == "object"
    }

    incoming_object_states: dict[str, set[str]] = {}
    outgoing_object_states: dict[str, set[str]] = {}
    for rel in relations:
        if rel.get("data", {}).get("type") != "controlflow":
            continue
        src = rel.get("source")
        tgt = rel.get("target")
        if src in object_nodes and tgt in actions:
            s = _norm_state(object_nodes[src].get("data", {}).get("state", ""))
            if s:
                incoming_object_states.setdefault(tgt, set()).add(s)
        if src in actions and tgt in object_nodes:
            s = _norm_state(object_nodes[tgt].get("data", {}).get("state", ""))
            if s:
                outgoing_object_states.setdefault(src, set()).add(s)

    predecessors: dict[str, set[str]] = {}
    for edge in workflow_edges:
        if len(edge) < 2:
            continue
        src, tgt = edge[0], edge[1]
        if src in actions and tgt in actions:
            predecessors.setdefault(tgt, set()).add(src)

    action_from_state: dict[str, str] = {}
    action_to_state: dict[str, str] = {}

    for aid, action in actions.items():
        in_states = sorted(incoming_object_states.get(aid, set()))
        out_states = sorted(outgoing_object_states.get(aid, set()))
        action_from_state[aid] = in_states[0] if in_states else ""

        if out_states:
            action_to_state[aid] = out_states[0]
        else:
            action_to_state[aid] = _norm_state(f"{action.get('name', aid)} done")

    for aid, action in actions.items():
        if action_from_state.get(aid):
            continue
        pred_states = {
            action_to_state[p]
            for p in predecessors.get(aid, set())
            if action_to_state.get(p)
        }
        if len(pred_states) == 1:
            action_from_state[aid] = next(iter(pred_states))
        elif len(pred_states) > 1:
            action_from_state[aid] = "or_" + "_".join(sorted(pred_states))
        else:
            action_from_state[aid] = "start"

    states = {"start"}
    transitions = []
    for aid, action in actions.items():
        actor_id = action.get("actor")
        from_state = action_from_state.get(aid, "start") or "start"
        to_state = action_to_state.get(aid, "done") or "done"
        states.add(from_state)
        states.add(to_state)
        transitions.append({
            "id": f"tr_{aid}_{from_state}_{to_state}",
            "action_id": aid,
            "from": from_state,
            "to": to_state,
            "actor": actor_id,
            "action": action.get("name", aid),
            "auto": bool(action.get("auto", False)),
        })

    entity_names = [e.get("name", "") for e in parser_dsl.get("entities", []) or [] if e.get("name")]
    actor_names = [a.get("name", "") for a in parser_dsl.get("actors", []) or [] if a.get("name")]
    return {
        "entities": entity_names,
        "states": sorted(states),
        "actors": actor_names,
        "transitions": transitions,
    }


def _build_screens(classifiers: list, relations: list) -> List[ScreenInfo]:
    """Build a ScreenInfo for every non-automatic action in the classifier list.

    Models are inferred from object classifiers reachable via controlflow edges.
    CRUD flags are inferred from action name words matched against keyword sets.
    """
    obj_by_id: dict[str, dict] = {
        c["id"]: c for c in classifiers if c["data"].get("type") == "object"
    }

    def _connected_models(action_id: str) -> list[str]:
        models: list[str] = []
        for r in relations:
            if r["data"].get("type") != "controlflow":
                continue
            other_id: str = ""
            if r["source"] == action_id:
                other_id = r["target"]
            elif r["target"] == action_id:
                other_id = r["source"]
            if other_id and other_id in obj_by_id:
                clsname = obj_by_id[other_id]["data"].get("clsName", "")
                if clsname and clsname not in models:
                    models.append(clsname)
        return models

    screens: List[ScreenInfo] = []
    for c in classifiers:
        d = c["data"]
        if d.get("type") != "action" or d.get("isAutomatic"):
            continue
        name: str = d.get("name", "")
        words = set(name.lower().split())
        screens.append(ScreenInfo(
            page_id=c["id"],
            page_name=name,
            screen_type="",
            has_create=bool(words & _CREATE_KEYWORDS),
            has_update=bool(words & _UPDATE_KEYWORDS),
            has_delete=bool(words & _DELETE_KEYWORDS),
            models=_connected_models(c["id"]),
            sections_count=1,
        ))
    return screens


def parser_node(state: PipelineState) -> dict:
    """Parse metadata JSON (classifiers + relations format) → ScreenInfo list + diagram summary + DSL."""
    try:
        metadata = json.loads(state["metadata"])
        classifiers: list = metadata.get("classifiers", [])
        relations: list = metadata.get("relations", [])
        screens = _build_screens(classifiers, relations)
        diagram_summary = _build_diagram_summary(classifiers, relations)
        diagrams: list = metadata.get("diagrams", [])
        parser_dsl = _build_parser_dsl(classifiers, relations, diagrams)
        flow_graph = _build_flow_graph(classifiers, relations, parser_dsl)
        parser_dsl["flow_graph"] = flow_graph
        return {
            "screens": screens,
            "diagram_summary": diagram_summary,
            "parser_dsl": parser_dsl,
            "flow_graph": flow_graph,
            "error": None,
        }
    except Exception as exc:
        logger.exception("parser_node failed")
        return {
            "screens": [],
            "diagram_summary": {"usecase": [], "activity": [], "classes": []},
            "parser_dsl": {"actors": [], "objects": [], "activities": [], "workflow": {"transitions": []}},
            "flow_graph": {"entities": [], "states": [], "actors": [], "transitions": []},
            "error": str(exc),
        }


# ─────────────────────────────────────────────────────────────────────────────
# Page Synthesis — deterministic UI segmentation compiler pass
#    Input:  parser_dsl (actors / entities / actions / workflow)
#    Output: list of PageSpec dicts, one per navigational unit
#
#    Algorithm (three phases):
#      1. Filter   — skip auto=True actions (no human UI)
#      2. Cluster  — group manual actions by actor; within each actor
#                    group, merge pairs whose affinity score > THRESHOLD
#      3. Cut      — if a cluster > MAX_ACTIONS_PER_PAGE, split it
# ─────────────────────────────────────────────────────────────────────────────

_PAGE_AFFINITY_THRESHOLD = 0.5   # minimum score to share a page
_MAX_ACTIONS_PER_PAGE    = 5     # hard split ceiling per page


def _synthesise_pages(parser_dsl: dict) -> dict:
    """Pure, deterministic page synthesis.

    Returns a ui_ir-format dict:
        {
          "apps": [
            {
              "actor_id": str,                # actor id
              "pages": [
                {
                  "name":       str,          # PascalCase page name
                  "components": [ComponentSpec],
                }
              ],
            }
          ],
          "routing": {
            "auth_role_map": {actor_id: "/<actor_id>"},
          },
        }

    ComponentSpec:
        {
          "type":        str,           # form | detail | delete_confirm | list
          "bind_action": str,           # action id that triggers this component
          "entity_id":   str | None,    # entity this component operates on
          "fields":      [str],         # entity field names (empty if no entity)
        }

    Guarantees:
    - Auto actions produce no pages.
    - Actions for different actors are never on the same page.
    - Same input always produces the same output (deterministic).
    - An empty or missing DSL returns {"apps": [], "routing": {"auth_role_map": {}}}.
    """
    _EMPTY: dict = {"apps": [], "routing": {"auth_role_map": {}}}

    flow_graph = parser_dsl.get("flow_graph") or {}
    transitions = flow_graph.get("transitions", []) if isinstance(flow_graph, dict) else []
    if transitions:
        actors = {a["id"]: a for a in parser_dsl.get("actors", []) or []}
        actor_groups: dict[tuple[str, str], list[dict]] = {}
        for t in transitions:
            if t.get("auto"):
                continue
            actor_id = t.get("actor")
            if not actor_id or actor_id not in actors:
                continue
            from_state = _norm_state(t.get("from", "start")) or "start"
            actor_groups.setdefault((actor_id, from_state), []).append(t)

        if not actor_groups:
            return _EMPTY

        actions_by_id = {a["id"]: a for a in parser_dsl.get("actions", []) or []}
        entities_by_id = {e["id"]: e for e in parser_dsl.get("entities", []) or []}

        apps_by_actor: dict[str, list] = {}
        for actor_id, state in sorted(actor_groups.keys()):
            group = actor_groups[(actor_id, state)]
            actor_name = actors.get(actor_id, {}).get("name", actor_id)
            state_token = "".join(w.capitalize() for w in state.split("_")) or "State"
            page_name = f"{''.join(w.capitalize() for w in actor_name.replace('-', ' ').split())}{state_token}Page"
            page_id = "_".join(actor_name.lower().replace("-", "_").split()) + f"_{state}_page"
            action_ids = [t["action_id"] for t in group]
            transition_ids = [t["id"] for t in group]
            intent_hints = []
            for t in group:
                act = actions_by_id.get(t["action_id"], {})
                entity_ids = act.get("input", []) or []
                entity_names = [
                    entities_by_id.get(eid, {}).get("name", eid)
                    for eid in entity_ids
                ]
                attribute_contracts = []
                binding_groups = []
                operation_hint = {
                    "endpoint": f"/action/{t['action_id']}/",
                    "allowed": ["create", "update", "delete", "readonly"],
                    "kind": "llm_decide",
                }
                field_context = parser_dsl.get("field_context", {})
                for eid in entity_ids:
                    entity = entities_by_id.get(eid, {})
                    entity_name = entity.get("name", eid)
                    fields = entity.get("fields", []) or []
                    fc_list = field_context.get(entity_name, [])
                    fc_by_field = {fc["field"]: fc for fc in fc_list}
                    binds = []
                    for field in fields:
                        bind_expr = f"{entity_name}.{field}"
                        binds.append(bind_expr)
                        fc = fc_by_field.get(field, {})
                        contract: dict = {
                            "entity_id": eid,
                            "entity_name": entity_name,
                            "attribute": field,
                            "bind": bind_expr,
                            "field_type": fc.get("type", "str"),
                            "ui_policy": {
                                "validation": [],
                                "operations": operation_hint,
                            },
                        }
                        if fc.get("decision_condition"):
                            contract["decision_condition"] = True
                            if fc.get("decided_by_actor"):
                                contract["decided_by_actor"] = fc["decided_by_actor"]
                        if fc.get("first_produced_by"):
                            contract["first_produced_by"] = fc["first_produced_by"]
                        attribute_contracts.append(contract)
                    if len(binds) >= 2:
                        binding_groups.append({
                            "entity_id": eid,
                            "entity_name": entity_name,
                            "bind": binds,
                            "kind": "attribute_set_projection",
                        })
                intent_hints.append({
                    "action_id": t["action_id"],
                    "action_name": act.get("name", t["action_id"]),
                    "transition_id": t["id"],
                    "entity_ids": entity_ids,
                    "entity_names": entity_names,
                    "attribute_contracts": attribute_contracts,
                    "binding_groups": binding_groups,
                    "workflow_context": {
                        "entity_flow": act.get("entity_flow", {}),
                        "step_order": act.get("step_order", 0),
                        "upstream_actions": act.get("upstream_actions", []),
                        "downstream_actions": act.get("downstream_actions", []),
                        "control_flow": act.get("control_flow", []),
                        "actor_name": act.get("actor_name", ""),
                        "state_transitions": act.get("state_transitions", {}),
                    },
                })
            apps_by_actor.setdefault(actor_id, []).append({
                "page_id": page_id,
                "name": page_name,
                "state": state,
                "action_ids": action_ids,
                "transition_ids": transition_ids,
                "intent_hints": intent_hints,
            })

        apps = [
            {
                "actor_id": actor_id,
                "actor_name": actors.get(actor_id, {}).get("name", actor_id),
                "pages": pages,
            }
            for actor_id, pages in apps_by_actor.items()
        ]
        routing = {"auth_role_map": {a: f"/{a}" for a in apps_by_actor}}
        return {"apps": apps, "routing": routing}

    actors  = {a["id"]: a for a in parser_dsl.get("actors",  []) or []}
    actions = {a["id"]: a for a in parser_dsl.get("actions", []) or []}
    edges   = parser_dsl.get("workflow", {}).get("edges", []) or []

    # ── Phase 1: filter manual actions only ──────────────────────────────────
    manual = {
        aid: act
        for aid, act in actions.items()
        if not act.get("auto", False)
        and act.get("actor") in actors
    }
    if not manual:
        return _EMPTY

    # ── Build adjacency set from workflow edges ──────────────────────────────
    adjacent: set[tuple] = set()
    for edge in edges:
        if len(edge) >= 2:
            adjacent.add((edge[0], edge[1]))
            adjacent.add((edge[1], edge[0]))   # treat as undirected for affinity

    # ── Phase 2: greedy cluster per actor ────────────────────────────────────
    def _affinity(a_id: str, b_id: str) -> float:
        a, b = manual[a_id], manual[b_id]
        score = 0.0
        if a.get("actor") == b.get("actor"):
            score += 0.4
        if (a_id, b_id) in adjacent:
            score += 0.3
        # shared input entity
        a_inputs = set(a.get("input", []) or [])
        b_inputs = set(b.get("input", []) or [])
        if a_inputs & b_inputs:
            score += 0.3
        return score

    # Initialise: each action is its own cluster
    clusters: list[list[str]] = [[aid] for aid in manual]

    changed = True
    while changed:
        changed = False
        merged: list[list[str]] = []
        used = [False] * len(clusters)
        for i in range(len(clusters)):
            if used[i]:
                continue
            current = clusters[i]
            for j in range(i + 1, len(clusters)):
                if used[j]:
                    continue
                other = clusters[j]
                # Hard constraint: never mix actors
                actor_i = manual[current[0]].get("actor")
                actor_j = manual[other[0]].get("actor")
                if actor_i != actor_j:
                    continue
                # Would merge violate size limit?
                if len(current) + len(other) > _MAX_ACTIONS_PER_PAGE:
                    continue
                # Check average affinity between all pairs across the two clusters
                pairs = [(a, b) for a in current for b in other]
                avg_score = sum(_affinity(a, b) for a, b in pairs) / len(pairs)
                if avg_score >= _PAGE_AFFINITY_THRESHOLD:
                    current = current + other
                    used[j] = True
                    changed = True
            merged.append(current)
            used[i] = True
        clusters = merged

    # ── Phase 3: cut oversized clusters ─────────────────────────────────────
    final_clusters: list[list[str]] = []
    for cluster in clusters:
        if len(cluster) <= _MAX_ACTIONS_PER_PAGE:
            final_clusters.append(cluster)
        else:
            for k in range(0, len(cluster), _MAX_ACTIONS_PER_PAGE):
                final_clusters.append(cluster[k: k + _MAX_ACTIONS_PER_PAGE])

    # ── Emit ui_ir ──────────────────────────────────────────────────────────
    entity_list = parser_dsl.get("entities", []) or []
    entity_by_id = {e["id"]: e for e in entity_list}

    def _page_name(actor_name: str, page_num: int) -> str:
        safe = actor_name.lower().replace("-", "_").replace(" ", "_")
        raw = f"{safe}_page" if page_num == 0 else f"{safe}_page_{page_num + 1}"
        return "".join(w.capitalize() for w in raw.split("_"))

    # Group clusters by actor, preserving ordering
    apps_by_actor: dict[str, list] = {}
    actor_page_counter: dict[str, int] = {}
    for cluster in final_clusters:
        actor_id = manual[cluster[0]].get("actor", "")
        actor_name = actors.get(actor_id, {}).get("name", actor_id)
        page_num = actor_page_counter.get(actor_id, 0)
        actor_page_counter[actor_id] = page_num + 1
        apps_by_actor.setdefault(actor_id, []).append({
            "name":       _page_name(actor_name, page_num),
            "action_ids": cluster,
        })

    apps = [
        {"actor_id": actor_id, "actor_name": actors.get(actor_id, {}).get("name", actor_id), "pages": pages}
        for actor_id, pages in apps_by_actor.items()
    ]
    routing = {"auth_role_map": {a: f"/{a}" for a in apps_by_actor}}
    return {"apps": apps, "routing": routing}


# ─────────────────────────────────────────────────────────────────────────────
# UI Designer Agent
#    Takes the final UX design and generates a modern Tailwind-based
#    Django base.html + style.css. The Jinja2-generated page content
#    blocks automatically inherit the new look.
# ─────────────────────────────────────────────────────────────────────────────


def _enforce_field_policies(ui_design: dict) -> dict:
    """Post-process LLM output: enforce field_policies on AST nodes.

    For each component, read its field_policies and:
    - Remove AST nodes whose 'bind' matches a hidden field.
    - Convert input/textarea/select nodes for readonly fields into span nodes.
    Also removes hidden fields from the component's 'attributes' list.
    """

    def _bind_field_name(bind_val: str) -> str | None:
        """Extract the field name from a bind like 'Entity.field'."""
        if not bind_val or not isinstance(bind_val, str):
            return None
        parts = bind_val.rsplit(".", 1)
        return parts[-1] if parts else None

    def _is_hidden_node(node: dict, hidden_fields: set) -> bool:
        """Check if a node binds to a hidden field."""
        bind = node.get("bind", "")
        fname = _bind_field_name(bind)
        return fname is not None and fname in hidden_fields

    def _strip_hidden_nodes(nodes: list, hidden_fields: set) -> list:
        """Recursively remove nodes bound to hidden fields and their label siblings."""
        if not hidden_fields:
            return nodes
        result = []
        skip_next_label_for: set | None = None
        i = 0
        while i < len(nodes):
            node = nodes[i]
            if not isinstance(node, dict):
                result.append(node)
                i += 1
                continue

            # Check if this node directly binds to a hidden field
            if _is_hidden_node(node, hidden_fields):
                # Also remove the preceding label if it was just added
                if result and isinstance(result[-1], dict) and result[-1].get("tag") == "label":
                    result.pop()
                i += 1
                continue

            # Check if next sibling is a hidden input — then this label should be skipped
            tag = node.get("tag", "")
            if tag == "label" and i + 1 < len(nodes):
                next_node = nodes[i + 1] if isinstance(nodes[i + 1], dict) else {}
                if _is_hidden_node(next_node, hidden_fields):
                    i += 1  # skip label; the hidden node itself will be skipped next iteration
                    continue

            # Recurse into children
            new_node = dict(node)
            if "children" in new_node and isinstance(new_node["children"], list):
                new_node["children"] = _strip_hidden_nodes(new_node["children"], hidden_fields)
            if "else_children" in new_node and isinstance(new_node["else_children"], list):
                new_node["else_children"] = _strip_hidden_nodes(new_node["else_children"], hidden_fields)
            result.append(new_node)
            i += 1
        return result

    def _convert_readonly_nodes(nodes: list, readonly_fields: set) -> list:
        """Recursively mark nodes bound to readonly fields as display-only.

        Generic — no hardcoded tag or attr lists:
        - Sets variant="readonly" so theme tokens control the visual style.
        - Strips htmx dict to remove all server interaction.
        - Preserves tag, attrs, text, bind, children — structure stays intact
          so the theme can apply rich 'human in the loop' styling.
        """
        if not readonly_fields:
            return nodes
        result = []
        for node in nodes:
            if not isinstance(node, dict):
                result.append(node)
                continue
            new_node = dict(node)
            bind = new_node.get("bind", "")
            fname = _bind_field_name(bind)

            if fname and fname in readonly_fields:
                new_node["variant"] = "readonly"
                new_node.pop("htmx", None)

            # Always recurse into children
            if "children" in new_node and isinstance(new_node["children"], list):
                new_node["children"] = _convert_readonly_nodes(new_node["children"], readonly_fields)
            if "else_children" in new_node and isinstance(new_node["else_children"], list):
                new_node["else_children"] = _convert_readonly_nodes(new_node["else_children"], readonly_fields)
            result.append(new_node)
        return result

    ui_ir = ui_design.get("ui_ir", {})
    for app in ui_ir.get("apps", []):
        for page in app.get("pages", []):
            for region in page.get("regions", []):
                # Collect field_policies from all components in this region
                hidden_fields: set[str] = set()
                readonly_fields: set[str] = set()
                for comp in region.get("components", []):
                    fp = comp.get("field_policies", {})
                    for attr_name, policy in fp.items():
                        mode = policy.get("mode", "")
                        if mode == "hidden":
                            hidden_fields.add(attr_name)
                        elif mode == "readonly":
                            readonly_fields.add(attr_name)
                    # Remove hidden fields from attributes list
                    if "attributes" in comp and isinstance(comp["attributes"], list):
                        comp["attributes"] = [
                            a for a in comp["attributes"] if a not in hidden_fields
                        ]

                ast_nodes = region.get("ast", [])
                if ast_nodes:
                    ast_nodes = _strip_hidden_nodes(ast_nodes, hidden_fields)
                    ast_nodes = _convert_readonly_nodes(ast_nodes, readonly_fields)
                    region["ast"] = ast_nodes

    return ui_design


def _guardrail_entity_flow(ui_design: dict, page_ir: dict) -> dict:
    """Post-process guardrail: enforce hard entity_flow constraints on LLM output.

    1. consumes → all field_policies must be readonly (never editable).
    2. produces/read_write → at least one field must be editable in some component.
       If the LLM made everything readonly/hidden, flip the first non-decision field to editable.
    """
    # Build lookup: page_id → [{entity_flow, action_name}]
    page_flow: dict[str, list[dict]] = {}
    for app_ir in page_ir.get("apps", []):
        for page in app_ir.get("pages", []):
            pid = page.get("page_id", "")
            hints = page.get("intent_hints", [])
            for h in hints:
                wc = h.get("workflow_context", {})
                ef = wc.get("entity_flow", {})
                page_flow.setdefault(pid, []).append(ef)

    ui_ir = ui_design.get("ui_ir", {})
    for app in ui_ir.get("apps", []):
        for page in app.get("pages", []):
            pid = page.get("page_id", "")
            flows = page_flow.get(pid, [])
            if not flows:
                continue

            # Aggregate entity_flow for this page
            all_consumes = all(
                flow_val == "consumes"
                for ef in flows
                for flow_val in ef.values()
            ) if flows else False

            any_produces_or_rw = any(
                flow_val in ("produces", "read_write")
                for ef in flows
                for flow_val in ef.values()
            )

            for region in page.get("regions", []):
                for comp in region.get("components", []):
                    fp = comp.get("field_policies", {})

                    if all_consumes:
                        # HARD: consumes → force all to readonly
                        for attr_name, policy in fp.items():
                            if policy.get("mode") == "editable":
                                policy["mode"] = "readonly"
                                logger.debug("guardrail: %s.%s forced readonly (consumes)", pid, attr_name)

            if any_produces_or_rw:
                # Check if at least one editable field exists
                has_editable = False
                for region in page.get("regions", []):
                    for comp in region.get("components", []):
                        fp = comp.get("field_policies", {})
                        if any(p.get("mode") == "editable" for p in fp.values()):
                            has_editable = True
                            break
                    if has_editable:
                        break

                if not has_editable:
                    # Flip first non-hidden field to editable
                    flipped = False
                    for region in page.get("regions", []):
                        for comp in region.get("components", []):
                            fp = comp.get("field_policies", {})
                            for attr_name, policy in fp.items():
                                if policy.get("mode") != "hidden":
                                    policy["mode"] = "editable"
                                    logger.info("guardrail: %s.%s flipped to editable (produces/read_write needs inputs)", pid, attr_name)
                                    flipped = True
                                    break
                            if flipped:
                                break
                        if flipped:
                            break

    # Re-run _enforce_field_policies to fix AST after guardrail changes
    return _enforce_field_policies(ui_design)


def ui_designer_node(state: PipelineState) -> dict:
    """UI Designer: runs page synthesis then calls LLM for ui_ir component mapping."""
    from llm.prompts.agents import AGENT_UI_DESIGNER

    parser_dsl = state.get("parser_dsl") or {}

    # ── Deterministic page synthesis (pre-LLM) ───────────────────────────────
    page_ir = _synthesise_pages(parser_dsl)
    ui_layout_references = _build_ui_layout_references(n=5, blocks_per_page=6)

    prompt = AGENT_UI_DESIGNER.format(
        project_name=state["project_name"],
        application_name=state["application_name"],
        page_ir_json=json.dumps(page_ir, indent=2),
        parser_dsl_json=json.dumps(parser_dsl, indent=2),
        ui_layout_references=ui_layout_references,
    )

    try:
        raw = call_openai("gpt-4o", prompt)
        ui_design = _parse_json_response(raw)

        # Guardrail: ensure generated structure actually uses fetched layout hints.
        # If overlap is too low, retry once with a stricter reminder.
        align_ratio = _layout_alignment_ratio(ui_design, ui_layout_references)
        if align_ratio < 0.08:
            strict_prompt = (
                prompt
                + "\n\nSTRICT FETCHED-LAYOUT ENFORCEMENT:\n"
                + "Your previous output underused fetched LAYOUT_HINTS. Regenerate ui_ir and explicitly"
                + " reuse fetched layout utilities in attrs.class for page/region containers."
                + " Keep forms readable: do NOT place all form fields in one horizontal row;"
                + " form containers must be vertical stack or clear grid with spacing."
            )
            raw = call_openai("gpt-4o", strict_prompt)
            ui_design = _parse_json_response(raw)
        # Default ui_ir to the deterministic page_ir when LLM omits it
        ui_design.setdefault("ui_ir", page_ir)
        # Merge actor_name from page_ir into the LLM ui_ir (LLM may not emit it)
        page_ir_actor_names = {app["actor_id"]: app.get("actor_name") for app in page_ir.get("apps", [])}
        for app in ui_design["ui_ir"].get("apps", []):
            if not app.get("actor_name"):
                app["actor_name"] = page_ir_actor_names.get(app["actor_id"])
        # Enforce field_policies on AST: strip hidden fields, convert readonly
        ui_design = _enforce_field_policies(ui_design)
        # Guardrail: enforce hard entity_flow constraints (consumes→readonly, produces→has editables)
        ui_design = _guardrail_entity_flow(ui_design, page_ir)
        logger.info("ui_designer_node: %d ui_ir apps",
                    len(ui_design.get("ui_ir", {}).get("apps", [])))
        return {"page_ir": page_ir, "ui_design": ui_design, "error": None}
    except Exception as exc:
        logger.warning("ui_designer_node failed (%s); skipping UI enhancement", exc)
        return {"page_ir": page_ir, "ui_design": None, "error": None}  # non-fatal: Jinja2 fallback still works


# ── Theme Node ────────────────────────────────────────────────────────────────

def _collect_variants(obj: object, seen: set | None = None) -> list:
    """Recursively walk ui_design and collect unique {tag, variant} pairs from AST nodes."""
    if seen is None:
        seen = set()
    results = []
    if isinstance(obj, dict):
        variant = obj.get("variant")
        if variant:
            tag = obj.get("tag", "div")
            key = (tag, variant)
            if key not in seen:
                seen.add(key)
                results.append({"tag": tag, "variant": variant})
        for v in obj.values():
            results.extend(_collect_variants(v, seen))
    elif isinstance(obj, list):
        for item in obj:
            results.extend(_collect_variants(item, seen))
    return results


def theme_node(state: PipelineState) -> dict:
    """Theme Agent: inspects actual AST variant labels and generates matching design tokens.

    The LLM decides the token key namespace (region.*, component.*, element.*) based on
    the tag + variant context. No keys are hardcoded — tokens are driven entirely by what
    variants the UI Designer placed in the AST.
    """
    from llm.prompts.agents import AGENT_THEME_DESIGNER

    ui_design = state.get("ui_design") or {}
    variants = _collect_variants(ui_design)

    # Collect region types from page structures — the preview renderer wraps each
    # region in a <div variant="<region_type>"> so the theme must provide tokens.
    ui_ir = ui_design.get("ui_ir") or {}
    _region_type_seen: set[str] = set()
    for app in ui_ir.get("apps", []) or []:
        for page in app.get("pages", []) or []:
            for region in page.get("regions", []) or []:
                rtype = region.get("type")
                if rtype and rtype not in _region_type_seen:
                    _region_type_seen.add(rtype)
    existing_variant_keys = {v["variant"] for v in variants}
    for rtype in sorted(_region_type_seen):
        if rtype not in existing_variant_keys:
            variants.append({"tag": "div", "variant": rtype})
            existing_variant_keys.add(rtype)

    # Always inject structural page-level tokens so every theme covers the page shell.
    # These control <body> bg, <main> width/padding, and the content surface card.
    _PAGE_STRUCTURAL_VARIANTS = [
        {"tag": "body", "variant": "page.body"},
        {"tag": "main", "variant": "page.main"},
        {"tag": "div",  "variant": "page.surface"},
    ]
    for sv in _PAGE_STRUCTURAL_VARIANTS:
        if sv["variant"] not in existing_variant_keys:
            variants.append(sv)
            existing_variant_keys.add(sv["variant"])

    if not variants:
        logger.info("theme_node: no variants found in ui_design; skipping LLM call")
        return {"theme": {"name": "default", "tokens": {}}}

    design_goal = (state.get("theme") or {}).get("design_goal") or \
                  f"Clean professional UI for {state['project_name']}"
    theme_references = _build_ui_layout_references(n=4, blocks_per_page=5)
    component_references = _build_component_style_references(n=4, max_per_component=3)

    prompt = AGENT_THEME_DESIGNER.format(
        project_name=state["project_name"],
        application_name=state["application_name"],
        design_goal=design_goal,
        variants_json=json.dumps(variants, indent=2),
        theme_references=theme_references,
        component_references=component_references,
    )

    refine_prompt = state.get("refine_prompt")
    if refine_prompt:
        prompt += (
            f"\n\nREFINEMENT REQUEST FROM USER:\n{refine_prompt}\n"
            "Adjust the design tokens to satisfy this request. "
            "Keep all required variant keys — update only the Tailwind class values."
        )

    try:
        raw = call_openai("gpt-4o", prompt)
        theme = _parse_json_response(raw)
        logger.info(
            "theme_node: generated theme '%s' with %d tokens",
            theme.get("name"), len(theme.get("tokens", {})),
        )
        return {"theme": theme}
    except Exception as exc:
        logger.warning("theme_node failed (%s); using empty theme", exc)
        return {"theme": {"name": "default", "tokens": {}}}


def layout_options_node(state: PipelineState) -> dict:
    """Layout Options Agent: generates 5 distinct global layout presets for the designer to pick.

    Design references are fetched live from public design libraries (Flowbite, DaisyUI, MerakiUI)
    at runtime, so each pipeline run receives fresh HTML pattern examples as LLM context.
    Each option contains named elements (navbar, sidebar, footer, etc.) with:
    - html: standalone Tailwind snippet
    - position: top|left|right|bottom
    - config: semantic AST dict (logo, links, colors) for surgical refinement later
    """
    from llm.prompts.agents import AGENT_LAYOUT_OPTIONS

    theme = state.get("theme") or {}
    theme_name = theme.get("name", "default")
    tokens = theme.get("tokens") or {}

    # Always ensure structural page-shell tokens are in scope for layout options,
    # even if theme_node produced them in a fresh run's tokens dict.
    _PAGE_LAYOUT_KEYS = ["page.body", "page.main", "page.surface"]
    extended_tokens = dict(tokens)
    for k in _PAGE_LAYOUT_KEYS:
        extended_tokens.setdefault(k, "")

    parser_dsl = state.get("parser_dsl") or {}
    actors = [a.get("name", a.get("id", "")) for a in (parser_dsl.get("actors") or [])]

    design_references = _build_design_references(n=5)
    logger.info("layout_options_node: fetched design references (%d chars)", len(design_references))
    region_references = _build_ui_layout_references(n=3, blocks_per_page=5)
    logger.info("layout_options_node: fetched region references (%d chars)", len(region_references))

    prompt = AGENT_LAYOUT_OPTIONS.format(
        project_name=state["project_name"],
        application_name=state["application_name"],
        actors_json=json.dumps(actors),
        theme_name=theme_name,
        theme_token_keys=json.dumps(list(extended_tokens.keys())),
        design_references=design_references,
        region_references=region_references,
    )

    try:
        raw = call_openai("gpt-4o", prompt)
        raw = raw.strip()
        if raw.startswith("```"):
            lines = raw.split("\n")
            raw = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
        options = json.loads(raw)
        if not isinstance(options, list):
            raise ValueError("expected JSON array")
        # Ensure every option's theme_tokens covers exactly the same keys as the base theme.
        # LLMs sometimes omit keys or use wrong names — fill gaps with base theme values.
        for opt in options:
            opt_tokens = opt.get("theme_tokens") or {}
            merged = {}
            for key, base_val in extended_tokens.items():
                merged[key] = opt_tokens.get(key, base_val)
            opt["theme_tokens"] = merged
        logger.info("layout_options_node: generated %d layout options", len(options))
        return {"layout_options": options}
    except Exception as exc:
        logger.warning("layout_options_node failed (%s); returning empty options", exc)
        return {"layout_options": []}

