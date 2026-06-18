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

for f in files:
    if 'product_detail' in f['path'].lower():
        lines = f['content'].split('\n')
        # Print lines around the new section
        for i, line in enumerate(lines):
            if 'product_add_to_cart' in line:
                start = max(0, i-2)
                end = min(len(lines), i+60)
                print(f"\n=== Context around line {i+1} ===")
                for j in range(start, end):
                    print(f"{j+1:4d}: {lines[j]}")
                break
