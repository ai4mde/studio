import os
import json5
import re
import xml.etree.ElementTree as ET
from xml.dom import minidom

VALID_EXT = {".js", ".jsx", ".ts", ".tsx", ".mts", ".cts", ".d.ts"}
EXCLUDE_DIRS = {"node_modules", "dist", "build", ".next", ".git"}

FOLDER_ICON = "📁 "
FILE_ICON = "📄 "

IMPORT_RE = re.compile(r'import\s+.*?\s+from\s+[\'"](.+?)[\'"]')


# =========================
# COLOR MAP (your architecture)
# =========================
COLOR_MAP = {
    "features/ai": "#9467bd",          # purple
    "features/auth": "#ff7f0e",     # orange
    "features/browser": "#2ca02c",     # green
    "features/chatbot": "#17becf",     # cyan
    "features/diagram":  "#1f77b4",        # blue (primary)

    "features/interfaces": "#7f7f7f",  # gray (neutral structural)

    "features/metadata": "#bcbd22",    # olive
    "features/prototypes": "#8c564b",  # brown

    "features/releases": "#d62728",    # red (lifecycle / deployment)

    "shared/components": "#e377c2",   # pink
    "shared/hooks": "#00b5ad",        # teal variant
    "shared/state": "#393b79",        # deep indigo
}


# =========================
# DEFAULT NODE STYLE
# =========================
DEFAULT_NODE_STYLE = (
    "shape=rectangle;"
    "rounded=1;"
    "whiteSpace=wrap;"
    "html=1;"
    "fillColor=#1e1e1e;"
    "strokeColor=#ffffff;"
    "fontColor=#ffffff;"
    "fontSize=36;"
)

def load_tsconfig(path):
    with open(path, "r", encoding="utf-8") as f:
        return json5.load(f)

def resolve_root(tsconfig_path, tsconfig):
    base = os.path.dirname(os.path.abspath(tsconfig_path))
    compiler = tsconfig.get("compilerOptions", {})

    base_url = compiler.get("baseUrl")
    if base_url:
        candidate = os.path.abspath(os.path.join(base, base_url))
        if os.path.exists(candidate):
            return candidate

    return base

class Node:
    _counter = 2

    def __init__(self, name, path, depth):
        self.name = name
        self.path = path
        self.depth = depth
        self.children = []
        self.id = Node._counter
        Node._counter += 1
        self.color = None


# =========================
# TREE BUILD
# =========================
def build_tree(path, depth=0, path_index=None):
    node = Node(os.path.basename(path), path, depth)
    path_index[os.path.abspath(path)] = node

    try:
        entries = os.listdir(path)
    except:
        return node

    folders, files = [], []

    for e in entries:
        full = os.path.join(path, e)

        if os.path.isdir(full):
            if not e.startswith(".") and e not in EXCLUDE_DIRS:
                folders.append(e)
        else:
            if os.path.splitext(e)[1] in VALID_EXT:
                files.append(e)

    folders.sort()
    files.sort()

    for f in folders:
        node.children.append(
            build_tree(os.path.join(path, f), depth + 1, path_index)
        )

    for file in files:
        full = os.path.join(path, file)
        file_node = Node(file, full, depth + 1)
        path_index[os.path.abspath(full)] = file_node
        node.children.append(file_node)

    return node


