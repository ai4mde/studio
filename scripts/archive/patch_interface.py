import os, sys, django
sys.path.insert(0, '/usr/src/model')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'model.settings')
django.setup()

from metadata.models import Interface, Classifier
import uuid

# 1. Fix RelatedProduct.image_url type
rp = Classifier.objects.get(id='f72b270d-fea0-4160-9168-b3f4324d065d')
for attr in rp.data.get('attributes', []):
    if attr['name'] == 'image_url':
        attr['type'] = 'image'
rp.save()
print('OK: RelatedProduct.image_url -> image')

# 2. Section IDs
ID_GALLERY  = 'ff75e05d-a84e-426a-8565-7ac46d2ef7d6'
ID_PRODUCT  = 'f5b8d016196245e196ee24c9845cf656'
ID_DELIVERY = str(uuid.uuid4())
ID_SELLER   = str(uuid.uuid4())
ID_REVIEWS  = str(uuid.uuid4())
ID_RELATED  = '78f1b83a-0dd5-42db-9ffc-d3325b9a1183'

sections = [
    {
        'id': ID_GALLERY, 'name': 'Product Gallery',
        'class': 'c0000011-0000-5000-8000-000000000000',
        'layout': 'gallery', 'col_span': 6, 'text': '',
        'style': {'color': 'slate', 'density': 'normal', 'columns': '3', 'card_style': 'elevated', 'radius': 'xl'},
        'attributes': [
            {'name': 'image_url', 'type': 'image', 'derived': False, 'enum': None},
            {'name': 'alt_text',  'type': 'str',   'derived': False, 'enum': None},
        ],
        'operations': {'create': False, 'delete': False, 'update': False},
    },
    {
        'id': ID_PRODUCT, 'name': 'Product Info',
        'class': 'c0000002-0000-5000-8000-000000000000',
        'layout': 'detail', 'col_span': 6, 'text': '',
        'style': {'color': 'blue', 'density': 'normal', 'image_position': 'top', 'image_size': 'md', 'radius': 'xl', 'card_style': 'elevated'},
        'attributes': [
            {'name': 'name',           'type': 'str',   'derived': False, 'enum': None},
            {'name': 'brand',          'type': 'str',   'derived': False, 'enum': None},
            {'name': 'price',          'type': 'str',   'derived': False, 'enum': None},
            {'name': 'original_price', 'type': 'str',   'derived': False, 'enum': None},
            {'name': 'discount_pct',   'type': 'int',   'derived': False, 'enum': None},
            {'name': 'rating',         'type': 'str',   'derived': False, 'enum': None},
            {'name': 'review_count',   'type': 'int',   'derived': False, 'enum': None},
            {'name': 'description',    'type': 'str',   'derived': False, 'enum': None},
            {'name': 'stock_quantity', 'type': 'int',   'derived': False, 'enum': None},
            {'name': 'image_url',      'type': 'image', 'derived': False, 'enum': None},
        ],
        'operations': {'create': False, 'delete': False, 'update': False},
    },
    {
        'id': ID_DELIVERY, 'name': 'Delivery Options',
        'class': 'c0000012-0000-5000-8000-000000000000',
        'layout': 'list', 'col_span': 12, 'text': '',
        'style': {'color': 'green', 'density': 'compact', 'columns': '3', 'card_style': 'flat', 'radius': 'lg'},
        'attributes': [
            {'name': 'method',         'type': 'str',  'derived': False, 'enum': None},
            {'name': 'estimated_days', 'type': 'int',  'derived': False, 'enum': None},
            {'name': 'cost',           'type': 'str',  'derived': False, 'enum': None},
            {'name': 'is_free',        'type': 'bool', 'derived': False, 'enum': None},
            {'name': 'cutoff_time',    'type': 'str',  'derived': False, 'enum': None},
        ],
        'operations': {'create': False, 'delete': False, 'update': False},
    },
    {
        'id': ID_SELLER, 'name': 'Seller Info',
        'class': 'c0000004-0000-5000-8000-000000000000',
        'layout': 'card', 'col_span': 12, 'text': '',
        'style': {'color': 'slate', 'density': 'normal', 'columns': '1', 'card_style': 'outlined', 'radius': 'xl'},
        'attributes': [
            {'name': 'business_name', 'type': 'str',  'derived': False, 'enum': None},
            {'name': 'rating',        'type': 'str',  'derived': False, 'enum': None},
            {'name': 'is_verified',   'type': 'bool', 'derived': False, 'enum': None},
            {'name': 'ships_from',    'type': 'str',  'derived': False, 'enum': None},
            {'name': 'response_time', 'type': 'str',  'derived': False, 'enum': None},
        ],
        'operations': {'create': False, 'delete': False, 'update': False},
    },
    {
        'id': ID_REVIEWS, 'name': 'Customer Reviews',
        'class': 'c0000010-0000-5000-8000-000000000000',
        'layout': 'list', 'col_span': 12, 'text': '',
        'style': {'color': 'orange', 'density': 'normal', 'columns': '3', 'card_style': 'elevated', 'radius': 'xl'},
        'attributes': [
            {'name': 'rating',               'type': 'int',  'derived': False, 'enum': None},
            {'name': 'title',                'type': 'str',  'derived': False, 'enum': None},
            {'name': 'body',                 'type': 'str',  'derived': False, 'enum': None},
            {'name': 'is_verified_purchase', 'type': 'bool', 'derived': False, 'enum': None},
            {'name': 'created_at',           'type': 'str',  'derived': False, 'enum': None},
        ],
        'operations': {'create': True, 'delete': False, 'update': False},
    },
    {
        'id': ID_RELATED, 'name': 'Related Products',
        'class': 'f72b270d-fea0-4160-9168-b3f4324d065d',
        'layout': 'card', 'col_span': 12, 'text': '',
        'style': {'color': 'blue', 'density': 'normal', 'columns': '4', 'card_style': 'elevated', 'radius': 'xl'},
        'attributes': [
            {'name': 'image_url', 'type': 'image', 'derived': False, 'enum': None},
            {'name': 'name',      'type': 'str',   'derived': False, 'enum': None},
            {'name': 'price',     'type': 'int',   'derived': False, 'enum': None},
        ],
        'operations': {'create': False, 'delete': False, 'update': False},
    },
]

page = {
    'id': '1e719f407ebf4cbbb4b125ffb6492b29',
    'name': 'Product Detail',
    'type': {'label': 'Normal', 'value': 'normal'},
    'layout': {'label': 'Down', 'value': 'vertical'},
    'gap': {'label': 'Normal', 'value': 'normal'},
    'category': {'label': 'Product', 'value': {'id': '9ce7c462692540c19e546f1b60dba1c8', 'name': 'Product'}},
    'action': None,
    'single_record': True,
    'sections': [{'label': s['name'], 'value': s['id']} for s in sections],
}

iface = Interface.objects.get(id='ec58bb5b-fb1a-44c4-b9ff-dbc0c2a8944c')
iface.data = {**iface.data, 'sections': sections, 'pages': [page]}
iface.save()

print('OK: interface patched')
print(f'  page: {page["name"]}  single_record={page["single_record"]}')
for s in sections:
    print(f'  [{s["col_span"]:>2}col] {s["layout"]:8}  {s["name"]}')
