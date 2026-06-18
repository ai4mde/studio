from metadata.models import Interface
from llm.template_renderer import render_layout, normalize_interface_schema

iface = Interface.objects.get(id='ec58bb5b-fb1a-44c4-b9ff-dbc0c2a8944c')
interface_data = normalize_interface_schema(dict(iface.data or {}))

classifiers = [{"id": str(c.id), "data": c.data}
               for c in iface.system.classifiers.filter(data__type='class')]
relations = [{"id": str(r.id), "source": str(r.source_id), "target": str(r.target_id), "data": r.data}
             for r in iface.system.relations.all()]

files = render_layout(interface_data, classifiers, None,
                      interface_name=iface.name, relations=relations, preview_mode=False)

targets = {
    'product_detail': '/tmp/Customer_Product_Detail.html',
    'view_cart':      '/tmp/Customer_View_Cart.html',
}

for f in files:
    for key, out_path in targets.items():
        if key in f['path'].lower():
            with open(out_path, 'w') as fp:
                fp.write(f['content'])
            print(f"Written {f['path']} -> {out_path}")
