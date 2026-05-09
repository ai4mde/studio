import os, sys, django

PROTO_DIR = '/usr/src/prototypes/generated_prototypes/a0000002-0000-5000-8000-000000000000/c'
sys.path.insert(0, PROTO_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'c.settings')
django.setup()

from shared_models.models import (
    Category, Seller, Customer, Product,
    ProductImage, DeliveryOption, Review, RelatedProduct
)

# ── Category ──────────────────────────────────────────────────────────────────
cat = Category.objects.create(
    category_id='cat-001', name='Laptops', slug='laptops',
    parent_category_id='', depth=1
)
print(f'Category: {cat}')

# ── Seller ────────────────────────────────────────────────────────────────────
seller = Seller.objects.create(
    seller_id='sel-001', business_name='TechStore NL',
    rating='4.8', review_count=2341,
    is_verified=True, ships_from='Amsterdam',
    response_time='< 1 hour'
)
print(f'Seller: {seller}')

# ── Customer ──────────────────────────────────────────────────────────────────
customer = Customer.objects.create(
    customer_id='cust-001', email='jan@example.com',
    first_name='Jan', last_name='de Vries',
    phone='+31612345678', is_active=True
)
print(f'Customer: {customer}')

# ── Product ───────────────────────────────────────────────────────────────────
product = Product.objects.create(
    product_id='prod-001',
    name='ASUS VivoBook 15 Laptop',
    brand='ASUS',
    ean='8717306853798',
    description='High-performance laptop with AMD Ryzen 7, 16GB RAM, 512GB SSD and a 15.6" Full HD display. Perfect for work and entertainment.',
    price='€ 699,00',
    original_price='€ 849,00',
    discount_pct=18,
    stock_quantity=47,
    rating='4.3',
    review_count=1284,
    weight_kg='1.8',
    is_active=True,
    Category=cat,
    Seller=seller
)
print(f'Product: {product}')

# ── ProductImage (Gallery) ────────────────────────────────────────────────────
images = [
    ('img-001', 'https://images.unsplash.com/photo-1593642632559-0c6d3fc62b89?w=600&h=600&fit=crop', 'ASUS VivoBook front view', True, 1),
    ('img-002', 'https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=600&h=600&fit=crop', 'Keyboard close-up', False, 2),
    ('img-003', 'https://images.unsplash.com/photo-1525547719571-a2d4ac8945e2?w=600&h=600&fit=crop', 'Side port view', False, 3),
    ('img-004', 'https://images.unsplash.com/photo-1603302576837-37561b2e2302?w=600&h=600&fit=crop', 'Open lid display', False, 4),
    ('img-005', 'https://images.unsplash.com/photo-1484788984921-03950022c9ef?w=600&h=600&fit=crop', 'Touchpad detail', False, 5),
    ('img-006', 'https://images.unsplash.com/photo-1541807084-5c52b6b3adef?w=600&h=600&fit=crop', 'Full setup', False, 6),
]
for iid, thumb, alt, primary, order in images:
    ProductImage.objects.create(
        image_id=iid, product_id=product.product_id,
        thumb_url=thumb, alt_text=alt,
        is_primary=primary, sort_order=order,
        Product=product
    )
print(f'ProductImages: {len(images)} created')

# ── DeliveryOptions ───────────────────────────────────────────────────────────
deliveries = [
    ('del-001', 'Standard Delivery', 2, '€ 3,99', False, '23:00'),
    ('del-002', 'Free Delivery',      3, '€ 0,00', True,  '21:00'),
    ('del-003', 'Express Delivery',   1, '€ 9,99', False, '14:00'),
]
for oid, method, days, cost, free, cutoff in deliveries:
    DeliveryOption.objects.create(
        option_id=oid, product_id=product.product_id,
        method=method, estimated_days=days,
        cost=cost, is_free=free, cutoff_time=cutoff,
        Product=product
    )
print(f'DeliveryOptions: {len(deliveries)} created')

# ── Reviews ───────────────────────────────────────────────────────────────────
reviews = [
    ('rev-001', 5, 'Excellent value!', 'This laptop exceeded my expectations. Fast boot, great display, battery lasts all day.', True),
    ('rev-002', 4, 'Good performance', 'Runs smoothly for daily tasks. Fan gets loud under heavy load but overall satisfied.', True),
    ('rev-003', 5, 'Perfect for students', 'Lightweight and fast. Perfect for university. The screen quality is superb.', False),
    ('rev-004', 3, 'Decent but warm', 'Works fine but runs warm after extended use. Would recommend a cooling pad.', True),
]
for rid, rating, title, body, verified in reviews:
    Review.objects.create(
        review_id=rid, product_id=product.product_id,
        customer_id=customer.customer_id,
        rating=rating, title=title, body=body,
        is_verified_purchase=verified,
        Customer=customer, Product=product
    )
print(f'Reviews: {len(reviews)} created')

# ── RelatedProducts ───────────────────────────────────────────────────────────
related = [
    ('rel-001', 'Lenovo IdeaPad 3', 579),
    ('rel-002', 'HP Pavilion 15', 649),
    ('rel-003', 'Acer Aspire 5', 529),
    ('rel-004', 'Dell Inspiron 15', 719),
]
for rid, name, price in related:
    RelatedProduct.objects.create(
        product_id=rid, name=name, price=price,
        Product=product
    )
print(f'RelatedProducts: {len(related)} created')

print(f'\nDone! Visit /customer/product_detail?instance_id_ProductImage={product.pk} to see gallery with this product\'s images.')
print(f'Or visit /customer/product_detail for all data without gallery filtering.')
