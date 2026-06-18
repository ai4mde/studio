import sys
sys.path.insert(0, '/usr/src/model')

from metadata.models import Interface
from llm.template_renderer import render_layout, normalize_interface_schema

iface = Interface.objects.get(id='ec58bb5b-fb1a-44c4-b9ff-dbc0c2a8944c')
interface_data = dict(iface.data or {})
interface_data = normalize_interface_schema(interface_data)

classifiers = [
    {"id": str(c.id), "data": c.data}
    for c in iface.system.classifiers.filter(data__type='class')
]
relations = [
    {"id": str(r.id), "source": str(r.source_id), "target": str(r.target_id), "data": r.data}
    for r in iface.system.relations.all()
]

files = render_layout(interface_data, classifiers, None, interface_name=iface.name, relations=relations, preview_mode=False)

print(f"Total files rendered: {len(files)}")
for f in files:
    print(f"  {f['path']}")

# Check product_detail
for f in files:
    if 'product_detail' in f['path'].lower():
        print(f"\n=== {f['path']} ===")
        lines = f['content'].split('\n')
        print(f"Total lines: {len(lines)}")
        # Search for action_panel keyword
        for i, line in enumerate(lines):
            if 'addCartItem' in line or 'Add to Cart' in line:
                print(f"  Line {i+1}: {line.strip()[:120]}")
