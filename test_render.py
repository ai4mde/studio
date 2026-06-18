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

print(f"Total files: {len(files)}")
for f in files:
    path = f['path']
    content = f['content']

    # product_detail: check action_panel form
    if 'product_detail' in path.lower():
        has_form = 'custom_product_addCartItem' in content
        has_qty  = 'name="quantity"' in content
        has_btn  = 'Add to Cart' in content
        print(f"\n[product_detail] action_panel form={has_form}  qty_input={has_qty}  btn_label={has_btn}")
        if not has_form:
            # show relevant lines
            for i, line in enumerate(content.split('\n')):
                if 'add_to_cart' in line.lower() or 'action_panel' in line.lower():
                    print(f"  {i+1}: {line.strip()[:100]}")

    # view_cart: check CartItem list
    if 'view_cart' in path.lower() or 'cart' in path.lower():
        has_cartitem = 'cartitem' in content.lower() or 'cart_item' in content.lower()
        has_qty = 'quantity' in content
        print(f"\n[view_cart] path={path}")
        print(f"  cartitem_section={has_cartitem}  quantity_field={has_qty}")
        # Show a snippet
        for i, line in enumerate(content.split('\n')):
            if 'quantity' in line.lower() and 'cartitem' in content.lower():
                print(f"  {i+1}: {line.strip()[:100]}")
                break
