"""Patches the existing generated prototype with the new addCartItem method and action_panel template."""
import sys
sys.path.insert(0, '/usr/src/model')

import os
from metadata.models import Interface
from llm.template_renderer import render_layout, normalize_interface_schema

PROTO_PATH = "/usr/src/prototypes/generated_prototypes/a0000002-0000-5000-8000-000000000000/sync1781202455394"

# ── 1. Re-render product_detail template ──────────────────────────────────
iface = Interface.objects.get(id='ec58bb5b-fb1a-44c4-b9ff-dbc0c2a8944c')
interface_data = normalize_interface_schema(dict(iface.data or {}))

classifiers = [
    {"id": str(c.id), "data": c.data}
    for c in iface.system.classifiers.filter(data__type='class')
]
relations = [
    {"id": str(r.id), "source": str(r.source_id), "target": str(r.target_id), "data": r.data}
    for r in iface.system.relations.all()
]

files = render_layout(interface_data, classifiers, None, interface_name=iface.name, relations=relations, preview_mode=False)

updated_templates = 0
for f in files:
    if 'product_detail' not in f['path'].lower():
        continue
    dest = os.path.join(PROTO_PATH, "Customer", "templates", "Customer_Product_Detail.html")
    if os.path.exists(dest):
        with open(dest, "w") as wf:
            wf.write(f['content'])
        updated_templates += 1
        print(f"Updated: {dest}")

print(f"Templates updated: {updated_templates}")

# ── 2. Patch models.py to add addCartItem method to Product ──────────────
models_path = os.path.join(PROTO_PATH, "shared_models", "models.py")
if not os.path.exists(models_path):
    print(f"ERROR: models.py not found at {models_path}")
    sys.exit(1)

with open(models_path, "r") as f:
    models_content = f.read()

METHOD_BODY = """
    def addCartItem(self, quantity):
        cart = Cart.objects.first()
        if cart is None:
            cart = Cart.objects.create()
        CartItem.objects.create(cart=cart, product=self, quantity=int(quantity))
"""

# Check if already patched
if "addCartItem" in models_content:
    print("models.py already has addCartItem, skipping.")
else:
    # Find the Product class __str__ or end of class to insert before it
    # Insert after "class Product" and look for the next class definition or end
    import re
    # Find class Product block and add before its closing
    # Strategy: find the __str__ method of Product and insert after it
    product_str_pattern = r'(class Product\(.*?\):.*?)(class \w)'
    # Use a simpler approach: find `class CartItem` and insert before it
    # Actually, just add after the Product class's last method

    # Find class Product and inject
    # Look for def __str__(self): inside Product class
    # Insert after the last method before the next class

    # Find 'class Product'
    product_class_match = re.search(r'\nclass Product\(', models_content)
    if not product_class_match:
        print("ERROR: Could not find 'class Product' in models.py")
        sys.exit(1)

    product_start = product_class_match.start()

    # Find the next top-level class after Product
    next_class_match = re.search(r'\nclass \w', models_content[product_start + 1:])
    if next_class_match:
        insert_pos = product_start + 1 + next_class_match.start()
    else:
        insert_pos = len(models_content)

    # Insert the method before the next class
    patched = models_content[:insert_pos] + METHOD_BODY + "\n" + models_content[insert_pos:]

    with open(models_path, "w") as f:
        f.write(patched)

    print("Patched models.py: added addCartItem to Product class")

# Verify
with open(models_path, "r") as f:
    content = f.read()
if "addCartItem" in content:
    print("Verification: addCartItem found in models.py ✓")
else:
    print("ERROR: addCartItem NOT found in models.py")
