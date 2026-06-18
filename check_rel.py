from metadata.models import Interface
import json

iface = Interface.objects.get(id='ec58bb5b-fb1a-44c4-b9ff-dbc0c2a8944c')
data = iface.data or {}

print("=== product_detail page sections ===")
for p in data.get('pages', []):
    if p.get('id') == 'product_detail':
        print([s.get('value') for s in p.get('sections', [])])

print("\n=== view_cart page sections ===")
for p in data.get('pages', []):
    if 'view_cart' in p.get('id', ''):
        print(p['id'], "->", [s.get('value') for s in p.get('sections', [])])

print("\n=== product_detail_product_add_to_cart section ===")
for s in data.get('sections', []):
    if s.get('id') == 'product_detail_product_add_to_cart':
        print(json.dumps(s, indent=2))

print("\n=== view_cart_cartitem_list section ===")
for s in data.get('sections', []):
    if s.get('id') == 'view_cart_cartitem_list':
        print(json.dumps(s, indent=2))
