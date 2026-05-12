import os, sys, django
sys.path.insert(0, '/usr/src/model')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'model.settings')
django.setup()

from metadata.models import Classifier, Relation, System
from diagram.models import Diagram, Node, Edge

SYSTEM_ID  = 'a0000002-0000-5000-8000-000000000000'
PROJECT_ID = 'f3d1c958-af29-45b5-82cd-9145f5912423'
DIAGRAM_ID = 'd0000003-0000-5000-8000-000000000000'

system  = System.objects.get(id=SYSTEM_ID)
diagram = Diagram.objects.get(id=DIAGRAM_ID)

# ── 1. Create 3 new action classifiers ───────────────────────────────────────

new_classifiers = [
    {
        'id':   'ac000013-0000-5000-8000-000000000000',
        'name': 'Browse Products',
        'classes': ['Product', 'Category'],
        'actorNode': 'b0000002-0000-5000-8000-000000000000',
        'actorNodeName': 'Customer',
        'localPrecondition': 'Customer is on the homepage or search page',
        'localPostcondition': 'Customer sees a list of matching products',
    },
    {
        'id':   'ac000014-0000-5000-8000-000000000000',
        'name': 'View Product Detail',
        'classes': ['Product', 'ProductImage', 'DeliveryOption', 'Review'],
        'actorNode': 'b0000002-0000-5000-8000-000000000000',
        'actorNodeName': 'Customer',
        'localPrecondition': 'Customer has selected a product from the list',
        'localPostcondition': 'Customer views full product information including images, specs, and reviews',
    },
    {
        'id':   'ac000015-0000-5000-8000-000000000000',
        'name': 'Add to Cart',
        'classes': ['Cart', 'CartItem', 'Product'],
        'actorNode': 'b0000002-0000-5000-8000-000000000000',
        'actorNodeName': 'Customer',
        'localPrecondition': 'Customer is logged in and product is in stock',
        'localPostcondition': 'Product is added to the customer\'s cart',
    },
]

positions = {
    'ac000013-0000-5000-8000-000000000000': {'x': 300, 'y': -260},
    'ac000014-0000-5000-8000-000000000000': {'x': 300, 'y': -140},
    'ac000015-0000-5000-8000-000000000000': {'x': 300, 'y': -20},
}

for c in new_classifiers:
    cls_obj, created = Classifier.objects.get_or_create(
        id=c['id'],
        defaults={
            'project': system.project,
            'system':  system,
            'data': {
                'body': '',
                'name': c['name'],
                'page': None,
                'role': 'action',
                'type': 'action',
                'classes': c['classes'],
                'publish': None,
                'actorNode': c['actorNode'],
                'namespace': '',
                'operation': None,
                'subscribe': None,
                'customCode': None,
                'isAutomatic': False,
                'actorNodeName': c['actorNodeName'],
                'localPrecondition': c['localPrecondition'],
                'application_models': None,
                'localPostcondition': c['localPostcondition'],
            }
        }
    )
    pos = positions[c['id']]
    node_obj, _ = Node.objects.get_or_create(
        diagram=diagram,
        cls=cls_obj,
        defaults={'data': {'position': pos}}
    )
    print(f"{'Created' if created else 'Exists ':7} classifier: {c['name']}  node y={pos['y']}")

# ── 2. Move Initial node up to y=-380 ────────────────────────────────────────

initial_cls = Classifier.objects.get(id='ac000001-0000-5000-8000-000000000000')
initial_node = Node.objects.get(diagram=diagram, cls=initial_cls)
if initial_node.data['position']['y'] != -380:
    initial_node.data['position']['y'] = -380
    initial_node.save()
    print('Updated Initial node position → y=-380')
else:
    print('Initial node already at y=-380')

# ── 3. Update relation 10000201: Initial → Browse Products ───────────────────

ac000013 = Classifier.objects.get(id='ac000013-0000-5000-8000-000000000000')
rel_201 = Relation.objects.get(id='10000201-0000-5000-8000-000000000000')
if str(rel_201.target_id) != 'ac000013-0000-5000-8000-000000000000':
    rel_201.target = ac000013
    rel_201.save()
    print('Updated relation 10000201 target → Browse Products')
else:
    print('Relation 10000201 already points to Browse Products')

# ── 4. Create 3 new relations & edges ────────────────────────────────────────

ac000014 = Classifier.objects.get(id='ac000014-0000-5000-8000-000000000000')
ac000015 = Classifier.objects.get(id='ac000015-0000-5000-8000-000000000000')
ac000002 = Classifier.objects.get(id='ac000002-0000-5000-8000-000000000000')

controlflow_data = {
    'type': 'controlflow',
    'guard': '',
    'weight': '',
    'condition': None,
    'is_directed': True,
    'position_handlers': [],
}

new_relations = [
    ('10000213-0000-5000-8000-000000000000', ac000013, ac000014),
    ('10000214-0000-5000-8000-000000000000', ac000014, ac000015),
    ('10000215-0000-5000-8000-000000000000', ac000015, ac000002),
]

for rel_id, src, tgt in new_relations:
    rel_obj, created = Relation.objects.get_or_create(
        id=rel_id,
        defaults={
            'system': system,
            'source': src,
            'target': tgt,
            'data':   controlflow_data,
        }
    )
    edge_obj, edge_created = Edge.objects.get_or_create(
        diagram=diagram,
        rel=rel_obj,
        defaults={'data': {}}
    )
    print(f"{'Created' if created else 'Exists ':7} relation {rel_id[:12]}…  edge={'new' if edge_created else 'exists'}")

print('\nDone.')
