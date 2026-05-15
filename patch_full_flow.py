import os, sys, django, uuid
sys.path.insert(0, '/usr/src/model')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'model.settings')
django.setup()

from metadata.models import Interface

# ─── helpers ──────────────────────────────────────────────────────────────────
def sid(): return str(uuid.uuid4())

def attr(name, type_='str', derived=False, enum=None):
    return {'name': name, 'type': type_, 'derived': derived, 'enum': enum}

def ops(create=False, update=False, delete=False):
    return {'create': create, 'update': update, 'delete': delete}

def style(color, density='normal', card_style='elevated', columns='3',
          radius='xl', image_position='top', image_size='md'):
    return {
        'color': color, 'density': density, 'card_style': card_style,
        'columns': columns, 'radius': radius,
        'image_position': image_position, 'image_size': image_size,
    }

def sec(name, cls, layout, col_span, color, attrs, operations,
        density='normal', columns='3', card_style='elevated',
        radius='xl', text='', image_position='top', image_size='md',
        view_detail_page=None):
    d = {
        'id': sid(),
        'name': name,
        'class': cls,
        'layout': layout,
        'col_span': col_span,
        'text': text,
        'style': style(color, density, card_style, columns, radius, image_position, image_size),
        'attributes': attrs,
        'operations': operations,
    }
    if view_detail_page:
        d['view_detail_page'] = view_detail_page
    return d

def page(name, sections, type_='normal', single_record=False,
         layout='vertical', gap='normal', action=None, category=None):
    return {
        'id': sid().replace('-', ''),
        'name': name,
        'type': {'label': type_.title(), 'value': type_},
        'layout': {'label': layout.title(), 'value': layout},
        'gap': {'label': gap.title(), 'value': gap},
        'category': category,
        'action': action,
        'single_record': single_record,
        'sections': [{'label': s['name'], 'value': s['id']} for s in sections],
    }

def activity_action(node_id, name):
    # node_id must be the diagram node UUID (f0000202...), not the classifier UUID
    return {'label': name, 'value': node_id}

# ═══════════════════════════════════════════════════════════════════════════════
# CUSTOMER INTERFACE
# ═══════════════════════════════════════════════════════════════════════════════
C_IFACE_ID = 'ec58bb5b-fb1a-44c4-b9ff-dbc0c2a8944c'

# Keep existing Product Detail sections (IDs stay the same for stability)
existing_gallery  = {'id': 'ff75e05d-a84e-426a-8565-7ac46d2ef7d6', 'name': 'Product Gallery',  'class': 'c0000011-0000-5000-8000-000000000000', 'layout': 'gallery',  'col_span': 6,  'text': '', 'style': style('blue',   columns='3'), 'attributes': [attr('thumb_url','image'), attr('alt_text')],              'operations': ops()}
existing_product  = {'id': 'f5b8d016196245e196ee24c9845cf656',        'name': 'Product Info',    'class': 'c0000002-0000-5000-8000-000000000000', 'layout': 'detail',  'col_span': 6,  'text': '', 'style': style('blue',   image_position='top', image_size='md'), 'attributes': [attr('name'), attr('brand'), attr('price'), attr('original_price'), attr('discount_pct','int'), attr('rating'), attr('review_count','int'), attr('description'), attr('stock_quantity','int'), attr('image_url','image')], 'operations': ops()}
existing_delivery = {'id': '25871a09-7b35-4a25-bc5c-b340b889f509',   'name': 'Delivery Options','class': 'c0000012-0000-5000-8000-000000000000', 'layout': 'list',    'col_span': 12, 'text': '', 'style': style('green',  density='compact', columns='3', card_style='flat'), 'attributes': [attr('method'), attr('estimated_days','int'), attr('cost'), attr('is_free','bool'), attr('cutoff_time')], 'operations': ops()}
existing_seller   = {'id': '41e4c4b5-08ed-4e5d-8b35-bfe468fa6485',   'name': 'Seller Info',     'class': 'c0000004-0000-5000-8000-000000000000', 'layout': 'card',    'col_span': 12, 'text': '', 'style': style('slate',  columns='1', card_style='outlined'), 'attributes': [attr('business_name'), attr('rating'), attr('is_verified','bool'), attr('ships_from'), attr('response_time')], 'operations': ops()}
existing_reviews  = {'id': 'ea3b8dd1-446e-4623-9828-77156d639e1c',   'name': 'Customer Reviews','class': 'c0000010-0000-5000-8000-000000000000', 'layout': 'list',    'col_span': 12, 'text': '', 'style': style('orange', columns='3'), 'attributes': [attr('rating','int'), attr('title'), attr('body'), attr('is_verified_purchase','bool')], 'operations': ops(create=True)}
existing_related  = {'id': '78f1b83a-0dd5-42db-9ffc-d3325b9a1183',   'name': 'Related Products','class': 'f72b270d-fea0-4160-9168-b3f4324d065d', 'layout': 'card',    'col_span': 12, 'text': '', 'style': style('blue',   columns='4'), 'attributes': [attr('image_url','image'), attr('name'), attr('price','int')], 'operations': ops(), 'related_to': existing_product['id'], 'query': {'limit': 4}}

