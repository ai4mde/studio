from metadata.models import Interface
import json

iface = Interface.objects.get(id='ec58bb5b-fb1a-44c4-b9ff-dbc0c2a8944c')
data = iface.data or {}

# Find the new section
for s in data.get('sections', []):
    if s.get('id') == 'product_detail_product_add_to_cart':
        print("Found section:")
        print(json.dumps(s, indent=2))
        break

# Find product_detail page to show its sections
for p in data.get('pages', []):
    if p.get('id') == 'product_detail':
        print("\nproduct_detail sections:")
        for sec in p.get('sections', []):
            print(f"  {sec}")
