#!/usr/bin/env python3

import os
import sys
import xml.etree.ElementTree as ET

X_STEP = 250
Y_STEP = 16

def create_graph():
    mxfile = ET.Element("mxfile")
    diagram = ET.SubElement(mxfile, "diagram", name="Page-1")
    mxGraphModel = ET.SubElement(diagram, "mxGraphModel")
    root = ET.SubElement(mxGraphModel, "root")

    ET.SubElement(root, "mxCell", id="0")
    ET.SubElement(root, "mxCell", id="1", parent="0")

    return mxfile, root

def add_node(root, node_id, label, x, y, parent="1", style=""):
    cell = ET.SubElement(
        root,
        "mxCell",
        id=node_id,
        value=label,
        style=style,
        vertex="1",
        parent=parent
    )

    geom = ET.SubElement(
        cell,
        "mxGeometry",
        x=str(x),
        y=str(y),
        width="200",
        height="14",
        as_="geometry"
    )
    geom.set("as", "geometry")

def main():
    if len(sys.argv) != 3:
        print("Usage: python tree_to_drawio_xml.py <root_folder> <output.xml>")
        sys.exit(1)

    root_path = os.path.abspath(sys.argv[1])
    out_file = sys.argv[2]

    mxfile, root = create_graph()

    counter = [0]

    def new_id():
        counter[0] += 1
        return f"n{counter[0]}"

    def walk(path, parent_id, depth, y_counter):
        entries = sorted(os.listdir(path))
        entries = filter(lambda x: x[0] != ".", entries)
        entries = sorted(entries, key=lambda e: not os.path.isdir(os.path.join(path, e)))

        for e in entries:
            full = os.path.join(path, e)
            node_id = new_id()

            is_dir = os.path.isdir(full)

            style = (
                "fillColor=#dae8fc;strokeColor=#6c8ebf;fontStyle=1;"
                if is_dir else
                "fillColor=#ffffff;strokeColor=#999999;"
            )

            x = depth * X_STEP
            y = y_counter[0] * Y_STEP
            y_counter[0] += 1

            add_node(root, node_id, e, x, y, parent="1", style=style)

            if is_dir:
                walk(full, node_id, depth + 1, y_counter)

    root_id = new_id()
    add_node(
        root,
        root_id,
        os.path.basename(root_path) or root_path,
        0,
        0,
        parent="1",
        style="fillColor=#dae8fc;strokeColor=#6c8ebf;fontStyle=1;"
    )

    walk(root_path, root_id, 1, [1])

    tree = ET.ElementTree(mxfile)
    tree.write(out_file, encoding="utf-8", xml_declaration=True)

if __name__ == "__main__":
    main()