# ── Home: Product Browsing ────────────────────────────────────────────────────
s_product_list = sec(
    'Product List', 'c0000002-0000-5000-8000-000000000000',
    'card', 12, 'blue',
    [attr('image_url','image'), attr('name'), attr('brand'), attr('price'),
     attr('original_price'), attr('rating'), attr('discount_pct','int')],
    ops(), columns='4', card_style='elevated',
    view_detail_page='Product Detail',
)
s_category_filter = sec(
    'Categories', 'c0000003-0000-5000-8000-000000000000',
    'list', 3, 'slate',
    [attr('name'), attr('slug')],
    ops(), density='compact', card_style='flat',
)
s_featured = sec(
    'Featured Products', 'c0000002-0000-5000-8000-000000000000',
    'card', 9, 'blue',
    [attr('image_url','image'), attr('name'), attr('price'), attr('rating')],
    ops(), columns='3', card_style='elevated',
    view_detail_page='Product Detail',
)

# ── Product Detail: Add to Cart ───────────────────────────────────────────────
s_add_to_cart = sec(
    'Add to Cart', 'c0000006-0000-5000-8000-000000000000',
    'card', 12, 'orange',
    [attr('quantity','int'), attr('unit_price')],
    ops(create=True), columns='1', card_style='elevated',
)

# ── Shopping Cart ─────────────────────────────────────────────────────────────
s_cart_items = sec(
    'Cart Items', 'c0000006-0000-5000-8000-000000000000',
    'list', 8, 'orange',
    [attr('product_id'), attr('quantity','int'), attr('unit_price'), attr('subtotal')],
    ops(update=True, delete=True), density='normal', card_style='elevated',
)
s_cart_summary = sec(
    'Order Summary', 'c0000005-0000-5000-8000-000000000000',
    'detail', 4, 'slate',
    [attr('item_count','int'), attr('total_price')],
    ops(), columns='1', card_style='outlined',
)

# ── Checkout – Delivery Address ───────────────────────────────────────────────
s_delivery_address = sec(
    'Delivery Address', 'c0000013-0000-5000-8000-000000000000',
    'detail', 8, 'blue',
    [attr('street'), attr('house_number'), attr('city'), attr('postal_code'), attr('country')],
    ops(create=True, update=True), columns='1', card_style='elevated',
)
s_checkout_summary = sec(
    'Order Summary', 'c0000005-0000-5000-8000-000000000000',
    'detail', 4, 'slate',
    [attr('item_count','int'), attr('total_price')],
    ops(), columns='1', card_style='outlined',
)

# ── Checkout – Payment ────────────────────────────────────────────────────────
s_payment_methods = sec(
    'Payment Method', 'c0000009-0000-5000-8000-000000000000',
    'card', 8, 'purple',
    [attr('method'), attr('amount'), attr('currency')],
    ops(create=True), columns='3', card_style='elevated',
)
s_payment_summary = sec(
    'Payment Summary', 'c0000009-0000-5000-8000-000000000000',
    'detail', 4, 'slate',
    [attr('method'), attr('amount'), attr('currency')],
    ops(), columns='1', card_style='outlined',
)

# ── Order Confirmation ────────────────────────────────────────────────────────
s_order_confirm = sec(
    'Order Confirmed', 'c0000007-0000-5000-8000-000000000000',
    'detail', 12, 'green',
    [attr('order_id'), attr('status'), attr('total_amount'), attr('shipping_address_id')],
    ops(), columns='1', card_style='elevated', density='spacious',
)
s_order_lines = sec(
    'Your Items', 'c0000008-0000-5000-8000-000000000000',
    'list', 12, 'slate',
    [attr('product_id'), attr('quantity','int'), attr('unit_price'), attr('subtotal')],
    ops(), card_style='flat',
)

# ── Build Customer pages ───────────────────────────────────────────────────────
cat_product = {'label': 'Product', 'value': {'id': '9ce7c462692540c19e546f1b60dba1c8', 'name': 'Product'}}

p_home = page(
    'Browse Products',
    [s_category_filter, s_featured],
    type_='normal', layout='vertical', gap='normal',
)
p_product_detail = page(
    'Product Detail',
    [existing_product, existing_gallery, s_add_to_cart,
     existing_delivery, existing_seller, existing_reviews, existing_related],
    type_='normal', single_record=True,
    layout='vertical', gap='normal', category=cat_product,
)
p_cart = page(
    'Shopping Cart',
    [s_cart_items, s_cart_summary],
    type_='activity', layout='vertical', gap='normal',
    action=activity_action('f0000202-0000-5000-8000-000000000000', 'View Cart'),
)
p_checkout_address = page(
    'Checkout – Address',
    [s_delivery_address, s_checkout_summary],
    type_='activity', layout='vertical', gap='normal',
    action=activity_action('f0000204-0000-5000-8000-000000000000', 'Enter Shipping Address'),
)
p_checkout_payment = page(
    'Checkout – Payment',
    [s_payment_methods, s_payment_summary],
    type_='activity', layout='vertical', gap='normal',
    action=activity_action('f0000205-0000-5000-8000-000000000000', 'Select Payment Method'),
)
p_order_confirm = page(
    'Order Confirmation',
    [s_order_confirm, s_order_lines],
    type_='activity', layout='vertical', gap='normal',
    action=activity_action('f0000208-0000-5000-8000-000000000000', 'Create Order'),
)