# =========================
# DEPENDENCY SOLVER
# =========================
class DependencySolver:
    def __init__(self, root_path, tsconfig=None):
        self.root = os.path.abspath(root_path)
        self.tsconfig = tsconfig or {}

        compiler = self.tsconfig.get("compilerOptions", {})
        self.paths = compiler.get("paths", {}) or {}
        self.base_url = compiler.get("baseUrl")

        self.external = []
        self.unresolved = []
        self.internal = []

    def extract_imports(self, content):
        return IMPORT_RE.findall(content)

    def build_file_map(self):
        file_map = {}

        for dirpath, _, filenames in os.walk(self.root):
            for f in filenames:
                if os.path.splitext(f)[1] not in VALID_EXT:
                    continue

                full = os.path.abspath(os.path.join(dirpath, f))

                try:
                    with open(full, "r", encoding="utf-8") as file:
                        file_map[full] = file.read()
                except:
                    pass

        return file_map

    def resolve_file(self, path):
        path = os.path.normpath(path)

        candidates = [
            path,
            path + ".ts",
            path + ".tsx",
            path + ".js",
            path + ".jsx",
            path + ".mts",
            path + ".cts",
            os.path.join(path, "index.ts"),
            os.path.join(path, "index.tsx"),
            os.path.join(path, "index.js"),
            os.path.join(path, "index.jsx"),
        ]

        for c in candidates:
            if os.path.isfile(c):
                return os.path.abspath(c)

        return None

    def resolve_relative(self, source_file, imp):
        base_dir = os.path.dirname(source_file)
        return self.resolve_file(os.path.join(base_dir, imp))

    def resolve_alias(self, imp):
        imp = imp.replace("\\", "/")

        for alias, targets in self.paths.items():
            for target in targets:
                alias_base = alias.replace("/*", "")
                target_base = target.replace("/*", "")

                if alias.endswith("/*") and imp.startswith(alias_base + "/"):
                    rest = imp[len(alias_base) + 1:]
                    candidate = os.path.join(self.root, target_base, rest)
                    resolved = self.resolve_file(candidate)
                    if resolved:
                        return resolved

                if not alias.endswith("/*") and imp == alias_base:
                    candidate = os.path.join(self.root, target_base)
                    resolved = self.resolve_file(candidate)
                    if resolved:
                        return resolved

        return None

    def resolve_base(self, imp):
        if not self.base_url:
            return None

        candidate = os.path.join(self.root, self.base_url, imp)
        return self.resolve_file(candidate)

    def resolve_import(self, source_file, imp):
        imp = imp.replace("\\", "/")

        if imp.startswith("."):
            return self.resolve_relative(source_file, imp)

        if imp.startswith("$") or imp in self.paths:
            res = self.resolve_alias(imp)
            if res:
                return res

        base = self.resolve_base(imp)
        if base:
            return base

        return "EXTERNAL"

    def analyze_project(self):
        file_map = self.build_file_map()
        edges = []

        for path, content in file_map.items():
            for imp in self.extract_imports(content):
                result = self.resolve_import(path, imp)

                if result == "EXTERNAL":
                    self.external.append((path, imp))

                elif result:
                    self.internal.append((path, result))
                    edges.append((path, result))

                else:
                    self.unresolved.append((path, imp))

        return edges

    # =========================
    # COLOR LOGIC (FIXED)
    # =========================
    def get_module_key(self, abs_path):
        rel = os.path.relpath(abs_path, self.root).replace("\\", "/")

        parts = rel.split("/")

        if "features" in parts:
            i = parts.index("features")
            if i + 1 < len(parts):
                return f"features/{parts[i + 1]}"

        if "shared" in parts:
            i = parts.index("shared")
            if i + 1 < len(parts):
                return f"shared/{parts[i + 1]}"

        return None

    def get_color(self, abs_path):
        key = self.get_module_key(abs_path)
        return COLOR_MAP.get(key, None)


# =========================
# COLOR APPLICATION
# =========================
def apply_colors(path_index, solver):
    for abs_path, node in path_index.items():
        node.color = solver.get_color(abs_path)


# =========================
# GENERATE DIAGRAM
# =========================
def generate(tsconfig_path, output_file):
    tsconfig = load_tsconfig(tsconfig_path)
    root_path = resolve_root(tsconfig_path, tsconfig)

    path_index = {}
    build_tree(root_path, 0, path_index)

    id_to_node = {node.id: node for node in path_index.values()}

    solver = DependencySolver(root_path, tsconfig)
    raw_edges = solver.analyze_project()

    apply_colors(path_index, solver)

    edges = []
    for src, dst in raw_edges:
        if src in path_index and dst in path_index:
            edges.append((path_index[src].id, path_index[dst].id))

    mxfile = ET.Element("mxfile", host="app.diagrams.net")
    diagram = ET.SubElement(mxfile, "diagram", name="Project")
    model = ET.SubElement(diagram, "mxGraphModel")
    root = ET.SubElement(model, "root")

    ET.SubElement(root, "mxCell", {"id": "0"})
    ET.SubElement(root, "mxCell", {"id": "1", "parent": "0"})

    # NODES
    for node in path_index.values():
        color = node.color

        if color is None:
            style = DEFAULT_NODE_STYLE
        else:
            style = (
                "shape=rectangle;"
                "rounded=1;"
                "whiteSpace=wrap;"
                "html=1;"
                f"fillColor={color};"
                f"strokeColor={color};"
                "fontColor=#000000;"
                "fontSize=36;"
            )

        cell = ET.SubElement(root, "mxCell", {
            "id": str(node.id),
            "value": (FOLDER_ICON if node.children else FILE_ICON) + node.name,
            "vertex": "1",
            "parent": "1",
            "style": style
        })

        geom = ET.SubElement(cell, "mxGeometry")
        geom.set("x", str(node.depth * 1000))
        geom.set("y", str(node.id * 100))
        geom.set("width", "500")
        geom.set("height", "90")
        geom.set("as", "geometry")

    # EDGES
    edge_id = 10000
    for s, t in edges:
        src_node = id_to_node.get(s)
        color = src_node.color if src_node and src_node.color else "#999999"

        edge = ET.SubElement(root, "mxCell", {
            "id": str(edge_id),
            "edge": "1",
            "parent": "1",
            "source": str(s),
            "target": str(t),
            "style": (
                "html=1;"
                f"strokeColor={color};"
                "endArrow=block;"
                "edgeStyle=none;"
            )
        })

        ET.SubElement(edge, "mxGeometry", {"relative": "1", "as": "geometry"})
        edge_id += 1

    xml = minidom.parseString(ET.tostring(mxfile)).toprettyxml(indent="  ")

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(xml)


if __name__ == "__main__":
    import sys
    generate(sys.argv[2], sys.argv[1])