customer_sections = [
    existing_gallery, existing_product, existing_delivery, existing_seller,
    existing_reviews, existing_related,
    s_product_list, s_category_filter, s_featured,
    s_add_to_cart,
    s_cart_items, s_cart_summary,
    s_delivery_address, s_checkout_summary,
    s_payment_methods, s_payment_summary,
    s_order_confirm, s_order_lines,
]
customer_pages = [
    p_home, p_product_detail,
    p_cart, p_checkout_address, p_checkout_payment, p_order_confirm,
]

iface_c = Interface.objects.get(id=C_IFACE_ID)
iface_c.data = {**iface_c.data, 'sections': customer_sections, 'pages': customer_pages}
iface_c.save()
print('✓ Customer interface patched')
for p in customer_pages:
    print(f'  PAGE: {p["name"]}  type={p["type"]["value"]}')
for s in customer_sections:
    print(f'  SEC [{s["col_span"]:>2}col] {s["layout"]:8}  {s["name"]}')


# ═══════════════════════════════════════════════════════════════════════════════
# SELLER INTERFACE
# ═══════════════════════════════════════════════════════════════════════════════
S_IFACE_ID = '26608863-59e7-41eb-bc17-5221c6d2ea38'

# ── Seller sections ────────────────────────────────────────────────────────────
s_my_products = sec(
    'My Products', 'c0000002-0000-5000-8000-000000000000',
    'table', 12, 'blue',
    [attr('name'), attr('brand'), attr('price'), attr('original_price'),
     attr('stock_quantity','int'), attr('rating'), attr('is_active','bool')],
    ops(create=True, update=True, delete=True),
)
s_product_edit = sec(
    'Edit Product', 'c0000002-0000-5000-8000-000000000000',
    'detail', 12, 'blue',
    [attr('image_url','image'), attr('name'), attr('brand'), attr('description'),
     attr('price'), attr('original_price'), attr('discount_pct','int'),
     attr('stock_quantity','int'), attr('is_active','bool')],
    ops(update=True), columns='1', card_style='outlined',
)
s_incoming_orders = sec(
    'Incoming Orders', 'c0000007-0000-5000-8000-000000000000',
    'table', 12, 'orange',
    [attr('order_id'), attr('status'), attr('total_amount'), attr('customer_id'), attr('shipping_address_id')],
    ops(update=True),
)
s_order_detail = sec(
    'Order Detail', 'c0000007-0000-5000-8000-000000000000',
    'detail', 6, 'orange',
    [attr('order_id'), attr('status'), attr('total_amount'), attr('shipping_address_id')],
    ops(update=True), columns='1', card_style='elevated',
)
s_order_lines_seller = sec(
    'Order Items', 'c0000008-0000-5000-8000-000000000000',
    'list', 6, 'slate',
    [attr('product_id'), attr('quantity','int'), attr('unit_price'), attr('subtotal')],
    ops(), card_style='flat',
)
s_seller_stats = sec(
    'Sales Overview', 'c0000004-0000-5000-8000-000000000000',
    'card', 12, 'green',
    [attr('business_name'), attr('rating'), attr('review_count','int'),
     attr('is_verified','bool'), attr('ships_from'), attr('response_time')],
    ops(update=True), columns='2', card_style='elevated',
)

# ── Seller pages ───────────────────────────────────────────────────────────────
sp_dashboard = page(
    'Seller Dashboard',
    [s_seller_stats, s_my_products, s_incoming_orders],
    type_='normal', layout='vertical', gap='normal',
)
sp_product_mgmt = page(
    'Product Management',
    [s_product_edit],
    type_='normal', single_record=True, layout='vertical', gap='normal',
)
sp_order_mgmt = page(
    'Order Management',
    [s_order_detail, s_order_lines_seller],
    type_='activity', layout='vertical', gap='normal',
    action=activity_action('f0000209-0000-5000-8000-000000000000', 'Send Order Confirmation'),
)

seller_sections = [
    s_my_products, s_product_edit,
    s_incoming_orders, s_order_detail, s_order_lines_seller,
    s_seller_stats,
]
seller_pages = [sp_dashboard, sp_product_mgmt, sp_order_mgmt]

iface_s = Interface.objects.get(id=S_IFACE_ID)
prev_data = iface_s.data or {}
iface_s.data = {**prev_data, 'sections': seller_sections, 'pages': seller_pages}
iface_s.save()
print('\n✓ Seller interface patched')
for p in seller_pages:
    print(f'  PAGE: {p["name"]}  type={p["type"]["value"]}')
for s in seller_sections:
    print(f'  SEC [{s["col_span"]:>2}col] {s["layout"]:8}  {s["name"]}')

print('\nDone.')
